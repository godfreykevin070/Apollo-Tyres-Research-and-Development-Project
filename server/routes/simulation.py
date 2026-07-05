from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
import asyncio
import os
import subprocess
from typing import Optional
import json

from database import db
from auth import get_current_user
from services.abaqus import AbaqusService
from services.dependency_resolver import DependencyResolver
from services.simulation_service import SimulationService

router = APIRouter()

@router.get("/get-row-data")
async def get_row_data(protocol: str, runNumber: int, user=Depends(get_current_user)):
    """Get row data for a specific run number"""
    table_map = {
        'mf62': 'mf62_project_data',
        'mf52': 'mf52_project_data',
        'ftire': 'ftire_project_data',
        'cdtire': 'cdtire_project_data',
        'custom': 'custom_project_data'
    }
    
    table_name = table_map.get(protocol.lower())
    if not table_name:
        raise HTTPException(400, "Invalid protocol")
    
    elif table_name == "mf52_project_data":
        query = f"""
            SELECT number_of_runs, p, l, job, old_job, template_tydex, tydex_name,
                slip_angle, slip_ratio, inclination_angle, foltran, python_script
            FROM {table_name}
            WHERE number_of_runs = $1
        """
    elif table_name == "mf62_project_data":
        query = f"""
            SELECT number_of_runs, p, l, job, old_job, template_tydex, tydex_name, inflation_pressure,
                slip_angle, slip_ratio, inclination_angle, foltran, python_script
            FROM {table_name}
            WHERE number_of_runs = $1
        """
    elif table_name == "ftire_project_data":
        query = f"""
            SELECT number_of_runs, tests, loads, inflation_pressure, test_velocity, longitudinal_slip, 
            slip_angle, inclination_angle, cleat_orientation, job, old_job, template_tydex, 
            tydex_name, p, l
            FROM {table_name}
            WHERE number_of_runs = $1
        """
    elif table_name == "cdtire_project_data":
        query = f"""
            SELECT number_of_runs, p, l, job, old_job, template_tydex, tydex_name, velocity,
                slip_angle, slip_range, cleat, foltran, python_script
            FROM {table_name}
            WHERE number_of_runs = $1
        """
    
    row = await db.execute_one(query, runNumber)
    if not row:
        raise HTTPException(404, "Row not found")
    
    return {"success": True, "data": dict(row)}

@router.post("/resolve-job-dependencies")
async def resolve_dependencies(
    request: Request,
    user=Depends(get_current_user)
):
    """Resolve job dependencies and run Abaqus simulation"""
    data = await request.json()
    print("Received data:", data)
    
    project_id = int(data.get('projectId'))
    run_number = data.get('runNumber')

    project_name, protocol = await db.execute_one(
        "SELECT project_name, protocol FROM projects WHERE id = $1",
        project_id
    )
    
    if not all([project_name, protocol, run_number]):
        raise HTTPException(400, "Missing required parameters")
    
    # Check if user has permission for this project
    project = await db.execute_one(
        "SELECT user_email FROM projects WHERE id = $1",
        project_id
    )
    if not project:
        raise HTTPException(404, "Project not found")
    if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
        raise HTTPException(403, "Forbidden")
    
    resolver = DependencyResolver()
    result = await resolver.resolve_and_run(
        project_name=project_name,
        protocol=protocol,
        run_number=run_number
    )
    
    return result

@router.get("/check-odb-file")
async def check_odb_file(
    projectName: str,
    protocol: str,
    folderName: str,
    jobName: str,
    user=Depends(get_current_user)
):
    """Check if ODB file exists"""
    from services.file_service import FileService
    file_service = FileService()
    
    exists, path = file_service.check_odb_file(projectName, protocol, folderName, jobName)
    return {"success": True, "exists": exists, "path": path}

@router.get("/check-tydex-file")
async def check_tydex_file(
    projectName: str,
    protocol: str,
    folderName: str,
    tydexName: str,
    user=Depends(get_current_user)
):
    """Check if Tydex file exists"""
    from services.file_service import FileService
    file_service = FileService()
    
    exists, path = file_service.check_tydex_file(projectName, protocol, folderName, tydexName)
    return {"success": True, "exists": exists, "path": path}

