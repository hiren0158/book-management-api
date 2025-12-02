from typing import Optional
from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.model.user import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_id(self, id: int) -> Optional[User]:
        statement = select(User).where(User.id == id).options(selectinload(User.role))
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email).options(selectinload(User.role))
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_active_users(self, limit: int = 10, cursor: Optional[str] = None):
        return await self.list(
            limit=limit,
            cursor=cursor,
            filters={"is_active": True}
        )
