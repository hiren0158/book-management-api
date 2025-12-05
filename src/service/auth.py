import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.user import UserRepository
from src.repository.role import RoleRepository
from src.schema.user import UserCreate
from src.schema.auth import Token, TokenData

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))


class AuthService:
    def __init__(self, session: AsyncSession):
        self.user_repo = UserRepository(session)
        self.role_repo = RoleRepository(session)

    async def register(self, user_data: UserCreate) -> dict:
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise ValueError("Email already registered")

        # Validate role_id exists
        role = await self.role_repo.get_by_id(user_data.role_id)
        if not role:
            raise ValueError(
                f"Invalid role_id. Please select a valid role ID (1=Member, 2=Admin, 3=Librarian)"
            )

        hashed_password = self._hash_password(user_data.password)

        user_dict = user_data.model_dump()
        user_dict["hashed_password"] = hashed_password
        del user_dict["password"]

        try:
            user = await self.user_repo.create(user_dict)
            return {"id": user.id, "email": user.email, "name": user.name}
        except Exception as e:
            # Catch foreign key constraint errors and other database errors
            error_msg = str(e)
            if "foreign key" in error_msg.lower() or "role_id" in error_msg.lower():
                raise ValueError(
                    f"Invalid role_id. Please select a valid role ID (1=Member, 2=Admin, 3=Librarian)"
                )
            raise ValueError(f"Failed to create user: {error_msg}")

    async def login(self, email: str, password: str) -> Token:
        user = await self.user_repo.get_by_email(email)
        if not user or not self._verify_password(password, user.hashed_password):
            raise ValueError("Invalid credentials")

        if not user.is_active:
            raise ValueError("Account is inactive")

        access_token = self._create_access_token(
            {"user_id": user.id, "email": user.email}
        )
        refresh_token = self._create_refresh_token(
            {"user_id": user.id, "email": user.email}
        )

        return Token(access_token=access_token, refresh_token=refresh_token)

    async def refresh_token(self, refresh_token: str) -> Token:
        try:
            payload = jwt.decode(
                refresh_token, JWT_REFRESH_SECRET_KEY, algorithms=[ALGORITHM]
            )
            user_id = payload.get("user_id")
            email = payload.get("email")

            if not user_id:
                raise ValueError("Invalid token")

            user = await self.user_repo.get_by_id(user_id)
            if not user or not user.is_active:
                raise ValueError("Invalid token")

            access_token = self._create_access_token(
                {"user_id": user.id, "email": user.email}
            )
            new_refresh_token = self._create_refresh_token(
                {"user_id": user.id, "email": user.email}
            )

            return Token(access_token=access_token, refresh_token=new_refresh_token)

        except JWTError:
            raise ValueError("Invalid token")

    async def verify_token(self, token: str) -> TokenData:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")
            email = payload.get("email")

            if not user_id:
                raise ValueError("Invalid token")

            return TokenData(user_id=user_id, email=email)

        except JWTError:
            raise ValueError("Invalid token")

    def _hash_password(self, password: str) -> str:
        # Bcrypt has a 72-byte limit, truncate if needed
        if len(password.encode("utf-8")) > 72:
            password = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
        return pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def _create_access_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)

    def _create_refresh_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, JWT_REFRESH_SECRET_KEY, algorithm=ALGORITHM)
