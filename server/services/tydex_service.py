import os
import re
import asyncio
import subprocess
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from config import config
from services.file_service import FileService

logger = logging.getLogger(__name__)

class TydexService:
    """Service for generating Tydex files from ODB data"""
    
    def __init__(self):
        self.file_service = FileService()
        self.templates_dir = config.TEMPLATES_DIR
        self.projects_dir = config.PROJECTS_DIR
    
    async def generate_tydex(self, protocol: str, project_name: str, row_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate Tydex file using the Python extraction script.
        
        Flow:
        1. Run abaqus python extract_odb_data.py to extract CSV data from ODB
        2. Read template Tydex file
        3. Replace placeholders with extracted data and row data
        4. Write output Tydex file
        """
        template_tydex = row_data.get('template_tydex', '').strip()
        if not template_tydex:
            return {'success': False, 'message': 'No template_tydex provided'}
        
        # Ensure .tdx extension
        if not template_tydex.endswith('.tdx'):
            template_tydex += '.tdx'
        
        output_tydex = row_data.get('tydex_name', template_tydex)
        if not output_tydex.endswith('.tdx'):
            output_tydex += '.tdx'
        
        project_folder = f"{project_name}_{protocol}"
        p = row_data.get('p', '')
        l = row_data.get('l', '')
        folder_name = f"{p}_{l}"
        output_dir = os.path.join(self.projects_dir, project_folder, folder_name)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Step 1: Run Python script to extract ODB data
        odb_name = row_data.get('job', '').replace('.inp', '')
        odb_path = os.path.join(output_dir, f"{odb_name}.odb")
        
        if not os.path.exists(odb_path):
            return {'success': False, 'message': f'ODB file not found: {odb_path}'}
        
        script_path = os.path.join(os.path.dirname(config.PROJECTS_DIR), 'scripts', 'extract_odb_data.py')
        if not os.path.exists(script_path):
            return {'success': False, 'message': f'Python script not found: {script_path}'}
        
        # Run extraction
        temp_dir = os.path.join(output_dir, 'temp')
        try:
            await self._run_extraction_script(script_path, odb_path, output_dir)
        except Exception as e:
            return {'success': False, 'message': f'Extraction failed: {str(e)}'}
        
        # Step 2: Find template
        template_path = os.path.join(self.templates_dir, 'Tydex', protocol, template_tydex)
        if not os.path.exists(template_path):
            # Try fallback
            fallback = os.path.join(self.templates_dir, 'Tydex', template_tydex)
            if os.path.exists(fallback):
                template_path = fallback
            else:
                return {'success': False, 'message': f'Template not found: {template_tydex}'}
        
        # Step 3: Read template and generate Tydex
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        processed_content = self._process_template(template_content, temp_dir, row_data)
        
        # Step 4: Write output
        output_path = os.path.join(output_dir, output_tydex)
        with open(output_path, 'w') as f:
            f.write(processed_content)
        
        return {'success': True, 'message': 'Tydex file generated successfully'}
    
    async def _run_extraction_script(self, script_path: str, odb_path: str, output_dir: str):
        """Run the Python extraction script asynchronously"""
        cmd = ['abaqus', 'python', script_path, odb_path, output_dir]
        logger.info(f"Running extraction: {' '.join(cmd)}")
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=os.path.dirname(script_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8', errors='ignore')
            logger.error(f"Extraction failed: {error_msg}")
            raise Exception(f"Extraction script failed: {error_msg}")
    
    def _process_template(self, template_content: str, csv_dir: str, row_data: Dict[str, Any]) -> str:
        """Process the template with CSV data and row data"""
        # This is a simplified version; full implementation would read CSV files
        # and replace placeholders in the template.
        # For this example, we'll just replace some key values.
        
        lines = template_content.split('\n')
        processed_lines = []
        
        # Get parameters from row_data
        p = row_data.get('p', '')
        l = row_data.get('l', '')
        job = row_data.get('job', '')
        tydex_name = row_data.get('tydex_name', '')
        
        # Simple replacements (full implementation would be more complex)
        for line in lines:
            if line.strip().startswith('INCLANGL'):
                # Replace inclination angle
                if row_data.get('inclination_angle'):
                    angle = float(row_data['inclination_angle']) * 3.14159 / 180
                    line = re.sub(r'=\s*[\d.]+', f'= {angle:.6f}', line)
            
            if line.strip().startswith('LONGSLIP'):
                if row_data.get('slip_ratio'):
                    slip = float(row_data['slip_ratio']) / 100
                    line = re.sub(r'=\s*[\d.]+', f'= {slip:.6f}', line)
            
            if line.strip().startswith('SLIPANGL'):
                if row_data.get('slip_angle'):
                    angle = float(row_data['slip_angle']) * 3.14159 / 180
                    line = re.sub(r'=\s*[\d.]+', f'= {angle:.6f}', line)
            
            processed_lines.append(line)
        
        return '\n'.join(processed_lines)