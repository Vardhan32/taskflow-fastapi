import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project_success(client: AsyncClient):
    user_res = await client.post("/users", json={"name": "Owner", "email": "owner@example.com"})
    owner_id = user_res.json()["id"]

    proj_res = await client.post(
        "/projects",
        json={"name": "Alpha Project", "description": "Core app", "owner_id": owner_id},
    )
    assert proj_res.status_code == 201
    data = proj_res.json()
    assert data["name"] == "Alpha Project"
    assert data["owner_id"] == owner_id
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_project_invalid_owner_404(client: AsyncClient):
    proj_res = await client.post(
        "/projects",
        json={"name": "Ghost Project", "description": "No owner", "owner_id": 99999},
    )
    assert proj_res.status_code == 404
    assert proj_res.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_list_projects_and_filter(client: AsyncClient):
    u1 = (await client.post("/users", json={"name": "U1", "email": "u1@example.com"})).json()["id"]
    u2 = (await client.post("/users", json={"name": "U2", "email": "u2@example.com"})).json()["id"]

    await client.post("/projects", json={"name": "P1", "owner_id": u1})
    await client.post("/projects", json={"name": "P2", "owner_id": u1})
    await client.post("/projects", json={"name": "P3", "owner_id": u2})

    all_projs = await client.get("/projects")
    assert len(all_projs.json()) == 3

    u1_projs = await client.get(f"/projects?owner_id={u1}")
    assert len(u1_projs.json()) == 2


@pytest.mark.asyncio
async def test_update_and_delete_project(client: AsyncClient):
    user = (await client.post("/users", json={"name": "User", "email": "u@example.com"})).json()
    proj = (await client.post("/projects", json={"name": "Old Name", "owner_id": user["id"]})).json()

    patch_res = await client.patch(f"/projects/{proj['id']}", json={"name": "New Name"})
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "New Name"

    del_res = await client.delete(f"/projects/{proj['id']}")
    assert del_res.status_code == 204

    get_res = await client.get(f"/projects/{proj['id']}")
    assert get_res.status_code == 404
