from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import create_user, authenticate_user, verify_refresh_token
from app.utils.security import create_access_token, create_refresh_token
from app.utils.exceptions import UnauthorizedError
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    user = await create_user(db, user_data)
    return user


class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    login_data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise UnauthorizedError("Invalid email or password")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
        },
    }


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh_token(
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token:
        raise UnauthorizedError("Refresh token not provided")
    
    user_id = await verify_refresh_token(refresh_token)
    if not user_id:
        raise UnauthorizedError("Invalid or expired refresh token")
    
    access_token = create_access_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    response.delete_cookie(key="refresh_token", httponly=True, samesite="lax")
    return None


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    from app.dependencies import get_current_user
    
    user = await get_current_user(
        authorization=f"{credentials.scheme} {credentials.credentials}",
        db=db,
    )
    return user

