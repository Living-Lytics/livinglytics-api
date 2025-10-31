from fastapi import APIRouter, Depends, Request, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid

from database import get_db
from models import User, DataSource, Metric
from auth.security import get_current_user_email

router = APIRouter(prefix="/v1/widgets", tags=["widgets"])

class DataPoint(BaseModel):
    t: str  # ISO date
    v: float

class SeriesData(BaseModel):
    name: str
    points: List[DataPoint]

class StatsData(BaseModel):
    value: float
    delta: Optional[float] = None

class WidgetResponse(BaseModel):
    series: List[SeriesData]
    stats: StatsData

def calculate_compare_period(start_date: date, end_date: date) -> tuple[date, date]:
    """Calculate the comparison period based on the main period"""
    delta = end_date - start_date
    compare_end = start_date - timedelta(days=1)
    compare_start = compare_end - delta
    return compare_start, compare_end

def decimal_to_float(val: Optional[Decimal]) -> float:
    """Convert Decimal to float, handling None"""
    if val is None:
        return 0.0
    return float(val)

# Widget handler functions
async def widget_ga4_users(
    db: Session,
    user_id: uuid.UUID,
    start_date: date,
    end_date: date,
    compare_mode: str
) -> WidgetResponse:
    """GA4 Total Users widget"""
    # Query main period
    result = db.execute(
        select(Metric.metric_date, func.sum(Metric.metric_value).label("value"))
        .where(
            Metric.user_id == user_id,
            Metric.source_name == "google_analytics",
            Metric.metric_name == "total_users",
            Metric.metric_date >= start_date,
            Metric.metric_date <= end_date
        )
        .group_by(Metric.metric_date)
        .order_by(Metric.metric_date)
    ).all()
    
    points = [DataPoint(t=str(row.metric_date), v=decimal_to_float(row.value)) for row in result]
    total_value = sum(p.v for p in points)
    
    # Calculate delta if compare mode is not off
    delta = None
    if compare_mode != "off":
        compare_start, compare_end = calculate_compare_period(start_date, end_date)
        compare_result = db.execute(
            select(func.sum(Metric.metric_value))
            .where(
                Metric.user_id == user_id,
                Metric.source_name == "google_analytics",
                Metric.metric_name == "total_users",
                Metric.metric_date >= compare_start,
                Metric.metric_date <= compare_end
            )
        ).scalar()
        
        compare_value = decimal_to_float(compare_result)
        if compare_value > 0:
            delta = (total_value - compare_value) / compare_value
    
    return WidgetResponse(
        series=[SeriesData(name="Users", points=points)],
        stats=StatsData(value=total_value, delta=delta)
    )

async def widget_ga4_sessions(
    db: Session,
    user_id: uuid.UUID,
    start_date: date,
    end_date: date,
    compare_mode: str
) -> WidgetResponse:
    """GA4 Sessions widget"""
    result = db.execute(
        select(Metric.metric_date, func.sum(Metric.metric_value).label("value"))
        .where(
            Metric.user_id == user_id,
            Metric.source_name == "google_analytics",
            Metric.metric_name == "sessions",
            Metric.metric_date >= start_date,
            Metric.metric_date <= end_date
        )
        .group_by(Metric.metric_date)
        .order_by(Metric.metric_date)
    ).all()
    
    points = [DataPoint(t=str(row.metric_date), v=decimal_to_float(row.value)) for row in result]
    total_value = sum(p.v for p in points)
    
    delta = None
    if compare_mode != "off":
        compare_start, compare_end = calculate_compare_period(start_date, end_date)
        compare_result = db.execute(
            select(func.sum(Metric.metric_value))
            .where(
                Metric.user_id == user_id,
                Metric.source_name == "google_analytics",
                Metric.metric_name == "sessions",
                Metric.metric_date >= compare_start,
                Metric.metric_date <= compare_end
            )
        ).scalar()
        
        compare_value = decimal_to_float(compare_result)
        if compare_value > 0:
            delta = (total_value - compare_value) / compare_value
    
    return WidgetResponse(
        series=[SeriesData(name="Sessions", points=points)],
        stats=StatsData(value=total_value, delta=delta)
    )

async def widget_ga4_conv_rate(
    db: Session,
    user_id: uuid.UUID,
    start_date: date,
    end_date: date,
    compare_mode: str
) -> WidgetResponse:
    """GA4 Conversion Rate widget"""
    result = db.execute(
        select(Metric.metric_date, func.avg(Metric.metric_value).label("value"))
        .where(
            Metric.user_id == user_id,
            Metric.source_name == "google_analytics",
            Metric.metric_name == "conversion_rate",
            Metric.metric_date >= start_date,
            Metric.metric_date <= end_date
        )
        .group_by(Metric.metric_date)
        .order_by(Metric.metric_date)
    ).all()
    
    points = [DataPoint(t=str(row.metric_date), v=decimal_to_float(row.value)) for row in result]
    avg_value = sum(p.v for p in points) / len(points) if points else 0.0
    
    delta = None
    if compare_mode != "off":
        compare_start, compare_end = calculate_compare_period(start_date, end_date)
        compare_result = db.execute(
            select(func.avg(Metric.metric_value))
            .where(
                Metric.user_id == user_id,
                Metric.source_name == "google_analytics",
                Metric.metric_name == "conversion_rate",
                Metric.metric_date >= compare_start,
                Metric.metric_date <= compare_end
            )
        ).scalar()
        
        compare_value = decimal_to_float(compare_result)
        if compare_value > 0:
            delta = (avg_value - compare_value) / compare_value
    
    return WidgetResponse(
        series=[SeriesData(name="Conversion Rate", points=points)],
        stats=StatsData(value=avg_value, delta=delta)
    )

