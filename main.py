import os
import json
import logging
import requests
import hmac
import hashlib
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Depends, HTTPException, Header, Body, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from db import get_db, engine
from models import Base, User, Metric, DigestLog, EmailEvent
from github import Github, GithubException
from mailer import send_email_resend
from scheduler_utils import (
    get_last_completed_week,
    send_weekly_digest,
    run_weekly_digests,
    verify_unsubscribe_token,
    PT
)

# Configure basic logging
logging.basicConfig(level=logging.INFO)

APP_NAME = os.getenv("APP_NAME", "Living Lytics API")
API_KEY = os.getenv("FASTAPI_SECRET_KEY")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

if not API_KEY:
    raise RuntimeError("FASTAPI_SECRET_KEY not set")
if not ADMIN_TOKEN:
    logging.warning("⚠️  ADMIN_TOKEN not set - admin endpoints will be inaccessible")

app = FastAPI(title=APP_NAME)

ALLOW_ORIGINS = [
    "https://livinglytics.base44.app",
    "https://livinglytics.com",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

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
    """Initialize database indexes, constraints, and start scheduler on startup."""
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
    # Support both email and user_email parameters
    user_email_param = user_email or email
    
    # Default date range (last 30 days)
    if not start:
        start = (date.today() - timedelta(days=30)).isoformat()
    if not end:
        end = date.today().isoformat()
    
    logging.info(f"[EMAIL EVENTS] email={user_email_param}, start={start}, end={end}, page={page}, limit={limit}")
    
    # Build filters
    filters = []
    params = {"start": start, "end": end}
    
    if user_email_param:
        # Resolve email to account_id for strict scoping
        user = db.execute(select(User).where(User.email == user_email_param)).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail=f"User not found: {user_email_param}")
        filters.append("email = :email")
        params["email"] = user_email_param
    
    where_clause = " AND ".join(filters) if filters else "1=1"
    
    # Get event counts by type
    count_query = f"""
        SELECT event_type, COUNT(*) as count
        FROM email_events
        WHERE {where_clause}
          AND created_at >= :start::date
          AND created_at < :end::date + INTERVAL '1 day'
        GROUP BY event_type
    """
    count_result = db.execute(text(count_query), params).fetchall()
    counts = {row[0]: row[1] for row in count_result}
    
    # Get total count for pagination
    total_query = f"""
        SELECT COUNT(*)
        FROM email_events
        WHERE {where_clause}
          AND created_at >= :start::date
          AND created_at < :end::date + INTERVAL '1 day'
    """
    total = db.execute(text(total_query), params).scalar()
    
    # Get paginated events
    offset = (page - 1) * limit
    events_query = f"""
        SELECT created_at, event_type, provider_id, subject
        FROM email_events
        WHERE {where_clause}
          AND created_at >= :start::date
          AND created_at < :end::date + INTERVAL '1 day'
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """
    params["limit"] = limit
    params["offset"] = offset
    
    events_result = db.execute(text(events_query), params).fetchall()
    events = [
        {
            "ts": row[0].isoformat() if row[0] else None,
            "type": row[1],
            "message_id": row[2],
            "subject": row[3]
        }
        for row in events_result
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
