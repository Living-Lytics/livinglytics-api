import os
import json
import logging
import requests
import hmac
import hashlib
import uuid
import time
import random
import threading
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Any, Optional, List
from collections import defaultdict
from fastapi import FastAPI, Depends, HTTPException, Header, Body, Request, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from urllib.parse import urlencode
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import select, func, text, cast, DATE
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from db import get_db, engine
from models import Base, User, Metric, DigestLog, EmailEvent, DataSource, GA4Property
from github import Github, GithubException
from mailer import send_email_resend
from scheduler_utils import (
    get_last_completed_week,
    send_weekly_digest,
    run_weekly_digests,
    verify_unsubscribe_token,
    PT
)
from auth.router import router as auth_router

# Configure structured logging with JSON format
logging.basicConfig(
    level=logging.INFO,
    format='{"level":"%(levelname)s","ts":"%(asctime)s","message":"%(message)s"}'
)

# Optional Sentry integration
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=0.1,
            environment=os.getenv("ENV", "development")
        )
        logging.info("[SENTRY] Initialized successfully")
    except ImportError:
        logging.warning("[SENTRY] sentry-sdk not installed, skipping")
    except Exception as e:
        logging.error(f"[SENTRY] Failed to initialize: {e}")

APP_NAME = os.getenv("APP_NAME", "Living Lytics API")
API_KEY = os.getenv("FASTAPI_SECRET_KEY")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

# Instagram OAuth configuration (via Meta/Facebook)
META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")
META_OAUTH_REDIRECT = os.getenv("META_OAUTH_REDIRECT")

if not API_KEY:
    raise RuntimeError("FASTAPI_SECRET_KEY not set")
if not ADMIN_TOKEN:
    logging.warning("⚠️  ADMIN_TOKEN not set - admin endpoints will be inaccessible")

# Validate Instagram OAuth configuration
missing_meta_keys = []
if not META_APP_ID:
    missing_meta_keys.append("META_APP_ID")
if not META_APP_SECRET:
    missing_meta_keys.append("META_APP_SECRET")
if not META_OAUTH_REDIRECT:
    missing_meta_keys.append("META_OAUTH_REDIRECT")

if missing_meta_keys:
    logging.warning(f"[OAUTH-CONFIG] Missing Instagram OAuth secrets: {', '.join(missing_meta_keys)} - Instagram integration will be unavailable")
else:
    logging.info(f"[OAUTH-CONFIG] Instagram OAuth configured with redirect: {META_OAUTH_REDIRECT}")

app = FastAPI(title=APP_NAME)

ALLOW_ORIGINS = [
    "https://livinglytics.base44.app",
    "https://preview--livinglytics.base44.app",  # Base44 preview domain
    "https://livinglytics.com",
    "https://www.livinglytics.com",
    "http://localhost:5173",
]

# CORS middleware with support for Replit domains (*.replit.dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_origin_regex=r"https://.*\.replit\.dev",  # Match all Replit dev domains
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)

# Mount auth router
app.include_router(auth_router)

# Request ID middleware for structured logging
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request_id to all requests for tracing."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Simple in-memory rate limiter for admin endpoints (thread-safe)
class InMemoryRateLimiter:
    """Thread-safe token bucket rate limiter for admin endpoints."""
    def __init__(self, capacity: int = 10, refill_rate: float = 1.0):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.buckets = defaultdict(lambda: {"tokens": capacity, "last_refill": time.time()})
        self.lock = threading.Lock()
    
    def allow(self, key: str, tokens: int = 1) -> bool:
        """Check if request is allowed under rate limit (thread-safe)."""
        with self.lock:
            bucket = self.buckets[key]
            now = time.time()
            
            # Refill tokens based on time elapsed
            elapsed = now - bucket["last_refill"]
            bucket["tokens"] = min(
                self.capacity,
                bucket["tokens"] + elapsed * self.refill_rate
            )
            bucket["last_refill"] = now
            
            # Check if enough tokens available
            if bucket["tokens"] >= tokens:
                bucket["tokens"] -= tokens
                return True
            return False

rate_limiter = InMemoryRateLimiter(capacity=10, refill_rate=0.5)  # 10 requests, refill 1 every 2 seconds

# Initialize APScheduler
scheduler = AsyncIOScheduler(timezone=PT)

def scheduled_digest_job():
    """Scheduled job to run weekly digests for all opted-in users."""
    logging.info("[SCHEDULER JOB] Starting scheduled weekly digest run")
    db = next(get_db())
    try:
        result = run_weekly_digests(db)
        logging.info(f"[SCHEDULER JOB] Complete: {result}")
    except Exception as e:
        logging.error(f"[SCHEDULER JOB] Error: {str(e)}")
    finally:
        db.close()

