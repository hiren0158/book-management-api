from typing import Optional
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.model.role import Role
from .base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    def __init__(self, session: AsyncSession):
        super().__init__(Role, session)

    async def get_by_id(self, id: int) -> Optional[Role]:
        statement = select(Role).where(Role.id == id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Role]:
        statement = select(Role).where(Role.name == name)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

