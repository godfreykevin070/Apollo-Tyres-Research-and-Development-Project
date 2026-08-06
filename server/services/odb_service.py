import os
import subprocess
import tempfile
import logging
import time

logger = logging.getLogger(__name__)

class ODBService:
    """
    Service to extract ODB information using Abaqus Python.
    FastAPI cannot directly import odbAccess.
    """

    def __init__(self):
        self.abaqus_exe = os.getenv(
            "ABQ_EXE",
            "abaqus"
        )
        self.test_counter = 0


    def read_odb_content(self, odb_path: str):
        max_attempts = 60
        wait_time = 10

        for attempt in range(max_attempts):

            script = f'''from odbAccess import openOdb
odb = openOdb(r"{odb_path}")
status = str(odb.diagnosticData.jobStatus)
print(status)
odb.close()
'''

            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False
            ) as f:
                f.write(script)
                temp_script = f.name

            cmd = [
                self.abaqus_exe,
                "python",
                temp_script
            ]

            logger.info(
                f"ODB status check {attempt + 1}/{max_attempts}"
            )

            # ==========================================================
            # TESTING BLOCK (COMMENTED)
            #
            # Uncomment this block together with:
            #     self.test_counter = 0
            # in __init__().
            #
            # It simulates the ODB still being written for the first
            # three attempts, allowing you to verify retry logic.
            #
            # self.test_counter += 1
            
            # if self.test_counter < 4:
            #     logger.info(
            #         f"TEST: Simulating ODB still being written "
            #         f"(attempt {self.test_counter})"
            #     )
            #     if os.path.exists(temp_script):
            #         os.remove(temp_script)
            #     time.sleep(wait_time)
            #     continue
            # ==========================================================

            try:

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode != 0:

                    logger.error(result.stderr)

                    return {
                        "success": False,
                        "error": result.stderr
                    }

                status = result.stdout.strip()

                logger.info(
                    f"RAW ODB OUTPUT:\n{repr(status)}"
                )

                logger.info(
                    f"ODB Job Status: {status}"
                )

                if "JOB_STATUS_COMPLETED_SUCCESSFULLY" in status.upper():

                    logger.info(
                        "ODB completed successfully."
                    )

                    return {
                        "success": True,
                        "status": status
                    }

                elif "JOB_STATUS_ABORTED" in status.upper():

                    logger.error(
                        "ODB job aborted."
                    )

                    return {
                        "success": False,
                        "status": status
                    }

                else:

                    logger.info(
                        f"ODB still running. Waiting {wait_time}s..."
                    )

                    time.sleep(wait_time)

            except Exception as e:

                logger.error(str(e))

                return {
                    "success": False,
                    "status": str(e)
                }

            finally:

                if os.path.exists(temp_script):
                    os.remove(temp_script)

        logger.error("ODB validation timeout.")

        return {
            "success": False,
            "status": "ODB validation timeout"
        }

    def run_python_script(
        self,
        script_path: str,
        odb_path: str,
        working_dir: str
    ):
        cmd = [
            self.abaqus_exe,
            "python",
            script_path,
            odb_path
        ]

        logger.info(f"Running post-processing script: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:

                logger.error(
                    f"Python script failed ({result.returncode})"
                )

                logger.error(result.stderr)

                return {
                    "success": False,
                    "error": result.stderr or result.stdout
                }

            logger.info("Python script completed successfully.")

            return {
                "success": True,
                "output": result.stdout
            }

        except Exception as e:

            logger.exception("Python script execution failed.")

            return {
                "success": False,
                "error": str(e)
            }
        