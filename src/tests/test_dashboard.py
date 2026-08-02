"""Tests for the project dashboard/list endpoint."""


def test_dashboard_shows_zero_totals_for_project_with_no_tasks(client):
    client.post("/projects", json={
        "name": "Bathroom", "room": "Bathroom", "budget": 100_000,
        "start_date": "2026-08-01", "target_completion_date": "2026-09-01",
    })

    response = client.get("/projects")

    assert response.status_code == 200
    project = response.get_json()["projects"][0]
    assert project["total_est_cost"] == 0
    assert project["task_count"] == 0


def test_dashboard_sums_estimated_costs_across_tasks(client):
    create_response = client.post("/projects", json={
        "name": "Kitchen", "room": "Kitchen", "budget": 500_000,
        "start_date": "2026-08-01", "target_completion_date": "2026-09-01",
    })
    project_id = create_response.get_json()["id"]

    client.post(f"/projects/{project_id}/tasks", json={
        "description": "Cabinets", "est_cost": 200_000, "trade_category": "carpentry",
    })
    client.post(f"/projects/{project_id}/tasks", json={
        "description": "Plumbing", "est_cost": 150_000, "trade_category": "plumbing",
    })

    response = client.get("/projects")
    project = next(p for p in response.get_json()["projects"] if p["id"] == project_id)

    assert project["total_est_cost"] == 350_000
    assert project["task_count"] == 2


def test_dashboard_filters_by_room_partial_match(client):
    client.post("/projects", json={
        "name": "A", "room": "Kitchen", "budget": 100_000,
        "start_date": "2026-08-01", "target_completion_date": "2026-09-01",
    })
    client.post("/projects", json={
        "name": "B", "room": "Bathroom", "budget": 100_000,
        "start_date": "2026-08-01", "target_completion_date": "2026-09-01",
    })

    response = client.get("/projects?room=kit")

    projects = response.get_json()["projects"]
    assert len(projects) == 1
    assert projects[0]["room"] == "Kitchen"