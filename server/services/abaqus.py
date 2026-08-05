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
        self.default_cpus = int(os.getenv('ABQ_CPUS', 1))
        print("\n", self.default_cpus, "\n")
        self.default_ask_del = os.getenv('ABQ_ASK_DEL', 'no')
    
    def _build_command(self, config: Dict[str, Any]) -> List[str]:
        """
        Build Abaqus command based on configuration.
        
        Supports three patterns:
        1. No old job: abaqus job=JOB_NAME input=INPUT_FILE cpus=N ask_del=no int
        2. Has old job: abaqus job=JOB_NAME oldjob=OLD_JOB cpus=N ask_del=no int
        3. Has user subroutine: abq2024hf5f job=JOB_NAME oldjob=OLD_JOB user=USER_FILE.f cpus=N int
        """
        print("\n", config, "\n")
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
        print("\n", cmd, "\n")
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
        folder_path = config.get("folder_path")

        if not folder_path:
            raise ValueError("Folder path missing")

        cmd = self._build_command(config)

        logger.info(
            f"Running command in {folder_path}: {' '.join(cmd)}"
        )

        try:

            process = subprocess.Popen(
                cmd,
                cwd=folder_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )

            logger.info(
                f"Abaqus started successfully PID={process.pid}"
            )

            return_code = await asyncio.to_thread(process.wait)

            logger.info(
                f"Abaqus finished PID={process.pid} ExitCode={return_code}"
            )

            if return_code != 0:
                return {
                    "success": False,
                    "error": f"Abaqus exited with code {return_code}",
                    "job_name": config.get("job_name")
                }

            return {
                "success": True,
                "status": "completed",
                "job_name": config.get("job_name")
            }

        except Exception as e:

            logger.exception(
                "Failed to start Abaqus"
            )

            return {
                "success": False,
                "error": str(e),
                "job_name": config.get("job_name")
            }
    
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