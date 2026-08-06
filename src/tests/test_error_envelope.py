"""Tests for the consistent error envelope across error types."""

import pytest


def test_not_found_error_has_consistent_envelope(client):
    response = client.get("/projects/9999")

    body = response.get_json()
    assert response.status_code == 404
    assert body["error_code"] == "not_found"
    assert "message" in body
    assert "request_id" in body


def test_pydantic_validation_error_includes_field_details(client):
    response = client.post("/projects", json={"name": "Missing required fields"})

    assert response.status_code == 422
    body = response.get_json()
    assert body["error_code"] == "validation_error"
    assert "errors" in body
    fields_with_errors = {e["field"] for e in body["errors"]}
    assert "room" in fields_with_errors
    assert "budget" in fields_with_errors


def _valid_project_payload(**overrides) -> dict:
    payload = {
        "name": "Kitchen Remodel", "room": "Kitchen", "budget": 500_000,
        "start_date": "2026-08-01", "target_completion_date": "2026-09-01",
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize(
    "payload, invalid_field",
    [
        ({k: v for k, v in _valid_project_payload().items() if k != "name"}, "name"),
        ({k: v for k, v in _valid_project_payload().items() if k != "room"}, "room"),
        ({k: v for k, v in _valid_project_payload().items() if k != "budget"}, "budget"),
        ({k: v for k, v in _valid_project_payload().items() if k != "start_date"}, "start_date"),
        (_valid_project_payload(budget=-100), "budget"),
        (_valid_project_payload(name=""), "name"),
    ],
    ids=["missing_name", "missing_room", "missing_budget", "missing_start_date", "negative_budget", "empty_name"],
)
def test_project_create_validation_error_names_the_bad_field(client, payload, invalid_field):
    response = client.post("/projects", json=payload)

    assert response.status_code == 422
    body = response.get_json()
    assert body["error_code"] == "validation_error"
    fields_with_errors = {e["field"] for e in body["errors"]}
    assert invalid_field in fields_with_errors