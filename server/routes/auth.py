from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional

from database import db
from auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, get_current_active_user
)
from config import config

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: str
    user: dict
    message: Optional[str] = None

@router.post("/login")
async def login(request: LoginRequest):
    """Authenticate user and return JWT token"""
    user = await db.execute_one(
        "SELECT id, email, name, role, password, created_at, last_login FROM users WHERE email = $1",
        request.email
    )
    
    if not user:
        raise HTTPException(401, "Invalid email or password")
    
    if not verify_password(request.password, user['password']):
        raise HTTPException(401, "Invalid email or password")
    
    # Update last_login
    await db.execute(
        "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = $1",
        user['id']
    )
    
    # Create token
    token_data = {
        "userId": user['id'],
        "email": user['email'],
        "role": user['role'],
        "name": user['name'],
    }
    token = create_access_token(token_data)
    
    return LoginResponse(
        success=True,
        token=token,
        user={
            "id": user['id'],
            "email": user['email'],
            "name": user['name'],
            "role": user['role'],
            "created_at": user['created_at'].isoformat() if user['created_at'] else None,
            "last_login": user['last_login'].isoformat() if user['last_login'] else None,
        }
    )

@router.post("/logout")
async def logout(current_user = Depends(get_current_user)):
    """Logout user (client side token removal)"""
    return {"success": True, "message": "Logged out"}

@router.get("/me")
async def get_me(current_user = Depends(get_current_user)):
    """Get current user info"""
    # Get project count
    project_count = await db.execute_val(
        "SELECT COUNT(*) FROM projects WHERE user_email = $1",
        current_user['email']
    ) or 0
    
    # Calculate account age
    account_age_days = 0
    if current_user.get('created_at'):
        diff = datetime.utcnow() - current_user['created_at']
        account_age_days = diff.days
    
    return {
        "success": True,
        "user": {
            "id": current_user['id'],
            "email": current_user['email'],
            "name": current_user['name'],
            "role": current_user['role'],
            "created_at": current_user['created_at'].isoformat() if current_user.get('created_at') else None,
            "last_login": current_user.get('last_login').isoformat() if current_user.get('last_login') else None,
            "project_count": project_count,
            "account_age_days": account_age_days,
        }
    }

@router.get("/verify")
async def verify_token(current_user = Depends(get_current_user)):
    """Verify JWT token validity"""
    return {"success": True}