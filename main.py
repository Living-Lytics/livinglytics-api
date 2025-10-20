import os
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session
from db import get_db, engine
from models import Base, User, Metric

APP_NAME = os.getenv("APP_NAME", "Living Lytics API")
API_KEY = os.getenv("FASTAPI_SECRET_KEY")
ALLOW_ORIGINS = [o.strip() for o in os.getenv("ALLOW_ORIGINS", "*").split(",")]

app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS if ALLOW_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Light connectivity check (won't alter schema)
with engine.begin() as conn:
    conn.execute(text("select 1"))

def require_api_key(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    if API_KEY and token != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid token")

@app.get("/v1/health/liveness")
def liveness():
    return {"status": "ok"}

@app.get("/v1/health/readiness")
def readiness():
    ready = bool(API_KEY and os.getenv("DATABASE_URL") and os.getenv("SUPABASE_PROJECT_URL") and os.getenv("SUPABASE_ANON_KEY"))
    return {"ready": ready}

@app.post("/v1/dev/seed-user", dependencies=[Depends(require_api_key)])
def seed_user(email: str, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
        return {"created": True}
    return {"created": False}

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
        "sessions": float(agg("sessions")),
        "conversions": float(agg("conversions")),
        "ig_reach": float(agg("reach")),
        "engagement": float(agg("engagement")),
    }
