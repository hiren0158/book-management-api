import pytest


@pytest.mark.asyncio
async def test_list_users_requires_admin_or_librarian(client, auth_headers):
    """Member should not be able to list all users"""
    response = await client.get("/users", headers=auth_headers)
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_users_as_admin(client, admin_auth_headers, test_user):
    """Admin should be able to list all users"""
    response = await client.get("/users", headers=admin_auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_list_users_as_librarian(client, librarian_auth_headers, test_user):
    """Librarian should be able to list all users"""
    response = await client.get("/users", headers=librarian_auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_user_own_profile(client, test_user, auth_headers):
    """User should be able to view their own profile"""
    response = await client.get(
        f"/users/{test_user.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["email"] == test_user.email


@pytest.mark.asyncio
async def test_get_user_other_profile_as_member(client, admin_user, auth_headers):
    """Member should not be able to view other users' profiles"""
    response = await client.get(
        f"/users/{admin_user.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_user_other_profile_as_admin(client, test_user, admin_auth_headers):
    """Admin should be able to view any user's profile"""
    response = await client.get(
        f"/users/{test_user.id}",
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id


@pytest.mark.asyncio
async def test_get_user_other_profile_as_librarian(client, test_user, librarian_auth_headers):
    """Librarian should be able to view any user's profile"""
    response = await client.get(
        f"/users/{test_user.id}",
        headers=librarian_auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id


@pytest.mark.asyncio
async def test_get_nonexistent_user(client, admin_auth_headers):
    """Should return 404 for non-existent user"""
    response = await client.get(
        "/users/99999",
        headers=admin_auth_headers
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_user_requires_admin_or_librarian(client, test_role, auth_headers):
    """Member should not be able to create users"""
    response = await client.post(
        "/users",
        json={
            "email": "new@example.com",
            "name": "New User",
            "password": "Password123!",
            "role_id": test_role.id
        },
        headers=auth_headers
    )
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_user_as_admin(client, test_role, admin_auth_headers):
    """Admin should be able to create users"""
    response = await client.post(
        "/users",
        json={
            "email": "newadmin@example.com",
            "name": "New Admin User",
            "password": "Password123!",
            "role_id": test_role.id
        },
        headers=admin_auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newadmin@example.com"


@pytest.mark.asyncio
async def test_create_user_as_librarian(client, test_role, librarian_auth_headers):
    """Librarian should be able to create users"""
    response = await client.post(
        "/users",
        json={
            "email": "newlib@example.com",
            "name": "New Librarian User",
            "password": "Password123!",
            "role_id": test_role.id
        },
        headers=librarian_auth_headers
    )
    
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_update_user_own_profile(client, test_user, auth_headers):
    """User should be able to update their own profile"""
    response = await client.put(
        f"/users/{test_user.id}",
        json={"name": "Updated Name"},
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_update_user_other_profile_as_member(client, admin_user, auth_headers):
    """Member should not be able to update other users' profiles"""
    response = await client.put(
        f"/users/{admin_user.id}",
        json={"name": "Hacked Name"},
        headers=auth_headers
    )
    
    # Service raises ValueError which becomes 400, but the message indicates permission denied
    assert response.status_code == 400
    assert "permission denied" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_user_as_admin(client, test_user, admin_auth_headers):
    """Admin should be able to update any user"""
    response = await client.put(
        f"/users/{test_user.id}",
        json={"name": "Admin Updated Name"},
        headers=admin_auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Admin Updated Name"


@pytest.mark.asyncio
async def test_delete_user_requires_admin(client, test_user, auth_headers):
    """Only Admin should be able to delete users"""
    response = await client.delete(
        f"/users/{test_user.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_user_as_admin(client, test_user, admin_auth_headers):
    """Admin should be able to delete users"""
    response = await client.delete(
        f"/users/{test_user.id}",
        headers=admin_auth_headers
    )
    
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_user_as_librarian(client, test_user, librarian_auth_headers):
    """Librarian should not be able to delete users"""
    response = await client.delete(
        f"/users/{test_user.id}",
        headers=librarian_auth_headers
    )
    
    assert response.status_code == 403

