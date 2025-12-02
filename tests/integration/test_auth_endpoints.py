import pytest
from datetime import date


@pytest.mark.asyncio
async def test_register_endpoint(client, test_role):
    response = await client.post(
        "/auth/register",
        json={
            "email": "newuser@test.com",
            "name": "New User",
            "password": "Password123!",
            "role_id": test_role.id
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "newuser@test.com"
    assert "id" in data["user"]


@pytest.mark.asyncio
async def test_register_with_invalid_role_id(client):
    response = await client.post(
        "/auth/register",
        json={
            "email": "user@test.com",
            "name": "User",
            "password": "Password123!",
            "role_id": 0  # Invalid role_id (validation error)
        }
    )
    
    # Pydantic validation returns 422 for invalid field values
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_register_with_nonexistent_role_id(client):
    response = await client.post(
        "/auth/register",
        json={
            "email": "user@test.com",
            "name": "User",
            "password": "Password123!",
            "role_id": 999  # Non-existent role_id
        }
    )
    
    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "invalid role_id" in detail or "valid role id" in detail


@pytest.mark.asyncio
async def test_register_duplicate_email(client, test_role, test_user):
    response = await client.post(
        "/auth/register",
        json={
            "email": "test@example.com",  # Already exists
            "name": "Another User",
            "password": "Password123!",
            "role_id": test_role.id
        }
    )
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_weak_password(client, test_role):
    response = await client.post(
        "/auth/register",
        json={
            "email": "user@test.com",
            "name": "User",
            "password": "short",  # Too short
            "role_id": test_role.id
        }
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_endpoint(client, test_user):
    response = await client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpass123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client, test_user):
    response = await client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    response = await client.post(
        "/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "Password123!"
        }
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_endpoint(client, test_user):
    login_response = await client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpass123"
        }
    )
    
    refresh_token = login_response.json()["refresh_token"]
    
    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_token_invalid(client):
    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": "invalid_token"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_without_auth(client):
    response = await client.get("/users")
    
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_protected_endpoint_with_invalid_token(client):
    response = await client.get(
        "/users",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401
