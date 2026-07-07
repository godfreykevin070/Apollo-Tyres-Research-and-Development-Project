import subprocess
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

SERVER_DIR = PROJECT_ROOT / "server"
FRONTEND_DIR = PROJECT_ROOT / "Apollo-Tyres-Simulation-Software"

VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
NPM = shutil.which("npm.cmd") or shutil.which("npm")

def start_backend():
    subprocess.Popen(
        [str(VENV_PYTHON), "-m", "uvicorn", "main:app", "--reload"],
        cwd=SERVER_DIR,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

def start_frontend():
    subprocess.Popen(
        [NPM, "run", "dev"],
        cwd=FRONTEND_DIR,
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )

if __name__ == "__main__":
    start_backend()
    start_frontend()