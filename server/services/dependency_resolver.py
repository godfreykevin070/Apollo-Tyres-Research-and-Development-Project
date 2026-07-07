import os
import asyncio
import logging
from typing import Dict, Any, Optional, Set
from pathlib import Path

from database import db
from services.abaqus import AbaqusService
from services.file_service import FileService

logger = logging.getLogger(__name__)

class DependencyResolver:
    """
    Resolves job dependencies and executes simulations in the correct order.
    
    Handles three patterns:
    1. No old job: Execute directly
    2. Has old job: Recursively resolve and execute old job first
    3. Has user subroutine: Execute with fortran file
    """
    def __init__(self):
        self.abaqus = AbaqusService()
        self.file_service = FileService()
        self._visited = set()
        self.default_exe = os.getenv('ABQ_EXE', 'abaqus')
        self.default_cpus = int(os.getenv('ABQ_CPUS', 4))
        self.default_ask_del = os.getenv('ABQ_ASK_DEL', 'no')
    
    def _get_table_name(self, protocol: str) -> str:
        """Get the project data table name for a protocol"""
        table_map = {
            'mf62': 'mf62_project_data',
            'mf52': 'mf52_project_data',
            'ftire': 'ftire_project_data',
            'cdtire': 'cdtire_project_data',
            'custom': 'custom_project_data'
        }
        return table_map.get(protocol.lower())
    
    async def _get_row_data(self, protocol: str, run_number: int) -> Optional[Dict[str, Any]]:
        """Get row data from the database"""
        table_name = self._get_table_name(protocol)
        if not table_name:
            return None
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
        
        row = await db.execute_one(query, run_number)
        return dict(row) if row else None
    
    async def _update_run_status(
        self,
        protocol: str,
        run_number: int,
        status: str,
        error_message: str = None,
        odb_path: str = None,
    ):
        table_name = self._get_table_name(protocol)

        query = f"""
        UPDATE {table_name}
        SET
            run_status = $1::varchar,
            run_start_time = CASE
                WHEN $1::varchar = 'running'::varchar
                THEN CURRENT_TIMESTAMP
                ELSE run_start_time
            END,
            run_end_time = CASE
                WHEN $1::varchar IN (
                    'completed'::varchar,
                    'failed'::varchar
                )
                THEN CURRENT_TIMESTAMP
                ELSE run_end_time
            END,
            error_message = $2,
            odb_path = $3
        WHERE number_of_runs = $4
        """

        await db.execute(
            query,
            status,
            error_message,
            odb_path,
            run_number,
        )
    
    async def _check_odb_exists(self, project_name: str, protocol: str, 
                                 folder_name: str, job_name: str) -> bool:
        """Check if ODB file already exists"""
        exists, _ = self.file_service.check_odb_file(
            project_name, protocol, folder_name, job_name
        )
        return exists
    
    async def _run_job(self, config: Dict[str, Any], 
                       progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Run a single Abaqus job with the given configuration.
        
        Config:
            - job_name: str
            - input_file: str
            - old_job: Optional[str]
            - user_subroutine: Optional[str]
            - cpus: int
            - folder_path: str
            - run_number: int
            - abaqus_exe: str
        """
        run_number = config.get('run_number')
        folder_name = os.path.basename(config.get('folder_path', ''))
        
        if progress_callback:
            await progress_callback(run_number, 'running', 10, f"Starting job {config['job_name']}")
        
        # Run the job
        result = await self.abaqus.run_job(config)
        
        if progress_callback:
            if result.get('success'):
                await progress_callback(run_number, 'done', 100, f"Job {config['job_name']} completed")
            else:
                await progress_callback(run_number, 'failed', 100, 
                                       f"Job {config['job_name']} failed: {result.get('error', 'Unknown error')}")
        
        return result
    
    async def resolve_and_run(self, project_name: str, protocol: str, run_number: int,
                              progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Main entry point: resolve dependencies and run the simulation.
        
        Flow:
        1. Get row data from database
        2. Check if ODB already exists -> skip if done
        3. If old_job exists -> recursively resolve and run old job first
        4. Build Abaqus command based on job type
        5. Execute Abaqus
        6. Return result
        """
        self._visited = set()  # Reset visited set for each run
        
        return await self._resolve_and_run_recursive(
            project_name, protocol, run_number, progress_callback
        )
    
    async def _resolve_and_run_recursive(self, project_name: str, protocol: str, 
                                         run_number: int,
                                         progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Recursive dependency resolution.
        """
        # Get row data
        row_data = await self._get_row_data(protocol, run_number)
        if not row_data:
            await self._update_run_status(
                protocol,
                run_number,
                "failed",
                "Row data not found"
            )
            return {
                'success': False,
                'message': f'Row data not found for run {run_number}'
            }
        
        job_name = row_data.get('job', '').strip()
        if not job_name:
            return {
                'success': False,
                'message': f'No job specified for run {run_number}'
            }
        
        # Check if already visited (circular dependency)
        job_key = f"{job_name}_{run_number}"
        if job_key in self._visited:
            logger.warning(f"Circular dependency detected for {job_key}, skipping")
            return {
                'success': True,
                'message': f'Circular dependency avoided for {job_name}',
                'skipped': True
            }
        self._visited.add(job_key)
        
        # Check if ODB already exists
        folder_name = f"{row_data.get('p', '')}_{row_data.get('l', '')}"
        if await self._check_odb_exists(project_name, protocol, folder_name, job_name):
            logger.info(f"ODB already exists for {job_name}, skipping")
            if progress_callback:
                await progress_callback(run_number, 'done', 100, f"Job {job_name} already completed")
            
            await self._update_run_status(
                protocol,
                run_number,
                "completed"
            )

            return {
                "success": True,
                "message": f"ODB already exists for {job_name}",
                "skipped": True
            }
        
        # Determine job type
        job_config = self.abaqus._determine_job_type(row_data)
        old_job = job_config.get('old_job_name')
        user_subroutine = job_config.get('user_file')
        
        # Resolve old job dependency if exists
        if old_job:
            logger.info(f"Resolving dependency: {old_job} for {job_name}")
            # Find the run number for the old job
            old_run_number = await self._find_run_number_by_job(protocol, old_job)
            if old_run_number:
                result = await self._resolve_and_run_recursive(
                    project_name, protocol, old_run_number, progress_callback
                )
                if not result.get('success'):
                    return {
                        'success': False,
                        'message': f"Failed to resolve dependency {old_job}: {result.get('message', 'Unknown error')}"
                    }
            else:
                logger.warning(f"Old job {old_job} not found in database, attempting to run anyway")
        
        # Build Abaqus config
        folder_path = self.file_service.get_project_folder_path(project_name, protocol, folder_name)
        
        # Ensure folder exists
        os.makedirs(folder_path, exist_ok=True)
        
        # Check if input file exists, if not, try to find it or create from template
        input_file_path = os.path.join(folder_path, f"{job_name}.inp")
        if not os.path.exists(input_file_path):
            # Try to copy from templates
            template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'inp')
            template_path = os.path.join(template_dir, f"{job_name}.inp")
            if os.path.exists(template_path):
                import shutil
                shutil.copy2(template_path, input_file_path)
                logger.info(f"Copied template input file to {input_file_path}")
            else:
                # Create empty input file (this is a fallback)
                with open(input_file_path, 'w') as f:
                    f.write(f"*HEADING\n** Abaqus Input File for {job_name}\n")
                    f.write("*END\n")
                logger.warning(f"Created empty input file at {input_file_path}")
        
        abaqus_config = {
            "job_name": job_name,
            "input_file": f"{job_name}.inp",
            "old_job": old_job if old_job and old_job != "-" else None,
            "user_subroutine": user_subroutine if user_subroutine and user_subroutine != "-" else None,

            "python_script": row_data.get("python_script"),
            "speed_var": row_data.get("velocity"),

            "cpus": self._determine_cpus(row_data),
            "ask_del": "no",
            "abaqus_exe": self._determine_abaqus_exe(row_data, user_subroutine),
            "folder_path": folder_path,
            "run_number": run_number,
        }
        
        # Execute the job
        logger.info(f"Running Abaqus job: {job_name} with config: {abaqus_config}")
        
        if progress_callback:
            await progress_callback(run_number, 'running', 5, f"Running Abaqus: {job_name}")
        
        await self._update_run_status(
            protocol,
            run_number,
            "running"
        )
        
        result = await self._run_job(abaqus_config, progress_callback)
        
        # Check if ODB was created
        if result.get("success"):
            odb_path = os.path.join(
                folder_path,
                f"{job_name}.odb"
            )

            await self._update_run_status(
                protocol,
                run_number,
                "completed",
                odb_path=odb_path
            )

        else:
            await self._update_run_status(
                protocol,
                run_number,
                "failed",
                error_message=result.get("error") or result.get("stderr")
            )

        return result
    
    async def _find_run_number_by_job(self, protocol: str, job_name: str) -> Optional[int]:
        """Find the run number for a given job name"""
        table_name = self._get_table_name(protocol)
        if not table_name:
            return None
        
        # Try exact match and with .inp extension
        query = f"""
            SELECT number_of_runs 
            FROM {table_name}
            WHERE job = $1 OR job = $2
            LIMIT 1
        """
        
        result = await db.execute_one(query, job_name, job_name + '.inp')
        return result[0] if result else None
    
    def _determine_cpus(self, row_data: Dict[str, Any]) -> int:
        """Determine CPU count for the job. Max 4 for student version."""
        # Student version is limited to 4 CPUs
        base_cpus = 1
        
        # Could add logic to increase if needed, but student version caps at 4
        return base_cpus
    
    def _determine_abaqus_exe(self, row_data: Dict[str, Any], user_subroutine: Optional[str] = None) -> str:
        """Determine which Abaqus executable to use."""
        # For student version, use 'abaqus' as the executable
        # If user_subroutine is present, we might need to use a different version
        if user_subroutine or (row_data.get('foltran') and row_data['foltran'] != '-'):
            # Try to use the version that supports fortran
            return 'abq2024hf5f'
        return self.default_exe