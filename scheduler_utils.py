"""
Scheduler utilities for automatic weekly digests.
Handles period calculations, digest sending, and idempotent tracking.
"""
import os
import logging
import jwt
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from typing import Tuple, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from models import User, Metric, DigestLog
from mailer import send_email_resend

# Pacific timezone for all digest operations
PT = ZoneInfo("America/Los_Angeles")

# JWT secret for unsubscribe tokens
JWT_SECRET = os.getenv("FASTAPI_SECRET_KEY", "changeme")

def get_last_completed_week(tz: str = "America/Los_Angeles") -> Tuple[date, date]:
    """
    Calculate the last completed week (Monday 00:00:00 through Sunday 23:59:59).
    
    Args:
        tz: Timezone string (default: America/Los_Angeles)
    
    Returns:
        Tuple of (period_start_date, period_end_date)
    
    Example:
        If today is Tuesday Oct 24, 2025:
        - Returns (Oct 14, Oct 20) - the previous Monday-Sunday
    """
    timezone = ZoneInfo(tz)
    now = datetime.now(timezone)
    
    # Find current week's Monday
    days_since_monday = now.weekday()  # Monday=0, Sunday=6
    current_monday = (now - timedelta(days=days_since_monday)).date()
    
    # Last completed week ended last Sunday
    last_sunday = current_monday - timedelta(days=1)
    last_monday = last_sunday - timedelta(days=6)
    
    return (last_monday, last_sunday)

