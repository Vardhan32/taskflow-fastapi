import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_task_success(client: AsyncClient):
    user = (await client.post("/users", json={"name": "Dev", "email": "dev@example.com"})).json()
    proj = (await client.post("/projects", json={"name": "Project Alpha", "owner_id": user["id"]})).json()

    task_res = await client.post(
        "/tasks",
        json={
            "title": "Build Auth",
            "description": "JWT tokens",
            "status": "pending",
            "priority": "high",
            "due_date": "2026-12-31",
            "project_id": proj["id"],
            "assignee_id": user["id"],
        },
    )
    assert task_res.status_code == 201
    data = task_res.json()
    assert data["title"] == "Build Auth"
    assert data["status"] == "pending"
    assert data["priority"] == "high"
    assert data["project_id"] == proj["id"]
    assert data["assignee_id"] == user["id"]


@pytest.mark.asyncio
async def test_create_task_invalid_relations_404(client: AsyncClient):
    user = (await client.post("/users", json={"name": "Dev2", "email": "dev2@example.com"})).json()

    # Invalid project
    bad_proj = await client.post(
        "/tasks",
        json={"title": "T1", "project_id": 99999, "assignee_id": user["id"]},
    )
    assert bad_proj.status_code == 404
    assert bad_proj.json()["detail"] == "Project not found"

    # Invalid assignee
    proj = (await client.post("/projects", json={"name": "P2", "owner_id": user["id"]})).json()
    bad_assignee = await client.post(
        "/tasks",
        json={"title": "T2", "project_id": proj["id"], "assignee_id": 99999},
    )
    assert bad_assignee.status_code == 404
    assert bad_assignee.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_list_tasks_and_filters(client: AsyncClient):
    user = (await client.post("/users", json={"name": "Dev3", "email": "dev3@example.com"})).json()
    proj = (await client.post("/projects", json={"name": "P3", "owner_id": user["id"]})).json()

    t1 = await client.post(
        "/tasks",
        json={"title": "T1", "status": "pending", "priority": "low", "project_id": proj["id"]},
    )
    t2 = await client.post(
        "/tasks",
        json={"title": "T2", "status": "in_progress", "priority": "high", "project_id": proj["id"]},
    )
    t3 = await client.post(
        "/tasks",
        json={"title": "T3", "status": "completed", "priority": "high", "project_id": proj["id"]},
    )

    all_t = await client.get("/tasks")
    assert len(all_t.json()) == 3

    pending_t = await client.get("/tasks?status=pending")
    assert len(pending_t.json()) == 1
    assert pending_t.json()[0]["title"] == "T1"

    high_t = await client.get("/tasks?priority=high")
    assert len(high_t.json()) == 2


@pytest.mark.asyncio
async def test_update_task_status_endpoint(client: AsyncClient):
    user = (await client.post("/users", json={"name": "Dev4", "email": "dev4@example.com"})).json()
    proj = (await client.post("/projects", json={"name": "P4", "owner_id": user["id"]})).json()

    task = (await client.post(
        "/tasks",
        json={"title": "Task A", "project_id": proj["id"]},
    )).json()

    patch_res = await client.patch(f"/tasks/{task['id']}/status", json={"status": "completed"})
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient):
    user = (await client.post("/users", json={"name": "Dev5", "email": "dev5@example.com"})).json()
    proj = (await client.post("/projects", json={"name": "P5", "owner_id": user["id"]})).json()

    task = (await client.post(
        "/tasks",
        json={"title": "Task To Delete", "project_id": proj["id"]},
    )).json()

    del_res = await client.delete(f"/tasks/{task['id']}")
    assert del_res.status_code == 204

    get_res = await client.get(f"/tasks/{task['id']}")
    assert get_res.status_code == 404
