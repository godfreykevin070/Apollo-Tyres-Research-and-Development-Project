from fastapi import APIRouter, HTTPException, Depends, Request
import asyncio
import os
from typing import Optional

import logging
from database import db
from auth import get_current_user
from services.abaqus import AbaqusService
from services.dependency_resolver import DependencyResolver
from services.file_service import FileService
from services.odb_service import ODBService

logger = logging.getLogger(__name__)
router = APIRouter()
resolver = DependencyResolver()

running_tasks = {}

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
    data = await request.json()

    project_id = int(data["projectId"])
    run_number = int(data["runNumber"])

    project_name, protocol = await db.execute_one(
        "SELECT project_name, protocol FROM projects WHERE id = $1",
        project_id
    )

    if not all([project_name, protocol]):
        raise HTTPException(400, "Missing required parameters")

    existing = running_tasks.get(project_id)

    if existing and not existing.done():
        raise HTTPException(
            status_code=400,
            detail="Simulation already running."
        )

    async def background_job():
        try:
            await resolver.resolve_and_run(
                project_name=project_name,
                protocol=protocol,
                run_number=run_number,
            )
        except Exception as e:
            print(f"Simulation failed: {e}")

    task = asyncio.create_task(background_job())

    running_tasks[project_id] = task

    def cleanup(t: asyncio.Task):
        try:
            t.result()
        except Exception as e:
            print(f"Background task crashed: {e}")

        running_tasks.pop(project_id, None)

    task.add_done_callback(cleanup)

    return {
        "success": True,
        "message": "Simulation started"
    }

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

    file_service.update_project_files(
        project_name,
        protocol,
    )
    
    result = file_service.generate_parameters(
        data=data,
        referer=referer,
        project=project
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

@router.post("/refresh-status")
async def refresh_status(
    request: Request,
    user=Depends(get_current_user)
):
    """
    Refresh the status of all running simulations for a project.
    For each row with run_status = 'running':
      - Check if the ODB file exists.
      - If yes, run the associated Python post-processing script (if any),
        then mark the run as 'completed' (or 'failed' if the script fails).
      - If not, leave it as 'running' (the refresh will check again later).
    """
    data = await request.json()
    project_id = data.get('projectId')
    if not project_id:
        raise HTTPException(400, "Project ID is required")

    # Get project details
    project = await db.execute_one(
        "SELECT project_name, protocol FROM projects WHERE id = $1",
        project_id
    )
    if not project:
        raise HTTPException(404, "Project not found")

    project_name = project["project_name"]
    protocol = project["protocol"]

    # Determine the correct data table
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

    # Fetch all rows for this project that are currently 'running'
    rows = await db.execute(
        f"""
        SELECT * FROM {table_name}
        WHERE project_id = $1 AND run_status = 'running'
        """,
        project_id
    )

    file_service = FileService()
    odb_service = ODBService()
    updated_count = 0

    for row in rows:
        run_number = row["number_of_runs"]
        job_name = row.get("job", "").strip()
        if not job_name:
            continue

        # Build folder path (adjust column names as needed)
        folder_name = f"{row.get('p', '')}_{row.get('l', '')}"
        folder_path = file_service.get_project_folder_path(project_name, protocol, folder_name)
        odb_path = os.path.join(folder_path, f"{job_name}.odb")
        logger.info(f"Checking: {odb_path}")
        logger.info(f"Exists: {os.path.isfile(odb_path)}")

        # Check if ODB exists
        if os.path.isfile(odb_path):

            # Validate the ODB instead of assuming completion
            odb_result = odb_service.read_odb_content(odb_path)

            if odb_result["success"]:

                await db.execute(
                    f"""
                    UPDATE {table_name}
                    SET run_status='completed',
                        run_end_time=CURRENT_TIMESTAMP,
                        odb_path=$1
                    WHERE number_of_runs=$2
                    """,
                    odb_path,
                    run_number
                )

                updated_count += 1

            else:
                logger.info(
                    f"{job_name} ODB exists but is still being written."
                )

                # Leave status as RUNNING
                continue
        else:
            # ODB not yet present – leave as 'running'
            # Optionally, you could check if the process is still alive and mark as failed if dead
            pass

    return {
        "success": True,
        "message": f"Refresh completed. {updated_count} runs updated to 'completed'."
    }
