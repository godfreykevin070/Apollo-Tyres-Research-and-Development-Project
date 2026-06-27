from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, Form, File
from typing import Optional, List
import config
import json
import os

from database import db
from auth import get_current_user, get_current_manager
from services.simulation_service import SimulationService

router = APIRouter()

@router.get("/")
async def get_projects(user=Depends(get_current_user)):
    """Get all projects (filtered by role)"""
    is_manager = user['role'] in ['manager', 'admin']
    
    query = """
        SELECT p.*, COALESCE(u.name, SPLIT_PART(p.user_email, '@', 1)) as user_name
        FROM projects p
        LEFT JOIN users u ON p.user_email = u.email
    """
    
    if not is_manager:
        query += " WHERE p.user_email = $1"
        rows = await db.execute(query, user['email'])
    else:
        rows = await db.execute(query)
    
    return [dict(row) for row in rows]

@router.get("/{project_id}")
async def get_project(project_id: int, user=Depends(get_current_user)):
    """Get a single project by ID"""
    row = await db.execute_one(
        "SELECT * FROM projects WHERE id = $1",
        project_id
    )
    if not row:
        raise HTTPException(404, "Project not found")
    
    project = dict(row)
    
    # Check permission
    if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
        raise HTTPException(403, "Forbidden")
    
    return {"success": True, "project": project}

@router.post("/")
async def create_project(request: Request, user=Depends(get_current_user)):
    """Create a new project"""
    data = await request.json()
    
    required = ['project_name', 'region', 'department', 'tyre_size', 'protocol']
    for field in required:
        if not data.get(field):
            raise HTTPException(400, f"Missing required field: {field}")
    
    # Check if project name already exists for this user
    existing = await db.execute_one(
        "SELECT id FROM projects WHERE project_name = $1 AND user_email = $2",
        data['project_name'], user['email']
    )
    if existing:
        raise HTTPException(409, "Project name already exists")
    
    result = await db.execute_one(
        """
        INSERT INTO projects 
        (project_name, region, department, tyre_size, protocol, status, user_email, inputs)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id
        """,
        data['project_name'],
        data['region'],
        data['department'],
        data['tyre_size'],
        data['protocol'],
        data.get('status', 'Not Started'),
        user['email'],
        json.dumps(data.get('inputs', {}))
    )
    
    return {"success": True, "id": result['id'], "message": "Project created"}

