from fastapi import APIRouter, Depends, Request, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from openpyxl import load_workbook
import os
import json
from typing import List, Dict, Any
import logging

from database import db
from auth import get_current_user
from services.excel_service import ExcelService
from services.file_service import FileService

router = APIRouter()
excel_service = ExcelService()
file_service = FileService()
logger = logging.getLogger(__name__)

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
        'mf62': 'mf62_data',
        'mf52': 'mf52_data',
        'ftire': 'ftire_data',
        'cdtire': 'cdtire_data',
        'custom': 'custom_data'
    }
    
    table_name = table_map.get(protocol.lower(), 'mf62_data')
    
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
        'MF62': 'mf62_data',
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
            (project_id, number_of_runs, tests, inflation_pressure, loads, inclination_angle, 
             slip_angle, slip_ratio, test_velocity, job, old_job, 
             template_tydex, tydex_name, p, l)
            SELECT $1, number_of_runs, tests, inflation_pressure, loads, inclination_angle, 
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
            (project_id, number_of_runs, tests, inflation_pressure, velocity, 
             loads, camber, slip_angle, slip_range, cleat, 
             road_surface, job, old_job, template_tydex, tydex_name, p, l)
            SELECT $1, number_of_runs, tests, inflation_pressure, velocity, 
                   loads, camber, slip_angle, slip_range, cleat, 
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
async def store_mf52_data(user=Depends(get_current_user)):
    """Read MF52 Excel file from disk and store into mf52_data"""

    file_path = os.path.join(file_service.protocol_dir, "MF5pt2.xlsx")

    if not os.path.exists(file_path):
        raise HTTPException(404, f"File not found: {file_path}")

    try:
        # Read Excel
        excel_data = excel_service.read_excel_data(file_path)

        if not excel_data:
            raise HTTPException(400, "Excel file contains no data")

        # Clear scratch table
        await db.execute("TRUNCATE TABLE mf52_data")

        # Insert every row
        for row in excel_data:
            await db.execute(
                """
                INSERT INTO mf52_data
                (
                    number_of_runs,
                    tests,
                    inflation_pressure,
                    loads,
                    inclination_angle,
                    slip_angle,
                    slip_ratio,
                    test_velocity,
                    job,
                    old_job,
                    template_tydex,
                    tydex_name,
                    p,
                    l
                )
                VALUES
                (
                    $1,$2,$3,$4,$5,$6,$7,$8,
                    $9,$10,$11,$12,$13,$14
                )
                """,
                int(row.get("number_of_tests", 0)),
                str(row.get("tests", "")),
                str(row.get("inflation_pressure_psi", "")),
                str(row.get("loadskg", "")),
                str(row.get("inclination_angle", "")),
                str(row.get("slip_angle", "")),
                str(row.get("slip_ratio_", "")),
                str(row.get("test_velocity_kmph", "")),
                str(row.get("job", "")),
                str(row.get("old_job", "")), 
                str(row.get("template_tydex", "")),
                str(row.get("tydex_name", "")), 
                str(row.get("inflation_pressure_psi", "")),
                str(row.get("loadskg", ""))  
            )

        return {
            "success": True,
            "rows": len(excel_data),
            "message": f"Imported {len(excel_data)} rows."
        }

    except Exception as e:
        logger.exception("Failed to import MF52 Excel")
        raise HTTPException(500, str(e))

