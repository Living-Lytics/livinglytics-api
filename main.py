import os
import json
import logging
import requests
from datetime import date
from typing import Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session
from db import get_db, engine
from models import Base, User, Metric
from github import Github, GithubException

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

@app.post("/v1/digest/weekly", dependencies=[Depends(require_api_key)])
def weekly_digest(email: str, db: Session = Depends(get_db)):
    """Generate weekly digest summary for a user (scheduled function endpoint)."""
    logging.info(f"[WEEKLY DIGEST] Generating digest for {email}")
    
    # Get user
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        logging.warning(f"[WEEKLY DIGEST] User not found: {email}")
        raise HTTPException(status_code=404, detail="User not found")
    
    # Mock digest summary (replace with actual email sending later)
    summary = {
        "email": email,
        "period": "Last 7 days",
        "metrics": {
            "sessions": 0.0,
            "conversions": 0.0,
            "ig_reach": 0.0,
            "engagement": 0.0
        },
        "status": "mock_generated"
    }
    
    logging.info(f"[WEEKLY DIGEST] Generated for {email}: {json.dumps(summary)}")
    
    return {
        "success": True,
        "message": "Weekly digest generated (mock)",
        "summary": summary
    }
