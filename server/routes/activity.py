from fastapi import APIRouter, Depends, Request, HTTPException
from typing import Optional

from database import db
from auth import get_current_user
from models import ActivityLogCreate

router = APIRouter()

@router.post("/activity-log")
async def create_activity_log(request: Request, user=Depends(get_current_user)):
    """Log an activity - endpoint at /api/activity-log"""
    data = await request.json()
    
    # Get IP and user agent
    ip = request.client.host if request.client else None
    user_agent = request.headers.get('user-agent', '')
    
    # Parse browser/device (simplified)
    browser = 'Unknown'
    device = 'Desktop'
    if 'Chrome' in user_agent:
        browser = 'Chrome'
    elif 'Firefox' in user_agent:
        browser = 'Firefox'
    elif 'Safari' in user_agent:
        browser = 'Safari'
    elif 'Edge' in user_agent:
        browser = 'Edge'
    
    if 'Mobile' in user_agent:
        device = 'Mobile'
    elif 'Tablet' in user_agent:
        device = 'Tablet'
    
    result = await db.execute_one(
        """
        INSERT INTO activity_logs 
        (user_email, user_name, activity_type, action, description, status, ip_address, browser, device_type, related_entity_id, related_entity_type, project_name, metadata, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, CURRENT_TIMESTAMP)
        RETURNING *
        """,
        user['email'],
        user.get('name', user['email'].split('@')[0]),
        data.get('activity_type', 'System'),
        data.get('action', ''),
        data.get('description', ''),
        data.get('status', 'success'),
        ip,
        browser,
        device,
        data.get('related_entity_id'),
        data.get('related_entity_type'),
        data.get('project_name'),
        data.get('metadata', {})
    )
    
    return {"success": True, "log": dict(result)}

@router.get("/activity-log")
async def get_activity_logs(
    request: Request,
    activity_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user=Depends(get_current_user)
):
    """Get activity logs - endpoint at /api/activity-log GET"""
    is_manager = user['role'] in ['manager', 'admin']
    
    query = "SELECT * FROM activity_logs WHERE 1=1"
    params = []
    idx = 1
    
    if not is_manager:
        query += f" AND user_email = ${idx}"
        params.append(user['email'])
        idx += 1
    
    if activity_type:
        query += f" AND activity_type = ${idx}"
        params.append(activity_type)
        idx += 1
    
    if status:
        query += f" AND status = ${idx}"
        params.append(status)
        idx += 1
    
    if start_date:
        query += f" AND created_at >= ${idx}"
        params.append(start_date)
        idx += 1
    
    if end_date:
        query += f" AND created_at <= ${idx}"
        params.append(end_date)
        idx += 1
    
    # Count total
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    total = await db.execute_val(count_query, *params) or 0
    
    query += f" ORDER BY created_at DESC LIMIT ${idx} OFFSET ${idx+1}"
    params.extend([limit, offset])
    
    rows = await db.execute(query, *params)
    
    return {
        "success": True,
        "logs": [dict(row) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }

@router.get("/activity-log/stats")
async def get_activity_stats(user=Depends(get_current_user)):
    """Get activity statistics - endpoint at /api/activity-log/stats"""
    is_manager = user['role'] in ['manager', 'admin']
    
    # By type
    type_query = "SELECT activity_type, COUNT(*) as count FROM activity_logs"
    if not is_manager:
        type_query += " WHERE user_email = $1 GROUP BY activity_type"
        type_rows = await db.execute(type_query, user['email'])
    else:
        type_query += " GROUP BY activity_type"
        type_rows = await db.execute(type_query)
    
    # By status
    status_query = "SELECT status, COUNT(*) as count FROM activity_logs"
    if not is_manager:
        status_query += " WHERE user_email = $1 GROUP BY status"
        status_rows = await db.execute(status_query, user['email'])
    else:
        status_query += " GROUP BY status"
        status_rows = await db.execute(status_query)
    
    # Last 24 hours
    recent_query = "SELECT COUNT(*) FROM activity_logs WHERE created_at >= NOW() - INTERVAL '24 hours'"
    if not is_manager:
        recent_query += " AND user_email = $1"
        recent = await db.execute_val(recent_query, user['email']) or 0
    else:
        recent = await db.execute_val(recent_query) or 0
    
    return {
        "success": True,
        "stats": {
            "by_type": [dict(row) for row in type_rows],
            "by_status": [dict(row) for row in status_rows],
            "last_24_hours": recent,
        }
    }