@router.get("/get-run-times")
async def get_run_times(
    projectId: Optional[int] = None,
    protocol: Optional[str] = None,
    user=Depends(get_current_user)
):
    """Get recorded run times"""
    if not protocol:
        raise HTTPException(400, "Protocol required")
    
    table_map = {
        'mf62': 'mf62_project_data',
        'mf52': 'mf52_project_data',
        'ftire': 'ftire_project_data',
        'cdtire': 'cdtire_project_data',
        'custom': 'custom_project_data'
    }
    
    table_name = table_map.get(protocol.lower())
    if not table_name:
        raise HTTPException(400, "Invalid protocol")
    
    query = f"""
        SELECT number_of_runs, run_start_time, run_end_time, run_duration_seconds
        FROM {table_name}
        WHERE ($1::int IS NULL OR project_id = $1)
        ORDER BY number_of_runs
    """
    
    rows = await db.execute(query, projectId)
    return [dict(row) for row in rows]

@router.post("/record-run-time")
async def record_run_time(request: Request, user=Depends(get_current_user)):
    """Record run start/end times"""
    data = await request.json()
    project_id = data.get('projectId')
    protocol = data.get('protocol')
    run_number = data.get('runNumber')
    
    if not protocol or not run_number:
        raise HTTPException(400, "Protocol and runNumber required")
    
    table_map = {
        'mf62': 'mf62_project_data',
        'mf52': 'mf52_project_data',
        'ftire': 'ftire_project_data',
        'cdtire': 'cdtire_project_data',
        'custom': 'custom_project_data'
    }
    
    table_name = table_map.get(protocol.lower())
    if not table_name:
        raise HTTPException(400, "Invalid protocol")
    
    # Build update query
    updates = []
    params = []
    idx = 1
    
    if data.get('startTime'):
        updates.append(f"run_start_time = ${idx}")
        params.append(data['startTime'])
        idx += 1
    
    if data.get('endTime'):
        updates.append(f"run_end_time = ${idx}")
        params.append(data['endTime'])
        idx += 1
    
    if data.get('durationSeconds') is not None:
        updates.append(f"run_duration_seconds = ${idx}")
        params.append(data['durationSeconds'])
        idx += 1
    
    if not updates:
        return {"success": True, "message": "Nothing to update"}
    
    params.append(run_number)
    query = f"""
        UPDATE {table_name}
        SET {', '.join(updates)}
        WHERE number_of_runs = ${idx}
        RETURNING *
    """
    
    result = await db.execute_one(query, *params)
    
    return {"success": True, "updated": dict(result) if result else None}

@router.post("/stop-all")
async def stop_all(user=Depends(get_current_user)):
    """Stop all running simulations"""
    from services.abaqus import AbaqusService
    abaqus = AbaqusService()
    result = abaqus.stop_all()
    return result

@router.post("/generate-parameters")
async def generate_parameters(request: Request, user=Depends(get_current_user)):
    """Generate parameters.inc file"""
    from services.file_service import FileService
    data = await request.json()
    
    referer = request.headers.get('referer', '')
    file_service = FileService()

    project_id = int(data.get("projectId"))
    project = await db.execute_one(
        "SELECT * FROM projects WHERE id = $1",
        project_id
    )

    if not project:
        raise HTTPException(404, "Project not found")

    project_name = project["project_name"]
    protocol = data["protocol"]

    result = file_service.generate_parameters(
        data=data,
        referer=referer,
        project=project
    )

    file_service.update_project_files(
        project_name,
        protocol,
    )
    return result

@router.post("/create-protocol-folders")
async def create_protocol_folders(request: Request, user=Depends(get_current_user)):
    """Create protocol folder structure"""
    from services.file_service import FileService
    data = await request.json()
    
    project_name = data.get('projectName')
    protocol = data.get('protocol')
    
    if not project_name or not protocol:
        raise HTTPException(400, "Project name and protocol required")
    
    file_service = FileService()
    result = file_service.create_protocol_folders(project_name, protocol)
    return result
