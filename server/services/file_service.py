import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

from config import config

logger = logging.getLogger(__name__)

class FileService:
    """Service for file operations and folder management"""
    
    def __init__(self):
        self.projects_dir = config.PROJECTS_DIR
        self.templates_dir = config.TEMPLATES_DIR
        self.protocol_dir = config.PROTOCOL_DIR
        
        # Ensure directories exist
        os.makedirs(self.projects_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.protocol_dir, exist_ok=True)
    
    def get_project_folder_path(self, project_name: str, protocol: str, folder_name: str) -> str:
        """Get the full path to a project folder"""
        combined_name = f"{project_name}_{protocol}"
        return os.path.join(self.projects_dir, combined_name, folder_name)
    
    def get_odb_path(self, project_name: str, protocol: str, folder_name: str, job_name: str) -> str:
        """Get the ODB file path"""
        folder_path = self.get_project_folder_path(project_name, protocol, folder_name)
        return os.path.join(folder_path, f"{job_name}.odb")
    
    def check_odb_file(self, project_name: str, protocol: str, folder_name: str, job_name: str) -> Tuple[bool, str]:
        """Check if ODB file exists"""
        odb_path = self.get_odb_path(project_name, protocol, folder_name, job_name)
        exists = os.path.exists(odb_path)
        return exists, odb_path
    
    def check_tydex_file(self, project_name: str, protocol: str, folder_name: str, tydex_name: str) -> Tuple[bool, str]:
        """Check if Tydex file exists"""
        folder_path = self.get_project_folder_path(project_name, protocol, folder_name)
        
        # Ensure .tdx extension
        if not tydex_name.endswith('.tdx'):
            tydex_name += '.tdx'
        
        tydex_path = os.path.join(folder_path, tydex_name)
        exists = os.path.exists(tydex_path)
        return exists, tydex_path
    
    def create_protocol_folders(self, project_name: str, protocol: str) -> Dict[str, Any]:
        """
        Create protocol folder structure from templates.
        Copies template subfolders (P1_L1, P1_L2, etc.) to the project folder.
        """
        # Protocol name mapping
        protocol_map = {
            'MF62': 'MF6pt2',
            'MF52': 'MF5pt2',
            'FTire': 'FTire',
            'CDTire': 'CDTire',
            'Custom': 'Custom'
        }
        
        template_protocol = protocol_map.get(protocol, protocol)
        template_path = os.path.join(self.templates_dir, template_protocol)
        
        if not os.path.exists(template_path):
            logger.warning(f"Template folder not found: {template_path}")
            # Create the template folder structure
            os.makedirs(template_path, exist_ok=True)
            # Create a sample subfolder
            sample_folder = os.path.join(template_path, "P1_L1")
            os.makedirs(sample_folder, exist_ok=True)
            # Create a sample parameters.inc
            sample_inc = os.path.join(sample_folder, "parameters.inc")
            if not os.path.exists(sample_inc):
                with open(sample_inc, 'w') as f:
                    f.write("! Parameters file\n")
        
        # Create project folder
        combined_name = f"{project_name}_{protocol}"
        project_path = os.path.join(self.projects_dir, combined_name)
        os.makedirs(project_path, exist_ok=True)
        
        # Copy subfolders if template exists
        subfolders = []
        if os.path.exists(template_path):
            for item in os.listdir(template_path):
                item_path = os.path.join(template_path, item)
                if os.path.isdir(item_path):
                    dest_path = os.path.join(project_path, item)
                    if os.path.exists(dest_path):
                        shutil.rmtree(dest_path)
                    shutil.copytree(item_path, dest_path)
                    subfolders.append(item)
        
        # Copy parameters.inc if available
        parameters_path = os.path.join(self.templates_dir, 'inc', 'parameters.inc')
        if os.path.exists(parameters_path):
            for subfolder in subfolders:
                dest = os.path.join(project_path, subfolder, 'parameters.inc')
                if not os.path.exists(dest):
                    shutil.copy2(parameters_path, dest)
        
        return {
            'success': True,
            'message': 'Protocol folders created successfully',
            'foldersCreated': subfolders,
            'projectPath': combined_name
        }
    
    def generate_parameters(self, data: Dict[str, Any], referer: str) -> Dict[str, Any]:
        """
        Generate parameters.inc file from template.
        
        Args:
            data: Dictionary of parameter values
            referer: HTTP referer to determine which protocol template to use
        """
        # Determine template based on referer
        template_name = 'MF6pt2'  # Default
        if 'mf52' in referer:
            template_name = 'MF5pt2'
        elif 'ftire' in referer:
            template_name = 'FTire'
        elif 'cdtire' in referer:
            template_name = 'CDTire'
        elif 'custom' in referer:
            template_name = 'Custom'
        
        template_path = os.path.join(self.templates_dir, template_name, 'parameters_template.inc')
        if not os.path.exists(template_path):
            # Try the central templates/inc directory
            template_path = os.path.join(self.templates_dir, 'inc', 'parameters_template.inc')
            if not os.path.exists(template_path):
                # Create a default template
                os.makedirs(os.path.dirname(template_path), exist_ok=True)
                default_content = """! ============================================================
!  Parameters Template
!  Apollo Tyres R&D
! ============================================================

! Load settings
load1_kg=0.0
load2_kg=0.0
load3_kg=0.0
load4_kg=0.0
load5_kg=0.0

! Pressure settings
pressure1=0.0
pressure2=0.0
pressure3=0.0

! Speed settings
speed_kmph=0.0

! Angle settings
IA=0.0
SA=0.0
SR=0.0

! Rim settings
width=0.0
diameter=0.0
Outer_diameter=0.0
nomwidth=0.0
aspratio=0.0
"""
                with open(template_path, 'w') as f:
                    f.write(default_content)
        
        # Read template
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Replace parameters
        replacements = {
            'load1_kg': data.get('load1_kg'),
            'load2_kg': data.get('load2_kg'),
            'load3_kg': data.get('load3_kg'),
            'load4_kg': data.get('load4_kg'),
            'load5_kg': data.get('load5_kg'),
            'pressure1': data.get('pressure1'),
            'pressure2': data.get('pressure2'),
            'pressure3': data.get('pressure3'),
            'speed_kmph': data.get('speed_kmph'),
            'IA': data.get('IA'),
            'SA': data.get('SA'),
            'SR': data.get('SR'),
            'width': data.get('width'),
            'diameter': data.get('diameter'),
            'Outer_diameter': data.get('Outer_diameter'),
            'nomwidth': data.get('nomwidth'),
            'aspratio': data.get('aspratio'),
        }
        
        import re
        for key, value in replacements.items():
            if value is not None and str(value).strip():
                # Replace the parameter line
                param_name = key
                # Handle different parameter names
                if key == 'pressure1' and data.get('pressure1'):
                    # Also replace P1 if it exists as a separate parameter
                    pass
                pattern = rf'^{re.escape(param_name)}\s*=.*$'
                replacement = f"{param_name}={value}"
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        # Write parameters file
        output_path = os.path.join(self.templates_dir, 'inc', 'parameters.inc')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(content)
        
        return {
            'success': True,
            'message': 'Parameter file generated successfully'
        }