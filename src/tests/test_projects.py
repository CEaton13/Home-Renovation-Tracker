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
    assert body["status"] == "planning"
    assert body["name"] == "Kitchen Remodel"