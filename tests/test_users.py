import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_user_success(client: AsyncClient):
    response = await client.post(
        "/users",
        json={"name": "Alice Johnson", "email": "alice@example.com"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] > 0
    assert data["name"] == "Alice Johnson"
    assert data["email"] == "alice@example.com"
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_user_duplicate_email_409(client: AsyncClient):
    await client.post(
        "/users",
        json={"name": "Alice", "email": "alice@example.com"},
    )
    dup = await client.post(
        "/users",
        json={"name": "Alice Duplicate", "email": "alice@example.com"},
    )
    assert dup.status_code == 409
    assert dup.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_create_user_invalid_email_422(client: AsyncClient):
    response = await client.post(
        "/users",
        json={"name": "Bob", "email": "not-an-email"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_users_pagination(client: AsyncClient):
    for i in range(5):
        await client.post(
            "/users",
            json={"name": f"User {i}", "email": f"user{i}@example.com"},
        )
    resp = await client.get("/users?skip=0&limit=3")
    assert resp.status_code == 200
    assert len(resp.json()) == 3

    resp2 = await client.get("/users?skip=3&limit=3")
    assert resp2.status_code == 200
    assert len(resp2.json()) == 2


@pytest.mark.asyncio
async def test_get_user_and_404(client: AsyncClient):
    created = await client.post(
        "/users",
        json={"name": "Charlie", "email": "charlie@example.com"},
    )
    user_id = created.json()["id"]

    get_resp = await client.get(f"/users/{user_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Charlie"

    not_found = await client.get("/users/99999")
    assert not_found.status_code == 404
    assert not_found.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient):
    created = await client.post(
        "/users",
        json={"name": "David", "email": "david@example.com"},
    )
    user_id = created.json()["id"]

    patch_resp = await client.patch(
        f"/users/{user_id}",
        json={"name": "David Updated"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "David Updated"
    assert patch_resp.json()["email"] == "david@example.com"


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient):
    created = await client.post(
        "/users",
        json={"name": "Eve", "email": "eve@example.com"},
    )
    user_id = created.json()["id"]

    del_resp = await client.delete(f"/users/{user_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/users/{user_id}")
    assert get_resp.status_code == 404
