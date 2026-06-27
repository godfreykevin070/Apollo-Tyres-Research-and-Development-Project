from fastapi import APIRouter, Depends, Request, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
import os
import json
from typing import List, Dict, Any

from database import db
from auth import get_current_user
from services.excel_service import ExcelService
from services.file_service import FileService

router = APIRouter()
excel_service = ExcelService()
file_service = FileService()

@router.post("/store-excel-data")
async def store_excel_data(request: Request, user=Depends(get_current_user)):
    """Store Excel data from a protocol page"""
    data = await request.json()
    excel_data = data.get('data')
    protocol = data.get('protocol', 'mf62')
    
    if not excel_data or not isinstance(excel_data, list):
        raise HTTPException(400, "Invalid data format")
    
    if len(excel_data) == 0:
        raise HTTPException(400, "No data provided")
    
    # Determine which table to use based on protocol
    table_map = {
        'mf62': 'mf_data',
        'mf52': 'mf52_data',
        'ftire': 'ftire_data',
        'cdtire': 'cdtire_data',
        'custom': 'custom_data'
    }
    
    table_name = table_map.get(protocol.lower(), 'mf_data')
    
    # Truncate table first
    await db.execute(f"TRUNCATE TABLE {table_name}")
    
    # Get column names from first row
    columns = list(excel_data[0].keys())
    
    # Build insert query
    placeholders = ', '.join([f"${i+1}" for i in range(len(columns))])
    col_names = ', '.join(columns)
    query = f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})"
    
    # Insert all rows
    for row in excel_data:
        values = [row.get(col, '') for col in columns]
        await db.execute(query, *values)
    
    return {"success": True, "message": f"Stored {len(excel_data)} rows"}

@router.get("/read-protocol-excel")
async def read_protocol_excel(request: Request, user=Depends(get_current_user)):
    """Read protocol Excel file and return as binary"""
    referer = request.headers.get('referer', '')
    
    # Determine which Excel file to read
    file_name = "MF6pt2.xlsx"
    if 'mf52' in referer:
        file_name = "MF5pt2.xlsx"
    elif 'ftire' in referer:
        file_name = "FTire.xlsx"
    elif 'cdtire' in referer:
        file_name = "CDTire.xlsx"
    elif 'custom' in referer:
        file_name = "Custom.xlsx"
    
    file_path = os.path.join(file_service.protocol_dir, file_name)
    
    if not os.path.exists(file_path):
        # Try to create from template if available
        template_path = os.path.join(file_service.templates_dir, 'protocols', file_name)
        if os.path.exists(template_path):
            import shutil
            os.makedirs(file_service.protocol_dir, exist_ok=True)
            shutil.copy2(template_path, file_path)
        else:
            raise HTTPException(404, f"Protocol file not found: {file_name}")
    
    # Return file
    from fastapi.responses import FileResponse
    return FileResponse(
        file_path,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename=file_name
    )

@router.post("/save-excel")
async def save_excel_file(
    excelFile: UploadFile = File(...),
    user=Depends(get_current_user)
):
    """Save uploaded Excel file to protocol directory"""
    if not excelFile:
        raise HTTPException(400, "No file received")
    
    # Save as output.xlsx
    file_path = os.path.join(file_service.protocol_dir, 'output.xlsx')
    
    content = await excelFile.read()
    with open(file_path, 'wb') as f:
        f.write(content)
    
    return {"success": True, "message": "File saved", "filename": "output.xlsx"}

@router.get("/read-output-excel")
async def read_output_excel(user=Depends(get_current_user)):
    """Read output Excel file and return as binary"""
    file_path = os.path.join(file_service.protocol_dir, 'output.xlsx')
    
    if not os.path.exists(file_path):
        raise HTTPException(404, "Output file not found")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        file_path,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename='output.xlsx'
    )