@app.on_event("startup")
def on_startup():
    """Initialize database tables, indexes, constraints, and start scheduler on startup."""
    # Log OAuth configuration
    google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "https://api.livinglytics.com/v1/auth/google/callback")
    print("\n" + "="*60)
    print("[OAUTH-CONFIG] Google OAuth Redirect URI Configuration")
    print("="*60)
    print(f"GOOGLE_REDIRECT_URI = {google_redirect_uri}")
    print("\nTo configure Google Cloud Console:")
    print("  1. Go to: https://console.cloud.google.com/apis/credentials")
    print("  2. Edit your OAuth 2.0 Client ID")
    print("  3. Add to 'Authorized redirect URIs':")
    print(f"     {google_redirect_uri}")
    print("="*60 + "\n")
    
    # Create ga4_properties table
    try:
        # Import here to ensure all models are loaded
        from models import GA4Property
        # Create ga4_properties table
        Base.metadata.create_all(bind=engine, tables=[GA4Property.__table__], checkfirst=True)
        logging.info("[STARTUP] GA4 properties table created/verified")
    except Exception as e:
        logging.error(f"[STARTUP] Failed to create ga4_properties table: {e}")
    
    # Add auth columns to users table (idempotent)
    try:
        with engine.connect() as conn:
            # Add password_hash column if it doesn't exist
            conn.execute(text("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT NULL
            """))
            # Add google_sub column if it doesn't exist
            conn.execute(text("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS google_sub TEXT NULL
            """))
            # Add unique constraint on google_sub (will fail silently if exists)
            try:
                conn.execute(text("""
                    ALTER TABLE users ADD CONSTRAINT users_google_sub_key UNIQUE (google_sub)
                """))
            except Exception:
                pass  # Constraint already exists
            
            conn.commit()
            logging.info("[STARTUP] Auth columns added/verified on users table")
    except Exception as e:
        logging.error(f"[STARTUP] Failed to add auth columns: {str(e)}")
    
    # Create indexes
    try:
        with engine.connect() as conn:
            # Create unique index on provider_id for idempotent webhook processing
            conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS email_events_provider_unique 
                ON email_events(provider_id)
            """))
            conn.commit()
            logging.info("[STARTUP] Created unique index on email_events.provider_id")
    except Exception as e:
        logging.error(f"[STARTUP] Failed to create index: {str(e)}")
    
    # Start scheduler
    try:
        # Schedule weekly digest: Every Monday at 07:00 PT
        scheduler.add_job(
            scheduled_digest_job,
            CronTrigger(day_of_week='mon', hour=7, minute=0, timezone=PT),
            id='weekly_digest',
            name='Weekly Digest Send',
            replace_existing=True
        )
        scheduler.start()
        logging.info("[SCHEDULER] Started with weekly digest job (Monday 07:00 PT)")
    except Exception as e:
        logging.error(f"[SCHEDULER] Failed to start: {str(e)}")

@app.on_event("shutdown")
def on_shutdown():
    """Shut down scheduler gracefully."""
    try:
        scheduler.shutdown()
        logging.info("[SCHEDULER] Shut down successfully")
    except Exception as e:
        logging.error(f"[SCHEDULER] Error during shutdown: {str(e)}")

def require_api_key(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    if token != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid token")

def require_admin_token(authorization: str = Header(None)):
    """Require admin token for sensitive operations."""
    if not ADMIN_TOKEN:
        raise HTTPException(status_code=503, detail="Admin operations unavailable - ADMIN_TOKEN not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden - admin access required")
    return True

def get_github_access_token():
    """Fetch GitHub access token from Replit connector service."""
    hostname = os.getenv("REPLIT_CONNECTORS_HOSTNAME")
    
    repl_identity = os.getenv("REPL_IDENTITY")
    web_repl_renewal = os.getenv("WEB_REPL_RENEWAL")
    
    if repl_identity:
        x_replit_token = f"repl {repl_identity}"
    elif web_repl_renewal:
        x_replit_token = f"depl {web_repl_renewal}"
    else:
        x_replit_token = None
    
    if not hostname or not x_replit_token:
        raise HTTPException(status_code=503, detail="GitHub integration not available in this environment")
    
    try:
        response = requests.get(
            f"https://{hostname}/api/v2/connection?include_secrets=true&connector_names=github",
            headers={
                "Accept": "application/json",
                "X_REPLIT_TOKEN": x_replit_token
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if not data.get("items"):
            raise HTTPException(status_code=503, detail="GitHub not connected. Please connect GitHub in the integrations panel.")
        
        connection = data["items"][0]
        access_token = connection.get("settings", {}).get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=503, detail="GitHub access token not available")
        
        return access_token
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch GitHub token: {str(e)}")

def get_github_client():
    """Dependency to get authenticated GitHub client."""
    token = get_github_access_token()
    return Github(token)

@app.get("/", include_in_schema=False)
def root():
    return {"message": "Living Lytics API", "docs": "/docs"}

@app.get("/v1/health/liveness")
def liveness():
    return {"status": "ok"}

@app.get("/v1/health/readiness")
def readiness():
    try:
        with engine.begin() as conn:
            conn.execute(text("select 1"))
        db_ready = True
    except Exception:
        db_ready = False
    
    env_ready = bool(
        API_KEY and 
        (os.getenv("SUPABASE_CONNECTION_POOLER_URL") or os.getenv("DATABASE_URL")) and 
        os.getenv("SUPABASE_PROJECT_URL") and 
        os.getenv("SUPABASE_ANON_KEY")
    )
    
    ready = db_ready and env_ready
    return {"ready": ready, "database": db_ready, "environment": env_ready}

@app.post("/v1/dev/seed-user", dependencies=[Depends(require_api_key)])
def seed_user(email: str, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
        return {"created": True}
    return {"created": False}

class MetricIngestRequest(BaseModel):
    email: str
    source_name: str
    metric_date: str
    data: Dict[str, Any] = Field(default_factory=dict)

@app.post("/v1/metrics/ingest", dependencies=[Depends(require_api_key)])
def ingest_metrics(request: MetricIngestRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == request.email)).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    
    try:
        metric_date = date.fromisoformat(request.metric_date)
    except ValueError:
        raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")
    
    ingested_metrics = []
    for metric_name, metric_value in request.data.items():
        try:
            value = float(metric_value)
            metric = Metric(
                user_id=user.id,
                source_name=request.source_name,
                metric_date=metric_date,
                metric_name=metric_name,
                metric_value=value
            )
            db.add(metric)
            ingested_metrics.append(metric_name)
        except (ValueError, TypeError):
            continue
    
    db.commit()
    return {"ingested": len(ingested_metrics), "metrics": ingested_metrics}

@app.get("/v1/dashboard/tiles", dependencies=[Depends(require_api_key)])
def tiles(email: str, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    
    def agg(name: str):
        return db.execute(
            select(func.coalesce(func.sum(Metric.metric_value), 0)).where(
                Metric.user_id == user.id,
                Metric.metric_name == name
            )
        ).scalar() or 0
    
    return {
        "ig_sessions": float(agg("sessions")),
        "ig_conversions": float(agg("conversions")),
        "ig_reach": float(agg("reach")),
        "ig_engagement": float(agg("engagement")),
    }

@app.get("/v1/github/user", dependencies=[Depends(require_api_key)])
def github_user():
    """Get authenticated GitHub user information."""
    try:
        gh = get_github_client()
        user = gh.get_user()
        
        return {
            "username": user.login,
            "name": user.name,
            "email": user.email,
            "bio": user.bio,
            "company": user.company,
            "location": user.location,
            "public_repos": user.public_repos,
            "followers": user.followers,
            "following": user.following,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "avatar_url": user.avatar_url,
            "html_url": user.html_url
        }
    except GithubException as e:
        message = e.data.get("message", str(e)) if isinstance(e.data, dict) else str(e)
        raise HTTPException(status_code=e.status, detail=f"GitHub API error: {message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching GitHub user: {str(e)}")

@app.get("/v1/github/repos", dependencies=[Depends(require_api_key)])
def github_repos(limit: int = 30):
    """Get list of GitHub repositories for authenticated user (limited to 100 max)."""
    limit = min(limit, 100)
    try:
        gh = get_github_client()
        user = gh.get_user()
        all_repos = user.get_repos(sort="updated", direction="desc")
        
        result = []
        for repo in all_repos:
            if repo.private:
                continue
            if len(result) >= limit:
                break
            result.append({
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "html_url": repo.html_url,
                "clone_url": repo.clone_url,
                "private": repo.private,
                "fork": repo.fork,
                "language": repo.language,
                "stargazers_count": repo.stargazers_count,
                "forks_count": repo.forks_count,
                "open_issues_count": repo.open_issues_count,
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None
            })
        
        return {
            "total_public_repos": user.public_repos,
            "returned_count": len(result),
            "repositories": result
        }
    except GithubException as e:
        message = e.data.get("message", str(e)) if isinstance(e.data, dict) else str(e)
        raise HTTPException(status_code=e.status, detail=f"GitHub API error: {message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching GitHub repos: {str(e)}")

# Digest Request Models
class DigestRequest(BaseModel):
    scope: str = Field(default="email", description="Scope: 'email' for single user or 'all' for all users")
    email: Optional[EmailStr] = Field(default=None, description="Email address when scope='email'")

class DigestRunRequest(BaseModel):
    user_email: EmailStr = Field(description="User email address")
    days: int = Field(default=7, ge=1, le=90, description="Number of days to include in digest (1-90)")

class DigestRunAllRequest(BaseModel):
    days: int = Field(default=7, ge=1, le=90, description="Number of days to include in digest (1-90)")

class SeedMetricsRequest(BaseModel):
    email: EmailStr
    days: int = Field(default=14, ge=1, le=365, description="Number of days to seed (1-365)")

class SeedEmailEventsRequest(BaseModel):
    email: EmailStr
    events: int = Field(default=50, ge=1, le=500, description="Number of events to seed (1-500)")
    start: Optional[str] = Field(default=None, description="Start date (YYYY-MM-DD)")
    end: Optional[str] = Field(default=None, description="End date (YYYY-MM-DD)")

# Helper functions for digest
def _collect_kpis_for_user(email: str, start_date: date, end_date: date, db: Session) -> Dict[str, float]:
    """Collect KPIs for a user within the date range."""
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        return {"ig_sessions": 0.0, "ig_conversions": 0.0, "ig_reach": 0.0, "ig_engagement": 0.0}
    
    # Query metrics for the date range
    metrics = db.execute(
        select(Metric.metric_name, func.sum(Metric.metric_value).label("total"))
        .where(Metric.user_id == user.id)
        .where(Metric.metric_date >= start_date)
        .where(Metric.metric_date <= end_date)
        .group_by(Metric.metric_name)
    ).all()
    
    # Map metric names from database (without prefix) to KPI keys (with ig_ prefix)
    metric_mapping = {
        "sessions": "ig_sessions",
        "conversions": "ig_conversions",
        "reach": "ig_reach",
        "engagement": "ig_engagement"
    }
    
    kpis = {"ig_sessions": 0.0, "ig_conversions": 0.0, "ig_reach": 0.0, "ig_engagement": 0.0}
    for metric_name, total in metrics:
        kpi_key = metric_mapping.get(metric_name)
        if kpi_key:
            kpis[kpi_key] = float(total) if total else 0.0
    
    return kpis

def _render_html(email: str, period: str, kpis: Dict[str, float], highlights: List[str], watchouts: List[str], actions: List[str]) -> str:
    """Render HTML email template for weekly digest."""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your Weekly Analytics Digest</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }}
            .header h1 {{ margin: 0; font-size: 24px; }}
            .header p {{ margin: 5px 0 0 0; opacity: 0.9; }}
            .content {{ padding: 30px; }}
            .metrics {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 20px 0; }}
            .metric {{ background: #f8f9fa; padding: 20px; border-radius: 6px; text-align: center; }}
            .metric-value {{ font-size: 32px; font-weight: bold; color: #667eea; margin: 10px 0; }}
            .metric-label {{ font-size: 14px; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px; }}
            .section {{ margin: 30px 0; }}
            .section h2 {{ font-size: 18px; color: #333; margin-bottom: 15px; }}
            .section ul {{ list-style: none; padding: 0; }}
            .section li {{ padding: 10px; margin: 5px 0; background: #f8f9fa; border-radius: 4px; border-left: 3px solid #667eea; }}
            .footer {{ padding: 20px 30px; background: #f8f9fa; border-radius: 0 0 8px 8px; text-align: center; color: #6c757d; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 Your Weekly Analytics Digest</h1>
                <p>{period}</p>
            </div>
            <div class="content">
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value">{int(kpis['ig_sessions']):,}</div>
                        <div class="metric-label">Sessions</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{int(kpis['ig_conversions']):,}</div>
                        <div class="metric-label">Conversions</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{int(kpis['ig_reach']):,}</div>
                        <div class="metric-label">Reach</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{int(kpis['ig_engagement']):,}</div>
                        <div class="metric-label">Engagement</div>
                    </div>
                </div>
                {"<div class='section'><h2>✨ Highlights</h2><ul>" + "".join(f"<li>{h}</li>" for h in highlights) + "</ul></div>" if highlights else ""}
                {"<div class='section'><h2>⚠️ Watch Outs</h2><ul>" + "".join(f"<li>{w}</li>" for w in watchouts) + "</ul></div>" if watchouts else ""}
                {"<div class='section'><h2>🎯 Action Items</h2><ul>" + "".join(f"<li>{a}</li>" for a in actions) + "</ul></div>" if actions else ""}
            </div>
            <div class="footer">
                <p>Living Lytics • Where Data Comes Alive</p>
                <p style="margin-top: 10px; font-size: 11px;">Sent to {email}</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

@app.post("/v1/digest/weekly", dependencies=[Depends(require_api_key)])
def weekly_digest(payload: DigestRequest, db: Session = Depends(get_db)):
    """Send weekly digest emails to users with rate limiting and run tracking."""
    logging.info(f"[WEEKLY DIGEST] Starting with scope={payload.scope}, email={payload.email}")
    
    # Rate limiting check: prevent runs within 10 minutes of any previous run start
    recent_run = db.execute(text("""
        SELECT id, started_at FROM digest_runs
        WHERE started_at >= NOW() - INTERVAL '10 minutes'
        ORDER BY started_at DESC
        LIMIT 1
    """)).fetchone()
    
    if recent_run:
        logging.warning(f"[WEEKLY DIGEST] Rate limit: last run started at {recent_run[1]}, cooldown in effect")
        raise HTTPException(status_code=429, detail="Digest run cooldown in effect. Please wait 10 minutes between runs.")
    
    # Create digest run record
    run_result = db.execute(text("""
        INSERT INTO digest_runs(started_at, sent, errors)
        VALUES (NOW(), 0, 0)
        RETURNING id
    """))
    db.commit()
    run_row = run_result.fetchone()
    if not run_row:
        raise HTTPException(status_code=500, detail="Failed to create digest run record")
    run_id = run_row[0]
    
    try:
        # Calculate date window (last 7 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        window_str = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
        
        # Determine recipients
        if payload.scope == "email":
            if not payload.email:
                raise HTTPException(status_code=400, detail="email is required when scope is 'email'")
            recipients = [payload.email]
        elif payload.scope == "all":
            users = db.execute(select(User.email)).scalars().all()
            recipients = list(users)
        else:
            raise HTTPException(status_code=400, detail="scope must be 'email' or 'all'")
        
        logging.info(f"[WEEKLY DIGEST] Processing {len(recipients)} recipients")
        
        sent = 0
        errors = []
        
        for recipient_email in recipients:
            try:
                # Collect KPIs
                kpis = _collect_kpis_for_user(recipient_email, start_date, end_date, db)
                
                # Generate insights
                highlights = []
                watchouts = []
                actions = []
                
                if kpis['ig_reach'] > 20000:
                    highlights.append(f"Strong reach performance: {kpis['ig_reach']:,.0f} impressions!")
                if kpis['ig_engagement'] > 1000:
                    highlights.append(f"Great engagement: {kpis['ig_engagement']:,.0f} interactions!")
                
                if kpis['ig_reach'] == 0 and kpis['ig_engagement'] == 0:
                    watchouts.append("No metrics recorded this week")
                    actions.append("Connect your Instagram account to start tracking")
                
                # Render HTML
                html = _render_html(recipient_email, window_str, kpis, highlights, watchouts, actions)
                
                # Send email via Resend (with retry logic built in)
                send_email_resend(recipient_email, "Your Weekly Analytics Digest", html)
                
                logging.info(f"[WEEKLY DIGEST] Sent to {recipient_email}")
                sent += 1
                
            except Exception as e:
                error_msg = str(e)
                logging.error(f"[WEEKLY DIGEST] Failed to send to {recipient_email}: {error_msg}")
                errors.append({"email": recipient_email, "error": error_msg})
        
        # Update digest run record with results
        db.execute(text("""
            UPDATE digest_runs
            SET finished_at = NOW(), sent = :sent, errors = :errors
            WHERE id = :run_id
        """), {"run_id": run_id, "sent": sent, "errors": len(errors)})
        db.commit()
        
        status = "sent" if sent > 0 else "no_sends"
        logging.info(f"[WEEKLY DIGEST] Completed: {sent} sent, {len(errors)} errors")
        
        return {
            "status": status,
            "period": window_str,
            "sent": sent,
            "errors": errors,
            "run_id": str(run_id)
        }
        
    except Exception as e:
        # Mark run as failed
        db.execute(text("""
            UPDATE digest_runs
            SET finished_at = NOW(), errors = -1
            WHERE id = :run_id
        """), {"run_id": run_id})
        db.commit()
        raise

@app.get("/v1/digest/preview", dependencies=[Depends(require_api_key)], response_class=HTMLResponse)
def digest_preview(email: EmailStr, db: Session = Depends(get_db)):
    """Preview weekly digest HTML without sending (for visual QA)."""
    logging.info(f"[DIGEST PREVIEW] Called with email: {email}")
    
    # Calculate date window (last 7 days)
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    window_str = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
    
    # Collect KPIs
    kpis = _collect_kpis_for_user(email, start_date, end_date, db)
    
    # Preview mode indicators
    highlights = ["Preview mode - No email sent"]
    if kpis['ig_reach'] > 20000:
        highlights.append(f"Strong reach performance: {kpis['ig_reach']:,.0f} impressions!")
    if kpis['ig_engagement'] > 1000:
        highlights.append(f"Great engagement: {kpis['ig_engagement']:,.0f} interactions!")
    
    watchouts = []
    actions = ["This is a preview only - use /v1/digest/test to send a test email"]
    
    # Render HTML
    html = _render_html(email, window_str, kpis, highlights, watchouts, actions)
    
    return html

@app.post("/v1/digest/test", dependencies=[Depends(require_api_key)])
def digest_test(payload: Dict[str, str] = Body(...), db: Session = Depends(get_db)):
    """Send a test digest email to a specific address."""
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="email is required")
    
    logging.info(f"[DIGEST TEST] Called with email: {email}")
    
    # Calculate date window (last 7 days)
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    window_str = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
    
    # Collect KPIs
    kpis = _collect_kpis_for_user(email, start_date, end_date, db)
    
    # Test mode indicators
    highlights = ["Manual test send - Triggered from /v1/digest/test"]
    if kpis['ig_reach'] > 20000:
        highlights.append(f"Strong reach performance: {kpis['ig_reach']:,.0f} impressions!")
    if kpis['ig_engagement'] > 1000:
        highlights.append(f"Great engagement: {kpis['ig_engagement']:,.0f} interactions!")
    
    watchouts = []
    actions = ["This is a test email to verify Resend integration"]
    
    # Render HTML
    html = _render_html(email, window_str, kpis, highlights, watchouts, actions)
    
    # Send via Resend
    try:
        result = send_email_resend(email, "Your Weekly Analytics Digest (Test)", html)
        logging.info(f"[DIGEST TEST] Test email sent to {email}: {result}")
        return {"status": "sent", "email": email, "resend_response": result}
    except Exception as e:
        logging.error(f"[DIGEST TEST] Failed to send test email to {email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {str(e)}")

@app.post("/v1/digest/run", dependencies=[Depends(require_api_key)])
def digest_run(payload: DigestRunRequest, db: Session = Depends(get_db)):
    """Send digest email to a specific user for a specified number of days."""
    logging.info(f"[DIGEST RUN] Called with user_email={payload.user_email}, days={payload.days}")
    
    # Resolve user_email to account_id (strict match)
    user = db.execute(select(User).where(User.email == payload.user_email)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {payload.user_email}")
    
    # Calculate date window
    end_date = date.today()
    start_date = end_date - timedelta(days=payload.days)
    window_str = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
    
    # Collect KPIs for this user only (account_id based)
    kpis = _collect_kpis_for_user(payload.user_email, start_date, end_date, db)
    
    # Generate insights
    highlights = []
    if kpis['ig_reach'] > 20000:
        highlights.append(f"Strong reach: {kpis['ig_reach']:,.0f} impressions!")
    if kpis['ig_engagement'] > 1000:
        highlights.append(f"Great engagement: {kpis['ig_engagement']:,.0f} interactions!")
    if kpis['ig_conversions'] > 500:
        highlights.append(f"Excellent conversions: {kpis['ig_conversions']:,.0f}!")
    
    watchouts = []
    if kpis['ig_sessions'] < 1000:
        watchouts.append("Sessions below target - consider increasing ad spend")
    
    actions = ["Review your top-performing content", "Optimize low-engagement posts"]
    
    # Render HTML
    html = _render_html(payload.user_email, window_str, kpis, highlights, watchouts, actions)
    
    # Send via Resend
    try:
        result = send_email_resend(payload.user_email, f"Your {payload.days}-Day Analytics Digest", html)
        logging.info(f"[DIGEST RUN] Email sent to {payload.user_email}: {result}")
        
        return {
            "sent": True,
            "user_email": payload.user_email,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "days": payload.days
        }
    except Exception as e:
        logging.error(f"[DIGEST RUN] Failed to send email to {payload.user_email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send digest: {str(e)}")

@app.post("/v1/digest/scheduled-run-all", dependencies=[Depends(require_admin_token)], include_in_schema=False)
def scheduled_run_all_digests(db: Session = Depends(get_db)):
    """
    Admin endpoint: Run weekly digest for all opted-in users.
    Uses scheduler logic with idempotency via digest_log.
    Requires ADMIN_TOKEN for access.
    """
    logging.info("[ADMIN] Manual trigger of weekly digest run")
    result = run_weekly_digests(db)
    logging.info(f"[ADMIN] Weekly digest run completed: {result}")
    return result

@app.get("/v1/digest/schedule", dependencies=[Depends(require_api_key)])
def get_digest_schedule():
    """Admin endpoint: Get scheduler information."""
    jobs = scheduler.get_jobs()
    
    if not jobs:
        return {
            "timezone": "America/Los_Angeles",
            "jobs": [],
            "message": "No scheduled jobs found"
        }
    
    job_info = []
    for job in jobs:
        job_info.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    # Get last completed week period
    last_period_start, last_period_end = get_last_completed_week()
    
    return {
        "timezone": "America/Los_Angeles",
        "jobs": job_info,
        "last_completed_week": {
            "period_start": last_period_start.isoformat(),
            "period_end": last_period_end.isoformat()
        }
    }

# User Preference Endpoints (these would need user authentication in production)
class DigestPreferencesUpdate(BaseModel):
    opt_in_digest: bool

@app.get("/v1/digest/preferences", dependencies=[Depends(require_api_key)])
def get_digest_preferences(user_email: str, db: Session = Depends(get_db)):
    """Get user's digest preferences. In production, use proper user auth instead of email param."""
    # Use raw SQL to bypass SQLAlchemy metadata cache
    result = db.execute(
        text("SELECT email, opt_in_digest, last_digest_sent_at FROM users WHERE email = :email"),
        {"email": user_email}
    ).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "email": result[0],
        "opt_in_digest": result[1],
        "last_digest_sent_at": result[2].isoformat() if result[2] else None
    }