def generate_unsubscribe_token(user_id: str) -> str:
    """Generate JWT token for unsubscribe link."""
    payload = {
        "user_id": str(user_id),
        "purpose": "unsubscribe",
        "exp": datetime.utcnow() + timedelta(days=365)  # Valid for 1 year
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_unsubscribe_token(token: str) -> Optional[str]:
    """Verify and decode unsubscribe token. Returns user_id if valid."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("purpose") == "unsubscribe":
            return payload.get("user_id")
    except jwt.InvalidTokenError:
        pass
    return None

def _collect_kpis_for_period(
    user_id: str, 
    period_start: date, 
    period_end: date, 
    db: Session
) -> Dict[str, Any]:
    """
    Collect KPIs for a user within the date range.
    Returns totals and daily timeline.
    """
    # Query metrics for the period
    results = db.execute(
        select(
            Metric.metric_date,
            Metric.metric_name,
            func.sum(Metric.metric_value).label("total")
        )
        .where(Metric.user_id == user_id)
        .where(Metric.metric_date >= period_start)
        .where(Metric.metric_date <= period_end)
        .group_by(Metric.metric_date, Metric.metric_name)
        .order_by(Metric.metric_date)
    ).all()
    
    # Initialize timeline with all dates
    timeline = {}
    current_date = period_start
    while current_date <= period_end:
        timeline[current_date] = {
            "date": current_date,
            "sessions": 0,
            "conversions": 0,
            "reach": 0,
            "engagement": 0
        }
        current_date += timedelta(days=1)
    
    # Fill in actual data
    for metric_date, metric_name, total in results:
        if metric_name in timeline[metric_date]:
            timeline[metric_date][metric_name] = int(total) if total else 0
    
    # Calculate totals
    totals = {
        "sessions": 0,
        "conversions": 0,
        "reach": 0,
        "engagement": 0
    }
    
    for day_data in timeline.values():
        for metric in ["sessions", "conversions", "reach", "engagement"]:
            totals[metric] += day_data[metric]
    
    # Find best day (by conversions, fallback to sessions)
    best_day = max(timeline.values(), key=lambda x: (x["conversions"], x["sessions"]))
    
    return {
        "totals": totals,
        "timeline": list(timeline.values()),
        "best_day": best_day
    }

def _render_digest_html(
    user_email: str,
    user_id: str,
    period_start: date,
    period_end: date,
    kpis: Dict[str, Any],
    wow_deltas: Optional[Dict[str, float]] = None
) -> str:
    """Render HTML email for weekly digest with WoW deltas and unsubscribe link."""
    totals = kpis["totals"]
    best_day = kpis["best_day"]
    timeline = kpis["timeline"]
    
    period_str = f"{period_start.strftime('%b %d')} - {period_end.strftime('%b %d, %Y')}"
    
    # Helper to render delta badges
    def delta_badge(metric: str) -> str:
        if not wow_deltas or metric not in wow_deltas:
            return ""
        delta = wow_deltas[metric]
        if delta == 0:
            return ""
        
        color = "#10b981" if delta > 0 else "#ef4444"
        arrow = "↑" if delta > 0 else "↓"
        return f'<div style="color: {color}; font-size: 14px; margin-top: 5px;">{arrow} {abs(delta):.1f}% vs last week</div>'
    
    # Generate unsubscribe token and link
    unsubscribe_token = generate_unsubscribe_token(user_id)
    unsubscribe_url = f"https://api.livinglytics.com/v1/digest/unsubscribe?token={unsubscribe_token}"
    
    # Generate insights
    insights = []
    if totals["reach"] > 20000:
        insights.append(f"🎯 Strong reach: {totals['reach']:,} impressions")
    if totals["engagement"] > 1000:
        insights.append(f"💬 Great engagement: {totals['engagement']:,} interactions")
    if totals["conversions"] > 500:
        insights.append(f"🚀 Excellent conversions: {totals['conversions']:,}")
    
    if not insights:
        insights.append("📊 Keep building your presence!")
    
    insights_html = "".join([f"<li>{insight}</li>" for insight in insights])
    
    # Timeline sparkline data
    timeline_html = ""
    for day in timeline:
        day_str = day["date"].strftime("%a %m/%d")
        timeline_html += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">{day_str}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{day['sessions']:,}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{day['conversions']:,}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{day['reach']:,}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: right;">{day['engagement']:,}</td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center;">
                <h1 style="margin: 0; font-size: 28px;">Your Weekly Analytics</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">{period_str}</p>
            </div>
            
            <!-- Summary Cards -->
            <div style="padding: 30px;">
                <h2 style="margin: 0 0 20px 0; color: #333;">📊 Week Summary</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 30px;">
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea;">
                        <div style="color: #666; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">Sessions</div>
                        <div style="font-size: 32px; font-weight: bold; color: #333; margin-top: 5px;">{totals['sessions']:,}</div>
                        {delta_badge('sessions')}
                    </div>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #f093fb;">
                        <div style="color: #666; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">Conversions</div>
                        <div style="font-size: 32px; font-weight: bold; color: #333; margin-top: 5px;">{totals['conversions']:,}</div>
                        {delta_badge('conversions')}
                    </div>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #4facfe;">
                        <div style="color: #666; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">Reach</div>
                        <div style="font-size: 32px; font-weight: bold; color: #333; margin-top: 5px;">{totals['reach']:,}</div>
                        {delta_badge('reach')}
                    </div>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #43e97b;">
                        <div style="color: #666; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">Engagement</div>
                        <div style="font-size: 32px; font-weight: bold; color: #333; margin-top: 5px;">{totals['engagement']:,}</div>
                        {delta_badge('engagement')}
                    </div>
                </div>
                
                <!-- Insights -->
                <h2 style="margin: 30px 0 15px 0; color: #333;">💡 Key Insights</h2>
                <ul style="list-style: none; padding: 0; margin: 0;">
                    {insights_html}
                </ul>
                
                <!-- Best Day -->
                <div style="background: #fff8e1; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffd54f;">
                    <h3 style="margin: 0 0 10px 0; color: #f57c00;">⭐ Best Day</h3>
                    <p style="margin: 0; color: #666;">
                        <strong>{best_day['date'].strftime('%A, %B %d')}</strong> was your highest performing day with <strong>{best_day['conversions']:,} conversions</strong> and <strong>{best_day['sessions']:,} sessions</strong>.
                    </p>
                </div>
                
                <!-- Daily Breakdown -->
                <h2 style="margin: 30px 0 15px 0; color: #333;">📈 Daily Breakdown</h2>
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                    <thead>
                        <tr style="background: #f8f9fa;">
                            <th style="padding: 12px 8px; text-align: left; border-bottom: 2px solid #dee2e6;">Date</th>
                            <th style="padding: 12px 8px; text-align: right; border-bottom: 2px solid #dee2e6;">Sessions</th>
                            <th style="padding: 12px 8px; text-align: right; border-bottom: 2px solid #dee2e6;">Conv.</th>
                            <th style="padding: 12px 8px; text-align: right; border-bottom: 2px solid #dee2e6;">Reach</th>
                            <th style="padding: 12px 8px; text-align: right; border-bottom: 2px solid #dee2e6;">Eng.</th>
                        </tr>
                    </thead>
                    <tbody>
                        {timeline_html}
                    </tbody>
                </table>
                
                <!-- CTA -->
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://livinglytics.com" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; padding: 14px 32px; border-radius: 6px; font-weight: 600;">View Full Dashboard</a>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666;">
                <p style="margin: 0 0 10px 0;">Living Lytics Analytics</p>
                <p style="margin: 0;">
                    <a href="{unsubscribe_url}" style="color: #667eea; text-decoration: none;">Unsubscribe from weekly digests</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def send_weekly_digest(user_id: str, db: Session) -> Dict[str, Any]:
    """
    Send weekly digest to a single user with idempotency.
    
    Returns:
        Dict with status, message, and any relevant details
    """
    # 1. Resolve user and check opt-in
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user:
        return {"status": "error", "message": "User not found"}
    
    if not user.opt_in_digest:
        logging.info(f"[DIGEST] user_id={user.id} email={user.email} opted out, skipping")
        return {"status": "skipped", "message": "User opted out", "user_id": str(user.id)}
    
    # 2. Compute period
    period_start, period_end = get_last_completed_week()
    
    # 3. Check for existing digest_log entry (idempotency)
    existing = db.execute(
        select(DigestLog)
        .where(DigestLog.user_id == user_id)
        .where(DigestLog.period_start == period_start)
        .where(DigestLog.period_end == period_end)
        .where(DigestLog.status == 'sent')
    ).scalar_one_or_none()
    
    if existing:
        logging.info(f"[DIGEST] user_id={user.id} email={user.email} period={period_start} to {period_end} already sent")
        return {"status": "skipped", "message": "Already sent for this period", "user_id": str(user.id)}
    
    try:
        # 4. Query current week metrics
        kpis = _collect_kpis_for_period(user_id, period_start, period_end, db)
        
        # 5. Query previous week metrics for WoW comparison
        prev_period_end = period_start - timedelta(days=1)
        prev_period_start = prev_period_end - timedelta(days=6)
        prev_kpis = _collect_kpis_for_period(user_id, prev_period_start, prev_period_end, db)
        
        # Calculate WoW deltas
        wow_deltas = {}
        for metric in ["sessions", "conversions", "reach", "engagement"]:
            current = kpis["totals"][metric]
            previous = prev_kpis["totals"][metric]
            if previous > 0:
                wow_deltas[metric] = ((current - previous) / previous) * 100
            else:
                wow_deltas[metric] = 100.0 if current > 0 else 0.0
        
        # 6. Build subject with key delta
        best_metric = max(wow_deltas.items(), key=lambda x: x[1])
        if best_metric[1] > 5:
            subject = f"📈 Your Weekly Digest - {best_metric[0].capitalize()} up {best_metric[1]:.0f}%"
        else:
            subject = "Your Weekly Living Lytics Digest"
        
        # 7. Render email
        html = _render_digest_html(user.email, str(user.id), period_start, period_end, kpis, wow_deltas)
        
        # 8. Send via Resend
        result = send_email_resend(user.email, subject, html)
        
        # 9. Log success
        digest_log = DigestLog(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            status='sent',
            error_message=None
        )
        db.add(digest_log)
        
        # Update last_digest_sent_at
        user.last_digest_sent_at = datetime.now(PT)
        
        db.commit()
        
        logging.info(f"[DIGEST] ✅ user_id={user.id} email={user.email} period={period_start} to {period_end} status=sent")
        return {
            "status": "sent",
            "message": "Digest sent successfully",
            "user_id": str(user.id),
            "user_email": user.email,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat()
        }
        
    except Exception as e:
        # Log error
        logging.error(f"[DIGEST] ❌ user_id={user.id} email={user.email} period={period_start} to {period_end} status=error error={str(e)}")
        digest_log = DigestLog(
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            status='error',
            error_message=str(e)
        )
        db.add(digest_log)
        db.commit()
        
        return {
            "status": "error",
            "message": str(e),
            "user_id": str(user.id),
            "user_email": user.email,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat()
        }

def run_weekly_digests(db: Session) -> Dict[str, Any]:
    """
    Run weekly digests for all opted-in users.
    
    Returns:
        Summary of results
    """
    logging.info("[SCHEDULER] Running weekly digests for all opted-in users")
    
    # Get all opted-in users
    users = db.execute(
        select(User).where(User.opt_in_digest == True)
    ).scalars().all()
    
    results = {
        "total_users": len(users),
        "sent": 0,
        "skipped": 0,
        "errors": 0,
        "error_details": []
    }
    
    for user in users:
        result = send_weekly_digest(str(user.id), db)
        
        if result["status"] == "sent":
            results["sent"] += 1
        elif result["status"] == "skipped":
            results["skipped"] += 1
        elif result["status"] == "error":
            results["errors"] += 1
            results["error_details"].append(f"{user.email}: {result['message']}")
    
    logging.info(f"[SCHEDULER] Digest run complete: {results['sent']} sent, {results['skipped']} skipped, {results['errors']} errors")
    
    return results
