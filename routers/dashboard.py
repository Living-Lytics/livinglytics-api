from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import uuid

from database import get_db
from models import User, DataSource, UserDashboardLayout, AppSetting
from auth.security import get_current_user_email

router = APIRouter(prefix="/v1/dashboard", tags=["dashboard"])

VALID_WIDGET_KEYS = {
    "ga4.users", "ga4.sessions", "ga4.conv_rate", "ga4.traffic_channels",
    "meta.roas", "meta.cost_metrics",
    "ig.engagement_rate", "ig.content_perf",
    "corr.spend_vs_sessions"
}

class WidgetConfig(BaseModel):
    id: str
    size: str

class LayoutRequest(BaseModel):
    widgets: List[Dict[str, Any]]

@router.get("/meta")
def get_dashboard_meta(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get dashboard metadata including last sync, next scheduled sync, and connected sources"""
    email = get_current_user_email(request)
    
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        return {
            "last_sync_at": None,
            "next_scheduled_at": None,
            "connected_sources": {"ga4": False, "instagram": False, "meta": False}
        }
    
    # Get last sync time from app_settings
    last_sync_setting = db.execute(
        select(AppSetting).where(AppSetting.key == "last_sync")
    ).scalar_one_or_none()
    last_sync_at = last_sync_setting.value.get("timestamp") if last_sync_setting and last_sync_setting.value else None
    
    # Next scheduled sync is always 00:15 America/Los_Angeles (next day)
    # For now, we'll return a placeholder
    next_scheduled_at = None  # Will be computed by scheduler
    
    # Get connected sources
    connected_sources_result = db.execute(
        select(DataSource.source_name).where(DataSource.user_id == user.id)
    ).scalars().all()
    
    connected_sources = {
        "ga4": "google_analytics" in connected_sources_result,
        "instagram": "instagram" in connected_sources_result,
        "meta": "meta" in connected_sources_result
    }
    
    return {
        "last_sync_at": last_sync_at,
        "next_scheduled_at": next_scheduled_at,
        "connected_sources": connected_sources
    }

@router.get("/layout")
def get_dashboard_layout(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get user's dashboard layout"""
    email = get_current_user_email(request)
    
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        return {"widgets": []}
    
    layout = db.execute(
        select(UserDashboardLayout).where(UserDashboardLayout.user_id == user.id)
    ).scalar_one_or_none()
    
    if not layout:
        return {"widgets": []}
    
    return layout.layout

@router.post("/layout")
def save_dashboard_layout(
    layout_request: LayoutRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Save user's dashboard layout with widget validation"""
    email = get_current_user_email(request)
    
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate widget keys
    for widget in layout_request.widgets:
        if widget.get("id") not in VALID_WIDGET_KEYS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid widget key: {widget.get('id')}"
            )
    
    # Upsert layout
    existing_layout = db.execute(
        select(UserDashboardLayout).where(UserDashboardLayout.user_id == user.id)
    ).scalar_one_or_none()
    
    layout_data = {"widgets": layout_request.widgets, "version": 1}
    
    if existing_layout:
        existing_layout.layout = layout_data
        existing_layout.updated_at = datetime.utcnow()
    else:
        new_layout = UserDashboardLayout(
            user_id=user.id,
            layout=layout_data
        )
        db.add(new_layout)
    
    db.commit()
    
    return {"success": True, "layout": layout_data}
