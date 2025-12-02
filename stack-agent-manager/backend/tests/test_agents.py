import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_agent(client: AsyncClient, test_user):
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
    
    # Create stack first
    stack_response = await client.post(
        "/api/stacks",
        json={"name": "Test Stack", "description": "Test Description"},
        headers=headers,
    )
    stack_id = stack_response.json()["id"]
    
    # Create agent
    response = await client.post(
        f"/api/stacks/{stack_id}/agents",
        json={"name": "Test Agent", "description": "Test Agent Description"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Agent"
    assert data["stack_id"] == stack_id

