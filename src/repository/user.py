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

    async def list(self, limit: int = 10, cursor: Optional[str] = None, **kwargs):
        """Override base list to eager-load role relationship."""
        # Get the statement from the base class
        from sqlalchemy import select as sql_select
        
        # Start with User model and eager load the role
        statement = sql_select(User).options(selectinload(User.role))
        
        # Apply cursor-based pagination
        if cursor:
            cursor_data = self._decode_cursor(cursor)
            from datetime import datetime
            created_at = datetime.fromisoformat(cursor_data["created_at"])
            cursor_id = cursor_data["id"]
            
            from sqlalchemy import or_, and_
            statement = statement.where(
                or_(
                    User.created_at < created_at,
                    and_(
                        User.created_at == created_at,
                        User.id < cursor_id
                    )
                )
            )
        
        statement = statement.order_by(
            User.created_at.desc(),
            User.id.desc()
        ).limit(limit + 1)
        
        result = await self.session.execute(statement)
        items = list(result.scalars().all())
        
        next_cursor = None
        if len(items) > limit:
            items = items[:limit]
            last_item = items[-1]
            next_cursor = self._encode_cursor(last_item.created_at, last_item.id)
        
        return items, next_cursor

    async def get_active_users(self, limit: int = 10, cursor: Optional[str] = None):
        # Need to eagerly load relationships for proper serialization
        statement = select(User).where(User.is_active == True).options(selectinload(User.role))
        
        # Apply cursor-based pagination manually
        if cursor:
            from .base import BaseRepository
            cursor_data = BaseRepository._decode_cursor(self, cursor)
            from datetime import datetime
            created_at = datetime.fromisoformat(cursor_data["created_at"])
            cursor_id = cursor_data["id"]
            
            from sqlalchemy import or_, and_
            statement = statement.where(
                or_(
                    User.created_at < created_at,
                    and_(
                        User.created_at == created_at,
                        User.id < cursor_id
                    )
                )
            )
        
        statement = statement.order_by(
            User.created_at.desc(),
            User.id.desc()
        ).limit(limit + 1)
        
        result = await self.session.execute(statement)
        items = list(result.scalars().all())
        
        next_cursor = None
        if len(items) > limit:
            items = items[:limit]
            last_item = items[-1]
            from .base import BaseRepository
            next_cursor = BaseRepository._encode_cursor(self, last_item.created_at, last_item.id)
        
        return items, next_cursor

