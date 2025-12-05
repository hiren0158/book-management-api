from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_session
from src.service.user import UserService
from src.schema.user import UserCreate, UserUpdate, UserRead
from src.model.user import User
from src.api.dependencies import get_current_user, require_roles

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserRead])
async def list_users(
    limit: int = Query(10, ge=1, le=100),
    cursor: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("Admin", "Librarian"))
):
    user_service = UserService(session)
    users, next_cursor = await user_service.list_users(limit=limit, cursor=cursor)
    
    return users


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if user_id != current_user.id and current_user.role.name not in ["Admin", "Librarian"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied"
        )
    
    user_service = UserService(session)
    user = await user_service.get_user(user_id)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return user


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("Librarian", "Admin"))
):
    from src.service.auth import AuthService
    
    auth_service = AuthService(session)
    
    try:
        result = await auth_service.register(user_data)
        user_service = UserService(session)
        user = await user_service.get_user(result["id"])
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    user_service = UserService(session)

    try:
        user = await user_service.update_user(user_id, user_data, current_user)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("Admin"))
):
    user_service = UserService(session)
    
    success = await user_service.delete_user(user_id, current_user)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