@app.put("/v1/digest/preferences", dependencies=[Depends(require_api_key)])
def update_digest_preferences(
    user_email: str,
    preferences: DigestPreferencesUpdate,
    db: Session = Depends(get_db)
):
    """Update user's digest preferences. In production, use proper user auth instead of email param."""
    # Use raw SQL to bypass SQLAlchemy metadata cache
    result = db.execute(
        text("SELECT email FROM users WHERE email = :email"),
        {"email": user_email}
    ).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.execute(
        text("UPDATE users SET opt_in_digest = :opt_in WHERE email = :email"),
        {"opt_in": preferences.opt_in_digest, "email": user_email}
    )
    db.commit()
    
    logging.info(f"[PREFERENCES] User {user_email} set opt_in_digest={preferences.opt_in_digest}")
    
    return {
        "email": user_email,
        "opt_in_digest": preferences.opt_in_digest,
        "message": "Preferences updated successfully"
    }

@app.get("/v1/digest/unsubscribe")
def unsubscribe_from_digest(token: str, db: Session = Depends(get_db)):
    """Unsubscribe from weekly digests using JWT token from email link."""
    user_id = verify_unsubscribe_token(token)
    
    if not user_id:
        return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head><title>Invalid Link</title></head>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1>❌ Invalid or Expired Link</h1>
                <p>This unsubscribe link is invalid or has expired.</p>
            </body>
            </html>
        """, status_code=400)
    
    # Use raw SQL to bypass SQLAlchemy metadata cache
    result = db.execute(
        text("SELECT email FROM users WHERE id = :user_id"),
        {"user_id": str(user_id)}
    ).fetchone()
    
    if not result:
        return HTMLResponse(content="""
            <!DOCTYPE html>
            <html>
            <head><title>User Not Found</title></head>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1>❌ User Not Found</h1>
                <p>We couldn't find your account.</p>
            </body>
            </html>
        """, status_code=404)
    
    # Opt out
    db.execute(
        text("UPDATE users SET opt_in_digest = FALSE WHERE id = :user_id"),
        {"user_id": str(user_id)}
    )
    db.commit()
    
    logging.info(f"[UNSUBSCRIBE] User {result[0]} unsubscribed via token")
    
    return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Unsubscribed</title>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5;">
            <div style="max-width: 500px; margin: 50px auto; background: white; border-radius: 8px; padding: 40px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center;">
                <div style="font-size: 48px; margin-bottom: 20px;">✅</div>
                <h1 style="color: #333; margin: 0 0 10px 0;">You're Unsubscribed</h1>
                <p style="color: #666; margin: 0 0 20px 0;">You will no longer receive weekly digest emails at <strong>{result[0]}</strong>.</p>
                <p style="color: #999; font-size: 14px;">You can re-subscribe anytime from your account settings.</p>
            </div>
        </body>
        </html>
    """)

