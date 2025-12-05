import os
from dotenv import load_dotenv

# Load environment variables FIRST (before setting TESTING)
load_dotenv()

# Then set testing flag
os.environ["TESTING"] = "1"
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

from src.core.database import get_session
from src.model import Role, User, Book, Borrowing, Review
from main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with async_session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_role(db_session: AsyncSession) -> Role:
    role = Role(id=1, name="Member")
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role


@pytest_asyncio.fixture
async def admin_role(db_session: AsyncSession) -> Role:
    role = Role(id=2, name="Admin")
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role


@pytest_asyncio.fixture
async def librarian_role(db_session: AsyncSession) -> Role:
    role = Role(id=3, name="Librarian")
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_role: Role) -> User:
    from src.service.auth import pwd_context

    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password=pwd_context.hash("testpass123"),
        role_id=test_role.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, admin_role: Role) -> User:
    from src.service.auth import pwd_context

    user = User(
        email="admin@example.com",
        name="Admin User",
        hashed_password=pwd_context.hash("adminpass123"),
        role_id=admin_role.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_book(db_session: AsyncSession) -> Book:
    from datetime import date

    book = Book(
        title="Test Book",
        description="A test book description",
        isbn="978-0-123456-78-9",
        author="Test Author",
        genre="Fiction",
        published_date=date(2020, 1, 1),
    )
    db_session.add(book)
    await db_session.commit()
    await db_session.refresh(book)
    return book


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user: User) -> dict:
    response = await client.post(
        "/auth/login", json={"email": "test@example.com", "password": "testpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_auth_headers(client: AsyncClient, admin_user: User) -> dict:
    response = await client.post(
        "/auth/login", json={"email": "admin@example.com", "password": "adminpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def librarian_user(db_session: AsyncSession, librarian_role: Role) -> User:
    from src.service.auth import pwd_context

    user = User(
        email="librarian@example.com",
        name="Librarian User",
        hashed_password=pwd_context.hash("libpass123"),
        role_id=librarian_role.id,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def librarian_auth_headers(client: AsyncClient, librarian_user: User) -> dict:
    response = await client.post(
        "/auth/login", json={"email": "librarian@example.com", "password": "libpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
