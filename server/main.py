from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import logging
import datetime
from contextlib import asynccontextmanager

from config import config
from database import db
from routes import auth, projects, simulation, activity, tydex, manager, excel, compat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up Apollo Tyres Simulation Server...")
    await db.connect()
    logger.info("Database connection established")
    yield
    # Shutdown
    logger.info("Shutting down...")
    await db.close()
    logger.info("Database connection closed")

app = FastAPI(
    title="Apollo Tyres Simulation API",
    description="Backend API for Apollo Tyres Tyre Virtualization Tool",
    version="2.0.0",
    lifespan=lifespan
)

origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host middleware (for security)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure as needed for production
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(simulation.router, prefix="/api", tags=["Simulation"])  # Mount at /api for client compatibility
app.include_router(activity.router, prefix="/api", tags=["Activity"])  # Mount at /api
app.include_router(tydex.router, prefix="/api/tydex", tags=["Tydex"])
app.include_router(manager.router, prefix="/api/manager", tags=["Manager"])
app.include_router(excel.router, prefix="/api", tags=["Excel"])  # Include Excel router at /api

# Include compatibility router for legacy endpoints
app.include_router(compat.router, prefix="/api", tags=["Compatibility"])

@app.get("/")
async def root():
    return {
        "message": "Apollo Tyres Simulation API",
        "version": "2.0.0",
        "status": "running"
    }

@app.get("/api/ping")
async def ping():
    return {"ok": True, "ts": datetime.datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)