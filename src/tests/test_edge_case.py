"""Tests for edge-case business rules: completion blocking and re-completion."""


def _create_project(client) -> int:
    response = client.post("/projects", json={
        "name": "Kitchen", "room": "Kitchen", "budget": 500_000,
        "start_date": "2026-08-01", "target_completion_date": "2026-09-01",
    })
    return response.get_json()["id"]


def _create_task(client, project_id: int) -> int:
    response = client.post(f"/projects/{project_id}/tasks", json={
        "description": "Cabinets", "est_cost": 200_000, "trade_category": "carpentry",
    })
    return response.get_json()["id"]


def test_completing_project_with_open_task_is_blocked(client):
    project_id = _create_project(client)
    _create_task(client, project_id)  # left as 'todo'

    response = client.put(f"/projects/{project_id}", json={"project_status": "completed"})

    assert response.status_code == 409


def test_completing_project_with_all_tasks_done_succeeds(client):
    project_id = _create_project(client)
    task_id = _create_task(client, project_id)
    client.post(f"/tasks/{task_id}/complete", json={"actual_cost": 200_000})

    response = client.put(f"/projects/{project_id}", json={"project_status": "completed"})

    assert response.status_code == 200
    assert response.get_json()["project_status"] == "completed"


def test_recompleting_an_already_done_task_returns_409(client):
    project_id = _create_project(client)
    task_id = _create_task(client, project_id)
    client.post(f"/tasks/{task_id}/complete", json={"actual_cost": 200_000})

    response = client.post(f"/tasks/{task_id}/complete", json={"actual_cost": 999_999})

    assert response.status_code == 409