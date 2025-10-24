import os
import json
import logging
import requests
import hmac
import hashlib
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Depends, HTTPException, Header, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session
from db import get_db, engine
from models import Base, User, Metric
from github import Github, GithubException
from mailer import send_email_resend

# Configure basic logging
logging.basicConfig(level=logging.INFO)

APP_NAME = os.getenv("APP_NAME", "Living Lytics API")
API_KEY = os.getenv("FASTAPI_SECRET_KEY")
if not API_KEY:
    raise RuntimeError("FASTAPI_SECRET_KEY not set")

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

@app.on_event("startup")
def on_startup():
    """Initialize database indexes and constraints on startup."""
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

def require_api_key(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    if token != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid token")

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

@app.post("/v1/digest/run-all", dependencies=[Depends(require_api_key)])
def digest_run_all(payload: DigestRunAllRequest, db: Session = Depends(get_db)):
    """Admin endpoint: Send digest to all users with throttling."""
    logging.info(f"[DIGEST RUN-ALL] Starting for all users, days={payload.days}")
    
    # Get all users
    users = db.execute(select(User.email)).scalars().all()
    
    sent_count = 0
    error_count = 0
    errors = []
    
    for user_email in users:
        try:
            # Use the same logic as single digest
            end_date = date.today()
            start_date = end_date - timedelta(days=payload.days)
            window_str = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
            
            kpis = _collect_kpis_for_user(user_email, start_date, end_date, db)
            
            highlights = []
            if kpis['ig_reach'] > 20000:
                highlights.append(f"Strong reach: {kpis['ig_reach']:,.0f} impressions!")
            if kpis['ig_engagement'] > 1000:
                highlights.append(f"Great engagement: {kpis['ig_engagement']:,.0f} interactions!")
            
            watchouts = []
            actions = ["Review your analytics dashboard"]
            
            html = _render_html(user_email, window_str, kpis, highlights, watchouts, actions)
            
            send_email_resend(user_email, f"Your {payload.days}-Day Analytics Digest", html)
            sent_count += 1
            logging.info(f"[DIGEST RUN-ALL] Sent to {user_email}")
            
            # Throttle to avoid provider limits (0.5 second between sends)
            import time
            time.sleep(0.5)
            
        except Exception as e:
            error_count += 1
            error_msg = f"{user_email}: {str(e)}"
            errors.append(error_msg)
            logging.error(f"[DIGEST RUN-ALL] Failed for {error_msg}")
    
    logging.info(f"[DIGEST RUN-ALL] Complete: sent={sent_count}, errors={error_count}")
    
    return {
        "sent": sent_count,
        "errors": error_count,
        "error_details": errors[:10],  # Return first 10 errors
        "total_users": len(users),
        "days": payload.days
    }

# Metrics Timeline Endpoint
@app.get("/v1/metrics/timeline", dependencies=[Depends(require_api_key)])
def metrics_timeline(user_email: str, days: int = 7, db: Session = Depends(get_db)):
    """Get daily metrics timeline for a user (last N days)."""
    logging.info(f"[METRICS TIMELINE] user_email={user_email}, days={days}")
    
    # Resolve email to account_id (strict match)
    user = db.execute(select(User).where(User.email == user_email)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail=f"User not found: {user_email}")
    
    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)
    
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
    
    # Build timeline structure
    timeline = {}
    for metric_date, metric_name, total in results:
        date_str = metric_date.isoformat()
        if date_str not in timeline:
            timeline[date_str] = {
                "date": date_str,
                "sessions": 0,
                "conversions": 0,
                "reach": 0,
                "engagement": 0
            }
        
        # Map metric names (sessions, conversions, reach, engagement)
        if metric_name in timeline[date_str]:
            timeline[date_str][metric_name] = int(total) if total else 0
    
    # Convert to sorted list
    timeline_list = sorted(timeline.values(), key=lambda x: x["date"])
    
    logging.info(f"[METRICS TIMELINE] Returning {len(timeline_list)} days of data")
    
    return timeline_list

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
def email_events_summary(db: Session = Depends(get_db)):
    """Get summary of email events from last 24 hours."""
    
    # Get counts by event type for last 24 hours
    last_24h_result = db.execute(text("""
        SELECT event_type, COUNT(*) as count
        FROM email_events
        WHERE created_at >= NOW() - INTERVAL '24 hours'
        GROUP BY event_type
    """)).fetchall()
    
    last_24h = {row[0]: row[1] for row in last_24h_result}
    
    # Get latest 10 events
    latest_result = db.execute(text("""
        SELECT email, event_type, created_at
        FROM email_events
        ORDER BY created_at DESC
        LIMIT 10
    """)).fetchall()
    
    latest = [
        {
            "email": row[0],
            "event_type": row[1],
            "created_at": row[2].isoformat() if row[2] else None
        }
        for row in latest_result
    ]
    
    return {
        "last_24h": last_24h,
        "latest": latest
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