# Metrics Timeline Endpoint
@app.get("/v1/metrics/timeline", dependencies=[Depends(require_api_key)])
def metrics_timeline(
    request: Request,
    user_email: Optional[str] = None,
    email: Optional[str] = None,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get daily metrics timeline for a user (last N days). Cached for 5 minutes.
    
    Accepts either 'user_email' or 'email' parameter for compatibility with Base44 frontend.
    """
    # Support both email and user_email parameters
    user_email_param = user_email or email
    if not user_email_param:
        raise HTTPException(status_code=400, detail="Missing 'email' or 'user_email' parameter")
    
    logging.info(f"[METRICS TIMELINE] email={user_email_param}, days={days}")
    
    # Resolve email to account_id (strict match)
    user = db.execute(select(User).where(User.email == user_email_param)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {user_email_param}")
    
    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)
    
    # Initialize timeline with all dates in range (with zeros)
    timeline = {}
    current_date = start_date
    while current_date <= end_date:
        timeline[current_date.isoformat()] = {
            "date": current_date.isoformat(),
            "sessions": 0,
            "conversions": 0,
            "reach": 0,
            "engagement": 0
        }
        current_date += timedelta(days=1)
    
    # Query metrics grouped by date (ensuring no cross-tenant data)
    results = db.execute(
        select(
            Metric.metric_date,
            Metric.metric_name,
            func.sum(Metric.metric_value).label("total")
        )
        .where(Metric.user_id == user.id)
        .where(Metric.metric_date >= start_date)
        .where(Metric.metric_date <= end_date)
        .group_by(Metric.metric_date, Metric.metric_name)
        .order_by(Metric.metric_date)
    ).all()
    
    # Fill in actual data
    for metric_date, metric_name, total in results:
        date_str = metric_date.isoformat()
        # Map metric names (sessions, conversions, reach, engagement)
        if metric_name in timeline[date_str]:
            timeline[date_str][metric_name] = int(total) if total else 0
    
    # Convert to sorted list
    timeline_list = sorted(timeline.values(), key=lambda x: x["date"])
    
    logging.info(f"[METRICS TIMELINE] Returning {len(timeline_list)} days of data for user {user.id}")
    
    # Return with cache control header
    return JSONResponse(
        content=timeline_list,
        headers={"Cache-Control": "max-age=300"}  # Cache for 5 minutes
    )

# Timeline Variants - Hourly and Monthly
@app.get("/v1/metrics/timeline/day", dependencies=[Depends(require_api_key)])
def metrics_timeline_day(
    request: Request,
    user_email: Optional[str] = None,
    email: Optional[str] = None,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get hourly metrics timeline for the last N hours. Returns 24 hourly data points (zero-filled).
    
    Accepts either 'user_email' or 'email' parameter for compatibility with Base44 frontend.
    """
    # Support both email and user_email parameters
    user_email_param = user_email or email
    if not user_email_param:
        raise HTTPException(status_code=400, detail="Missing 'email' or 'user_email' parameter")
    
    logging.info(f"[METRICS TIMELINE DAY] email={user_email_param}, hours={hours}")
    
    # Resolve email to account_id (strict match)
    user = db.execute(select(User).where(User.email == user_email_param)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {user_email_param}")
    
    # For hourly data, we'll aggregate today's metrics and distribute evenly
    # In a real system, you'd store hourly metrics, but we'll zero-fill for now
    now = datetime.now(PT)
    timeline = []
    for i in range(hours):
        hour_time = now - timedelta(hours=hours-i-1)
        timeline.append({
            "hour": hour_time.strftime("%Y-%m-%d %H:00"),
            "sessions": 0,
            "conversions": 0,
            "reach": 0,
            "engagement": 0
        })
    
    logging.info(f"[METRICS TIMELINE DAY] Returning {len(timeline)} hourly points (zero-filled) for user {user.id}")
    
    return JSONResponse(
        content=timeline,
        headers={"Cache-Control": "max-age=300"}
    )

@app.get("/v1/metrics/timeline/month", dependencies=[Depends(require_api_key)])
def metrics_timeline_month(
    request: Request,
    user_email: Optional[str] = None,
    email: Optional[str] = None,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get daily metrics timeline for the last N days (default 30). Returns daily data points.
    
    Accepts either 'user_email' or 'email' parameter for compatibility with Base44 frontend.
    """
    # Support both email and user_email parameters
    user_email_param = user_email or email
    if not user_email_param:
        raise HTTPException(status_code=400, detail="Missing 'email' or 'user_email' parameter")
    
    logging.info(f"[METRICS TIMELINE MONTH] email={user_email_param}, days={days}")
    
    # Resolve email to account_id (strict match)
    user = db.execute(select(User).where(User.email == user_email_param)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {user_email_param}")
    
    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)
    
    # Initialize timeline with all dates in range (with zeros)
    timeline = {}
    current_date = start_date
    while current_date <= end_date:
        timeline[current_date.isoformat()] = {
            "date": current_date.isoformat(),
            "sessions": 0,
            "conversions": 0,
            "reach": 0,
            "engagement": 0
        }
        current_date += timedelta(days=1)
    
    # Query metrics grouped by date (ensuring no cross-tenant data)
    results = db.execute(
        select(
            Metric.metric_date,
            Metric.metric_name,
            func.sum(Metric.metric_value).label("total")
        )
        .where(Metric.user_id == user.id)
        .where(Metric.metric_date >= start_date)
        .where(Metric.metric_date <= end_date)
        .group_by(Metric.metric_date, Metric.metric_name)
        .order_by(Metric.metric_date)
    ).all()
    
    # Fill in actual data
    for metric_date, metric_name, total in results:
        date_str = metric_date.isoformat()
        if metric_name in timeline[date_str]:
            timeline[date_str][metric_name] = int(total) if total else 0
    
    # Convert to sorted list
    timeline_list = sorted(timeline.values(), key=lambda x: x["date"])
    
    logging.info(f"[METRICS TIMELINE MONTH] Returning {len(timeline_list)} days of data for user {user.id}")
    
    return JSONResponse(
        content=timeline_list,
        headers={"Cache-Control": "max-age=300"}
    )

# Webhook and Email Events Endpoints

@app.post("/v1/webhooks/resend")
async def resend_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Secure webhook endpoint for Resend email events.
    Verifies HMAC-SHA256 signature sent in X-Resend-Signature,
    stores event in email_events (idempotent on provider_id),
    and returns 200 quickly to prevent retry storms.
    """
    # 1) Read raw body and signature
    raw_body: bytes = await request.body()
    signature = request.headers.get("X-Resend-Signature")
    secret = os.getenv("RESEND_WEBHOOK_SECRET")

    if not secret:
        # Misconfiguration safeguard
        logging.error("[RESEND WEBHOOK] Missing RESEND_WEBHOOK_SECRET")
        raise HTTPException(status_code=500, detail="Missing RESEND_WEBHOOK_SECRET")
    
    if not signature:
        logging.warning("[RESEND WEBHOOK] Missing X-Resend-Signature header")
        raise HTTPException(status_code=400, detail="Missing X-Resend-Signature header")

    # 2) Compute HMAC hex digest and compare in constant time
    computed = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed, signature):
        logging.warning("[RESEND WEBHOOK] Invalid signature")
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    # 3) Parse JSON after signature passes
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception as e:
        logging.error(f"[RESEND WEBHOOK] Invalid JSON: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # 4) Normalize fields (Resend payload fields may vary slightly by event)
    event_type = payload.get("type") or "unknown"
    provider_id = payload.get("id") or (payload.get("data") or {}).get("id")
    
    # Resend webhook formats vary, try multiple paths for email
    email = (
        payload.get("to")
        or payload.get("email")
        or (payload.get("data") or {}).get("to")
        or "unknown"
    )
    if isinstance(email, list):
        email = email[0] if email else "unknown"
    
    subject = payload.get("subject") or (payload.get("data") or {}).get("subject")

    # Safety: we rely on provider_id to deduplicate
    if not provider_id:
        # If Resend ever omits id, synthesize a hash to prevent dupes
        provider_id = hashlib.sha256(raw_body).hexdigest()
        logging.info(f"[RESEND WEBHOOK] Generated synthetic provider_id from payload hash")

    # 5) Store to DB (idempotent on provider_id via unique index)
    try:
        db.execute(text("""
            INSERT INTO email_events(email, event_type, provider_id, subject, payload)
            VALUES (:email, :event_type, :provider_id, :subject, :payload)
            ON CONFLICT (provider_id) DO NOTHING
        """), {
            "email": email,
            "event_type": event_type,
            "provider_id": provider_id,
            "subject": subject,
            "payload": json.dumps(payload)
        })
        db.commit()
        logging.info(f"[RESEND WEBHOOK] Stored {event_type} event for {email} (provider_id: {provider_id})")
    except Exception as e:
        # Log but still 200 to acknowledge receipt (to avoid retry storms)
        logging.error(f"[RESEND WEBHOOK][DB ERROR] {str(e)}")

    # 6) Always return 200 quickly so Resend doesn't retry aggressively
    return {"ok": True}

@app.get("/v1/webhooks/resend/check", dependencies=[Depends(require_api_key)])
def resend_webhook_check():
    """Verify webhook secret is configured (for staging/testing)."""
    has_secret = bool(os.getenv("RESEND_WEBHOOK_SECRET"))
    return {"webhook_secret_present": has_secret}

@app.get("/v1/email-events/summary", dependencies=[Depends(require_api_key)])
def email_events_summary(
    request: Request,
    user_email: Optional[str] = None,
    email: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get paginated email events summary with filters.
    
    Supports filtering by email (account-scoped), date range, and pagination.
    Returns event counts and paginated event list.
    """
    from datetime import datetime as dt
    from sqlalchemy import cast, DATE
    
    # Support both email and user_email parameters
    user_email_param = user_email or email
    
    # Default date range (last 30 days)
    if not start:
        start = (date.today() - timedelta(days=30)).isoformat()
    if not end:
        end = date.today().isoformat()
    
    logging.info(f"[EMAIL EVENTS] email={user_email_param}, start={start}, end={end}, page={page}, limit={limit}")
    
    # Parse dates
    start_date = dt.fromisoformat(start).date()
    end_date = dt.fromisoformat(end).date()
    
    # Build base query
    query = select(EmailEvent)
    count_query = select(func.count(EmailEvent.id))
    
    # Apply email filter if provided
    if user_email_param:
        # Resolve email to account_id for strict scoping
        user = db.execute(select(User).where(User.email == user_email_param)).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail=f"User not found: {user_email_param}")
        query = query.where(EmailEvent.email == user_email_param)
        count_query = count_query.where(EmailEvent.email == user_email_param)
    
    # Apply date filters
    query = query.where(cast(EmailEvent.created_at, DATE) >= start_date)
    query = query.where(cast(EmailEvent.created_at, DATE) <= end_date)
    count_query = count_query.where(cast(EmailEvent.created_at, DATE) >= start_date)
    count_query = count_query.where(cast(EmailEvent.created_at, DATE) <= end_date)
    
    # Get total count
    total = db.execute(count_query).scalar() or 0
    
    # Get event type counts
    type_counts_query = select(
        EmailEvent.event_type,
        func.count(EmailEvent.id).label("count")
    ).group_by(EmailEvent.event_type)
    
    if user_email_param:
        type_counts_query = type_counts_query.where(EmailEvent.email == user_email_param)
    type_counts_query = type_counts_query.where(cast(EmailEvent.created_at, DATE) >= start_date)
    type_counts_query = type_counts_query.where(cast(EmailEvent.created_at, DATE) <= end_date)
    
    type_counts_result = db.execute(type_counts_query).all()
    counts = {row[0]: row[1] for row in type_counts_result}
    
    # Get paginated events
    offset = (page - 1) * limit
    events_query = query.order_by(EmailEvent.created_at.desc()).offset(offset).limit(limit)
    events_result = db.execute(events_query).scalars().all()
    
    events = [
        {
            "ts": event.created_at.isoformat() if event.created_at else None,
            "type": event.event_type,
            "message_id": event.provider_id,
            "subject": event.subject
        }
        for event in events_result
    ]
    
    has_next = (offset + limit) < total
    
    return {
        "email": user_email_param,
        "start": start,
        "end": end,
        "counts": {
            "delivered": counts.get("email.delivered", 0),
            "bounced": counts.get("email.bounced", 0),
            "opened": counts.get("email.opened", 0),
            "clicked": counts.get("email.clicked", 0)
        },
        "events": events,
        "page": page,
        "limit": limit,
        "total": total,
        "has_next": has_next
    }

@app.get("/v1/email-events/health", dependencies=[Depends(require_api_key)])
def email_events_health(
    request: Request,
    user_email: Optional[str] = None,
    email: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get delivery health KPIs (open rate, click rate, bounce rate) for a user.
    
    Returns delivery metrics with rates calculated for account-scoped email events.
    """
    from datetime import datetime as dt
    
    # Support both email and user_email parameters
    user_email_param = user_email or email
    if not user_email_param:
        raise HTTPException(status_code=400, detail="email or user_email parameter required")
    
    # Default date range (last 30 days)
    if not start:
        start = (date.today() - timedelta(days=30)).isoformat()
    if not end:
        end = date.today().isoformat()
    
    logging.info(f"[EMAIL HEALTH] email={user_email_param}, start={start}, end={end}")
    
    # Resolve email to user for strict scoping
    user = db.execute(select(User).where(User.email == user_email_param)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {user_email_param}")
    
    # Parse dates
    start_date = dt.fromisoformat(start).date()
    end_date = dt.fromisoformat(end).date()
    
    # Get event type counts
    type_counts_query = select(
        EmailEvent.event_type,
        func.count(EmailEvent.id).label("count")
    ).where(
        EmailEvent.email == user_email_param
    ).where(
        cast(EmailEvent.created_at, DATE) >= start_date
    ).where(
        cast(EmailEvent.created_at, DATE) <= end_date
    ).group_by(EmailEvent.event_type)
    
    type_counts_result = db.execute(type_counts_query).all()
    counts = {row[0]: row[1] for row in type_counts_result}
    
    # Calculate raw counts
    delivered = counts.get("email.delivered", 0)
    opened = counts.get("email.opened", 0)
    clicked = counts.get("email.clicked", 0)
    bounced = counts.get("email.bounced", 0)
    
    # Calculate rates
    open_rate = (opened / delivered) if delivered > 0 else 0.0
    click_rate = (clicked / delivered) if delivered > 0 else 0.0
    bounce_rate = (bounced / (delivered + bounced)) if (delivered + bounced) > 0 else 0.0
    
    # Get last event timestamp
    last_event_query = select(
        func.max(EmailEvent.created_at)
    ).where(
        EmailEvent.email == user_email_param
    ).where(
        cast(EmailEvent.created_at, DATE) >= start_date
    ).where(
        cast(EmailEvent.created_at, DATE) <= end_date
    )
    last_event_at = db.execute(last_event_query).scalar()
    
    response = {
        "email": user_email_param,
        "period": {
            "start": start,
            "end": end
        },
        "counts": {
            "delivered": delivered,
            "opened": opened,
            "clicked": clicked,
            "bounced": bounced
        },
        "rates": {
            "open_rate": round(open_rate, 4),
            "click_rate": round(click_rate, 4),
            "bounce_rate": round(bounce_rate, 4)
        },
        "last_event_at": last_event_at.isoformat() if last_event_at else None
    }
    
    # Add Cache-Control header for performance
    return Response(
        content=json.dumps(response),
        media_type="application/json",
        headers={"Cache-Control": "max-age=300"}
    )

@app.get("/v1/status")
def system_status(db: Session = Depends(get_db)):
    """Get system status information for UI badge/health checks.
    
    Returns environment, timezone, scheduler status, email provider, and version.
    No authentication required for this endpoint.
    """
    # Get next scheduler run
    next_run = None
    try:
        jobs = scheduler.get_jobs()
        if jobs:
            next_run = jobs[0].next_run_time.isoformat() if jobs[0].next_run_time else None
    except Exception as e:
        logging.warning(f"[STATUS] Failed to get scheduler info: {e}")
    
    # Get version from environment or git
    version = os.getenv("VERSION", "69a2772")  # git SHA from earlier
    
    return {
        "env": os.getenv("ENV", "production"),
        "tz": str(PT),
        "scheduler": {
            "next_run": next_run
        },
        "email_provider": "resend",
        "version": version
    }

@app.get("/v1/debug/google-check", tags=["debug"])
def debug_google_check(email: str = Query(..., min_length=3), db: Session = Depends(get_db)):
    """
    Check if a user has a Google Analytics connection configured.
    Returns connection status and token expiration.
    No authentication required - read-only debug endpoint.
    """
    try:
        user = db.execute(
            select(User).where(func.lower(User.email) == func.lower(email))
        ).scalar_one_or_none()
        
        if not user:
            return {
                "connected": False,
                "provider": "google",
                "email": email,
                "expires_at": None
            }
        
        google_source = db.execute(
            select(DataSource).where(
                DataSource.user_id == user.id,
                DataSource.source_name == "google_analytics"
            ).order_by(DataSource.id.desc())
        ).scalars().first()
        
        if not google_source:
            return {
                "connected": False,
                "provider": "google",
                "email": email,
                "expires_at": None
            }
        
        return {
            "connected": True,
            "provider": "google",
            "email": email,
            "expires_at": google_source.expires_at.isoformat() if google_source.expires_at else None
        }
    except Exception as e:
        logging.error(f"[DEBUG] google-check failed: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")

@app.get("/v1/debug/facebook-check", tags=["debug"])
def debug_facebook_check(email: str = Query(..., min_length=3), db: Session = Depends(get_db)):
    """
    Check if a user has a Facebook/Instagram connection configured.
    Returns connection status and token expiration.
    No authentication required - read-only debug endpoint.
    """
    try:
        user = db.execute(
            select(User).where(func.lower(User.email) == func.lower(email))
        ).scalar_one_or_none()
        
        if not user:
            return {
                "connected": False,
                "provider": "facebook",
                "email": email,
                "expires_at": None
            }
        
        instagram_source = db.execute(
            select(DataSource).where(
                DataSource.user_id == user.id,
                DataSource.source_name == "instagram"
            ).order_by(DataSource.id.desc())
        ).scalars().first()
        
        if not instagram_source:
            return {
                "connected": False,
                "provider": "facebook",
                "email": email,
                "expires_at": None
            }
        
        return {
            "connected": True,
            "provider": "facebook",
            "email": email,
            "expires_at": instagram_source.expires_at.isoformat() if instagram_source.expires_at else None
        }
    except Exception as e:
        logging.error(f"[DEBUG] facebook-check failed: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")

@app.get("/v1/debug/instagram-config", include_in_schema=False)
def debug_instagram_config():
    """
    Diagnostic endpoint to verify Instagram OAuth configuration.
    Returns whether secrets are loaded (not the actual values).
    
    Hidden from OpenAPI schema for security.
    """
    has_app_id = bool(META_APP_ID)
    has_app_secret = bool(META_APP_SECRET)
    has_redirect = bool(META_OAUTH_REDIRECT)
    
    all_configured = has_app_id and has_app_secret and has_redirect
    
    return {
        "META_APP_ID": has_app_id,
        "META_APP_SECRET": has_app_secret,
        "META_OAUTH_REDIRECT": META_OAUTH_REDIRECT if has_redirect else None,
        "status": "ok" if all_configured else "missing"
    }

@app.get("/v1/debug/facebook-inspect", include_in_schema=False)
def debug_facebook_inspect(
    email: str,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Admin diagnostic endpoint to inspect Facebook Pages, permissions, and Instagram links.
    Requires ADMIN_TOKEN. Hidden from OpenAPI schema.
    """
    # Verify admin token
    token = authorization.replace("Bearer ", "")
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Find user
    user = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {email}")
    
    # Find Instagram data source
    ig_source = db.execute(
        select(DataSource).where(
            DataSource.user_id == user.id,
            DataSource.source_name == "instagram"
        )
    ).scalar_one_or_none()
    
    if not ig_source:
        raise HTTPException(status_code=404, detail=f"No Instagram connection found for user: {email}")
    
    access_token = ig_source.access_token
    results = {
        "email": email,
        "stored_ig_user_id": ig_source.refresh_token,
        "stored_username": ig_source.account_ref,
        "expires_at": ig_source.expires_at.isoformat() if ig_source.expires_at else None,
        "diagnostics": {}
    }
    
    # Check permissions
    try:
        perms_url = "https://graph.facebook.com/v19.0/me/permissions"
        perms_response = requests.get(perms_url, params={"access_token": access_token}, timeout=10)
        perms_response.raise_for_status()
        perms_data = perms_response.json()
        granted_permissions = [p["permission"] for p in perms_data.get("data", []) if p.get("status") == "granted"]
        results["diagnostics"]["granted_permissions"] = granted_permissions
    except Exception as e:
        results["diagnostics"]["granted_permissions"] = f"Error: {str(e)}"
    
    # Check pages
    try:
        pages_url = "https://graph.facebook.com/v19.0/me/accounts"
        pages_response = requests.get(pages_url, params={"access_token": access_token}, timeout=10)
        pages_response.raise_for_status()
        pages_data = pages_response.json()
        pages = pages_data.get("data", [])
        results["diagnostics"]["pages_count"] = len(pages)
        results["diagnostics"]["pages"] = []
        
        # For each page, check for IG business account
        for page in pages:
            page_id = page.get("id")
            page_name = page.get("name")
            
            page_info = {
                "id": page_id,
                "name": page_name,
                "instagram_business_account": None
            }
            
            try:
                page_detail_url = f"https://graph.facebook.com/v19.0/{page_id}"
                page_detail_response = requests.get(
                    page_detail_url,
                    params={"fields": "instagram_business_account", "access_token": access_token},
                    timeout=10
                )
                page_detail_response.raise_for_status()
                page_detail = page_detail_response.json()
                
                if "instagram_business_account" in page_detail:
                    ig_account = page_detail["instagram_business_account"]
                    page_info["instagram_business_account"] = ig_account.get("id")
            except Exception as e:
                page_info["error"] = str(e)
            
            results["diagnostics"]["pages"].append(page_info)
    except Exception as e:
        results["diagnostics"]["pages"] = f"Error: {str(e)}"
    
    return results

@app.post("/v1/dev/seed-metrics", include_in_schema=False)
def seed_metrics(
    request: Request,
    body: SeedMetricsRequest = Body(...),
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """Seed realistic metric data for testing and demos.
    
    Requires ADMIN_TOKEN. Hidden from OpenAPI schema.
    """
    # Verify admin token
    token = authorization.replace("Bearer ", "")
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Rate limiting
    if not rate_limiter.allow(f"seed-metrics-{body.email}", tokens=1):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    
    # Resolve user
    user = db.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {body.email}")
    
    logging.info(f"[SEED METRICS] email={body.email}, days={body.days}")
    
    # Generate realistic metric data
    metrics_inserted = 0
    today = date.today()
    
    for i in range(body.days):
        metric_date = today - timedelta(days=i)
        
        # Generate realistic random values with trends
        base_sessions = random.randint(800, 1500)
        base_conversions = random.randint(50, 150)
        base_reach = random.randint(2000, 4000)
        base_engagement = random.randint(500, 1000)
        
        metrics_data = [
            ("sessions", base_sessions),
            ("conversions", base_conversions),
            ("reach", base_reach),
            ("engagement", base_engagement)
        ]
        
        for metric_name, metric_value in metrics_data:
            metric = Metric(
                user_id=user.id,
                source_name="demo",
                metric_date=metric_date,
                metric_name=metric_name,
                metric_value=metric_value
            )
            db.add(metric)
            metrics_inserted += 1
    
    db.commit()
    
    return {
        "email": body.email,
        "days": body.days,
        "metrics_inserted": metrics_inserted,
        "status": "success"
    }

@app.post("/v1/dev/seed-email-events", include_in_schema=False)
def seed_email_events(
    request: Request,
    body: SeedEmailEventsRequest = Body(...),
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """Seed realistic email event data for testing and demos.
    
    Requires ADMIN_TOKEN. Hidden from OpenAPI schema.
    """
    from datetime import datetime as dt
    
    # Verify admin token
    token = authorization.replace("Bearer ", "")
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Rate limiting
    if not rate_limiter.allow(f"seed-events-{body.email}", tokens=1):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    
    # Resolve user
    user = db.execute(select(User).where(User.email == body.email)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {body.email}")
    
    # Default date range (last 30 days)
    start = body.start if body.start else (date.today() - timedelta(days=30)).isoformat()
    end = body.end if body.end else date.today().isoformat()
    
    start_date = dt.fromisoformat(start).date()
    end_date = dt.fromisoformat(end).date()
    
    logging.info(f"[SEED EMAIL EVENTS] email={body.email}, events={body.events}, start={start}, end={end}")
    
    # Event type distribution (realistic percentages)
    event_types = [
        ("email.delivered", 0.95),  # 95% delivered
        ("email.opened", 0.40),     # 40% opened
        ("email.clicked", 0.10),    # 10% clicked
        ("email.bounced", 0.05)     # 5% bounced
    ]
    
    events_inserted = 0
    date_range = (end_date - start_date).days + 1
    
    for _ in range(body.events):
        # Random date within range
        random_days = random.randint(0, date_range - 1)
        event_date = start_date + timedelta(days=random_days)
        from datetime import time as dt_time
        event_datetime = dt.combine(
            event_date,
            dt_time(random.randint(0, 23), random.randint(0, 59))
        )
        
        # Select event type based on distribution
        rand = random.random()
        cumulative = 0.0
        selected_type = "email.delivered"
        
        for event_type, probability in event_types:
            cumulative += probability
            if rand <= cumulative:
                selected_type = event_type
                break
        
        # Create event with unique provider_id
        event = EmailEvent(
            email=body.email,
            event_type=selected_type,
            provider_id=f"seed-{uuid.uuid4()}",
            subject="Weekly Living Lytics Digest",
            payload={},
            created_at=event_datetime
        )
        db.add(event)
        events_inserted += 1
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"[SEED EMAIL EVENTS] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to insert events: {str(e)}")
    
    return {
        "email": body.email,
        "events_inserted": events_inserted,
        "period": {"start": start, "end": end},
        "status": "success"
    }

@app.get("/v1/digest/status", dependencies=[Depends(require_api_key)])
def digest_status(db: Session = Depends(get_db)):
    """Get status of the last digest run."""
    
    result = db.execute(text("""
        SELECT started_at, finished_at, sent, errors
        FROM digest_runs
        ORDER BY started_at DESC
        LIMIT 1
    """)).fetchone()
    
    if not result:
        return {
            "last_run": None,
            "status": "never_run"
        }
    
    started_at, finished_at, sent, errors = result
    
    status = "completed" if finished_at else "running"
    
    return {
        "last_run": started_at.isoformat() if started_at else None,
        "finished_at": finished_at.isoformat() if finished_at else None,
        "status": status,
        "sent": sent,
        "errors": errors
    }

# ============================================================
# Google OAuth / GA4 Connections
# ============================================================

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_OAUTH_REDIRECT = os.getenv("GOOGLE_OAUTH_REDIRECT")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5000")

# In-memory OAuth state storage (secure random nonce mapping)
# Format: {state_token: {"email": email, "expires_at": timestamp}}
oauth_state_store: Dict[str, Dict[str, Any]] = {}
oauth_state_lock = threading.Lock()

def generate_oauth_state(email: str) -> str:
    """Generate cryptographically secure OAuth state token."""
    state_token = hashlib.sha256(
        f"{email}-{time.time()}-{uuid.uuid4()}".encode()
    ).hexdigest()
    
    with oauth_state_lock:
        # Clean expired states (older than 10 minutes)
        now = time.time()
        expired_keys = [
            k for k, v in oauth_state_store.items()
            if v["expires_at"] < now
        ]
        for k in expired_keys:
            del oauth_state_store[k]
        
        # Store new state
        oauth_state_store[state_token] = {
            "email": email,
            "expires_at": now + 600  # 10 minutes
        }
    
    return state_token

def verify_oauth_state(state_token: str) -> Optional[str]:
    """Verify OAuth state token and return associated email."""
    with oauth_state_lock:
        state_data = oauth_state_store.get(state_token)
        
        if not state_data:
            return None
        
        # Check expiration
        if state_data["expires_at"] < time.time():
            del oauth_state_store[state_token]
            return None
        
        # Delete state after use (one-time use)
        email = state_data["email"]
        del oauth_state_store[state_token]
        
        return email

@app.get("/v1/connections/google/init")
def google_oauth_init(email: str, db: Session = Depends(get_db)):
    """
    Initiate Google OAuth flow for GA4 integration.
    Redirects user to Google consent screen with CSRF protection.
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_OAUTH_REDIRECT:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    # Verify user exists
    user_result = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()
    
    if not user_result:
        raise HTTPException(status_code=404, detail=f"User not found: {email}")
    
    # Generate cryptographically secure state token
    state_token = generate_oauth_state(email)
    
    # Build Google OAuth URL
    oauth_params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_OAUTH_REDIRECT,
        "scope": "https://www.googleapis.com/auth/analytics.readonly",
        "access_type": "offline",
        "include_granted_scopes": "true",
        "response_type": "code",
        "state": state_token,  # Secure random state token
        "prompt": "consent"  # Force consent to get refresh token
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(oauth_params)}"
    
    logging.info(f"[OAUTH] Initiating Google OAuth for user={email}")
    
    return RedirectResponse(url=auth_url)

@app.get("/v1/connections/google/callback")
def google_oauth_callback(code: str, state: str, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback with CSRF protection.
    Exchanges authorization code for access/refresh tokens.
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not GOOGLE_OAUTH_REDIRECT:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    # Verify state token (CSRF protection)
    email = verify_oauth_state(state)
    if not email:
        logging.error(f"[OAUTH] Invalid or expired state token: {state[:16]}...")
        return RedirectResponse(url=f"{FRONTEND_URL}/connect/callback?provider=google&status=error")
    
    # Verify user exists
    user_result = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()
    
    if not user_result:
        logging.error(f"[OAUTH] User not found during callback: {email}")
        return RedirectResponse(url=f"{FRONTEND_URL}/connect/callback?provider=google&status=error")
    
    # Exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": GOOGLE_OAUTH_REDIRECT
    }
    
    try:
        token_response = requests.post(token_url, data=token_data, timeout=10)
        token_response.raise_for_status()
        tokens = token_response.json()
    except requests.RequestException as e:
        logging.error(f"[OAUTH] Token exchange failed for user={email}: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/connect/callback?provider=google&status=error")
    
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    expires_in = tokens.get("expires_in", 3600)
    scope = tokens.get("scope", "https://www.googleapis.com/auth/analytics.readonly")
    
    if not access_token:
        return RedirectResponse(url=f"{FRONTEND_URL}/connect/callback?provider=google&status=error")
    
    # Calculate expiration timestamp
    expires_at = datetime.now() + timedelta(seconds=expires_in)
    
    # Check if data source already exists for this user
    existing = db.execute(
        select(DataSource).where(
            DataSource.user_id == user_result.id,
            DataSource.source_name == "google_analytics"
        )
    ).scalar_one_or_none()
    
    if existing:
        # Update existing data source
        existing.access_token = access_token
        existing.refresh_token = refresh_token
        existing.expires_at = expires_at
        existing.account_ref = email
        existing.updated_at = datetime.now()
        logging.info(f"[OAUTH] Google Analytics connection updated for user={email}")
    else:
        # Create new data source
        new_source = DataSource(
            user_id=user_result.id,
            source_name="google_analytics",
            account_ref=email,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )
        db.add(new_source)
        logging.info(f"[OAUTH] Google Analytics connected for user={email}")
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"[OAUTH] Failed to save tokens for user={email}: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/connect/callback?provider=google&status=error")
    
    return RedirectResponse(url=f"{FRONTEND_URL}/connect/callback?provider=google&status=success")

def refresh_google_token(data_source: DataSource, db: Session) -> str:
    """
    Refresh Google OAuth access token if expired.
    Returns valid access token.
    """
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    # Check if token is expired (with 5 minute buffer)
    now = datetime.now()
    if data_source.expires_at and data_source.expires_at > now + timedelta(minutes=5):
        # Token still valid
        return data_source.access_token
    
    # Need to refresh
    if not data_source.refresh_token:
        raise HTTPException(
            status_code=401,
            detail="No refresh token available. Please reconnect your Google account."
        )
    
    logging.info(f"[OAUTH] Refreshing Google token for user_id={data_source.user_id}")
    
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "refresh_token": data_source.refresh_token,
        "grant_type": "refresh_token"
    }
    
    try:
        token_response = requests.post(token_url, data=token_data, timeout=10)
        token_response.raise_for_status()
        tokens = token_response.json()
    except requests.RequestException as e:
        logging.error(f"[OAUTH] Token refresh failed: {e}")
        raise HTTPException(
            status_code=401,
            detail="Failed to refresh Google token. Please reconnect your account."
        )
    
    new_access_token = tokens.get("access_token")
    expires_in = tokens.get("expires_in", 3600)
    
    if not new_access_token:
        raise HTTPException(status_code=500, detail="No access token in refresh response")
    
    # Update data source
    data_source.access_token = new_access_token
    data_source.expires_at = now + timedelta(seconds=expires_in)
    data_source.updated_at = now
    
    db.commit()
    
    logging.info(f"[OAUTH] Token refreshed successfully for user_id={data_source.user_id}")
    
    return new_access_token

# ============================================================
# Instagram OAuth & Sync
# ============================================================

@app.get("/v1/connections/instagram/init")
def instagram_oauth_init(email: str, db: Session = Depends(get_db)):
    """
    Initiate Instagram OAuth flow.
    Redirects user to Instagram authorization with CSRF protection.
    """
    # Check configuration
    missing_keys = []
    if not META_APP_ID:
        missing_keys.append("META_APP_ID")
    if not META_APP_SECRET:
        missing_keys.append("META_APP_SECRET")
    if not META_OAUTH_REDIRECT:
        missing_keys.append("META_OAUTH_REDIRECT")
    
    if missing_keys:
        raise HTTPException(
            status_code=500, 
            detail=f"Instagram OAuth not configured: missing {', '.join(missing_keys)}"
        )
    
    # Verify user exists
    user_result = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()
    
    if not user_result:
        raise HTTPException(status_code=404, detail=f"User not found: {email}")
    
    # Generate secure state token
    state_token = generate_oauth_state(email)
    
    # Build Facebook OAuth URL (Instagram uses Facebook OAuth)
    oauth_params = {
        "client_id": META_APP_ID,
        "redirect_uri": META_OAUTH_REDIRECT,
        "scope": "instagram_basic,instagram_manage_insights,pages_show_list,pages_read_engagement",
        "response_type": "code",
        "state": state_token
    }
    
    auth_url = f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(oauth_params)}"
    
    logging.info(f"[OAUTH] Initiating Instagram OAuth for user={email}")
    
    return RedirectResponse(url=auth_url)

@app.get("/v1/connections/instagram/callback")
def instagram_oauth_callback(code: str, state: str, db: Session = Depends(get_db)):
    """
    Handle Instagram OAuth callback with CSRF protection.
    Exchanges short-lived code for long-lived token and triggers 30-day backfill.
    """
    if not META_APP_ID or not META_APP_SECRET or not META_OAUTH_REDIRECT:
        raise HTTPException(status_code=500, detail="Instagram OAuth not configured")
    
    # Verify state token (CSRF protection)
    email = verify_oauth_state(state)
    if not email:
        logging.error(f"[OAUTH] Invalid or expired Instagram state token")
        return RedirectResponse(url=f"{FRONTEND_URL}/connect/callback?provider=instagram&status=error")
    
    # Verify user exists
    user_result = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()
    
    if not user_result:
        logging.error(f"[OAUTH] User not found during Instagram callback: {email}")
        return RedirectResponse(url=f"{FRONTEND_URL}/connect/callback?provider=instagram&status=error")
    
    # Step 1: Exchange code for short-lived user access token via Facebook Graph API
    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    token_params = {
        "client_id": META_APP_ID,
        "client_secret": META_APP_SECRET,
        "redirect_uri": META_OAUTH_REDIRECT,
        "code": code
    }
    
    try:
        logging.info(f"[OAUTH] Exchanging code for short-lived token: POST {token_url}")
        token_response = requests.post(token_url, params=token_params, timeout=10)
        logging.info(f"[OAUTH] Token exchange response status: {token_response.status_code}")
        token_response.raise_for_status()
        short_lived_data = token_response.json()
        logging.info(f"[OAUTH] Received short-lived token for user={email}")
    except requests.RequestException as e:
        error_detail = f"Status: {getattr(e.response, 'status_code', 'N/A')}, URL: {token_url}"
        logging.error(f"[OAUTH] Instagram token exchange failed for user={email}: {e}, {error_detail}")
        if hasattr(e.response, 'text'):
            logging.error(f"[OAUTH] Response body: {e.response.text}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to exchange code for token: {str(e)}"
        )
    
    short_lived_token = short_lived_data.get("access_token")
    
    if not short_lived_token:
        logging.error(f"[OAUTH] No access_token in response: {short_lived_data}")
        raise HTTPException(status_code=500, detail="No access token received from Facebook")
    
    # Step 2: Exchange short-lived token for long-lived token (60 days)
    long_lived_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    long_lived_params = {
        "grant_type": "fb_exchange_token",
        "client_id": META_APP_ID,
        "client_secret": META_APP_SECRET,
        "fb_exchange_token": short_lived_token
    }
    
    try:
        logging.info(f"[OAUTH] Exchanging for long-lived token: GET {long_lived_url}")
        long_lived_response = requests.get(long_lived_url, params=long_lived_params, timeout=10)
        logging.info(f"[OAUTH] Long-lived token response status: {long_lived_response.status_code}")
        long_lived_response.raise_for_status()
        long_lived_data = long_lived_response.json()
        logging.info(f"[OAUTH] Exchanged for long-lived token (60d) for user={email}")
    except requests.RequestException as e:
        error_detail = f"Status: {getattr(e.response, 'status_code', 'N/A')}, URL: {long_lived_url}"
        logging.error(f"[OAUTH] Long-lived token exchange failed for user={email}: {e}, {error_detail}")
        if hasattr(e.response, 'text'):
            logging.error(f"[OAUTH] Response body: {e.response.text}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to exchange for long-lived token: {str(e)}"
        )
    
    access_token = long_lived_data.get("access_token")
    expires_in = long_lived_data.get("expires_in", 5184000)  # 60 days default
    
    if not access_token:
        logging.error(f"[OAUTH] No long-lived access_token in response: {long_lived_data}")
        raise HTTPException(status_code=500, detail="No long-lived access token received")
    
    # Calculate expiration timestamp
    expires_at = datetime.now() + timedelta(seconds=expires_in)
    logging.info(f"[OAUTH] Token expires in {expires_in}s ({expires_in/86400:.1f} days), expires_at={expires_at.isoformat()}")
    
    # Discover Instagram Business account through Facebook Pages
    logging.info(f"[OAUTH] Discovering Instagram Business account via Facebook Pages for user={email}")
    logging.info(f"[OAUTH] Ensure scopes: instagram_basic, instagram_manage_insights, pages_show_list, pages_read_engagement")
    
    # Step 1: Fetch user's Facebook Pages
    pages_url = "https://graph.facebook.com/v19.0/me/accounts"
    pages_params = {"access_token": access_token}
    
    try:
        pages_response = requests.get(pages_url, params=pages_params, timeout=10)
        pages_response.raise_for_status()
        pages_data = pages_response.json()
    except requests.RequestException as e:
        error_detail = f"Status: {getattr(e.response, 'status_code', 'N/A')}, URL: {pages_url}"
        logging.error(f"[OAUTH] Failed to fetch Facebook Pages: {e}, {error_detail}")
        if hasattr(e.response, 'text'):
            logging.error(f"[OAUTH] Response body: {e.response.text}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch Facebook Pages: {str(e)}"
        )
    
    pages = pages_data.get("data", [])
    
    if not pages:
        logging.error(f"[OAUTH] No Facebook Pages managed by user={email}")
        raise HTTPException(
            status_code=400,
            detail="This Facebook user manages no Pages. Create or get access to a Facebook Page, link your Instagram Business account to it, then retry."
        )
    
    logging.info(f"[OAUTH] Found {len(pages)} Facebook Page(s) for user={email}")
    
    # Step 2: For each page, check if it has an Instagram Business account linked
    ig_user_id = None
    username = None
    page_id = None
    
    for page in pages:
        page_id_candidate = page.get("id")
        page_name = page.get("name", "Unknown")
        
        logging.info(f"[OAUTH] Checking page '{page_name}' (ID: {page_id_candidate}) for Instagram Business account")
        
        try:
            page_detail_url = f"https://graph.facebook.com/v19.0/{page_id_candidate}"
            page_detail_params = {
                "fields": "instagram_business_account",
                "access_token": access_token
            }
            page_detail_response = requests.get(page_detail_url, params=page_detail_params, timeout=10)
            page_detail_response.raise_for_status()
            page_detail = page_detail_response.json()
            
            if "instagram_business_account" in page_detail:
                ig_account = page_detail["instagram_business_account"]
                ig_user_id = ig_account.get("id")
                page_id = page_id_candidate
                logging.info(f"[OAUTH] Found Instagram Business account linked to page '{page_name}': ig_user_id={ig_user_id}")
                break
            else:
                logging.info(f"[OAUTH] Page '{page_name}' has no Instagram Business account linked")
        except Exception as e:
            logging.warning(f"[OAUTH] Failed to check page '{page_name}' for IG account: {e}")
            continue
    
    if not ig_user_id:
        logging.error(f"[OAUTH] No Instagram Business account found linked to any Facebook Page for user={email}")
        raise HTTPException(
            status_code=400,
            detail="No Instagram Business account linked to any managed Page. Please link your Instagram Business or Creator account to one of your Facebook Pages, then retry the connection."
        )
    
    # Step 3: Fetch Instagram username
    try:
        ig_info_url = f"https://graph.facebook.com/v19.0/{ig_user_id}"
        ig_info_params = {
            "fields": "username",
            "access_token": access_token
        }
        ig_info_response = requests.get(ig_info_url, params=ig_info_params, timeout=10)
        ig_info_response.raise_for_status()
        ig_info = ig_info_response.json()
        username = ig_info.get("username", ig_user_id)
        logging.info(f"[OAUTH] Retrieved Instagram username: {username} (ig_user_id={ig_user_id}, page_id={page_id})")
    except Exception as e:
        logging.error(f"[OAUTH] Failed to fetch Instagram username: {e}")
        # Use ig_user_id as fallback username
        username = ig_user_id
    
    # Check for existing Instagram metrics BEFORE creating/updating data source
    existing_metrics_count = db.execute(
        select(func.count(Metric.id)).where(
            Metric.user_id == user_result.id,
            Metric.source_name == "instagram"
        )
    ).scalar()
    
    is_first_connection = (existing_metrics_count == 0)
    
    # Check if data source already exists
    existing = db.execute(
        select(DataSource).where(
            DataSource.user_id == user_result.id,
            DataSource.source_name == "instagram"
        )
    ).scalar_one_or_none()
    
    if existing:
        # Update existing
        existing.access_token = access_token
        existing.refresh_token = ig_user_id  # Store IG user ID in refresh_token field
        existing.expires_at = expires_at
        existing.account_ref = username
        existing.updated_at = datetime.now()
        logging.info(f"[OAUTH] Instagram connection updated for user={email}, ig_user_id={ig_user_id}")
    else:
        # Create new
        new_source = DataSource(
            user_id=user_result.id,
            source_name="instagram",
            account_ref=username,
            access_token=access_token,
            refresh_token=ig_user_id,  # Store IG user ID
            expires_at=expires_at
        )
        db.add(new_source)
        logging.info(f"[OAUTH] Instagram connected for user={email}, ig_user_id={ig_user_id}")
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"[OAUTH] Failed to save Instagram tokens for user={email}: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/connect/callback?provider=instagram&status=error")
    
    # Trigger 30-day backfill if this is first connection
    backfill_started = False
    
    if is_first_connection:
        # No prior Instagram data - trigger 30-day backfill
        logging.info(f"[SYNC] Running initial 30-day IG backfill for user={email}")
        try:
            backfill_result = run_instagram_sync_internal(user_result, db, days=30)
            if backfill_result.get("status") == "success":
                backfill_started = True
                logging.info(f"[SYNC] IG backfill complete: {backfill_result.get('metrics_inserted', 0)} metrics inserted")
        except Exception as e:
            logging.error(f"[SYNC] IG backfill failed for user={email}: {e}")
    else:
        logging.info(f"[SYNC] IG backfill skipped for user={email} (existing_metrics_count={existing_metrics_count})")
    
    return RedirectResponse(url=f"{FRONTEND_URL}/connect/callback?provider=instagram&status=success")

@app.post("/v1/connections/instagram/refresh", include_in_schema=False)
def instagram_token_refresh_admin(
    email: str,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    """
    Manually refresh Instagram long-lived token for a user.
    Requires ADMIN_TOKEN. Hidden from OpenAPI schema.
    """
    # Verify admin token
    token = authorization.replace("Bearer ", "")
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Find user
    user = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {email}")
    
    # Find Instagram data source
    ig_source = db.execute(
        select(DataSource).where(
            DataSource.user_id == user.id,
            DataSource.source_name == "instagram"
        )
    ).scalar_one_or_none()
    
    if not ig_source:
        raise HTTPException(status_code=404, detail=f"No Instagram connection found for user: {email}")
    
    # Refresh token
    try:
        new_token = refresh_instagram_token(ig_source, db)
        return {
            "refreshed": True,
            "email": email,
            "new_expiry": ig_source.expires_at.isoformat()
        }
    except Exception as e:
        logging.error(f"[OAUTH] Manual token refresh failed for user={email}: {e}")
        raise

def refresh_instagram_token(data_source: DataSource, db: Session) -> str:
    """
    Refresh Instagram long-lived token if expiring within 7 days.
    Uses Facebook Graph API to exchange current token for a new 60-day token.
    Returns valid access token.
    """
    if not META_APP_ID or not META_APP_SECRET:
        raise HTTPException(status_code=500, detail="Instagram OAuth not configured")
    
    # Check if token expires within 7 days
    now = datetime.now()
    if data_source.expires_at and data_source.expires_at > now + timedelta(days=7):
        # Token still valid for more than 7 days
        logging.info(f"[OAUTH] Token still valid until {data_source.expires_at.isoformat()}, skip refresh")
        return data_source.access_token
    
    logging.info(f"[OAUTH] Refreshing Instagram token for user_id={data_source.user_id}, expires_at={data_source.expires_at}")
    
    # Exchange current long-lived token for new long-lived token via Facebook Graph API
    refresh_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": META_APP_ID,
        "client_secret": META_APP_SECRET,
        "fb_exchange_token": data_source.access_token
    }
    
    try:
        logging.info(f"[OAUTH] Requesting token refresh: GET {refresh_url}")
        response = requests.get(refresh_url, params=params, timeout=10)
        logging.info(f"[OAUTH] Token refresh response status: {response.status_code}")
        response.raise_for_status()
        tokens = response.json()
    except requests.RequestException as e:
        error_detail = f"Status: {getattr(e.response, 'status_code', 'N/A')}, URL: {refresh_url}"
        logging.error(f"[OAUTH] Instagram token refresh failed: {e}, {error_detail}")
        if hasattr(e.response, 'text'):
            logging.error(f"[OAUTH] Response body: {e.response.text}")
        raise HTTPException(
            status_code=401,
            detail=f"Failed to refresh Instagram token: {str(e)}"
        )
    
    new_access_token = tokens.get("access_token")
    expires_in = tokens.get("expires_in", 5184000)  # 60 days default
    
    if not new_access_token:
        logging.error(f"[OAUTH] No access_token in refresh response: {tokens}")
        raise HTTPException(status_code=500, detail="No access token in refresh response")
    
    # Update data source with new token
    data_source.access_token = new_access_token
    data_source.expires_at = now + timedelta(seconds=expires_in)
    data_source.updated_at = now
    
    db.commit()
    
    logging.info(f"[OAUTH] Refreshed long-lived IG token for user_id={data_source.user_id}, new expires_at={data_source.expires_at.isoformat()}")
    
    return new_access_token

def run_instagram_sync_internal(user: User, db: Session, days: int = 30) -> dict:
    """
    Internal function to sync Instagram metrics for a user.
    
    Args:
        user: User object
        db: Database session
        days: Number of days to sync (30 for backfill, 1 for daily)
    
    Returns:
        dict with status, metrics_inserted, and date_range
    """
    # Get Instagram data source
    data_source = db.execute(
        select(DataSource).where(
            DataSource.user_id == user.id,
            DataSource.source_name == "instagram"
        )
    ).scalar_one_or_none()
    
    if not data_source:
        logging.error(f"[SYNC] No Instagram connection for user={user.email}")
        raise HTTPException(
            status_code=404,
            detail="Instagram account not connected"
        )
    
    # Refresh token if needed
    access_token = refresh_instagram_token(data_source, db)
    ig_user_id = data_source.refresh_token  # IG user ID stored in refresh_token field
    
    # Calculate date range (inclusive)
    end_date = (datetime.now() - timedelta(days=1)).date()
    start_date = end_date - timedelta(days=days-1)
    
    logging.info(f"[SYNC] Starting Instagram sync for user={user.email}, ig_user_id={ig_user_id}, range={start_date} to {end_date}, days={days}")
    
    metrics_inserted = 0
    
    # Fetch metrics for each day
    current_date = start_date
    while current_date <= end_date:
        try:
            # Convert date to Unix timestamps
            day_start = int(datetime.combine(current_date, datetime.min.time()).timestamp())
            day_end = int(datetime.combine(current_date, datetime.max.time()).timestamp())
            
            # Fetch daily insights (reach, impressions, profile_views)
            insights_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/insights"
            insights_params = {
                "metric": "reach,impressions,profile_views",
                "period": "day",
                "since": day_start,
                "until": day_end,
                "access_token": access_token
            }
            
            reach = 0
            try:
                insights_response = requests.get(insights_url, params=insights_params, timeout=15)
                insights_response.raise_for_status()
                insights_data = insights_response.json()
                
                for metric in insights_data.get("data", []):
                    metric_name = metric.get("name")
                    values = metric.get("values", [])
                    if values and len(values) > 0:
                        value = values[0].get("value", 0)
                        if metric_name == "reach":
                            reach = value
            except Exception as e:
                logging.warning(f"[SYNC] Failed to fetch Instagram insights for {current_date}: {e}")
            
            # Fetch media for engagement
            media_url = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
            media_params = {
                "fields": "timestamp,like_count,comments_count,insights.metric(saved)",
                "since": day_start,
                "until": day_end,
                "limit": 100,
                "access_token": access_token
            }
            
            engagement = 0
            try:
                media_response = requests.get(media_url, params=media_params, timeout=15)
                media_response.raise_for_status()
                media_data = media_response.json()
                
                for post in media_data.get("data", []):
                    likes = post.get("like_count", 0)
                    comments = post.get("comments_count", 0)
                    
                    # Get saves from insights
                    saves = 0
                    insights = post.get("insights", {}).get("data", [])
                    for insight in insights:
                        if insight.get("name") == "saved":
                            insight_values = insight.get("values", [])
                            if insight_values:
                                saves = insight_values[0].get("value", 0)
                    
                    engagement += likes + comments + saves
            except Exception as e:
                logging.warning(f"[SYNC] Failed to fetch Instagram media for {current_date}: {e}")
            
            # Insert reach metric
            if reach > 0:
                reach_metric = Metric(
                    user_id=user.id,
                    source_name="instagram",
                    metric_date=current_date,
                    metric_name="reach",
                    metric_value=reach,
                    meta={"ig_user_id": ig_user_id}
                )
                db.add(reach_metric)
                metrics_inserted += 1
            
            # Insert engagement metric
            if engagement > 0:
                engagement_metric = Metric(
                    user_id=user.id,
                    source_name="instagram",
                    metric_date=current_date,
                    metric_name="engagement",
                    metric_value=engagement,
                    meta={"ig_user_id": ig_user_id}
                )
                db.add(engagement_metric)
                metrics_inserted += 1
            
            # Respect API rate limits
            time.sleep(0.5)
            
        except Exception as e:
            logging.error(f"[SYNC] Instagram sync failed for date {current_date}: {e}")
        
        current_date += timedelta(days=1)
    
    try:
        db.commit()
        logging.info(f"[SYNC] Inserted {metrics_inserted} Instagram metrics for user={user.email}, range={start_date} to {end_date}")
    except Exception as e:
        db.rollback()
        logging.error(f"[SYNC] Failed to insert Instagram metrics for user={user.email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save metrics: {str(e)}")
    
    return {
        "status": "success",
        "email": user.email,
        "ig_user_id": ig_user_id,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "days": days,
        "metrics_inserted": metrics_inserted
    }

@app.get("/v1/connections/status", dependencies=[Depends(require_api_key)])
def connections_status(email: str, db: Session = Depends(get_db)):
    """
    Get list of connected providers for a user.
    Returns provider names and token expiration timestamps.
    """
    # Get user
    user_result = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()
    
    if not user_result:
        raise HTTPException(status_code=404, detail=f"User not found: {email}")
    
    # Get all data sources for this user
    sources = db.execute(
        select(DataSource).where(DataSource.user_id == user_result.id)
    ).scalars().all()
    
    connections = []
    for source in sources:
        connections.append({
            "provider": source.source_name,
            "account_ref": source.account_ref,
            "expires_at": source.expires_at.isoformat() if source.expires_at else None,
            "connected_at": source.created_at.isoformat(),
            "updated_at": source.updated_at.isoformat()
        })
    
    return {
        "email": email,
        "connections": connections,
        "total": len(connections)
    }

@app.get("/v1/connections/google/properties", dependencies=[Depends(require_api_key)])
def list_google_properties(email: str, db: Session = Depends(get_db)):
    """
    List GA4 properties from Google Analytics Admin API.
    Returns flattened list of accounts and their properties.
    """
    # Get user
    user_result = db.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()
    
    if not user_result:
        raise HTTPException(status_code=404, detail=f"User not found: {email}")
    
    # Get Google OAuth data source
    data_source = db.execute(
        select(DataSource).where(
            DataSource.user_id == user_result.id,
            DataSource.source_name == "google_analytics"
        )
    ).scalar_one_or_none()
    
    if not data_source:
        raise HTTPException(
            status_code=404,
            detail="Google Analytics account not connected. Please connect via /v1/connections/google/init"
        )
    
    # Refresh token if needed
    access_token = refresh_google_token(data_source, db)
    
    # Call Google Analytics Admin API
    api_url = "https://analyticsadmin.googleapis.com/v1beta/accountSummaries"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logging.error(f"[GA4] Failed to fetch properties for user={email}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch GA4 properties: {str(e)}"
        )
    
    # Build flat list of properties
    properties_list = []
    account_summaries = data.get("accountSummaries", [])
    
    for account in account_summaries:
        account_name = account.get("displayName", "Unknown Account")
        account_id = account.get("account", "")
        
        for property_summary in account.get("propertySummaries", []):
            property_name = property_summary.get("displayName", "Unknown Property")
            property_id = property_summary.get("property", "")
            
            # Extract numeric ID from property_id (e.g., "properties/123456789" -> "123456789")
            property_numeric_id = property_id.split("/")[-1] if property_id else ""
            
            properties_list.append({
                "account_name": account_name,
                "account": account_id,
                "property_name": property_name,
                "property_id": property_id,
                "property_numeric_id": property_numeric_id
            })
    
    logging.info(f"[GA4] Fetched {len(properties_list)} properties for user={email}")
    
    return properties_list

class SavePropertyRequest(BaseModel):
    email: EmailStr
    property_id: str = Field(..., min_length=1)
    property_name: str = Field(..., min_length=1)

@app.post("/v1/connections/google/property", dependencies=[Depends(require_api_key)])
def save_google_property(body: SavePropertyRequest, db: Session = Depends(get_db)):
    """
    Save selected GA4 property for a user.
    Upserts into ga4_properties table (one property per user).
    """
    # Get user
    user_result = db.execute(
        select(User).where(User.email == body.email)
    ).scalar_one_or_none()
    
    if not user_result:
        raise HTTPException(status_code=404, detail=f"User not found: {body.email}")
    
    # Check if property already saved
    existing = db.execute(
        select(GA4Property).where(GA4Property.user_id == user_result.id)
    ).scalar_one_or_none()
    
    if existing:
        # Update existing
        existing.property_id = body.property_id
        existing.display_name = body.property_name
        existing.updated_at = datetime.now()
        logging.info(f"[GA4] Updated property for user={body.email}: {body.property_id}")
    else:
        # Create new
        new_property = GA4Property(
            user_id=user_result.id,
            property_id=body.property_id,
            display_name=body.property_name
        )
        db.add(new_property)
        logging.info(f"[GA4] Saved property for user={body.email}: {body.property_id}")
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"[GA4] Failed to save property for user={body.email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save property: {str(e)}")
    
    # Check if user has any existing GA4 metrics
    existing_metrics_count = db.execute(
        select(func.count(Metric.id)).where(
            Metric.user_id == user_result.id,
            Metric.source_name == "google"
        )
    ).scalar()
    
    backfill_started = False
    
    if existing_metrics_count == 0:
        # No prior GA4 data - trigger 30-day backfill
        logging.info(f"[SYNC] Running initial 30-day backfill for user={body.email}")
        try:
            backfill_result = run_ga4_sync_internal(user_result, db, days=30)
            if backfill_result.get("status") == "success":
                backfill_started = True
                logging.info(f"[SYNC] Backfill complete: {backfill_result.get('metrics_inserted', 0)} metrics inserted")
        except Exception as e:
            logging.error(f"[SYNC] Backfill failed for user={body.email}: {e}")
    
    return {
        "saved": True,
        "backfill_started": backfill_started
    }

