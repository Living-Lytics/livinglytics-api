import os
import json
import logging
import requests
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Depends, HTTPException, Header, Body
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

ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "*")

app = FastAPI(title=APP_NAME)

if ALLOW_ORIGINS == "*":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https://(www\.livinglytics\.com|app\.base44\.com|([a-z0-9-]+\.)+base44\.com|([a-z0-9-]+\.)+onrender\.com|([a-z0-9-]+\.)+replit\.app|([a-z0-9-]+\.)+repl\.co)$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
    return {"message": "Living Lytics API is running", "docs": "/docs"}

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
                <p>Hi there,</p>
                <p>Here's your weekly analytics summary for <strong>{email}</strong>:</p>
                
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-label">Sessions</div>
                        <div class="metric-value">{kpis.get('ig_sessions', 0):,.0f}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Conversions</div>
                        <div class="metric-value">{kpis.get('ig_conversions', 0):,.0f}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Reach</div>
                        <div class="metric-value">{kpis.get('ig_reach', 0):,.0f}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Engagement</div>
                        <div class="metric-value">{kpis.get('ig_engagement', 0):,.0f}</div>
                    </div>
                </div>
                
                {f'''
                <div class="section">
                    <h2>✨ Highlights</h2>
                    <ul>
                        {''.join(f'<li>{h}</li>' for h in highlights)}
                    </ul>
                </div>
                ''' if highlights else ''}
                
                {f'''
                <div class="section">
                    <h2>⚠️ Watch Outs</h2>
                    <ul>
                        {''.join(f'<li>{w}</li>' for w in watchouts)}
                    </ul>
                </div>
                ''' if watchouts else ''}
                
                {f'''
                <div class="section">
                    <h2>🎯 Action Items</h2>
                    <ul>
                        {''.join(f'<li>{a}</li>' for a in actions)}
                    </ul>
                </div>
                ''' if actions else ''}
                
                <p style="margin-top: 30px;">Keep up the great work!</p>
            </div>
            <div class="footer">
                <p>Living Lytics - Your Analytics Partner</p>
                <p>This is an automated weekly digest. Reply to this email if you have questions.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html

def _recipient_list(scope: str, email: Optional[str], db: Session) -> List[str]:
    """Get list of recipient emails based on scope."""
    if scope == "email":
        if not email:
            raise HTTPException(status_code=400, detail="Email required when scope='email'")
        # Verify user exists
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail=f"User not found: {email}")
        return [email]
    elif scope == "all":
        # Get all users
        users = db.execute(select(User.email)).scalars().all()
        return list(users)
    else:
        raise HTTPException(status_code=400, detail="Invalid scope. Must be 'email' or 'all'")

@app.post("/v1/digest/weekly", dependencies=[Depends(require_api_key)])
def weekly_digest(payload: DigestRequest, db: Session = Depends(get_db)):
    """Generate and send weekly digest emails (scheduled function endpoint)."""
    # Calculate date window (last 7 days)
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    window_str = f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}"
    
    logging.info(f"[WEEKLY DIGEST] Starting for scope={payload.scope}, email={payload.email}, period={window_str}")
    
    # Get recipients
    recipients = _recipient_list(payload.scope, payload.email, db)
    
    sent = 0
    errors = []
    
    for recipient_email in recipients:
        try:
            # Collect KPIs
            kpis = _collect_kpis_for_user(recipient_email, start_date, end_date, db)
            
            # Generate insights (simple logic for now)
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
            
            # Send email via Resend
            send_email_resend(recipient_email, "Your Weekly Analytics Digest", html)
            
            logging.info(f"[WEEKLY DIGEST] Sent to {recipient_email}")
            sent += 1
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"[WEEKLY DIGEST] Failed to send to {recipient_email}: {error_msg}")
            errors.append({"email": recipient_email, "error": error_msg})
    
    status = "sent" if sent > 0 else "no_sends"
    logging.info(f"[WEEKLY DIGEST] Completed: {sent} sent, {len(errors)} errors")
    
    return {
        "status": status,
        "period": window_str,
        "sent": sent,
        "errors": errors
    }

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
