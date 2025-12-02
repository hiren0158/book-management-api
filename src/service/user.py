from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.user import UserRepository
from src.model.user import User
from src.schema.user import UserUpdate


class UserService:
    ROLE_ADMIN = "Admin"
    ROLE_LIBRARIAN = "Librarian"
    ROLE_MEMBER = "Member"

    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)

    async def get_user(self, user_id: int) -> Optional[User]:
        return await self.user_repo.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        return await self.user_repo.get_by_email(email)

    async def list_users(self, limit: int = 10, cursor: Optional[str] = None):
        return await self.user_repo.list(limit=limit, cursor=cursor)

    async def update_user(
        self,
        user_id: int,
        user_data: UserUpdate,
        current_user: User
    ) -> User:
        if user_id != current_user.id and current_user.role.name != self.ROLE_ADMIN:
            raise ValueError("Permission denied")

        update_dict = user_data.model_dump(exclude_unset=True)
        
        if "password" in update_dict:
            from src.service.auth import pwd_context
            update_dict["hashed_password"] = pwd_context.hash(update_dict.pop("password"))

        user = await self.user_repo.update(user_id, update_dict)
        if not user:
            raise ValueError("User not found")

        return user

    async def delete_user(self, user_id: int, current_user: User) -> bool:
        if current_user.role.name != self.ROLE_ADMIN:
            raise ValueError("Only Admin can delete users")

        return await self.user_repo.delete(user_id)

    async def deactivate_user(self, user_id: int, current_user: User) -> User:
        if current_user.role.name != self.ROLE_ADMIN:
            raise ValueError("Only Admin can deactivate users")

        user = await self.user_repo.update(user_id, {"is_active": False})
        if not user:
            raise ValueError("User not found")

        return user

    def check_permission(self, user: User, required_role: str) -> bool:
        role_hierarchy = {
            self.ROLE_ADMIN: 3,
            self.ROLE_LIBRARIAN: 2,
            self.ROLE_MEMBER: 1
        }
        
        user_level = role_hierarchy.get(user.role.name, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
