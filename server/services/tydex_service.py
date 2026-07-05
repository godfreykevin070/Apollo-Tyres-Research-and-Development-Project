import os
import re
import math
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
    
    async def generate_tydex(
        self,
        protocol: str,
        project_name: str,
        row_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a Tydex file.

        Flow:
        1. Extract CSV data from ODB using Abaqus Python.
        2. Read the template Tydex file.
        3. Replace placeholders with extracted data.
        4. Save the generated Tydex file.
        """

        # ----------------------------
        # Template name
        # ----------------------------
        template_tydex = row_data.get("template_tydex", "").strip()

        if not template_tydex:
            return {
                "success": False,
                "message": "No template_tydex provided"
            }

        if not template_tydex.endswith(".tdx"):
            template_tydex += ".tdx"

        output_tydex = row_data.get("tydex_name", template_tydex)

        if not output_tydex.endswith(".tdx"):
            output_tydex += ".tdx"

        # ----------------------------
        # Project paths
        # ----------------------------
        project_folder = f"{project_name}_{protocol}"

        p = row_data.get("p", "")
        l = row_data.get("l", "")

        run_dir = os.path.join(
            self.projects_dir,
            project_folder,
            f"{p}_{l}"
        )

        csv_dir = os.path.join(run_dir, "csv_files")

        os.makedirs(csv_dir, exist_ok=True)

        # ----------------------------
        # ODB file
        # ----------------------------
        odb_name = row_data.get("job", "").replace(".inp", "")
        odb_path = os.path.join(run_dir, f"{odb_name}.odb")

        if not os.path.exists(odb_path):
            return {
                "success": False,
                "message": f"ODB file not found:\n{odb_path}"
            }

        # ----------------------------
        # Extraction script
        # ----------------------------
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "scripts",
            "extract_odb_data.py",
        )

        if not os.path.exists(script_path):
            return {
                "success": False,
                "message": f"Python script not found:\n{script_path}"
            }

        # ----------------------------
        # Run extraction
        # ----------------------------
        try:
            await asyncio.to_thread(
                self._run_extraction_script,
                script_path,
                odb_path,
                csv_dir,
            )
        except Exception as e:
            logger.exception("ODB extraction failed")
            return {
                "success": False,
                "message": str(e),
            }

        # Ensure extraction produced CSVs
        csv_files = [
            f for f in os.listdir(csv_dir)
            if f.lower().endswith(".csv")
        ]

        if not csv_files:
            return {
                "success": False,
                "message": "No CSV files were generated from the ODB."
            }

        logger.info("Generated %d CSV files", len(csv_files))

        # ----------------------------
        # Locate template
        # ----------------------------
        PROTOCOL_FOLDER = {
            "MF52": "MF5pt2",
            "MF62": "MF6pt2",
        }
        template_folder = PROTOCOL_FOLDER.get(protocol, protocol)

        template_path = os.path.join(
            self.templates_dir,
            "Tydex",
            template_folder,
            template_tydex,
        )

        if not os.path.exists(template_path):
            fallback = os.path.join(
                self.templates_dir,
                "Tydex",
                template_tydex,
            )

            if os.path.exists(fallback):
                template_path = fallback
            else:
                return {
                    "success": False,
                    "message": f"Template not found: {template_tydex}"
                }

        # ----------------------------
        # Read template
        # ----------------------------
        with open(template_path, "r") as f:
            template_content = f.read()

        # ----------------------------
        # Process template
        # ----------------------------
        processed_content = self._process_template(
            template_content,
            csv_dir,
            row_data,
        )

        # ----------------------------
        # Save output
        # ----------------------------
        # Create Tydex folder
        tydex_dir = os.path.join(run_dir, "tydex")
        os.makedirs(tydex_dir, exist_ok=True)

        # Save the file inside it
        output_path = os.path.join(tydex_dir, output_tydex)

        with open(output_path, "w") as f:
            f.write(processed_content)

        logger.info("Generated Tydex file: %s", output_path)

        return {
            "success": True,
            "message": "Tydex file generated successfully",
            "output_file": output_path,
        }

    def _run_extraction_script(self, script_path, odb_path, output_dir):
        cmd = [
            "abaqus",
            "python",
            script_path,
            odb_path,
            output_dir,
        ]

        logger.info(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(script_path),
            capture_output=True,
            text=True,
            shell=True
        )

        logger.info(f"Return code: {result.returncode}")
        logger.info(f"STDOUT:\n{result.stdout}")
        logger.info(f"STDERR:\n{result.stderr}")

        if result.returncode != 0:
            raise Exception(
                f"Return Code: {result.returncode}\n\n"
                f"STDOUT:\n{result.stdout}\n\n"
                f"STDERR:\n{result.stderr}"
            )
    
    # def _process_template(self, template_content: str, csv_dir: str, row_data: Dict[str, Any]) -> str:
    #     """Process the template with CSV data and row data"""
        
    #     lines = template_content.split('\n')
    #     processed_lines = []
        
    #     # Get parameters from row_data
    #     p = row_data.get('p', '')
    #     l = row_data.get('l', '')
    #     job = row_data.get('job', '')
    #     tydex_name = row_data.get('tydex_name', '')
        
    #     # Simple replacements (full implementation would be more complex)
    #     for line in lines:
    #         if line.strip().startswith('INCLANGL'):
    #             # Replace inclination angle
    #             if row_data.get('inclination_angle'):
    #                 angle = float(row_data['inclination_angle']) * 3.14159 / 180
    #                 line = re.sub(r'=\s*[\d.]+', f'= {angle:.6f}', line)
            
    #         if line.strip().startswith('LONGSLIP'):
    #             if row_data.get('slip_ratio'):
    #                 slip = float(row_data['slip_ratio']) / 100
    #                 line = re.sub(r'=\s*[\d.]+', f'= {slip:.6f}', line)
            
    #         if line.strip().startswith('SLIPANGL'):
    #             if row_data.get('slip_angle'):
    #                 angle = float(row_data['slip_angle']) * 3.14159 / 180
    #                 line = re.sub(r'=\s*[\d.]+', f'= {angle:.6f}', line)
            
    #         processed_lines.append(line)
        
    #     return '\n'.join(processed_lines)

    def _process_template(
        self,
        template_content: str,
        csv_dir: str,
        row_data: Dict[str, Any]
    ) -> str:
        def resolve_value(value, input_value):
            """
            Resolve database value.

            Examples:
                "2"      -> 2.0
                "-3"     -> -3.0
                "IA"     -> input_value
                "-IA"    -> -input_value
                "SA"     -> input_value
                "-SA"    -> -input_value
            """
            if value is None:
                return None

            value = str(value).strip()

            # Direct number
            try:
                return float(value)
            except ValueError:
                pass

            variable = value.upper()

            if variable.startswith("-"):
                sign = -1
                variable = variable[1:]
            else:
                sign = 1

            if input_value is None or str(input_value).strip() == "":
                return None

            return sign * float(input_value)

        # -----------------------
        # Resolve all parameters
        # -----------------------

        ia = resolve_value(
            row_data.get("inclination_angle"),
            row_data.get("IA")
        )

        sa = resolve_value(
            row_data.get("slip_angle"),
            row_data.get("SA")
        )

        sr = resolve_value(
            row_data.get("slip_ratio"),
            row_data.get("SR")
        )

        vel = resolve_value(
            row_data.get("test_velocity"),
            row_data.get("speed_kmph")
        )

        processed_lines = []

        for line in template_content.splitlines():

            stripped = line.strip()

            # -------------------------
            # Camber
            # -------------------------

            if stripped.startswith("INCLANGL") and ia is not None:
                line = re.sub(
                    r"=\s*.*$",
                    f"= {math.radians(ia):.6f}",
                    line
                )

            # -------------------------
            # Slip Angle
            # -------------------------

            elif stripped.startswith("SLIPANGL") and sa is not None:
                line = re.sub(
                    r"=\s*.*$",
                    f"= {math.radians(sa):.6f}",
                    line
                )

            # -------------------------
            # Slip Ratio
            # -------------------------

            elif stripped.startswith("LONGSLIP") and sr is not None:
                line = re.sub(
                    r"=\s*.*$",
                    f"= {sr/100:.6f}",
                    line
                )

            # -------------------------
            # Velocity
            # -------------------------

            elif stripped.startswith("TESTVEL") and vel is not None:
                line = re.sub(
                    r"=\s*.*$",
                    f"= {vel:.6f}",
                    line
                )

            processed_lines.append(line)

        return "\n".join(processed_lines)