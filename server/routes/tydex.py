from fastapi import APIRouter, Depends, Request, HTTPException
import os
import json

from database import db
from auth import get_current_user
from services.tydex_service import TydexService
from services.file_service import FileService

router = APIRouter()
tydex_service = TydexService()
file_service = FileService()

@router.get("/{project_id}")
async def get_tydex_files(project_id: int, user=Depends(get_current_user)):
    """Get all Tydex files for a project"""
    # Check permission
    project = await db.execute_one(
        "SELECT user_email FROM projects WHERE id = $1",
        project_id
    )
    if not project:
        raise HTTPException(404, "Project not found")
    if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
        raise HTTPException(403, "Forbidden")
    
    rows = await db.execute(
        "SELECT id, protocol, filename, created_at FROM tydex_files WHERE project_id = $1 ORDER BY created_at DESC",
        project_id
    )
    return [dict(row) for row in rows]

@router.get("/{project_id}/{file_id}")
async def get_tydex_file(project_id: int, file_id: int, user=Depends(get_current_user)):
    """Get a specific Tydex file with content"""
    row = await db.execute_one(
        "SELECT * FROM tydex_files WHERE project_id = $1 AND id = $2",
        project_id, file_id
    )
    if not row:
        raise HTTPException(404, "Tydex file not found")
    
    # Check permission
    project = await db.execute_one(
        "SELECT user_email FROM projects WHERE id = $1",
        project_id
    )
    if not project:
        raise HTTPException(404, "Project not found")
    if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
        raise HTTPException(403, "Forbidden")
    
    return dict(row)

@router.post("/{project_id}")
async def save_tydex_file(project_id: int, request: Request, user=Depends(get_current_user)):
    """Save a generated Tydex file"""
    data = await request.json()
    protocol = data.get('protocol')
    filename = data.get('filename')
    content = data.get('content')
    
    if not all([protocol, filename, content]):
        raise HTTPException(400, "protocol, filename, and content required")
    
    # Check permission
    project = await db.execute_one(
        "SELECT user_email FROM projects WHERE id = $1",
        project_id
    )
    if not project:
        raise HTTPException(404, "Project not found")
    if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
        raise HTTPException(403, "Forbidden")
    
    result = await db.execute_one(
        """
        INSERT INTO tydex_files (project_id, protocol, filename, content, created_at)
        VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
        ON CONFLICT (project_id, filename) DO UPDATE SET content = EXCLUDED.content, created_at = CURRENT_TIMESTAMP
        RETURNING id, filename, created_at
        """,
        project_id, protocol, filename, content
    )
    
    return {"success": True, "message": "Tydex file saved", "file": dict(result)}

@router.post("/generate")
async def generate_tydex(request: Request, user=Depends(get_current_user)):
    """Generate Tydex file from template and ODB data"""
    data = await request.json()
    project_id = int(data.get('projectId'))
    project = await db.execute_one(
        "SELECT project_name, protocol FROM projects WHERE id = $1",
        project_id
    )
    if not project:
        raise HTTPException(404, "Project not found")
    
    project_name = project["project_name"]
    protocol = project["protocol"]
    row_data = data.get('rowData')
    
    if not all([protocol, project_id, row_data]):
        raise HTTPException(400, "protocol, projectName, and rowData required")
    
    if user['role'] not in ['manager', 'admin']:
        # Check if user owns this project
        project_owner = await db.execute_one(
            "SELECT user_email FROM projects WHERE id = $1",
            project_id
        )
        if project_owner and project_owner['user_email'] != user['email']:
            raise HTTPException(403, "Forbidden")
    
    result = await tydex_service.generate_tydex(protocol, project_name, row_data)
    return result

@router.post("/open")
async def open_tydex_file(request: Request, user=Depends(get_current_user)):
    """Open a Tydex file in notepad (server-side)"""
    data = await request.json()
    protocol = data.get('protocol')
    project_name = data.get('projectName')
    p = data.get('p')
    l = data.get('l')
    tydex_name = data.get('tydex_name')
    
    if not all([protocol, project_name, p, l, tydex_name]):
        raise HTTPException(400, "Missing required parameters")
    
    # Check permission
    project = await db.execute_one(
        "SELECT id FROM projects WHERE project_name = $1",
        project_name
    )
    if not project:
        raise HTTPException(404, "Project not found")
    if user['role'] not in ['manager', 'admin']:
        project_owner = await db.execute_one(
            "SELECT user_email FROM projects WHERE project_name = $1",
            project_name
        )
        if project_owner and project_owner['user_email'] != user['email']:
            raise HTTPException(403, "Forbidden")
    
    exists, path = file_service.check_tydex_file(project_name, protocol, f"{p}_{l}", tydex_name)
    if not exists:
        raise HTTPException(404, f"Tydex file not found: {tydex_name}")
    
    # Open in notepad (Windows only)
    import subprocess
    try:
        subprocess.Popen(['notepad.exe', path], shell=True)
        return {"success": True, "message": "Tydex file opened in notepad"}
    except Exception as e:
        raise HTTPException(500, f"Failed to open file: {str(e)}")