@router.patch("/{project_id}")
async def update_project(project_id: int, request: Request, user=Depends(get_current_user)):
    """Update project (name, inputs, etc.)"""
    data = await request.json()
    
    # Check existence and permission
    project = await db.execute_one("SELECT * FROM projects WHERE id = $1", project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
        raise HTTPException(403, "Forbidden")
    
    updates = []
    params = []
    idx = 1
    
    if data.get('project_name'):
        updates.append(f"project_name = ${idx}")
        params.append(data['project_name'])
        idx += 1
    
    if data.get('inputs') is not None:
        updates.append(f"inputs = ${idx}")
        params.append(json.dumps(data['inputs']))
        idx += 1
    
    if updates:
        params.append(project_id)
        query = f"UPDATE projects SET {', '.join(updates)} WHERE id = ${idx} RETURNING *"
        result = await db.execute_one(query, *params)
        return {"success": True, "project": dict(result)}
    
    return {"success": True, "project": dict(project)}

@router.put("/{project_id}/inputs")
async def update_project_inputs(project_id: int, request: Request, user=Depends(get_current_user)):
    """Update project inputs JSONB field"""
    data = await request.json()
    inputs = data.get('inputs', {})
    
    # Check existence and permission
    project = await db.execute_one("SELECT * FROM projects WHERE id = $1", project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
        raise HTTPException(403, "Forbidden")
    
    result = await db.execute_one(
        "UPDATE projects SET inputs = $1 WHERE id = $2 RETURNING *",
        json.dumps(inputs), project_id
    )
    
    return {"success": True, "project": dict(result)}

@router.patch("/{project_id}/name")
async def rename_project(project_id: int, request: Request, user=Depends(get_current_user)):
    """Rename a project"""
    data = await request.json()
    new_name = data.get('project_name')
    
    if not new_name or len(new_name) < 3:
        raise HTTPException(400, "Project name must be at least 3 characters")
    
    # Check existence and permission
    project = await db.execute_one("SELECT * FROM projects WHERE id = $1", project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
        raise HTTPException(403, "Forbidden")
    
    # Check if new name already exists for this user
    existing = await db.execute_one(
        "SELECT id FROM projects WHERE project_name = $1 AND user_email = $2 AND id != $3",
        new_name, user['email'], project_id
    )
    if existing:
        raise HTTPException(409, "Project name already exists")
    
    result = await db.execute_one(
        "UPDATE projects SET project_name = $1 WHERE id = $2 RETURNING *",
        new_name, project_id
    )
    
    return {"success": True, "project": dict(result)}

@router.patch("/{project_id}/status")
async def update_project_status(project_id: int, request: Request, user=Depends(get_current_user)):
    """Update project status"""
    data = await request.json()
    status = data.get('status')
    
    valid_statuses = ['Not Started', 'In Progress', 'Completed', 'Archived']
    if status not in valid_statuses:
        raise HTTPException(400, f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    # Check permission
    project = await db.execute_one("SELECT * FROM projects WHERE id = $1", project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
        raise HTTPException(403, "Forbidden")
    
    # Build query
    if status == 'Completed':
        query = "UPDATE projects SET status = $1, completed_at = CURRENT_TIMESTAMP WHERE id = $2 RETURNING *"
    else:
        query = "UPDATE projects SET status = $1, completed_at = NULL WHERE id = $2 RETURNING *"
    
    result = await db.execute_one(query, status, project_id)
    return {"success": True, "project": dict(result)}

@router.delete("/{project_id}")
async def delete_project(project_id: int, user=Depends(get_current_user)):
    """Delete a project (and cascade to related data)"""
    # Check permission
    project = await db.execute_one("SELECT * FROM projects WHERE id = $1", project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
        raise HTTPException(403, "Forbidden")
    
    await db.execute("DELETE FROM projects WHERE id = $1", project_id)
    return {"success": True, "message": "Project deleted"}

@router.patch("/{project_id}/archive")
async def archive_project(project_id: int, user=Depends(get_current_user)):
    """Archive a project"""
    project = await db.execute_one("SELECT * FROM projects WHERE id = $1", project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
        raise HTTPException(403, "Forbidden")
    
    result = await db.execute_one(
        "UPDATE projects SET previous_status = status, status = 'Archived' WHERE id = $1 RETURNING *",
        project_id
    )
    return {"success": True, "project": dict(result)}

@router.patch("/{project_id}/unarchive")
async def unarchive_project(project_id: int, user=Depends(get_current_user)):
    """Unarchive a project"""
    project = await db.execute_one("SELECT * FROM projects WHERE id = $1", project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
        raise HTTPException(403, "Forbidden")
    
    result = await db.execute_one(
        "UPDATE projects SET status = COALESCE(previous_status, 'Not Started'), previous_status = NULL WHERE id = $1 RETURNING *",
        project_id
    )
    return {"success": True, "project": dict(result)}

@router.get("/{project_id}/matrix")
async def get_project_matrix(project_id: int, user=Depends(get_current_user)):
    """Get matrix data for a project"""
    project = await db.execute_one("SELECT protocol, user_email FROM projects WHERE id = $1", project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
        raise HTTPException(403, "Forbidden")
    
    protocol = project['protocol']
    table_map = {
        'MF62': 'mf62_project_data',
        'MF52': 'mf52_project_data',
        'FTire': 'ftire_project_data',
        'CDTire': 'cdtire_project_data',
        'Custom': 'custom_project_data'
    }
    table_name = table_map.get(protocol)
    if not table_name:
        raise HTTPException(400, f"Unknown protocol: {protocol}")
    
    rows = await db.execute(
        f"SELECT * FROM {table_name} WHERE project_id = $1 ORDER BY number_of_runs",
        project_id
    )
    return {"success": True, "protocol": protocol, "rows": [dict(r) for r in rows]}

@router.post("/check-exists")
async def check_project_exists(request: Request, user=Depends(get_current_user)):
    """Check if a project name already exists for the user"""
    data = await request.json()
    project_name = data.get('projectName')
    protocol = data.get('protocol')
    
    if not project_name:
        raise HTTPException(400, "Project name required")
    
    row = await db.execute_one(
        "SELECT id, project_name, protocol, status, user_email FROM projects WHERE project_name = $1 AND user_email = $2",
        project_name, user['email']
    )
    
    if row:
        return {
            "success": True,
            "exists": True,
            "project": dict(row),
            "folderName": f"{project_name}_{protocol or row['protocol']}"
        }
    else:
        return {
            "success": True,
            "exists": False,
            "project": None,
            "folderName": f"{project_name}_{protocol}"
        }

@router.post("/mark-complete")
async def mark_project_complete(request: Request, user=Depends(get_current_user)):
    data = await request.json()
    project_name = data.get('projectName')
    
    if not project_name:
        raise HTTPException(400, "Project name required")
    
    result = await db.execute_one(
        "UPDATE projects SET status = 'Completed', completed_at = CURRENT_TIMESTAMP WHERE project_name = $1 AND user_email = $2 RETURNING *",
        project_name, user['email']
    )
    if not result:
        raise HTTPException(404, "Project not found")
    
    return {"success": True, "message": "Project marked as completed"}

@router.post("/mark-in-progress")
async def mark_project_in_progress(request: Request, user=Depends(get_current_user)):
    data = await request.json()
    project_id = data.get('projectId')
    
    if not project_id:
        raise HTTPException(400, "Project ID required")
    
    result = await db.execute_one(
        "UPDATE projects SET status = 'In Progress', completed_at = NULL WHERE id = $1 AND user_email = $2 RETURNING *",
        project_id, user['email']
    )
    if not result:
        raise HTTPException(404, "Project not found or not yours")
    
    return {"success": True, "message": "Project marked as In Progress"}

@router.get("/history")
async def get_project_history(all: bool = False, user=Depends(get_current_user)):
    """Get project history for the user (or all if manager and all=1)"""
    is_manager = user['role'] in ['manager', 'admin']
    
    if all and is_manager:
        rows = await db.execute(
            "SELECT * FROM projects ORDER BY created_at DESC"
        )
    else:
        rows = await db.execute(
            "SELECT * FROM projects WHERE user_email = $1 ORDER BY created_at DESC",
            user['email']
        )
    
    return [dict(row) for row in rows]

@router.post("/{project_id}/drafts/{protocol}")
async def save_draft(project_id: int, protocol: str, request: Request, user=Depends(get_current_user)):
    """Save draft inputs and matrix for a project"""
    data = await request.json()
    inputs_json = data.get('inputs_json', {})
    matrix_json = data.get('matrix_json', {})
    
    # Check permission
    project = await db.execute_one("SELECT * FROM projects WHERE id = $1", project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
        raise HTTPException(403, "Forbidden")
    
    result = await db.execute_one(
        """
        INSERT INTO protocol_drafts (project_id, protocol, inputs_json, matrix_json, updated_at)
        VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
        ON CONFLICT (project_id, protocol) 
        DO UPDATE SET inputs_json = EXCLUDED.inputs_json, 
                      matrix_json = EXCLUDED.matrix_json, 
                      updated_at = CURRENT_TIMESTAMP
        RETURNING *
        """,
        project_id, protocol, json.dumps(inputs_json), json.dumps(matrix_json)
    )
    
    return {"ok": True, "draft": dict(result) if result else None}