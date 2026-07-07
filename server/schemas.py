from typing import Optional, Dict, Any, List
from pydantic import BaseModel

# Auth schemas
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: str
    user: Dict[str, Any]
    message: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# Project schemas
class ProjectResponse(BaseModel):
    success: bool
    project: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class ProjectsResponse(BaseModel):
    success: bool
    projects: List[Dict[str, Any]]

# Simulation schemas
class ResolveDependenciesRequest(BaseModel):
    projectName: str
    protocol: str
    runNumber: int

class ResolveDependenciesResponse(BaseModel):
    success: bool
    message: str
    job: Optional[str] = None

class RecordRunTimeRequest(BaseModel):
    projectId: Optional[int] = None
    projectName: Optional[str] = None
    protocol: str
    runNumber: int
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    durationSeconds: Optional[int] = None

# Tydex schemas
class GenerateTydexRequest(BaseModel):
    protocol: str
    projectName: str
    rowData: Dict[str, Any]

class OpenTydexRequest(BaseModel):
    protocol: str
    projectName: str
    p: str
    l: str
    tydex_name: str

# Activity schemas
class ActivityLogRequest(BaseModel):
    activity_type: str
    action: str
    description: str
    status: str = 'success'
    related_entity_id: Optional[int] = None
    related_entity_type: Optional[str] = None
    project_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None