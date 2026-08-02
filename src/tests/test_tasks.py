"""Tests for task CRUD endpoints."""


def _create_project(client) -> int:
    response = client.post("/projects", json={
        "name": "Kitchen", "room": "Kitchen", "budget": 500_000,
        "start_date": "2026-08-01", "target_completion_date": "2026-09-01",
    })
    return response.get_json()["id"]


def test_create_task_returns_201_with_todo_status(client):
    project_id = _create_project(client)

    response = client.post(f"/projects/{project_id}/tasks", json={
        "description": "Install cabinets", "est_cost": 200_000, "trade_category": "carpentry",
    })

    assert response.status_code == 201
    body = response.get_json()
    assert body["task_status"] == "todo"
    assert body["actual_cost"] is None


def test_create_task_under_nonexistent_project_returns_404(client):
    response = client.post("/projects/9999/tasks", json={
        "description": "Install cabinets", "est_cost": 200_000, "trade_category": "carpentry",
    })

    assert response.status_code == 404


def test_list_tasks_filters_by_trade(client):
    project_id = _create_project(client)
    client.post(f"/projects/{project_id}/tasks", json={
        "description": "Cabinets", "est_cost": 200_000, "trade_category": "carpentry",
    })
    client.post(f"/projects/{project_id}/tasks", json={
        "description": "Plumbing", "est_cost": 150_000, "trade_category": "plumbing",
    })

    response = client.get(f"/projects/{project_id}/tasks?trade_category=plumbing")

    tasks = response.get_json()["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["trade_category"] == "plumbing"


def test_delete_task_without_confirmation_returns_409(client):
    project_id = _create_project(client)
    create_response = client.post(f"/projects/{project_id}/tasks", json={
        "description": "Cabinets", "est_cost": 200_000, "trade_category": "carpentry",
    })
    task_id = create_response.get_json()["id"]

    response = client.delete(f"/tasks/{task_id}")

    assert response.status_code == 409