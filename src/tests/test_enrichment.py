"""Tests for AI enrichment on the project create"""

from tests.stubs import StubFailureClient, StubMalformedClient, StubSuccessClient


def _sample_project_payload() -> dict:
    return {
        "name": "Kitchen Remodel", "room": "Kitchen", "budget": 500_000,
        "start_date": "2026-08-01", "target_completion_date": "2026-09-01",
    }


def test_create_project_with_successful_enrichment_populates_fields(app, client):
    app.config["ENRICHMENT_CLIENT"] = StubSuccessClient()

    response = client.post("/projects", json=_sample_project_payload())

    assert response.status_code == 201
    body = response.get_json()
    assert body["enrichment_status"] == "complete"


def test_create_project_survives_enrichment_client_exception(app, client):
    app.config["ENRICHMENT_CLIENT"] = StubFailureClient()

    response = client.post("/projects", json=_sample_project_payload())

    assert response.status_code == 201  # create must still succeed
    body = response.get_json()
    assert body["enrichment_status"] == "failed"


def test_create_project_survives_malformed_enrichment_response(app, client):
    app.config["ENRICHMENT_CLIENT"] = StubMalformedClient()

    response = client.post("/projects", json=_sample_project_payload())

    assert response.status_code == 201  # create must still succeed
    assert response.get_json()["enrichment_status"] == "failed"


def test_create_project_succeeds_with_no_enrichment_client_configured(app, client):
    app.config["ENRICHMENT_CLIENT"] = None

    response = client.post("/projects", json=_sample_project_payload())

    assert response.status_code == 201
    assert response.get_json()["enrichment_status"] == "pending"