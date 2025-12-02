import pytest
from datetime import datetime
from src.service.auth import AuthService
from src.schema.user import UserCreate


@pytest.mark.asyncio
async def test_register_user(db_session, test_role):
    """Test user registration with valid role"""
    auth_service = AuthService(db_session)
    
    user_data = UserCreate(
        email="newuser@example.com",
        name="New User",
        password="Password123!",
        role_id=test_role.id  # Use existing role from fixture
    )
    
    result = await auth_service.register(user_data)
    
    assert result["email"] == "newuser@example.com"
    assert result["name"] == "New User"
    assert "id" in result


@pytest.mark.asyncio
async def test_register_duplicate_email(db_session, test_user):
    auth_service = AuthService(db_session)
    
    user_data = UserCreate(
        email="test@example.com",
        name="Duplicate User",
        password="Password123!",
        role_id=1
    )
    
    with pytest.raises(ValueError, match="Email already registered"):
        await auth_service.register(user_data)


@pytest.mark.asyncio
async def test_login_success(db_session, test_user):
    auth_service = AuthService(db_session)
    
    token = await auth_service.login("test@example.com", "testpass123")
    
    assert token.access_token is not None
    assert token.refresh_token is not None
    assert token.token_type == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(db_session, test_user):
    auth_service = AuthService(db_session)
    
    with pytest.raises(ValueError, match="Invalid credentials"):
        await auth_service.login("test@example.com", "wrongpassword")


@pytest.mark.asyncio
async def test_refresh_token(db_session, test_user):
    auth_service = AuthService(db_session)
    
    token = await auth_service.login("test@example.com", "testpass123")
    
    # Wait to ensure token timestamp changes
    import asyncio
    await asyncio.sleep(1)
    
    new_token = await auth_service.refresh_token(token.refresh_token)
    
    assert new_token.access_token is not None
    assert new_token.refresh_token is not None
    assert new_token.access_token != token.access_token


@pytest.mark.asyncio
async def test_verify_token(db_session, test_user):
    auth_service = AuthService(db_session)
    
    token = await auth_service.login("test@example.com", "testpass123")
    token_data = await auth_service.verify_token(token.access_token)
    
    assert token_data.email == "test@example.com"
    assert token_data.user_id == test_user.id