@router.post("/store-project-matrix")
async def store_project_matrix(request: Request, user=Depends(get_current_user)):
    """Copy matrix data from scratch table to project table"""
    data = await request.json()
    project_id = data.get('projectId')
    protocol = data.get('protocol')
    
    if not project_id or not protocol:
        raise HTTPException(400, "projectId and protocol required")
    
    # Check permission
    project = await db.execute_one(
        "SELECT user_email FROM projects WHERE id = $1",
        project_id
    )
    if not project:
        raise HTTPException(404, "Project not found")
    if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
        raise HTTPException(403, "Forbidden")
    
    # Map scratch table to project table
    scratch_table_map = {
        'MF62': 'mf_data',
        'MF52': 'mf52_data',
        'FTire': 'ftire_data',
        'CDTire': 'cdtire_data',
        'Custom': 'custom_data'
    }
    
    project_table_map = {
        'MF62': 'mf62_project_data',
        'MF52': 'mf52_project_data',
        'FTire': 'ftire_project_data',
        'CDTire': 'cdtire_project_data',
        'Custom': 'custom_project_data'
    }
    
    scratch_table = scratch_table_map.get(protocol)
    project_table = project_table_map.get(protocol)
    
    if not scratch_table or not project_table:
        raise HTTPException(400, f"Invalid protocol: {protocol}")
    
    # Delete existing rows for this project
    await db.execute(f"DELETE FROM {project_table} WHERE project_id = $1", project_id)
    
    # Copy rows based on protocol
    if protocol == 'MF62':
        query = f"""
            INSERT INTO {project_table} 
            (project_id, number_of_runs, tests, ips, loads, inclination_angle, 
             slip_angle, slip_ratio, test_velocity, job, old_job, 
             template_tydex, tydex_name, p, l)
            SELECT $1, number_of_runs, tests, ips, loads, inclination_angle, 
                   slip_angle, slip_ratio, test_velocity, job, old_job, 
                   template_tydex, tydex_name, p, l
            FROM {scratch_table}
        """
    elif protocol == 'MF52':
        query = f"""
            INSERT INTO {project_table}
            (project_id, number_of_runs, tests, inflation_pressure, loads, 
             inclination_angle, slip_angle, slip_ratio, test_velocity, 
             job, old_job, template_tydex, tydex_name, p, l)
            SELECT $1, number_of_runs, tests, inflation_pressure, loads, 
                   inclination_angle, slip_angle, slip_ratio, test_velocity, 
                   job, old_job, template_tydex, tydex_name, p, l
            FROM {scratch_table}
        """
    elif protocol == 'FTire':
        query = f"""
            INSERT INTO {project_table}
            (project_id, number_of_runs, tests, loads, inflation_pressure, 
             test_velocity, longitudinal_slip, slip_angle, inclination_angle, 
             cleat_orientation, job, old_job, template_tydex, tydex_name, p, l)
            SELECT $1, number_of_runs, tests, loads, inflation_pressure, 
                   test_velocity, longitudinal_slip, slip_angle, inclination_angle, 
                   cleat_orientation, job, old_job, template_tydex, tydex_name, p, l
            FROM {scratch_table}
        """
    elif protocol == 'CDTire':
        query = f"""
            INSERT INTO {project_table}
            (project_id, number_of_runs, test_name, inflation_pressure, velocity, 
             preload, camber, slip_angle, displacement, slip_range, cleat, 
             road_surface, job, old_job, template_tydex, tydex_name, p, l)
            SELECT $1, number_of_runs, test_name, inflation_pressure, velocity, 
                   preload, camber, slip_angle, displacement, slip_range, cleat, 
                   road_surface, job, old_job, template_tydex, tydex_name, p, l
            FROM {scratch_table}
        """
    else:  # Custom
        query = f"""
            INSERT INTO {project_table}
            (project_id, number_of_runs, tests, inflation_pressure, loads, 
             inclination_angle, slip_angle, slip_ratio, test_velocity, 
             cleat_orientation, displacement, job, old_job, 
             template_tydex, tydex_name, p, l)
            SELECT $1, number_of_runs, tests, inflation_pressure, loads, 
                   inclination_angle, slip_angle, slip_ratio, test_velocity, 
                   cleat_orientation, displacement, job, old_job, 
                   template_tydex, tydex_name, p, l
            FROM {scratch_table}
        """
    
    await db.execute(query, project_id)
    
    return {"success": True, "message": "Matrix data saved to project table"}

@router.post("/store-mf52-data")
async def store_mf52_data(request: Request, user=Depends(get_current_user)):
    """Store MF52 data from Excel"""
    data = await request.json()
    excel_data = data.get('data')
    
    if not excel_data or not isinstance(excel_data, list):
        raise HTTPException(400, "Invalid data format")
    
    await db.execute("TRUNCATE TABLE mf52_data")
    
    for row in excel_data:
        await db.execute(
            """
            INSERT INTO mf52_data 
            (number_of_runs, tests, inflation_pressure, loads, inclination_angle, 
             slip_angle, slip_ratio, test_velocity, job, old_job, 
             template_tydex, tydex_name, p, l)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """,
            row.get('number_of_runs', 0),
            row.get('tests', ''),
            row.get('inflation_pressure', ''),
            row.get('loads', ''),
            row.get('inclination_angle', ''),
            row.get('slip_angle', ''),
            row.get('slip_ratio', ''),
            row.get('test_velocity', ''),
            row.get('job', ''),
            row.get('old_job', ''),
            row.get('template_tydex', ''),
            row.get('tydex_name', ''),
            row.get('p', ''),
            row.get('l', '')
        )
    
    return {"success": True, "message": f"Stored {len(excel_data)} rows"}

