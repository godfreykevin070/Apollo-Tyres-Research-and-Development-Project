from fastapi import APIRouter, Depends, Request, HTTPException, UploadFile, File
from typing import Optional
import os

from database import db
from auth import get_current_user, get_current_manager
from routes import auth, projects, simulation, activity, tydex

from config import config

router = APIRouter()

# ============================================
# AUTH COMPATIBILITY ENDPOINTS
# ============================================

@router.post("/login")
async def login_compat(request: Request):
    """Compatibility endpoint for /api/login"""
    from routes.auth import LoginRequest
    data = await request.json()
    login_req = LoginRequest(email=data.get('email'), password=data.get('password'))
    return await auth.login(login_req)

@router.get("/me")
async def me_compat(user=Depends(get_current_user)):
    """Compatibility endpoint for /api/me"""
    return await auth.get_me(user)

@router.get("/verify-token")
async def verify_token_compat(user=Depends(get_current_user)):
    """Compatibility endpoint for /api/verify-token"""
    return {"success": True}

@router.post("/logout")
async def logout_compat(user=Depends(get_current_user)):
    """Compatibility endpoint for /api/logout"""
    return {"success": True, "message": "Logged out"}

# ============================================
# PROJECT COMPATIBILITY ENDPOINTS
# ============================================

@router.post("/save-project")
async def save_project_compat(request: Request, user=Depends(get_current_user)):
    """Compatibility endpoint for /api/save-project"""
    return await projects.create_project(request, user)

@router.post("/check-project-exists")
async def check_project_exists_compat(request: Request, user=Depends(get_current_user)):
    """Compatibility endpoint for /api/check-project-exists"""
    return await projects.check_project_exists(request, user)

@router.post("/mark-project-complete")
async def mark_project_complete_compat(request: Request, user=Depends(get_current_user)):
    """Compatibility endpoint for /api/mark-project-complete"""
    return await projects.mark_project_complete(request, user)

@router.post("/mark-project-in-progress")
async def mark_project_in_progress_compat(request: Request, user=Depends(get_current_user)):
    """Compatibility endpoint for /api/mark-project-in-progress"""
    return await projects.mark_project_in_progress(request, user)

@router.get("/project-history")
async def project_history_compat(all: bool = False, user=Depends(get_current_user)):
    """Compatibility endpoint for /api/project-history"""
    return await projects.get_project_history(all, user)

@router.get("/project-inputs")
async def project_inputs_compat(limit: int = 200, user=Depends(get_current_user)):
    """Compatibility endpoint for /api/project-inputs"""
    is_manager = user['role'] in ['manager', 'admin']
    
    query = """
        SELECT id, project_name, protocol, inputs, created_at 
        FROM projects 
        WHERE inputs IS NOT NULL AND inputs != '{}'::jsonb
    """
    if not is_manager:
        query += " AND user_email = $1"
        rows = await db.execute(query + f" ORDER BY created_at DESC LIMIT {limit}", user['email'])
    else:
        rows = await db.execute(query + f" ORDER BY created_at DESC LIMIT {limit}")
    
    return [dict(row) for row in rows]

# ============================================
# SIMULATION COMPATIBILITY ENDPOINTS
# ============================================

@router.get("/get-row-data")
async def get_row_data_compat(protocol: str, runNumber: int, user=Depends(get_current_user)):
    """Compatibility endpoint for /api/get-row-data"""
    return await simulation.get_row_data(protocol, runNumber, user)

@router.post("/resolve-job-dependencies")
async def resolve_dependencies_compat(request: Request, user=Depends(get_current_user)):
    """Compatibility endpoint for /api/resolve-job-dependencies"""
    return await simulation.resolve_dependencies(request, user)

@router.get("/check-odb-file")
async def check_odb_file_compat(
    projectName: str,
    protocol: str,
    folderName: str,
    jobName: str,
    user=Depends(get_current_user)
):
    """Compatibility endpoint for /api/check-odb-file"""
    return await simulation.check_odb_file(projectName, protocol, folderName, jobName, user)

@router.get("/check-tydex-file")
async def check_tydex_file_compat(
    projectName: str,
    protocol: str,
    folderName: str,
    tydexName: str,
    user=Depends(get_current_user)
):
    """Compatibility endpoint for /api/check-tydex-file"""
    return await simulation.check_tydex_file(projectName, protocol, folderName, tydexName, user)

