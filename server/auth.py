from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from config import config
from database import db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(security)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token.credentials,
            config.JWT_SECRET,
            algorithms=[config.JWT_ALGORITHM]
        )
        email: str = payload.get("email")
        user_id: str = payload.get("userId")
        
        if email is None or user_id is None:
            raise credentials_exception
        
        # Get user from database
        user = await db.execute_one(
            "SELECT id, email, name, role, created_at, last_login FROM users WHERE id = $1 AND email = $2",
            user_id, email
        )
        
        if user is None:
            raise credentials_exception
            
        return dict(user)
        
    except JWTError:
        raise credentials_exception

async def get_current_active_user(current_user = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Invalid user")
    return current_user

async def get_current_manager(current_user = Depends(get_current_user)):
    if current_user.get('role') not in ['manager', 'admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access required"
        )
    return current_user