@router.post("/store-ftire-data")
async def store_ftire_data(request: Request, user=Depends(get_current_user)):
    """Store FTire data from Excel"""
    data = await request.json()
    excel_data = data.get('data')
    
    if not excel_data or not isinstance(excel_data, list):
        raise HTTPException(400, "Invalid data format")
    
    await db.execute("TRUNCATE TABLE ftire_data")
    
    for row in excel_data:
        await db.execute(
            """
            INSERT INTO ftire_data 
            (number_of_runs, tests, loads, inflation_pressure, test_velocity,
             longitudinal_slip, slip_angle, inclination_angle, cleat_orientation, 
             job, old_job, template_tydex, tydex_name, p, l)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            """,
            row.get('number_of_runs', 0),
            row.get('tests', ''),
            row.get('loads', ''),
            row.get('inflation_pressure', ''),
            row.get('test_velocity', ''),
            row.get('longitudinal_slip', ''),
            row.get('slip_angle', ''),
            row.get('inclination_angle', ''),
            row.get('cleat_orientation', ''),
            row.get('job', ''),
            row.get('old_job', ''),
            row.get('template_tydex', ''),
            row.get('tydex_name', ''),
            row.get('p', ''),
            row.get('l', '')
        )
    
    return {"success": True, "message": f"Stored {len(excel_data)} rows"}

@router.post("/store-cdtire-data")
async def store_cdtire_data(request: Request, user=Depends(get_current_user)):
    """Store CDTire data from Excel"""
    data = await request.json()
    excel_data = data.get('data')
    
    if not excel_data or not isinstance(excel_data, list):
        raise HTTPException(400, "Invalid data format")
    
    await db.execute("TRUNCATE TABLE cdtire_data")
    
    for row in excel_data:
        await db.execute(
            """
            INSERT INTO cdtire_data 
            (number_of_runs, test_name, inflation_pressure, velocity, preload,
             camber, slip_angle, displacement, slip_range, cleat, road_surface, 
             job, old_job, template_tydex, tydex_name, p, l)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
            """,
            row.get('number_of_runs', 0),
            row.get('test_name', ''),
            row.get('inflation_pressure', ''),
            row.get('velocity', ''),
            row.get('preload', ''),
            row.get('camber', ''),
            row.get('slip_angle', ''),
            row.get('displacement', ''),
            row.get('slip_range', ''),
            row.get('cleat', ''),
            row.get('road_surface', ''),
            row.get('job', ''),
            row.get('old_job', ''),
            row.get('template_tydex', ''),
            row.get('tydex_name', ''),
            row.get('p', ''),
            row.get('l', '')
        )
    
    return {"success": True, "message": f"Stored {len(excel_data)} rows"}

@router.post("/store-custom-data")
async def store_custom_data(request: Request, user=Depends(get_current_user)):
    """Store Custom protocol data from Excel"""
    data = await request.json()
    excel_data = data.get('data')
    
    if not excel_data or not isinstance(excel_data, list):
        raise HTTPException(400, "Invalid data format")
    
    await db.execute("TRUNCATE TABLE custom_data")
    
    for row in excel_data:
        await db.execute(
            """
            INSERT INTO custom_data 
            (number_of_runs, tests, inflation_pressure, loads,
             inclination_angle, slip_angle, slip_ratio, test_velocity, 
             cleat_orientation, displacement, job, old_job, 
             template_tydex, tydex_name, p, l)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            """,
            row.get('number_of_runs', 0),
            row.get('tests', ''),
            row.get('inflation_pressure', ''),
            row.get('loads', ''),
            row.get('inclination_angle', ''),
            row.get('slip_angle', ''),
            row.get('slip_ratio', ''),
            row.get('test_velocity', ''),
            row.get('cleat_orientation', ''),
            row.get('displacement', ''),
            row.get('job', ''),
            row.get('old_job', ''),
            row.get('template_tydex', ''),
            row.get('tydex_name', ''),
            row.get('p', ''),
            row.get('l', '')
        )
    
    return {"success": True, "message": f"Stored {len(excel_data)} rows"}