@router.get("/get-run-times")
async def get_run_times_compat(
    projectId: Optional[int] = None,
    protocol: Optional[str] = None,
    user=Depends(get_current_user)
):
    """Compatibility endpoint for /api/get-run-times"""
    return await simulation.get_run_times(projectId, protocol, user)

@router.post("/record-run-time")
async def record_run_time_compat(request: Request, user=Depends(get_current_user)):
    """Compatibility endpoint for /api/record-run-time"""
    return await simulation.record_run_time(request, user)

@router.post("/stop-all")
async def stop_all_compat(user=Depends(get_current_user)):
    """Compatibility endpoint for /api/stop-all"""
    return await simulation.stop_all(user)

@router.post("/generate-parameters")
async def generate_parameters_compat(request: Request, user=Depends(get_current_user)):
    """Compatibility endpoint for /api/generate-parameters"""
    return await simulation.generate_parameters(request, user)

@router.post("/create-protocol-folders")
async def create_protocol_folders_compat(request: Request, user=Depends(get_current_user)):
    """Compatibility endpoint for /api/create-protocol-folders"""
    return await simulation.create_protocol_folders(request, user)

@router.post("/upload-mesh-file")
async def upload_mesh_file_compat(request: Request, user=Depends(get_current_user)):
    """Compatibility endpoint for /api/upload-mesh-file"""

    # Get the uploaded file
    form = await request.form()
    mesh_file = form.get('meshFile')
    
    if not mesh_file:
        raise HTTPException(400, "No file uploaded")
    
    project_id = form.get("projectId")
    if not project_id:
        raise HTTPException(status_code=400, detail="Project ID is required")

    project_id = int(project_id)
    project_name, protocol = await db.execute_one(
        "SELECT project_name, protocol FROM projects WHERE id = $1",
        project_id
    )
    
    if not all([project_name, protocol]):
        raise HTTPException(400, "Missing required parameters")

    combined_name = f"{project_name}_{protocol}"
    upload_dir = os.path.join(
        os.path.dirname(config.TEMPLATES_DIR),
        "projects",
        combined_name,
    )
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, mesh_file.filename)
    
    # Save file
    with open(file_path, 'wb') as f:
        content = await mesh_file.read()
        f.write(content)
    
    return {"success": True, "message": "Mesh file uploaded", "filename": mesh_file.filename}

# ============================================
# ACTIVITY LOG COMPATIBILITY ENDPOINTS
# ============================================

@router.post("/activity-log")
async def activity_log_compat(request: Request, user=Depends(get_current_user)):
    """Compatibility endpoint for /api/activity-log"""
    return await activity.create_activity_log(request, user)

@router.get("/activity-log")
async def get_activity_log_compat(
    request: Request,
    activity_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user=Depends(get_current_user)
):
    """Compatibility endpoint for /api/activity-log GET"""
    return await activity.get_activity_logs(
        request, activity_type, status, start_date, end_date, limit, offset, user
    )

@router.get("/activity-log/stats")
async def activity_stats_compat(user=Depends(get_current_user)):
    """Compatibility endpoint for /api/activity-log/stats"""
    return await activity.get_activity_stats(user)

# ============================================
# TYDEX COMPATIBILITY ENDPOINTS
# ============================================

@router.post("/generate-tydex")
async def generate_tydex_compat(request: Request, user=Depends(get_current_user)):
    """Compatibility endpoint for /api/generate-tydex"""
    return await tydex.generate_tydex(request, user)

@router.post("/open-tydex-file")
async def open_tydex_file_compat(request: Request, user=Depends(get_current_user)):
    """Compatibility endpoint for /api/open-tydex-file"""
    return await tydex.open_tydex_file(request, user)

# ============================================
# SYSTEM INFO ENDPOINT
# ============================================

@router.get("/system-info")
async def system_info_compat(user=Depends(get_current_user)):
    """Get system information"""
    from datetime import datetime
    return {
        "success": True,
        "data": {
            "current_timestamp": datetime.now().isoformat(),
            "user_login": user.get('name', user.get('email', 'unknown'))
        }
    }
