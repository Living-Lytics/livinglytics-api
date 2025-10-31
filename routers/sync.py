from fastapi import APIRouter, Depends, Request, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import uuid
import asyncio
import os

from db import get_db
from models import User, DataSource, AppSetting

router = APIRouter(prefix="/v1/sync", tags=["sync"])

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class SyncJob(BaseModel):
    job_id: str
    status: JobStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    results: Optional[Dict[str, Any]] = None

# In-memory job tracking (would use Redis in production)
SYNC_JOBS: Dict[str, SyncJob] = {}

def require_admin_token(authorization: str = Header(None)):
    """Verify admin token for admin-only endpoints"""
    admin_token = os.getenv("ADMIN_TOKEN")
    if not admin_token:
        raise HTTPException(status_code=500, detail="Admin token not configured")
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token = authorization.replace("Bearer ", "")
    if token != admin_token:
        raise HTTPException(status_code=403, detail="Invalid admin token")
    
    return True

async def sync_ga4_data(db: Session, user_id: uuid.UUID) -> Dict[str, Any]:
    """Sync GA4 data for a user (stub - reuse existing sync logic)"""
    # TODO: Import and call your existing GA4 sync service
    return {"source": "ga4", "records": 0, "success": True}

async def sync_instagram_data(db: Session, user_id: uuid.UUID) -> Dict[str, Any]:
    """Sync Instagram data for a user (stub - reuse existing sync logic)"""
    # TODO: Import and call your existing Instagram sync service
    return {"source": "instagram", "records": 0, "success": True}

async def sync_meta_data(db: Session, user_id: uuid.UUID) -> Dict[str, Any]:
    """Sync Meta data for a user (stub - reuse existing sync logic)"""
    # TODO: Import and call your existing Meta sync service
    return {"source": "meta", "records": 0, "success": True}

async def run_sync_job(job_id: str, db: Session):
    """Background task to run sync job"""
    job = SYNC_JOBS.get(job_id)
    if not job:
        return
    
    try:
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        
        results = {
            "sources_synced": [],
            "total_records": 0,
            "errors": []
        }
        
        # Get all users with connected data sources
        users_result = db.execute(
            select(User.id, DataSource.source_name)
            .join(DataSource, User.id == DataSource.user_id)
            .distinct()
        ).all()
        
        user_sources = {}
        for user_id, source_name in users_result:
            if user_id not in user_sources:
                user_sources[user_id] = []
            user_sources[user_id].append(source_name)
        
        # Sync each user's connected sources
        for user_id, sources in user_sources.items():
            for source in sources:
                try:
                    if source == "google_analytics":
                        result = await sync_ga4_data(db, user_id)
                        results["sources_synced"].append(result)
                        results["total_records"] += result.get("records", 0)
                    elif source == "instagram":
                        result = await sync_instagram_data(db, user_id)
                        results["sources_synced"].append(result)
                        results["total_records"] += result.get("records", 0)
                    elif source == "meta":
                        result = await sync_meta_data(db, user_id)
                        results["sources_synced"].append(result)
                        results["total_records"] += result.get("records", 0)
                except Exception as e:
                    results["errors"].append(f"{source}: {str(e)}")
        
        # Update last sync timestamp
        last_sync_setting = db.execute(
            select(AppSetting).where(AppSetting.key == "last_sync")
        ).scalar_one_or_none()
        
        sync_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "job_id": job_id,
            "records_synced": results["total_records"]
        }
        
        if last_sync_setting:
            last_sync_setting.value = sync_data
            last_sync_setting.updated_at = datetime.utcnow()
        else:
            new_setting = AppSetting(key="last_sync", value=sync_data)
            db.add(new_setting)
        
        db.commit()
        
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.results = results
        
    except Exception as e:
        job.status = JobStatus.FAILED
        job.completed_at = datetime.utcnow()
        job.error = str(e)
        db.rollback()

@router.post("/all/run")
async def trigger_sync(
    db: Session = Depends(get_db),
    _admin: bool = Depends(require_admin_token)
):
    """Manually trigger sync for all connected data sources (admin only)"""
    job_id = str(uuid.uuid4())
    
    # Create job
    job = SyncJob(
        job_id=job_id,
        status=JobStatus.PENDING
    )
    SYNC_JOBS[job_id] = job
    
    # Run sync in background
    asyncio.create_task(run_sync_job(job_id, db))
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Sync job started"
    }

@router.get("/job/{job_id}")
async def get_sync_job(
    job_id: str,
    _admin: bool = Depends(require_admin_token)
):
    """Get sync job status and results (admin only)"""
    job = SYNC_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job

@router.get("/status")
async def get_sync_status(
    db: Session = Depends(get_db),
    _admin: bool = Depends(require_admin_token)
):
    """Get overall sync status and recent jobs (admin only)"""
    # Get last sync info
    last_sync_setting = db.execute(
        select(AppSetting).where(AppSetting.key == "last_sync")
    ).scalar_one_or_none()
    
    last_sync_info = last_sync_setting.value if last_sync_setting else None
    
    # Get recent jobs
    recent_jobs = [
        {
            "job_id": job.job_id,
            "status": job.status,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }
        for job in list(SYNC_JOBS.values())[-10:]  # Last 10 jobs
    ]
    
    return {
        "last_sync": last_sync_info,
        "recent_jobs": recent_jobs,
        "total_jobs": len(SYNC_JOBS)
    }

# Scheduled sync function (called by APScheduler)
async def scheduled_sync():
    """Daily scheduled sync at 00:15 America/Los_Angeles"""
    from db import SessionLocal
    
    db = SessionLocal()
    try:
        job_id = f"scheduled-{datetime.utcnow().isoformat()}"
        job = SyncJob(job_id=job_id, status=JobStatus.PENDING)
        SYNC_JOBS[job_id] = job
        
        await run_sync_job(job_id, db)
        
        print(f"[SYNC-SCHEDULER] Completed scheduled sync job: {job_id}")
    except Exception as e:
        print(f"[SYNC-SCHEDULER] Error in scheduled sync: {e}")
    finally:
        db.close()
