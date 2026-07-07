from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr

# User models
class User(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: str
    created_at: datetime
    last_login: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = 'engineer'

# Project models
class Project(BaseModel):
    id: int
    project_name: str
    region: str
    department: str
    tyre_size: str
    protocol: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    user_email: str
    inputs: Optional[Dict[str, Any]] = None
    previous_status: Optional[str] = None

class ProjectCreate(BaseModel):
    project_name: str
    region: str
    department: str
    tyre_size: str
    protocol: str
    status: str = 'Not Started'
    inputs: Optional[Dict[str, Any]] = None

# Simulation models
class RowData(BaseModel):
    number_of_runs: int
    p: str
    l: str
    job: str
    old_job: Optional[str] = None
    template_tydex: Optional[str] = None
    tydex_name: Optional[str] = None
    slip_angle: Optional[str] = None
    slip_ratio: Optional[str] = None
    inclination_angle: Optional[str] = None
    foltran: Optional[str] = None
    python_script: Optional[str] = None

class AbaqusJobConfig(BaseModel):
    jobName: str
    inputFile: str
    oldJob: Optional[str] = None
    userSubroutine: Optional[str] = None
    cpus: int = 4
    askDel: bool = True
    abaqusExe: str = 'abaqus'
    folderPath: str
    runNumber: int

# Tydex models
class TydexFile(BaseModel):
    id: int
    project_id: int
    protocol: str
    filename: str
    content: Optional[str] = None
    created_at: datetime

class TydexFileCreate(BaseModel):
    protocol: str
    filename: str
    content: str

# Activity log models
class ActivityLog(BaseModel):
    id: int
    user_email: str
    user_name: Optional[str] = None
    activity_type: str
    action: str
    description: str
    status: str
    ip_address: Optional[str] = None
    browser: Optional[str] = None
    device_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    related_entity_type: Optional[str] = None
    project_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

class ActivityLogCreate(BaseModel):
    activity_type: str
    action: str
    description: str
    status: str = 'success'
    related_entity_id: Optional[int] = None
    related_entity_type: Optional[str] = None
    project_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None