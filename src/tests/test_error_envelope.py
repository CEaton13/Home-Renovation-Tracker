"""Tests for the consistent error envelope across error types."""


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