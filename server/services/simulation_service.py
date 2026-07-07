import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import json

from database import db
from services.abaqus import AbaqusService
from services.dependency_resolver import DependencyResolver
from services.file_service import FileService

logger = logging.getLogger(__name__)

class SimulationService:
    """High-level service for managing simulations"""
    
    def __init__(self):
        self.abaqus = AbaqusService()
        self.resolver = DependencyResolver()
        self.file_service = FileService()
        self._running_jobs: Dict[str, asyncio.Task] = {}
    
    async def run_simulation(self, project_name: str, protocol: str, run_number: int) -> Dict[str, Any]:
        """
        Run a complete simulation for a given run number
        
        Args:
            project_name: Name of the project
            protocol: Protocol name (MF62, MF52, etc.)
            run_number: Run number to execute
        
        Returns:
            Dict with success status and results
        """
        return await self.resolver.resolve_and_run(project_name, protocol, run_number)
    
    async def run_multiple_simulations(self, project_name: str, protocol: str, 
                                        run_numbers: List[int]) -> Dict[str, Any]:
        """
        Run multiple simulations sequentially
        
        Args:
            project_name: Name of the project
            protocol: Protocol name
            run_numbers: List of run numbers to execute
        
        Returns:
            Dict with results for each run
        """
        results = {}
        for run_number in run_numbers:
            try:
                result = await self.run_simulation(project_name, protocol, run_number)
                results[str(run_number)] = result
            except Exception as e:
                results[str(run_number)] = {'success': False, 'error': str(e)}
        
        return {
            'success': all(r.get('success', False) for r in results.values()),
            'results': results
        }
    
    def stop_all_simulations(self) -> Dict[str, Any]:
        """Stop all running simulations"""
        return self.abaqus.stop_all()
    
    async def get_simulation_status(self, project_name: str, protocol: str, run_number: int) -> Dict[str, Any]:
        """
        Get the status of a simulation
        
        Returns:
            Dict with status information
        """
        # Get row data
        table_map = {
            'mf62': 'mf62_project_data',
            'mf52': 'mf52_project_data',
            'ftire': 'ftire_project_data',
            'cdtire': 'cdtire_project_data',
            'custom': 'custom_project_data'
        }
        table_name = table_map.get(protocol.lower())
        
        if not table_name:
            return {'success': False, 'error': 'Invalid protocol'}
        
        row = await db.execute_one(
            f"SELECT p, l, job, old_job FROM {table_name} WHERE number_of_runs = $1",
            run_number
        )
        
        if not row:
            return {'success': False, 'error': 'Row not found'}
        
        row = dict(row)
        folder_name = f"{row['p']}_{row['l']}"
        job_name = row['job']
        
        # Check ODB file
        exists, path = self.file_service.check_odb_file(
            project_name, protocol, folder_name, job_name
        )
        
        return {
            'success': True,
            'status': 'completed' if exists else 'pending',
            'odb_exists': exists,
            'odb_path': path if exists else None,
            'folder': folder_name,
            'job': job_name
        }
    
    async def get_project_status(self, project_name: str, protocol: str) -> Dict[str, Any]:
        """
        Get status of all runs in a project
        """
        table_map = {
            'mf62': 'mf62_project_data',
            'mf52': 'mf52_project_data',
            'ftire': 'ftire_project_data',
            'cdtire': 'cdtire_project_data',
            'custom': 'custom_project_data'
        }
        table_name = table_map.get(protocol.lower())
        
        if not table_name:
            return {'success': False, 'error': 'Invalid protocol'}
        
        rows = await db.execute(f"SELECT number_of_runs, p, l, job FROM {table_name}")
        
        statuses = {}
        for row in rows:
            row = dict(row)
            run_number = row['number_of_runs']
            folder_name = f"{row['p']}_{row['l']}"
            job_name = row['job']
            
            exists, _ = self.file_service.check_odb_file(
                project_name, protocol, folder_name, job_name
            )
            statuses[run_number] = 'completed' if exists else 'pending'
        
        return {
            'success': True,
            'statuses': statuses
        }