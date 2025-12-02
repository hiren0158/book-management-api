from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_session
from src.service.auth import AuthService
from src.schema.user import UserCreate
from src.schema.auth import Token
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    auth_service = AuthService(session)
    
    try:
        user = await auth_service.register(user_data)
        return {"message": "User registered successfully", "user": user}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"Internal error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during registration"
        )


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    session: AsyncSession = Depends(get_session)
):
    auth_service = AuthService(session)
    
    try:
        token = await auth_service.login(login_data.email, login_data.password)
        return token
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshRequest,
    session: AsyncSession = Depends(get_session)
):
    auth_service = AuthService(session)
    
    try:
        token = await auth_service.refresh_token(refresh_data.refresh_token)
        return token
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
