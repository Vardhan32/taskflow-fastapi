import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_overview_stats(client: AsyncClient):
    # Empty stats initially
    init_res = await client.get("/stats/overview")
    assert init_res.status_code == 200
    init_data = init_res.json()
    assert init_data["users"] == 0
    assert init_data["projects"] == 0
    assert init_data["tasks"] == 0

    # Create 1 user, 1 project, 2 tasks (1 pending, 1 completed)
    user = (await client.post("/users", json={"name": "Stat User", "email": "stat@example.com"})).json()
    proj = (await client.post("/projects", json={"name": "Stat Proj", "owner_id": user["id"]})).json()
    await client.post("/tasks", json={"title": "T1", "status": "pending", "project_id": proj["id"]})
    await client.post("/tasks", json={"title": "T2", "status": "completed", "project_id": proj["id"]})

    stat_res = await client.get("/stats/overview")
    assert stat_res.status_code == 200
    data = stat_res.json()
    assert data["users"] == 1
    assert data["projects"] == 1
    assert data["tasks"] == 2
    assert data["pending_tasks"] == 1
    assert data["completed_tasks"] == 1
    assert data["in_progress_tasks"] == 0


@pytest.mark.asyncio
async def test_project_stats_and_404(client: AsyncClient):
    user = (await client.post("/users", json={"name": "User P", "email": "p@example.com"})).json()
    proj = (await client.post("/projects", json={"name": "Proj Stats", "owner_id": user["id"]})).json()

    await client.post("/tasks", json={"title": "T1", "status": "in_progress", "project_id": proj["id"]})

    proj_stats = await client.get(f"/stats/projects/{proj['id']}")
    assert proj_stats.status_code == 200
    data = proj_stats.json()
    assert data["total_tasks"] == 1
    assert data["in_progress_tasks"] == 1

    not_found = await client.get("/stats/projects/99999")
    assert not_found.status_code == 404
