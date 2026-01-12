import logging
logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.auth import hash_password, verify_password, create_token, get_current_user
from pydantic import BaseModel, Field, EmailStr

router = APIRouter(prefix='/auth')
security = HTTPBearer()

class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., example='user1@apitest.com')
    password: str = Field(..., min_length=4, example='password123')
    

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., example='user1@apitest.com')
    password: str = Field(..., example='password123')
    

@router.post('/register')
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail='user already registered to email address')
    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {'id': user.id, 'email': user.email, 'is_admin': user.is_admin}


@router.post('/login')
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='invalid credentials')
    token = create_token(user.id)
    return {'access_token': token, 'token_type': 'bearer'}

@router.get('/me')
def me(current_user: User = Depends(get_current_user), credentials: HTTPBearer = Depends(security)):
    '''Created for testing purposes of token validity.
    If token is valid, returns information of the current user.
    '''
    return {'id': current_user.id, 'email': current_user.email, 'is_admin': current_user.is_admin}

# Unused endpoint
# @router.get('/test_admin_access')
# def test_admin_access(current_user: User = Depends(get_current_user)):
#     '''Endpoint to test admin access.
#     Raises 403 if the current user is not an admin.
#     '''
#     if not current_user.is_admin:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='admin access required')
#     return {'detail': 'admin access granted'}