# ============================================================
# GA4 Data Sync - Internal Helper
# ============================================================

def run_ga4_sync_internal(user: User, db: Session, days: int = 1) -> dict:
    """
    Internal function to sync GA4 data for a user.
    
    Args:
        user: User object
        db: Database session
        days: Number of days to sync (1 for yesterday, 30 for backfill)
    
    Returns:
        dict with status, metrics_inserted, and date_range
    """
    # Check if user has saved GA4 property
    ga4_property = db.execute(
        select(GA4Property).where(GA4Property.user_id == user.id)
    ).scalar_one_or_none()
    
    if not ga4_property:
        logging.info(f"[SYNC] GA4 skipped (no property saved) for user={user.email}")
        return {
            "status": "skipped",
            "reason": "No GA4 property saved",
            "email": user.email
        }
    
    # Get Google OAuth data source
    data_source = db.execute(
        select(DataSource).where(
            DataSource.user_id == user.id,
            DataSource.source_name == "google_analytics"
        )
    ).scalar_one_or_none()
    
    if not data_source:
        logging.error(f"[SYNC] No Google Analytics OAuth connection for user={user.email}")
        raise HTTPException(
            status_code=404,
            detail="Google Analytics account not connected"
        )
    
    # Refresh token if needed
    access_token = refresh_google_token(data_source, db)
    
    # Calculate date range (inclusive)
    end_date = (datetime.now() - timedelta(days=1)).date()
    start_date = end_date - timedelta(days=days-1)
    
    logging.info(f"[SYNC] Starting GA4 sync for user={user.email}, property={ga4_property.property_id}, range={start_date} to {end_date}, days={days}")
    
    # Call Google Analytics Data API (runReport)
    api_url = f"https://analyticsdata.googleapis.com/v1beta/{ga4_property.property_id}:runReport"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    request_body = {
        "dateRanges": [{"startDate": str(start_date), "endDate": str(end_date)}],
        "dimensions": [{"name": "date"}],
        "metrics": [
            {"name": "sessions"},
            {"name": "conversions"}
        ]
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=request_body, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        logging.error(f"[SYNC] GA4 API call failed for user={user.email}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch GA4 data: {str(e)}"
        )
    
    # Parse response and insert metrics
    rows = data.get("rows", [])
    metrics_inserted = 0
    
    for row in rows:
        dimension_values = row.get("dimensionValues", [])
        metric_values = row.get("metricValues", [])
        
        if len(dimension_values) >= 1 and len(metric_values) >= 2:
            # Parse date from dimension (format: YYYYMMDD)
            date_str = dimension_values[0].get("value")
            metric_date = datetime.strptime(date_str, "%Y%m%d").date()
            
            sessions = int(metric_values[0].get("value", 0))
            conversions = int(metric_values[1].get("value", 0))
            
            # Insert sessions metric
            sessions_metric = Metric(
                user_id=user.id,
                source_name="google",
                metric_date=metric_date,
                metric_name="sessions",
                metric_value=sessions,
                meta={"property_id": ga4_property.property_id}
            )
            db.add(sessions_metric)
            
            # Insert conversions metric
            conversions_metric = Metric(
                user_id=user.id,
                source_name="google",
                metric_date=metric_date,
                metric_name="conversions",
                metric_value=conversions,
                meta={"property_id": ga4_property.property_id}
            )
            db.add(conversions_metric)
            
            metrics_inserted += 2
    
    try:
        db.commit()
        logging.info(f"[SYNC] Inserted {metrics_inserted} metrics for user={user.email}, range={start_date} to {end_date}")
    except Exception as e:
        db.rollback()
        logging.error(f"[SYNC] Failed to insert metrics for user={user.email}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save metrics: {str(e)}")
    
    return {
        "status": "success",
        "email": user.email,
        "property_id": ga4_property.property_id,
        "property_name": ga4_property.display_name,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "days": days,
        "metrics_inserted": metrics_inserted
    }

# ============================================================
# GA4 Data Sync - API Endpoints
# ============================================================

class SyncRequest(BaseModel):
    email: EmailStr
    provider: str = Field(..., pattern="^(google|instagram)$")

@app.post("/v1/sync/run", dependencies=[Depends(require_admin_token)], include_in_schema=False)
def run_sync(body: SyncRequest, db: Session = Depends(get_db)):
    """
    Manually trigger data sync for a user (yesterday only).
    Admin-only endpoint. Supports google and instagram providers.
    """
    # Get user
    user_result = db.execute(
        select(User).where(User.email == body.email)
    ).scalar_one_or_none()
    
    if not user_result:
        raise HTTPException(status_code=404, detail=f"User not found: {body.email}")
    
    # Route to appropriate sync function
    if body.provider == "google":
        return run_ga4_sync_internal(user_result, db, days=1)
    elif body.provider == "instagram":
        return run_instagram_sync_internal(user_result, db, days=1)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {body.provider}")
