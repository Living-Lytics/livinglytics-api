from fastapi import APIRouter, Depends, Request, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid
import os
import json

from db import get_db
from models import User, DataSource, Metric
from auth.security import get_current_user_email_optional

router = APIRouter(prefix="/v1/insights", tags=["insights"])

class InsightGroup(BaseModel):
    group: str
    bullets: List[str]

class InsightsResponse(BaseModel):
    items: List[InsightGroup]

def decimal_to_float(val: Optional[Decimal]) -> float:
    """Convert Decimal to float, handling None"""
    if val is None:
        return 0.0
    return float(val)

def calculate_compare_period(start_date: date, end_date: date) -> tuple[date, date]:
    """Calculate the comparison period based on the main period"""
    delta = end_date - start_date
    compare_end = start_date - timedelta(days=1)
    compare_start = compare_end - delta
    return compare_start, compare_end

async def gather_insights_context(
    db: Session,
    user_id: uuid.UUID,
    start_date: date,
    end_date: date,
    connected_sources: Dict[str, bool]
) -> Dict[str, Any]:
    """Gather key aggregates for insights generation"""
    context = {}
    compare_start, compare_end = calculate_compare_period(start_date, end_date)
    
    # GA4 metrics
    if connected_sources.get("ga4", False):
        # Sessions
        sessions = db.execute(
            select(func.sum(Metric.metric_value))
            .where(
                Metric.user_id == user_id,
                Metric.source_name == "google_analytics",
                Metric.metric_name == "sessions",
                Metric.metric_date >= start_date,
                Metric.metric_date <= end_date
            )
        ).scalar()
        
        sessions_prev = db.execute(
            select(func.sum(Metric.metric_value))
            .where(
                Metric.user_id == user_id,
                Metric.source_name == "google_analytics",
                Metric.metric_name == "sessions",
                Metric.metric_date >= compare_start,
                Metric.metric_date <= compare_end
            )
        ).scalar()
        
        context["ga4_sessions"] = decimal_to_float(sessions)
        context["ga4_sessions_prev"] = decimal_to_float(sessions_prev)
        context["ga4_sessions_change"] = (
            ((context["ga4_sessions"] - context["ga4_sessions_prev"]) / context["ga4_sessions_prev"])
            if context["ga4_sessions_prev"] > 0 else 0
        )
    
    # Instagram metrics
    if connected_sources.get("instagram", False):
        # Reach
        reach = db.execute(
            select(func.sum(Metric.metric_value))
            .where(
                Metric.user_id == user_id,
                Metric.source_name == "instagram",
                Metric.metric_name == "reach",
                Metric.metric_date >= start_date,
                Metric.metric_date <= end_date
            )
        ).scalar()
        
        # Engagement
        engagement = db.execute(
            select(func.avg(Metric.metric_value))
            .where(
                Metric.user_id == user_id,
                Metric.source_name == "instagram",
                Metric.metric_name == "engagement",
                Metric.metric_date >= start_date,
                Metric.metric_date <= end_date
            )
        ).scalar()
        
        context["ig_reach"] = decimal_to_float(reach)
        context["ig_engagement"] = decimal_to_float(engagement)
    
    # Meta metrics
    if connected_sources.get("meta", False):
        # Spend
        spend = db.execute(
            select(func.sum(Metric.metric_value))
            .where(
                Metric.user_id == user_id,
                Metric.source_name == "meta",
                Metric.metric_name == "spend",
                Metric.metric_date >= start_date,
                Metric.metric_date <= end_date
            )
        ).scalar()
        
        # ROAS
        roas = db.execute(
            select(func.avg(Metric.metric_value))
            .where(
                Metric.user_id == user_id,
                Metric.source_name == "meta",
                Metric.metric_name == "roas",
                Metric.metric_date >= start_date,
                Metric.metric_date <= end_date
            )
        ).scalar()
        
        context["meta_spend"] = decimal_to_float(spend)
        context["meta_roas"] = decimal_to_float(roas)
    
    return context

