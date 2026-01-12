import logging
logger = logging.getLogger(__name__)

import os
from datetime import datetime, timedelta
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.models import User
from app.database import get_db

# Config (keep simple)
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')
ACCESS_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))

# Minimal password hashing wrapper
pwd = CryptContext(schemes=['bcrypt'], deprecated='auto')


def hash_password(password: str) -> str:
    return pwd.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd.verify(plain, hashed)


def create_token(user_id: int, expires_minutes: Optional[int] = ACCESS_EXPIRE_MINUTES) -> str:
    expiry = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode = {'sub': str(user_id), 'exp': expiry}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    '''
    Retrieve the current user based on the JWT token in the Authorization header.
    Returns logged-in user or raises 401 if invalid or missing.

    Expects header: Authorization: Bearer <jwt>
    '''
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.warning('Missing or invalid authorisation header')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='missing or invalid authorisation header')
    token = auth_header.split(' ')[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get('sub'))
    except (JWTError, ValueError):
        logger.warning('Invalid token')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='invalid token')
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning('User not found for token')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='user not found')
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not getattr(current_user, 'is_admin', False):
        logger.warning('Admin privileges required')
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='admin privileges required')
    return current_user