import os
import asyncio
import logging
from typing import Dict, Any, Optional, Set
from pathlib import Path

from database import db
from services.abaqus import AbaqusService
from services.file_service import FileService
from services.odb_service import ODBService

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
        self.odb_service = ODBService()
        self._visited = set()
        self.default_exe = os.getenv('ABQ_EXE', 'abaqus')
        self.default_cpus = int(os.getenv('ABQ_CPUS', 1))
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
                    slip_angle, slip_range, cleat, cpus, foltran, python_script
                FROM {table_name}
                WHERE number_of_runs = $1
            """
        else:
            query = f"""
                SELECT number_of_runs, tests, loads, inflation_pressure, test_velocity, 
                slip_angle, slip_ratio, inclination_angle, cleat_orientation, job, old_job, template_tydex, 
                tydex_name, p, l
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
        self._visited = set()

        master_row = await self._get_row_data(protocol, run_number)

        logger.info(
            f"Using run {run_number} as master parameter source."
        )

        return await self._resolve_and_run_recursive(
            project_name,
            protocol,
            run_number,
            master_row,
            progress_callback
        )
            
    async def _resolve_and_run_recursive(
        self,
        project_name: str,
        protocol: str,
        run_number: int,
        master_row: Dict[str, Any],
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Recursive dependency resolution.
        Now only sets status to 'running', starts the Abaqus job,
        and returns immediately.  Status completion/failure is handled
        by the refresh endpoint.
        """
        # Get row data
        row_data = await self._get_row_data(protocol, run_number)
        if not row_data:
            await self._update_run_status(
                protocol,
                run_number,
                "failed",
                error_message="Row data not found"
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

        # Check for circular dependencies
        job_key = f"{job_name}_{run_number}"
        if job_key in self._visited:
            logger.warning(f"Circular dependency detected for {job_key}, skipping")
            return {
                'success': True,
                'message': f'Circular dependency avoided for {job_name}',
                'skipped': True
            }
        self._visited.add(job_key)

        # Determine job type (old job, user subroutine)
        job_config = self.abaqus._determine_job_type(row_data)
        old_job = job_config.get('old_job_name')
        user_subroutine = job_config.get('user_file')

        # Resolve dependency (only run if dependency is NOT already completed)
        if old_job:
            logger.info(f"Resolving dependency: {old_job} for {job_name}")

            old_run_number = await self._find_run_number_by_job(protocol, old_job)

            if old_run_number is None:
                logger.warning(
                    f"Old job '{old_job}' not found in database. Continuing..."
                )
            else:

                dependency_completed = await self._is_completed(
                    protocol,
                    old_run_number
                )

                if dependency_completed:
                    logger.info(
                        f"Dependency '{old_job}' already completed. Skipping."
                    )

                else:
                    logger.info(
                        f"Dependency '{old_job}' not completed. Running first."
                    )

                    result = await self._resolve_and_run_recursive(
                        project_name,
                        protocol,
                        old_run_number,
                        master_row,
                        progress_callback
                    )

                    if not result.get("success", False):
                        return {
                            "success": False,
                            "message": (
                                f"Dependency '{old_job}' failed: "
                                f"{result.get('message', 'Unknown error')}"
                            )
                        }

        # Build folder path
        folder_name = f"{row_data.get('p', '')}_{row_data.get('l', '')}"
        folder_path = self.file_service.get_project_folder_path(project_name, protocol, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        # Ensure input file exists
        input_file_path = os.path.join(folder_path, f"{job_name}.inp")
        if not os.path.exists(input_file_path):
            logger.error(f"Input file not found: {input_file_path}")
            await self._update_run_status(
                protocol,
                run_number,
                "failed",
                error_message=f"Input file not found: {job_name}.inp"
            )
            return {
                "success": False,
                "message": f"Input file not found: {job_name}.inp"
            }

        # Build Abaqus configuration
        abaqus_config = {
            "job_name": job_name,
            "input_file": f"{job_name}.inp",

            # dependency information still comes from current row
            "old_job": old_job if old_job and old_job != "-" else None,
            "user_subroutine": user_subroutine if user_subroutine and user_subroutine != "-" else None,

            # execution parameters come from master row
            "python_script": row_data.get("python_script"),
            "speed_var": master_row.get("velocity"),
            "cpus": self._determine_cpus(row_data),
            "ask_del": "no",
            "abaqus_exe": self._determine_abaqus_exe(row_data, user_subroutine),

            "folder_path": folder_path,
            "run_number": run_number,
        }

        # Run Python Script Before Job
        python_script = row_data.get("python_script")

        if python_script and python_script.strip() and python_script != "-":

            script_path = os.path.join(
                os.path.dirname(folder_path),
                python_script
            )

            if not os.path.isfile(script_path):

                logger.error(
                    f"Python script not found: {script_path}"
                )

                await self._update_run_status(
                    protocol,
                    run_number,
                    "failed",
                    error_message=f"Python script not found: {python_script}"
                )

                return {
                    "success": False,
                    "message": f"Python script not found: {python_script}"
                }

            logger.info(
                f"Running pre-processing script: {python_script}"
            )

            if old_job:
                script_odb = os.path.join(folder_path, f"{old_job}.odb")
            else:
                script_odb = os.path.join(folder_path, f"{job_name}.odb")

            script_result = self.odb_service.run_python_script(
                script_path=script_path,
                odb_path=script_odb,
                working_dir=folder_path
            )

            if not script_result["success"]:

                logger.error(
                    f"Pre-processing script failed: {python_script}"
                )

                await self._update_run_status(
                    protocol,
                    run_number,
                    "failed",
                    error_message=script_result["error"]
                )

                return {
                    "success": False,
                    "message": script_result["error"]
                }

        # Set status to running and start the job
        logger.info(f"Starting Abaqus job: {job_name}")
        if progress_callback:
            await progress_callback(run_number, 'running', 5, f"Running Abaqus: {job_name}")

        await self._update_run_status(protocol, run_number, "running")

        # Start the job (does not wait for completion)
        result = await self._run_job(abaqus_config, progress_callback)

        if not result.get("success"):
            await self._update_run_status(
                protocol,
                run_number,
                "failed",
                error_message=result.get("error")
            )
            return result

        # Wait until ODB is created and readable
        odb_path = os.path.join(
            folder_path,
            f"{job_name}.odb"
        )

        timeout = 120
        poll_interval = 5
        elapsed = 0

        while True:
            # Check if ODB file exists
            if os.path.isfile(odb_path):
                logger.info(f"{job_name}.odb detected. Reading ODB...")

                try:
                    odb_content = await asyncio.to_thread(
                        self.odb_service.read_odb_content,
                        odb_path
                    )

                    if odb_content.get("success"):
                        logger.info(
                            f"{job_name} completed successfully."
                        )

                        await self._update_run_status(
                            protocol,
                            run_number,
                            "completed",
                            odb_path=odb_path
                        )

                        return {
                            "success": True,
                            "message": "Analysis completed successfully."
                        }

                    else:

                        logger.error(
                            f"{job_name} analysis failed."
                        )

                        await self._update_run_status(
                            protocol,
                            run_number,
                            "failed",
                            error_message=odb_content.get("status", "Analysis failed")
                        )

                        if os.path.exists(odb_path):
                            os.remove(odb_path)
                            logger.warning(f"Deleted failed ODB: {odb_path}")

                        return {
                            "success": False,
                            "message": odb_content.get("status", "Analysis failed")
                        }

                except Exception as e:

                    logger.error(
                        f"ODB processing failed: {e}"
                    )

                    # DELETE INVALID ODB
                    if os.path.exists(odb_path):
                        os.remove(odb_path)
                        logger.warning(
                            f"Deleted failed ODB: {odb_path}"
                        )

                    await self._update_run_status(
                        protocol,
                        run_number,
                        "failed",
                        error_message=str(e)
                    )

                    return {
                        "success": False,
                        "message": str(e)
                    }

            if elapsed >= timeout:

                logger.error(
                    f"Timeout waiting for valid ODB: {job_name}"
                )

                await self._update_run_status(
                    protocol,
                    run_number,
                    "failed",
                    error_message="Timed out waiting for valid ODB"
                )

                return {
                    "success": False,
                    "message": "Timed out waiting for valid ODB"
                }

            logger.info(
                f"Waiting for valid {job_name}.odb..."
            )

            await asyncio.sleep(
                poll_interval
            )

            elapsed += poll_interval

    async def _get_run_status(self, protocol: str, run_number: int):
        table = self._get_table_name(protocol)

        row = await db.execute_one(
            f"""
            SELECT run_status
            FROM {table}
            WHERE number_of_runs=$1
            """,
            run_number,
        )

        return row["run_status"] if row else None

    async def _is_completed(self, protocol: str, run_number: int) -> bool:
        table = self._get_table_name(protocol)

        row = await db.execute_one(
            f"""
            SELECT run_status
            FROM {table}
            WHERE number_of_runs=$1
            """,
            run_number,
        )

        if not row:
            return False

        return row["run_status"] == "completed"
    
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
        """
        Determine the CPU count for the Abaqus job.

        Priority:
        1. Use the CPU count specified in the database row (if present).
        2. Otherwise use the value from ABQ_CPUS in the .env file.
        """

        cpus = row_data.get("cpus")
        print("\n", cpus, "\n")

        # Use .env default if database doesn't specify CPUs
        if cpus in (None, "", "-"):
            cpus = self.default_cpus

        try:
            cpus = int(cpus)
        except (TypeError, ValueError):
            cpus = self.default_cpus

        logger.info(f"Using {cpus} CPU(s) for Abaqus job")

        return cpus
        
    def _determine_abaqus_exe(self, row_data: Dict[str, Any], user_subroutine: Optional[str] = None) -> str:
        """Determine which Abaqus executable to use."""
        # For student version, use 'abaqus' as the executable
        # If user_subroutine is present, we might need to use a different version
        if user_subroutine or (row_data.get('foltran') and row_data['foltran'] != '-'):
            # Try to use the version that supports fortran
            return 'abq2024hf5f'
        return self.default_exe
    
    