async def generate_llm_insights(context: Dict[str, Any]) -> Optional[List[InsightGroup]]:
    """Generate insights using OpenAI LLM"""
    try:
        import openai
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        
        client = openai.OpenAI(api_key=api_key)
        
        prompt = f"""You are an analytics insights assistant. Based on the following data, generate 3-5 short, actionable insights grouped by theme (Cross-channel, Ads, Traffic, etc.). Only cite metrics that are present in the data.

Data: {json.dumps(context, indent=2)}

Return your response as a JSON object with this structure:
{{
  "items": [
    {{"group": "Cross-channel", "bullets": ["insight 1", "insight 2"]}},
    {{"group": "Ads", "bullets": ["insight 3"]}},
    {{"group": "Traffic", "bullets": ["insight 4", "insight 5"]}}
  ]
}}

Keep insights concise (1-2 sentences each) and actionable."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data analytics assistant that provides actionable insights."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return [InsightGroup(**item) for item in result.get("items", [])]
    
    except Exception as e:
        print(f"LLM insights generation failed: {e}")
        return None

def generate_rule_based_insights(context: Dict[str, Any], connected_sources: Dict[str, bool]) -> List[InsightGroup]:
    """Generate fallback rule-based insights"""
    insights = []
    
    # Traffic insights
    if "ga4_sessions_change" in context:
        traffic_bullets = []
        change_pct = context["ga4_sessions_change"] * 100
        
        if abs(change_pct) > 5:
            direction = "increased" if change_pct > 0 else "decreased"
            traffic_bullets.append(
                f"Sessions {direction} by {abs(change_pct):.1f}% vs previous period."
            )
        else:
            traffic_bullets.append("Sessions remained stable compared to previous period.")
        
        if traffic_bullets:
            insights.append(InsightGroup(group="Traffic", bullets=traffic_bullets))
    
    # Instagram insights
    if connected_sources.get("instagram", False) and "ig_reach" in context:
        ig_bullets = []
        if context["ig_reach"] > 0:
            ig_bullets.append(
                f"Instagram reached {context['ig_reach']:.0f} users during this period."
            )
        if context.get("ig_engagement", 0) > 0:
            ig_bullets.append(
                f"Average engagement rate: {context['ig_engagement']:.2f}%."
            )
        
        if ig_bullets:
            insights.append(InsightGroup(group="Social Media", bullets=ig_bullets))
    
    # Meta/Ads insights
    if connected_sources.get("meta", False) and "meta_spend" in context:
        ads_bullets = []
        if context["meta_spend"] > 0:
            ads_bullets.append(
                f"Ad spend: ${context['meta_spend']:.2f} with ROAS of {context.get('meta_roas', 0):.2f}x."
            )
        
        if ads_bullets:
            insights.append(InsightGroup(group="Ads", bullets=ads_bullets))
    
    # Cross-channel insights
    if connected_sources.get("ga4", False) and connected_sources.get("meta", False):
        if "ga4_sessions" in context and "meta_spend" in context:
            if context["meta_spend"] > 0 and context["ga4_sessions"] > 0:
                cost_per_session = context["meta_spend"] / context["ga4_sessions"]
                insights.append(InsightGroup(
                    group="Cross-channel",
                    bullets=[f"Cost per session: ${cost_per_session:.2f}. Consider optimizing ad targeting."]
                ))
    
    return insights if insights else [InsightGroup(group="General", bullets=["Not enough data available for insights."])]

@router.get("")
async def get_insights(
    request: Request,
    start: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end: date = Query(..., description="End date (YYYY-MM-DD)"),
    compare: str = Query("off", description="Compare mode: off, previous, custom"),
    db: Session = Depends(get_db)
) -> InsightsResponse:
    """Generate AI-powered insights based on connected data sources and date range"""
    email = get_current_user_email_optional(request)
    if not email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get connected sources
    connected_sources_result = db.execute(
        select(DataSource.source_name).where(DataSource.user_id == user.id)
    ).scalars().all()
    
    connected_sources = {
        "ga4": "google_analytics" in connected_sources_result,
        "instagram": "instagram" in connected_sources_result,
        "meta": "meta" in connected_sources_result
    }
    
    # Gather context
    context = await gather_insights_context(db, user.id, start, end, connected_sources)
    context["connected_sources"] = connected_sources
    
    # Try LLM first, fall back to rule-based
    llm_insights = await generate_llm_insights(context)
    
    if llm_insights:
        return InsightsResponse(items=llm_insights)
    else:
        rule_insights = generate_rule_based_insights(context, connected_sources)
        return InsightsResponse(items=rule_insights)