@router.post("/process-mf52")
async def process_mf52(
    request: Request, 
    user=Depends(get_current_user)
):
    """Process MF52 protocol data"""
    try:
        data = await request.json()

        project_id = data.get("projectId")
        project_id = int(project_id)
        parameters = data.get("parameters", {})

        if not project_id:
            raise HTTPException(400, "Project ID is required")

        # 1. Verify project and permissions
        project = await db.execute_one(
            "SELECT id, project_name, user_email FROM projects WHERE id = $1",
            project_id
        )
        if not project:
            raise HTTPException(404, "Project not found")
        
        if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
            raise HTTPException(403, "Forbidden")

        # 2. Save parameters to project
        if parameters:
            await db.execute(
                "UPDATE projects SET inputs = $1 WHERE id = $2",
                json.dumps(parameters),
                project_id
            )
            
            # 4. Copy from scratch table to project table
            # Delete existing rows for this project
            await db.execute(
                "DELETE FROM mf52_project_data WHERE project_id = $1", 
                project_id
            )
            
            # Get column names from the scratch table (excluding id, created_at)
            cols_query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'mf52_data'
                AND column_name NOT IN ('id', 'created_at')
                ORDER BY ordinal_position
            """
            col_rows = await db.execute(cols_query)
            col_names = [row['column_name'] for row in col_rows]
            
            if col_names:
                col_list = ', '.join(col_names)
                # Copy data from scratch to project table
                insert_query = f"""
                    INSERT INTO mf52_project_data (project_id, {col_list})
                    SELECT $1, {col_list}
                    FROM mf52_data
                """
                await db.execute(insert_query, project_id)

        # 5. Generate parameter files (if needed)
        try:
            # This would call your file_service to generate parameters
            # file_service.generate_parameters(parameters, '/mf52')
            pass
        except Exception as e:
            print(f"Warning: Could not generate parameters: {e}")

        # 6. Update project status
        await db.execute(
            "UPDATE projects SET status = $1 WHERE id = $2",
            'processing',
            project_id
        )

        return {
            "success": True,
            "message": "MF52 processing completed successfully",
            "projectId": project_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in process_mf52: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(500, f"Error processing MF52: {str(e)}")

# ============================================================
# MF62
# ============================================================

@router.post("/store-mf62-data")
async def store_mf62_data(user=Depends(get_current_user)):
    """Read MF62 Excel file from disk and store into mf62_data"""
    file_path = os.path.join(file_service.protocol_dir, "MF6pt2.xlsx")

    if not os.path.exists(file_path):
        raise HTTPException(404, f"File not found: {file_path}")

    try:
        # Read Excel
        excel_data = excel_service.read_excel_data(file_path)

        if not excel_data:
            raise HTTPException(400, "Excel file contains no data")

        # Clear scratch table
        await db.execute("TRUNCATE TABLE mf62_data")

        # Insert every row
        for row in excel_data:
            await db.execute(
                """
                INSERT INTO mf62_data
                (
                    number_of_runs, tests, inflation_pressure, loads, inclination_angle,
                    slip_angle, slip_ratio, test_velocity,
                    job, old_job, template_tydex, tydex_name, p, l
                )
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
                """,
                int(row.get("number_of_tests", 0)),
                str(row.get("tests", "")),
                str(row.get("inflation_pressure_psi", "")),
                str(row.get("loadskg", "")),
                str(row.get("inclination_angle", "")),
                str(row.get("slip_angle", "")),
                str(row.get("slip_ratio_", "")),
                str(row.get("test_velocity_kmph", "")),
                str(row.get("job", "")),
                str(row.get("old_job", "")),
                str(row.get("template_tydex", "")),
                str(row.get("tydex_name", "")),
                str(row.get("inflation_pressure_psi", "")),
                str(row.get("loadskg", ""))
            )

        return {
            "success": True,
            "rows": len(excel_data),
            "message": f"Imported {len(excel_data)} rows."
        }
    except Exception as e:
        logger.exception("Failed to import MF62 Excel")
        raise HTTPException(500, str(e))


@router.post("/process-mf62")
async def process_mf62(request: Request, user=Depends(get_current_user)):
    """Process MF62 protocol data"""
    try:
        data = await request.json()
        project_id = int(data.get("projectId"))
        parameters = data.get("parameters", {})

        if not project_id:
            raise HTTPException(400, "Project ID is required")

        project = await db.execute_one(
            "SELECT id, project_name, user_email FROM projects WHERE id = $1",
            project_id
        )
        if not project:
            raise HTTPException(404, "Project not found")
        if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
            raise HTTPException(403, "Forbidden")

        if parameters:
            await db.execute(
                "UPDATE projects SET inputs = $1 WHERE id = $2",
                json.dumps(parameters), project_id
            )

            await db.execute(
                "DELETE FROM mf62_project_data WHERE project_id = $1",
                project_id
            )

            cols_query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'mf62_data'
                AND column_name NOT IN ('id', 'created_at')
                ORDER BY ordinal_position
            """
            col_rows = await db.execute(cols_query)
            col_names = [row['column_name'] for row in col_rows]

            if col_names:
                col_list = ', '.join(col_names)
                insert_query = f"""
                    INSERT INTO mf62_project_data (project_id, {col_list})
                    SELECT $1, {col_list}
                    FROM mf62_data
                """
                await db.execute(insert_query, project_id)

        await db.execute(
            "UPDATE projects SET status = $1 WHERE id = $2",
            'processing', project_id
        )

        return {
            "success": True,
            "message": "MF62 processing completed successfully",
            "projectId": project_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in process_mf62")
        raise HTTPException(500, f"Error processing MF62: {str(e)}")

# ============================================================
# FTire
# ============================================================

@router.post("/store-ftire-data")
async def store_ftire_data(user=Depends(get_current_user)):
    """Read FTire Excel file and store into ftire_data (upsert on conflict)"""
    file_path = os.path.join(file_service.protocol_dir, "FTire.xlsx")

    if not os.path.exists(file_path):
        raise HTTPException(404, f"File not found: {file_path}")

    try:
        # Read Excel
        excel_data = excel_service.read_excel_data(file_path)

        if not excel_data:
            raise HTTPException(400, "Excel file contains no data")

        # Clear scratch table
        await db.execute("TRUNCATE TABLE ftire_data")

        # Insert every row
        for row in excel_data:
            print("row: ", row)
            await db.execute(
                """
                INSERT INTO ftire_data
                (
                    number_of_runs, tests, loads, inflation_pressure, test_velocity,
                    longitudinal_slip, slip_angle, inclination_angle, cleat_orientation,
                    job, old_job, template_tydex, tydex_name, p, l
                )
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
                """,
                int(row.get("number_of_tests", 0)),
                str(row.get("test", "")),
                str(row.get("load_n", "")),
                str(row.get("ip_kpa", "")),
                str(row.get("speed_kmph", "")),
                str(row.get("longitudinal_slip_", "")),
                str(row.get("slip_angle_deg", "")),
                str(row.get("inclination_angle_deg", "")),
                str(row.get("cleat_orientation_w.r.t_axial_direction_deg", "")),
                str(row.get("job", "")),
                str(row.get("old_job", "")),
                str(row.get("template_tydex", "")),
                str(row.get("tydex_name", "")),
                str(row.get("ip_kpa", "")),
                str(row.get("load_n", ""))
            )

        return {
            "success": True,
            "rows": len(excel_data),
            "message": f"Imported {len(excel_data)} rows."
        }
    except Exception as e:
        logger.exception("Failed to import FTire Excel")
        raise HTTPException(500, str(e))


@router.post("/process-ftire")
async def process_ftire(request: Request, user=Depends(get_current_user)):
    """Process FTire protocol data"""
    try:
        data = await request.json()
        project_id = int(data.get("projectId"))
        parameters = data.get("parameters", {})

        if not project_id:
            raise HTTPException(400, "Project ID is required")

        project = await db.execute_one(
            "SELECT id, project_name, user_email FROM projects WHERE id = $1",
            project_id
        )
        if not project:
            raise HTTPException(404, "Project not found")
        if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
            raise HTTPException(403, "Forbidden")

        if parameters:
            await db.execute(
                "UPDATE projects SET inputs = $1 WHERE id = $2",
                json.dumps(parameters), project_id
            )

            await db.execute(
                "DELETE FROM ftire_project_data WHERE project_id = $1",
                project_id
            )

            cols_query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'ftire_data'
                AND column_name NOT IN ('id', 'created_at')
                ORDER BY ordinal_position
            """
            col_rows = await db.execute(cols_query)
            col_names = [row['column_name'] for row in col_rows]

            if col_names:
                col_list = ', '.join(col_names)
                insert_query = f"""
                    INSERT INTO ftire_project_data (project_id, {col_list})
                    SELECT $1, {col_list}
                    FROM ftire_data
                """
                await db.execute(insert_query, project_id)

        await db.execute(
            "UPDATE projects SET status = $1 WHERE id = $2",
            'processing', project_id
        )

        return {
            "success": True,
            "message": "FTire processing completed successfully",
            "projectId": project_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in process_ftire")
        raise HTTPException(500, f"Error processing FTire: {str(e)}")


# ============================================================
# CDTire
# ============================================================

@router.post("/store-cdtire-data")
async def store_cdtire_data(user=Depends(get_current_user)):
    """Read CDTire Excel file and store into cdtire_data (upsert on conflict)"""
    file_path = os.path.join(file_service.protocol_dir, "CDTire.xlsx")
    print(file_path)

    if not os.path.exists(file_path):
        raise HTTPException(404, f"File not found: {file_path}")

    try:
        # Read Excel
        excel_data = excel_service.read_excel_data(file_path)

        if not excel_data:
            raise HTTPException(400, "Excel file contains no data")

        # Clear scratch table
        await db.execute("TRUNCATE TABLE cdtire_data")

        # Insert every row
        for row in excel_data:
            await db.execute(
                """
                INSERT INTO cdtire_data(
                    number_of_runs,
                    tests,
                    inflation_pressure,
                    velocity,
                    loads,
                    camber,
                    slip_angle,
                    slip_range,
                    cleat,
                    road_surface,
                    job,
                    old_job,
                    template_tydex,
                    tydex_name,
                    p,
                    l,
                    foltran,
                    python_script
                )
                VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18)
                """,
                int(row.get("no_of_tests", 0)),
                str(row.get("test_name", "")),
                str(row.get("inflation_pressure_bar", "")),
                str(row.get("speed_km_h", "")),
                str(row.get("load_n", "")),
                str(row.get("camber_deg", "")),
                str(row.get("slip_angle_deg", "")),
                str(row.get("slip_range_", "")),
                str(row.get("cleat", "")),
                str(row.get("road_surface", "")),
                str(row.get("job", "")),
                str(row.get("old_job", "")),
                str(row.get("template_tydex", "")),
                str(row.get("tydex_name", "")),
                str(row.get("inflation_pressure_bar", "")),
                str(row.get("load_n", "")),
                str(row.get("folrtran", "")),
                str(row.get("python_script", ""))                  
            )

        return {
            "success": True,
            "rows": len(excel_data),
            "message": f"Imported {len(excel_data)} rows."
        }
    except Exception as e:
        logger.exception("Failed to import CDTire Excel")
        raise HTTPException(500, str(e))


@router.post("/process-cdtire")
async def process_cdtire(request: Request, user=Depends(get_current_user)):
    """Process CDTire protocol data"""
    try:
        data = await request.json()
        project_id = int(data.get("projectId"))
        parameters = data.get("parameters", {})

        if not project_id:
            raise HTTPException(400, "Project ID is required")

        project = await db.execute_one(
            "SELECT id, project_name, user_email FROM projects WHERE id = $1",
            project_id
        )
        if not project:
            raise HTTPException(404, "Project not found")
        if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
            raise HTTPException(403, "Forbidden")

        if parameters:
            await db.execute(
                "UPDATE projects SET inputs = $1 WHERE id = $2",
                json.dumps(parameters), project_id
            )

            await db.execute(
                "DELETE FROM cdtire_project_data WHERE project_id = $1",
                project_id
            )

            cols_query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'cdtire_data'
                AND column_name NOT IN ('id', 'created_at')
                ORDER BY ordinal_position
            """
            col_rows = await db.execute(cols_query)
            col_names = [row['column_name'] for row in col_rows]

            if col_names:
                col_list = ', '.join(col_names)
                insert_query = f"""
                    INSERT INTO cdtire_project_data (project_id, {col_list})
                    SELECT $1, {col_list}
                    FROM cdtire_data
                """
                await db.execute(insert_query, project_id)

        await db.execute(
            "UPDATE projects SET status = $1 WHERE id = $2",
            'processing', project_id
        )

        return {
            "success": True,
            "message": "CDTire processing completed successfully",
            "projectId": project_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in process_cdtire")
        raise HTTPException(500, f"Error processing CDTire: {str(e)}")


# ============================================================
# Custom
# ============================================================

@router.post("/store-custom-data")
async def store_custom_data(user=Depends(get_current_user)):
    """Read Custom Excel file and store into custom_data (upsert on conflict)"""
    file_path = os.path.join(file_service.protocol_dir, "Custom.xlsx")
    if not os.path.exists(file_path):
        raise HTTPException(404, f"File not found: {file_path}")

    try:
        excel_data = excel_service.read_excel_data(file_path)
        if not excel_data:
            raise HTTPException(400, "Excel file contains no data")

        await db.execute("TRUNCATE TABLE custom_data")

        for row in excel_data:
            run_num = row.get("number_of_runs")
            if run_num is None or str(run_num).strip() == "":
                run_num = 0
            else:
                run_num = int(run_num)

            await db.execute(
                """
                INSERT INTO custom_data
                (
                    number_of_runs, tests, inflation_pressure, loads,
                    inclination_angle, slip_angle, slip_ratio, test_velocity,
                    cleat_orientation, displacement, job, old_job,
                    template_tydex, tydex_name, p, l
                )
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)
                ON CONFLICT (number_of_runs) DO UPDATE SET
                    tests = EXCLUDED.tests,
                    inflation_pressure = EXCLUDED.inflation_pressure,
                    loads = EXCLUDED.loads,
                    inclination_angle = EXCLUDED.inclination_angle,
                    slip_angle = EXCLUDED.slip_angle,
                    slip_ratio = EXCLUDED.slip_ratio,
                    test_velocity = EXCLUDED.test_velocity,
                    cleat_orientation = EXCLUDED.cleat_orientation,
                    displacement = EXCLUDED.displacement,
                    job = EXCLUDED.job,
                    old_job = EXCLUDED.old_job,
                    template_tydex = EXCLUDED.template_tydex,
                    tydex_name = EXCLUDED.tydex_name,
                    p = EXCLUDED.p,
                    l = EXCLUDED.l
                """,
                run_num,
                str(row.get("tests", "")),
                str(row.get("inflation_pressure", "")),
                str(row.get("loads", "")),
                str(row.get("inclination_angle", "")),
                str(row.get("slip_angle", "")),
                str(row.get("slip_ratio", "")),
                str(row.get("test_velocity", "")),
                str(row.get("cleat_orientation", "")),
                str(row.get("displacement", "")),
                str(row.get("job", "")),
                str(row.get("old_job", "")),
                str(row.get("template_tydex", "")),
                str(row.get("tydex_name", "")),
                str(row.get("p", "")),
                str(row.get("l", ""))
            )

        return {
            "success": True,
            "rows": len(excel_data),
            "message": f"Imported {len(excel_data)} rows."
        }
    except Exception as e:
        logger.exception("Failed to import Custom Excel")
        raise HTTPException(500, str(e))


@router.post("/process-custom")
async def process_custom(request: Request, user=Depends(get_current_user)):
    """Process Custom protocol data"""
    try:
        data = await request.json()
        project_id = int(data.get("projectId"))
        parameters = data.get("parameters", {})

        if not project_id:
            raise HTTPException(400, "Project ID is required")

        project = await db.execute_one(
            "SELECT id, project_name, user_email FROM projects WHERE id = $1",
            project_id
        )
        if not project:
            raise HTTPException(404, "Project not found")
        if user['role'] not in ['manager', 'admin'] and project['user_email'] != user['email']:
            raise HTTPException(403, "Forbidden")

        if parameters:
            await db.execute(
                "UPDATE projects SET inputs = $1 WHERE id = $2",
                json.dumps(parameters), project_id
            )

            await db.execute(
                "DELETE FROM custom_project_data WHERE project_id = $1",
                project_id
            )

            cols_query = """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'custom_data'
                AND column_name NOT IN ('id', 'created_at')
                ORDER BY ordinal_position
            """
            col_rows = await db.execute(cols_query)
            col_names = [row['column_name'] for row in col_rows]

            if col_names:
                col_list = ', '.join(col_names)
                insert_query = f"""
                    INSERT INTO custom_project_data (project_id, {col_list})
                    SELECT $1, {col_list}
                    FROM custom_data
                """
                await db.execute(insert_query, project_id)

        await db.execute(
            "UPDATE projects SET status = $1 WHERE id = $2",
            'processing', project_id
        )

        return {
            "success": True,
            "message": "Custom processing completed successfully",
            "projectId": project_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in process_custom")
        raise HTTPException(500, f"Error processing Custom: {str(e)}")