async def widget_ga4_traffic_channels(
    db: Session,
    user_id: uuid.UUID,
    start_date: date,
    end_date: date,
    compare_mode: str
) -> WidgetResponse:
    """GA4 Traffic by Channel widget"""
    # Get top channels from metadata
    result = db.execute(
        select(Metric.metric_date, Metric.meta, func.sum(Metric.metric_value).label("value"))
        .where(
            Metric.user_id == user_id,
            Metric.source_name == "google_analytics",
            Metric.metric_name == "sessions",
            Metric.metric_date >= start_date,
            Metric.metric_date <= end_date
        )
        .group_by(Metric.metric_date, Metric.meta)
        .order_by(Metric.metric_date)
    ).all()
    
    # Aggregate by channel
    channel_data = {}
    total = 0.0
    for row in result:
        channel = row.meta.get("channel", "Direct") if row.meta else "Direct"
        if channel not in channel_data:
            channel_data[channel] = []
        channel_data[channel].append(DataPoint(t=str(row.metric_date), v=decimal_to_float(row.value)))
        total += decimal_to_float(row.value)
    
    series = [SeriesData(name=channel, points=points) for channel, points in channel_data.items()]
    
    return WidgetResponse(
        series=series,
        stats=StatsData(value=total, delta=None)
    )

async def widget_meta_roas(
    db: Session,
    user_id: uuid.UUID,
    start_date: date,
    end_date: date,
    compare_mode: str
) -> WidgetResponse:
    """Meta ROAS widget"""
    result = db.execute(
        select(Metric.metric_date, func.avg(Metric.metric_value).label("value"))
        .where(
            Metric.user_id == user_id,
            Metric.source_name == "meta",
            Metric.metric_name == "roas",
            Metric.metric_date >= start_date,
            Metric.metric_date <= end_date
        )
        .group_by(Metric.metric_date)
        .order_by(Metric.metric_date)
    ).all()
    
    points = [DataPoint(t=str(row.metric_date), v=decimal_to_float(row.value)) for row in result]
    avg_value = sum(p.v for p in points) / len(points) if points else 0.0
    
    delta = None
    if compare_mode != "off":
        compare_start, compare_end = calculate_compare_period(start_date, end_date)
        compare_result = db.execute(
            select(func.avg(Metric.metric_value))
            .where(
                Metric.user_id == user_id,
                Metric.source_name == "meta",
                Metric.metric_name == "roas",
                Metric.metric_date >= compare_start,
                Metric.metric_date <= compare_end
            )
        ).scalar()
        
        compare_value = decimal_to_float(compare_result)
        if compare_value > 0:
            delta = (avg_value - compare_value) / compare_value
    
    return WidgetResponse(
        series=[SeriesData(name="ROAS", points=points)],
        stats=StatsData(value=avg_value, delta=delta)
    )

async def widget_meta_cost_metrics(
    db: Session,
    user_id: uuid.UUID,
    start_date: date,
    end_date: date,
    compare_mode: str
) -> WidgetResponse:
    """Meta Cost Metrics widget (CPC, CPM, etc)"""
    # Get cost per click
    cpc_result = db.execute(
        select(Metric.metric_date, func.avg(Metric.metric_value).label("value"))
        .where(
            Metric.user_id == user_id,
            Metric.source_name == "meta",
            Metric.metric_name == "cpc",
            Metric.metric_date >= start_date,
            Metric.metric_date <= end_date
        )
        .group_by(Metric.metric_date)
        .order_by(Metric.metric_date)
    ).all()
    
    cpc_points = [DataPoint(t=str(row.metric_date), v=decimal_to_float(row.value)) for row in cpc_result]
    avg_cpc = sum(p.v for p in cpc_points) / len(cpc_points) if cpc_points else 0.0
    
    return WidgetResponse(
        series=[SeriesData(name="CPC", points=cpc_points)],
        stats=StatsData(value=avg_cpc, delta=None)
    )

