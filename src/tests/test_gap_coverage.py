"""Tests filling coverage gaps in the other test files."""

def _create_project(client) -> int:
    response = client.post("/projects", json={
        "name": "Kitchen", "room": "Kitchen", "budget": 500_000,
        "start_date": "2026-08-01", "target_completion_date": "2026-09-01",
    })
    return response.get_json()["id"]


def test_delete_project_with_existing_tasks_is_blocked(client):
    project_id = _create_project(client)
    client.post(f"/projects/{project_id}/tasks", json={
        "description": "Cabinets", "est_cost": 200_000, "trade_category": "carpentry",
    })

    response = client.delete(f"/projects/{project_id}?confirm=true")

    assert response.status_code == 409
    assert client.get(f"/projects/{project_id}").status_code == 200  # project still exists


def test_update_task_revises_estimate_without_touching_status(client):
    project_id = _create_project(client)
    create_response = client.post(f"/projects/{project_id}/tasks", json={
        "description": "Cabinets", "est_cost": 200_000, "trade_category": "carpentry",
    })
    task_id = create_response.get_json()["id"]

    response = client.put(f"/tasks/{task_id}", json={"est_cost": 250_000})

    assert response.status_code == 200
    body = response.get_json()
    assert body["est_cost"] == 250_000
    assert body["task_status"] == "todo"  # unchanged


def test_update_task_reassigns_trade_and_advances_status(client):
    project_id = _create_project(client)
    create_response = client.post(f"/projects/{project_id}/tasks", json={
        "description": "Cabinets", "est_cost": 200_000, "trade_category": "carpentry",
    })
    task_id = create_response.get_json()["id"]

    response = client.put(f"/tasks/{task_id}", json={"trade_category": "general", "task_status": "in_progress"})

    assert response.status_code == 200
    body = response.get_json()
    assert body["trade_category"] == "general"
    assert body["task_status"] == "in_progress"