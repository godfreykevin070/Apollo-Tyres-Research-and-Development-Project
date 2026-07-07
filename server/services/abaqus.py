import os
import subprocess
import asyncio
import signal
import logging
from typing import Optional, Dict, List, Any
from pathlib import Path
import shlex

logger = logging.getLogger(__name__)

# Global tracking of running processes
_running_processes: Dict[int, subprocess.Popen] = {}

class AbaqusService:
    """Service for managing Abaqus simulations"""
    
    def __init__(self):
        self.default_exe = os.getenv('ABQ_EXE', 'abaqus')
        self.default_cpus = int(os.getenv('ABQ_CPUS', 4))
        self.default_ask_del = os.getenv('ABQ_ASK_DEL', 'no')
    
    def _build_command(self, config: Dict[str, Any]) -> List[str]:
        """
        Build Abaqus command based on configuration.
        
        Supports three patterns:
        1. No old job: abaqus job=JOB_NAME input=INPUT_FILE cpus=N ask_del=no int
        2. Has old job: abaqus job=JOB_NAME oldjob=OLD_JOB cpus=N ask_del=no int
        3. Has user subroutine: abq2024hf5f job=JOB_NAME oldjob=OLD_JOB user=USER_FILE.f cpus=N int
        """
        exe = config.get('abaqus_exe', self.default_exe)
        job_name = config.get('job_name', '')
        input_file = config.get('input_file', f"{job_name}.inp")
        old_job = config.get('old_job')
        user_subroutine = config.get('user_subroutine')
        cpus = config.get('cpus', self.default_cpus)
        ask_del = config.get('ask_del', self.default_ask_del)
        
        if not job_name:
            raise ValueError("Job name is required")
        
        # For student version, we need to use the correct executable
        # and ensure ask_del=no is set
        cmd = [exe]
        
        # For student version, we might need to use 'abaqus' directly
        if exe == 'abaqus':
            cmd.append(f"job={job_name}")
            cmd.append(f"input={input_file}")
            
            if old_job and old_job != '-' and old_job.strip():
                cmd.append(f"oldjob={old_job}")
            
            if user_subroutine and user_subroutine.strip():
                if not user_subroutine.endswith('.f'):
                    user_subroutine += '.f'
                cmd.append(f"user={user_subroutine}")
            
            cmd.append(f"cpus={cpus}")
            cmd.append(f"ask_del={ask_del}")
            cmd.append("int")
        else:
            # For other versions (like abq2024hf5f)
            cmd.append(f"job={job_name}")
            cmd.append(f"input={input_file}")
            
            if old_job and old_job != '-' and old_job.strip():
                cmd.append(f"oldjob={old_job}")
            
            if user_subroutine and user_subroutine.strip():
                if not user_subroutine.endswith('.f'):
                    user_subroutine += '.f'
                cmd.append(f"user={user_subroutine}")
            
            cmd.append(f"cpus={cpus}")
            cmd.append("int")
        
        logger.info(f"Built command: {' '.join(cmd)}")
        return cmd
    
    def _determine_job_type(self, row_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine the job type and build configuration based on row data.
        """

        job = (row_data.get("job") or "").strip()
        old_job = (row_data.get("old_job") or "").strip()
        foltran = (row_data.get("foltran") or "").strip()
        python_script = (row_data.get("python_script") or "").strip()

        has_user = bool(foltran and foltran != "-")
        has_old_job = bool(old_job and old_job != "-" and old_job != job)

        return {
            "job_name": job,
            "old_job_name": old_job if has_old_job else None,
            "user_file": foltran if has_user else None,
            "python_script": python_script if python_script and python_script != "-" else None,
            "has_old_job": has_old_job,
            "has_user_subroutine": has_user,
        }
    
    async def run_job(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run an Abaqus job asynchronously with real-time output capture.
        """
        folder_path = config.get('folder_path')
        if not folder_path or not os.path.exists(folder_path):
            raise ValueError(f"Folder path does not exist: {folder_path}")
        
        # Build command
        cmd = self._build_command(config)
        
        # Set working directory
        cwd = folder_path
        
        logger.info(f"Running command in {cwd}: {' '.join(cmd)}")
        
        # Create process with pipes for stdout and stderr
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        
        # Store process reference for stop-all
        _running_processes[process.pid] = process
        
        try:
            # Use asyncio.wait_for with a timeout
            try:
                stdout, stderr = process.communicate(timeout=7200)
            except asyncio.TimeoutError:
                logger.error(f"Job {config.get('job_name')} timed out after 2 hours")
                process.kill()
                process.wait()

                return {
                    "success": False,
                    "exit_code": -1,
                    "error": "Job execution timed out after 2 hours",
                    "job_name": config.get("job_name"),
                    "folder": folder_path,
                }
            
            exit_code = process.returncode
            
            # Log output
            if stdout:
                logger.debug(stdout[:500] if stdout else "")
            if stderr:
                logger.debug(stderr[:500] if stderr else "")
            
            # Check if the job completed successfully
            if exit_code == 0:

                job_name = config.get("job_name")
                odb_path = os.path.join(folder_path, f"{job_name}.odb")

                if os.path.exists(odb_path):

                    logger.info(f"ODB file created: {odb_path}")

                    # ----------------------------------------------------
                    # Execute protocol python script (if specified)
                    # ----------------------------------------------------
                    python_script = config.get("python_script")

                    if python_script:

                        project_root = os.path.dirname(folder_path)
                        script_path = os.path.join(project_root, python_script)

                        if os.path.isfile(script_path):

                            speed_var = config.get("speed_var", "Vel")

                            python_cmd = [
                                config.get("abaqus_exe", self.default_exe),
                                "python",
                                script_path,
                                odb_path,
                                speed_var
                            ]

                            logger.info(
                                f"Running post-processing: {' '.join(python_cmd)}"
                            )

                            try:

                                post = subprocess.run(
                                    python_cmd,
                                    cwd=folder_path,
                                    capture_output=True,
                                    text=True,
                                    check=True
                                )

                                logger.info(
                                    "Post-processing completed successfully."
                                )

                                if post.stdout:
                                    logger.info(post.stdout)

                                if post.stderr:
                                    logger.warning(post.stderr)

                            except subprocess.CalledProcessError as e:

                                logger.exception(
                                    "Post-processing script failed."
                                )

                                logger.error(e.stdout)

                                logger.error(e.stderr)

                        else:

                            logger.warning(
                                f"Python script not found: {script_path}"
                            )

                else:
                    logger.warning(f"ODB file not found after job completion: {odb_path}")
            
            return {
                'success': exit_code == 0,
                'exit_code': exit_code,
                'stdout': stdout or "",
                'stderr': stderr or "",
                'job_name': config.get('job_name'),
                'folder': folder_path,
            }
            
        except Exception as e:
            logger.error(f"Error running Abaqus job: {e}")
            process.kill()
            process.wait()
            return {
                'success': False,
                'exit_code': -1,
                'error': str(e),
                'job_name': config.get('job_name'),
                'folder': folder_path,
            }
        finally:
            # Remove process from tracking
            if process.pid in _running_processes:
                del _running_processes[process.pid]
    
    def stop_all(self) -> Dict[str, Any]:
        """Stop all running Abaqus processes"""
        result = {'requested': 0, 'killed': [], 'errors': []}
        
        for pid, process in list(_running_processes.items()):
            result['requested'] += 1
            try:
                # Try graceful termination first
                process.terminate()
                # Wait a moment for graceful termination
                import time
                time.sleep(0.5)
                
                # Force kill if still running
                if process.poll() is None:
                    process.kill()
                
                result['killed'].append(pid)
                logger.info(f"Killed Abaqus process {pid}")
            except Exception as e:
                result['errors'].append(str(e))
                logger.error(f"Error killing process {pid}: {e}")
        
        return result
    
    def get_running_jobs(self) -> List[int]:
        """Get PIDs of running Abaqus jobs"""
        return list(_running_processes.keys())