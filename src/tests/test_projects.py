"""Tests for project CRUD endpoints."""

import pytest

def _sample_project_payload() -> dict:
    return {
        "name": "Kitchen Remodel",
        "room": "Kitchen",
        "budget": 500_000,
        "start_date": "2026-08-01",
        "target_completion_date": "2026-09-01",
    }

def test_create_project_returns_201_with_planning_status(client):
    response = client.post("/projects", json=_sample_project_payload())

    assert response.status_code == 201
    body = response.get_json()
    assert body["project_status"] == "planning"
    assert body["name"] == "Kitchen Remodel"

def test_get_project_returns_created_project(client):
    create_response = client.post("/projects", json=_sample_project_payload())
    project_id = create_response.get_json()["id"]

    response = client.get(f"/projects/{project_id}")

    assert response.status_code == 200
    assert response.get_json()["id"] == project_id


def test_get_nonexistent_project_returns_404(client):
    response = client.get("/projects/9999")

    assert response.status_code == 404
    assert response.get_json()["error_code"] == "not_found"


def test_update_project_changes_only_specified_field(client):
    create_response = client.post("/projects", json=_sample_project_payload())
    project_id = create_response.get_json()["id"]

    response = client.put(f"/projects/{project_id}", json={"budget": 600_000})

    assert response.status_code == 200
    body = response.get_json()
    assert body["budget"] == 600_000
    assert body["name"] == "Kitchen Remodel"  # unchanged


def test_delete_project_without_confirmation_returns_409(client):
    create_response = client.post("/projects", json=_sample_project_payload())
    project_id = create_response.get_json()["id"]

    response = client.delete(f"/projects/{project_id}")

    assert response.status_code == 409


def test_delete_project_with_confirmation_returns_204(client):
    create_response = client.post("/projects", json=_sample_project_payload())
    project_id = create_response.get_json()["id"]

    response = client.delete(f"/projects/{project_id}?confirm=true")

    assert response.status_code == 204
    assert client.get(f"/projects/{project_id}").status_code == 404


@pytest.mark.parametrize(
    "method, query, json_body",
    [
        ("get", "", None),
        ("put", "", {"budget": 100_000}),
        ("delete", "?confirm=true", None),
    ],
    ids=["get", "put", "delete"],
)
def test_project_not_found_returns_consistent_404_envelope(client, method, query, json_body):
    response = getattr(client, method)(f"/projects/9999{query}", json=json_body)

    assert response.status_code == 404
    body = response.get_json()
    assert body["error_code"] == "not_found"
    assert "request_id" in body