async def widget_ig_engagement_rate(
    db: Session,
    user_id: uuid.UUID,
    start_date: date,
    end_date: date,
    compare_mode: str
) -> WidgetResponse:
    """Instagram Engagement Rate widget"""
    result = db.execute(
        select(Metric.metric_date, func.avg(Metric.metric_value).label("value"))
        .where(
            Metric.user_id == user_id,
            Metric.source_name == "instagram",
            Metric.metric_name == "engagement",
            Metric.metric_date >= start_date,
            Metric.metric_date <= end_date
        )
        .group_by(Metric.metric_date)
        .order_by(Metric.metric_date)
    ).all()
    
    points = [DataPoint(t=str(row.metric_date), v=decimal_to_float(row.value)) for row in result]
    avg_value = sum(p.v for p in points) / len(points) if points else 0.0
    
    delta = None
    if compare_mode != "off":
        compare_start, compare_end = calculate_compare_period(start_date, end_date)
        compare_result = db.execute(
            select(func.avg(Metric.metric_value))
            .where(
                Metric.user_id == user_id,
                Metric.source_name == "instagram",
                Metric.metric_name == "engagement",
                Metric.metric_date >= compare_start,
                Metric.metric_date <= compare_end
            )
        ).scalar()
        
        compare_value = decimal_to_float(compare_result)
        if compare_value > 0:
            delta = (avg_value - compare_value) / compare_value
    
    return WidgetResponse(
        series=[SeriesData(name="Engagement", points=points)],
        stats=StatsData(value=avg_value, delta=delta)
    )

async def widget_ig_content_perf(
    db: Session,
    user_id: uuid.UUID,
    start_date: date,
    end_date: date,
    compare_mode: str
) -> WidgetResponse:
    """Instagram Content Performance widget"""
    # Get reach data
    result = db.execute(
        select(Metric.metric_date, func.sum(Metric.metric_value).label("value"))
        .where(
            Metric.user_id == user_id,
            Metric.source_name == "instagram",
            Metric.metric_name == "reach",
            Metric.metric_date >= start_date,
            Metric.metric_date <= end_date
        )
        .group_by(Metric.metric_date)
        .order_by(Metric.metric_date)
    ).all()
    
    points = [DataPoint(t=str(row.metric_date), v=decimal_to_float(row.value)) for row in result]
    total_value = sum(p.v for p in points)
    
    return WidgetResponse(
        series=[SeriesData(name="Reach", points=points)],
        stats=StatsData(value=total_value, delta=None)
    )

async def widget_corr_spend_vs_sessions(
    db: Session,
    user_id: uuid.UUID,
    start_date: date,
    end_date: date,
    compare_mode: str
) -> WidgetResponse:
    """Correlation: Meta Spend vs GA4 Sessions"""
    # Get Meta spend
    spend_result = db.execute(
        select(Metric.metric_date, func.sum(Metric.metric_value).label("value"))
        .where(
            Metric.user_id == user_id,
            Metric.source_name == "meta",
            Metric.metric_name == "spend",
            Metric.metric_date >= start_date,
            Metric.metric_date <= end_date
        )
        .group_by(Metric.metric_date)
        .order_by(Metric.metric_date)
    ).all()
    
    spend_points = [DataPoint(t=str(row.metric_date), v=decimal_to_float(row.value)) for row in spend_result]
    
    # Get GA4 sessions
    sessions_result = db.execute(
        select(Metric.metric_date, func.sum(Metric.metric_value).label("value"))
        .where(
            Metric.user_id == user_id,
            Metric.source_name == "google_analytics",
            Metric.metric_name == "sessions",
            Metric.metric_date >= start_date,
            Metric.metric_date <= end_date
        )
        .group_by(Metric.metric_date)
        .order_by(Metric.metric_date)
    ).all()
    
    sessions_points = [DataPoint(t=str(row.metric_date), v=decimal_to_float(row.value)) for row in sessions_result]
    
    total_spend = sum(p.v for p in spend_points)
    total_sessions = sum(p.v for p in sessions_points)
    
    return WidgetResponse(
        series=[
            SeriesData(name="Spend", points=spend_points),
            SeriesData(name="Sessions", points=sessions_points)
        ],
        stats=StatsData(value=total_spend, delta=None)
    )

# Widget registry
WIDGET_HANDLERS = {
    "ga4.users": widget_ga4_users,
    "ga4.sessions": widget_ga4_sessions,
    "ga4.conv_rate": widget_ga4_conv_rate,
    "ga4.traffic_channels": widget_ga4_traffic_channels,
    "meta.roas": widget_meta_roas,
    "meta.cost_metrics": widget_meta_cost_metrics,
    "ig.engagement_rate": widget_ig_engagement_rate,
    "ig.content_perf": widget_ig_content_perf,
    "corr.spend_vs_sessions": widget_corr_spend_vs_sessions,
}

@router.get("/{key}")
async def get_widget_data(
    key: str,
    start: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end: date = Query(..., description="End date (YYYY-MM-DD)"),
    compare: str = Query("off", description="Compare mode: off, previous, custom"),
    request: Request = None,
    db: Session = Depends(get_db)
) -> WidgetResponse:
    """Get widget data for a specific key with date range and compare mode"""
    email = get_current_user_email(request)
    
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate widget key
    if key not in WIDGET_HANDLERS:
        raise HTTPException(status_code=404, detail=f"Widget '{key}' not found")
    
    # Get widget handler and execute
    handler = WIDGET_HANDLERS[key]
    try:
        result = await handler(db, user.id, start, end, compare)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching widget data: {str(e)}")
