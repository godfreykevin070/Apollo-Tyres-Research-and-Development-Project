import os
import re
import shutil
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from database import db
from datetime import datetime

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
        template_path = os.path.join(
            os.path.dirname(self.templates_dir),
            "templates",
            template_protocol
        )
        
        if not os.path.exists(template_path):
            logger.warning(f"Template folder not found: {template_path}")
            raise FileNotFoundError(f"Template folder not found: {template_path}")
        
        # Create project folder
        combined_name = f"{project_name}_{protocol}"
        project_path = os.path.join(self.projects_dir, combined_name)
        os.makedirs(project_path, exist_ok=True)
        
        # Copy everything (both files and folders)
        subfolders = []

        if os.path.exists(template_path):
            for item in os.listdir(template_path):

                src = os.path.join(template_path, item)
                dst = os.path.join(project_path, item)

                if os.path.isdir(src):
                    # Replace existing directory
                    if os.path.exists(dst):
                        shutil.rmtree(dst)

                    shutil.copytree(src, dst)
                    subfolders.append(item)

                elif os.path.isfile(src):
                    # Replace existing file
                    shutil.copy2(src, dst)

                logger.info(f"Copied: {src} -> {dst}")
        
        return {
            'success': True,
            'message': 'Protocol folders created successfully',
            'foldersCreated': subfolders,
            'projectPath': combined_name
        }
    
    def generate_parameters(
        self,
        data: Dict[str, Any],
        referer: str,
        project: str
    ) -> Dict[str, Any]:
        """
        Generate parameters.inc from the protocol template and save it
        in the project root.
        """

        protocol_templates = {
            "MF52": "mf52.inc",
            "MF62": "mf62.inc",
            "FTire": "ftire.inc",
            "CDTire": "cdtire.inc",
            "Custom": "custom.inc",
        }

        protocol = data["protocol"]
        project_name = project["project_name"]

        if protocol not in protocol_templates:
            raise ValueError(f"Unsupported protocol: {protocol}")

        # Template file
        template_path = os.path.join(
            self.templates_dir,
            "inc",
            protocol_templates[protocol]
        )

        if not os.path.exists(template_path):
            raise FileNotFoundError(
                f"Template not found: {template_path}"
            )
        print(f"Template Path: \n{template_path}\n")

        # Read template
        with open(template_path, "r") as f:
            content = f.read()

        replacements = {
            "Project name": project["project_name"],
            "tyre size": project["tyre_size"],
            "OE": "Apollo Tyres",
            "user": project["user_email"],
            "date": datetime.now().date(),

            "load1_kg": data.get("l1"),
            "load2_kg": data.get("l2"),
            "load3_kg": data.get("l3"),
            "load4_kg": data.get("l4"),
            "load5_kg": data.get("l5"),

            "pressure1": data.get("p1"),
            "pressure2": data.get("p2"),
            "pressure3": data.get("p3"),

            "speed_kmph": data.get("vel"),

            "IA": data.get("ia"),
            "SA": data.get("sa"),
            "SR": data.get("sr"),

            "width": data.get("rimWidth"),
            "diameter": data.get("rimDiameter"),
            "Outer_diameter": data.get("outerDiameter"),
            "nomwidth": data.get("nominalWidth"),
            "aspratio": data.get("aspectRatio"),
        }

        for key, value in replacements.items():

            if value is None or str(value).strip() == "":
                continue

            value = str(value)

            # Header fields use :
            if key in ["Project name", "tyre size", "OE", "user", "date"]:
                pattern = rf"^{re.escape(key)}\s*:.*$"
                replacement = f"{key}: {value}"

            # Parameter fields use =
            else:
                pattern = rf"^{re.escape(key)}\s*=.*$"
                replacement = f"{key}={value}"

            content = re.sub(
                pattern,
                replacement,
                content,
                flags=re.MULTILINE
            )

        # Project folder
        combined_name = f"{project_name}_{protocol}"

        project_path = os.path.join(
            self.projects_dir,
            combined_name
        )

        os.makedirs(project_path, exist_ok=True)

        # Save as parameters.inc
        output_path = os.path.join(
            project_path,
            "parameters.inc"
        )

        with open(output_path, "w") as f:
            f.write(content)

        logger.info(f"Generated parameter file: {output_path}")

        return {
            "success": True,
            "message": "Parameter file generated successfully",
            "path": output_path
        }
        
    def update_project_files(
        self,
        project_name: str,
        protocol: str,
    ):

        combined_name = f"{project_name}_{protocol}"

        project_path = os.path.join(
            self.projects_dir,
            combined_name
        )

        # create protocol folders automatically
        self.create_protocol_folders(project_name, protocol)

        for folder in os.listdir(project_path):

            folder_path = os.path.join(project_path, folder)

            if not os.path.isdir(folder_path):
                continue

        return {
            "success": True,
            "message": "Project files updated successfully."
        }
    
