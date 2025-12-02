import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_stack(client: AsyncClient, test_user):
    # Login first
    login_response = await client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "TestPassword123!",
        },
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create stack
    response = await client.post(
        "/api/stacks",
        json={"name": "Test Stack", "description": "Test Description"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Stack"
    assert data["description"] == "Test Description"


@pytest.mark.asyncio
async def test_list_stacks(client: AsyncClient, test_user):
    login_response = await client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "TestPassword123!",
        },
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get("/api/stacks", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

