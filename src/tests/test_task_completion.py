"""Tests for the complete-task endpoint and its effect on project totals."""


def _create_project(client, budget: int = 500_000) -> int:
    response = client.post("/projects", json={
        "name": "Kitchen", "room": "Kitchen", "budget": budget,
        "start_date": "2026-08-01", "target_completion_date": "2026-09-01",
    })
    return response.get_json()["id"]


def _create_task(client, project_id: int, est_cost: int = 200_000) -> int:
    response = client.post(f"/projects/{project_id}/tasks", json={
        "description": "Cabinets", "est_cost": est_cost, "trade_category": "carpentry",
    })
    return response.get_json()["id"]


def test_complete_task_sets_status_done_and_records_actual_cost(client):
    project_id = _create_project(client)
    task_id = _create_task(client, project_id)

    response = client.post(f"/tasks/{task_id}/complete", json={"actual_cost": 210_000})

    assert response.status_code == 200
    body = response.get_json()
    assert body["task_status"] == "done"
    assert body["actual_cost"] == 210_000


def test_complete_task_without_actual_cost_returns_422(client):
    project_id = _create_project(client)
    task_id = _create_task(client, project_id)

    response = client.post(f"/tasks/{task_id}/complete", json={})

    assert response.status_code == 422


def test_complete_task_updates_project_totals(client):
    project_id = _create_project(client, budget=500_000)
    task_id = _create_task(client, project_id, est_cost=200_000)

    response = client.post(f"/tasks/{task_id}/complete", json={"actual_cost": 180_000})

    totals = response.get_json()["project_totals"]
    assert totals["total_actual_cost"] == 180_000
    assert totals["remaining_budget"] == 320_000
    assert totals["over_budget"] is False


def test_complete_task_over_budget_is_accepted_and_flagged(client):
    project_id = _create_project(client, budget=100_000)
    task_id = _create_task(client, project_id, est_cost=100_000)

    response = client.post(f"/tasks/{task_id}/complete", json={"actual_cost": 150_000})

    assert response.status_code == 200  # accepted, not rejected
    totals = response.get_json()["project_totals"]
    assert totals["over_budget"] is True
    assert totals["remaining_budget"] == -50_000


def test_complete_nonexistent_task_returns_404(client):
    response = client.post("/tasks/9999/complete", json={"actual_cost": 100_000})

    assert response.status_code == 404