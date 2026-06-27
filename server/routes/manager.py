from fastapi import APIRouter, HTTPException, Depends, Request
from passlib.context import CryptContext

from database import db
from auth import get_current_manager, get_password_hash

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get("/users")
async def get_users(manager=Depends(get_current_manager)):
    """Get all users (engineers) for manager"""
    rows = await db.execute(
        """
        SELECT u.id, u.name, u.email, u.role, u.created_at, u.last_login,
               COALESCE(p.project_count, 0) AS project_count
        FROM users u
        LEFT JOIN (
            SELECT user_email, COUNT(*) AS project_count
            FROM projects
            GROUP BY user_email
        ) p ON p.user_email = u.email
        WHERE u.role = 'engineer'
        ORDER BY u.created_at DESC
        """
    )
    return {"success": True, "users": [dict(row) for row in rows]}

@router.post("/add-user")
async def add_user(request: Request, manager=Depends(get_current_manager)):
    """Add a new engineer"""
    data = await request.json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'engineer')
    
    if not all([name, email, password]):
        raise HTTPException(400, "Name, email, and password required")
    
    if len(password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    
    # Check if email exists
    existing = await db.execute_one("SELECT id FROM users WHERE email = $1", email)
    if existing:
        raise HTTPException(409, "Email already exists")
    
    # Generate user ID
    import random
    import string
    def generate_user_id():
        letters = ''.join(random.choices(string.ascii_uppercase, k=3))
        numbers = ''.join(random.choices(string.digits, k=3))
        return f"USR-{letters}{numbers}"
    
    user_id = generate_user_id()
    # Ensure uniqueness
    while await db.execute_one("SELECT id FROM users WHERE id = $1", user_id):
        user_id = generate_user_id()
    
    hashed = pwd_context.hash(password)
    
    result = await db.execute_one(
        """
        INSERT INTO users (id, name, email, password, role, created_at)
        VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
        RETURNING id, name, email, role
        """,
        user_id, name, email, hashed, role
    )
    
    return {"success": True, "user": dict(result)}

@router.post("/reset-password")
async def reset_password(request: Request, manager=Depends(get_current_manager)):
    """Reset an engineer's password"""
    data = await request.json()
    engineer_email = data.get('engineerEmail')
    new_password = data.get('newPassword')
    
    if not engineer_email or not new_password:
        raise HTTPException(400, "Engineer email and new password required")
    
    if len(new_password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    
    # Check user exists and is engineer
    user = await db.execute_one(
        "SELECT id, role FROM users WHERE email = $1",
        engineer_email
    )
    if not user:
        raise HTTPException(404, "User not found")
    if user['role'] != 'engineer':
        raise HTTPException(403, "Can only reset passwords for engineers")
    
    hashed = pwd_context.hash(new_password)
    await db.execute(
        "UPDATE users SET password = $1, updated_at = CURRENT_TIMESTAMP WHERE email = $2",
        hashed, engineer_email
    )
    
    return {"success": True, "message": "Password reset successfully", "user": {"email": engineer_email}}