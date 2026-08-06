"""Tests for AI enrichment on project create and update"""

from tests.stubs import CountingStubClient, StubFailureClient, StubMalformedClient, StubSuccessClient


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


def test_update_project_budget_reruns_enrichment(app, client):
    stub = CountingStubClient()
    app.config["ENRICHMENT_CLIENT"] = stub
    project_id = client.post("/projects", json=_sample_project_payload()).get_json()["id"]
    assert stub.call_count == 1

    response = client.put(f"/projects/{project_id}", json={"budget": 600_000})

    assert response.status_code == 200
    assert response.get_json()["enrichment_status"] == "complete"
    assert stub.call_count == 2


def test_update_project_name_reruns_enrichment(app, client):
    stub = CountingStubClient()
    app.config["ENRICHMENT_CLIENT"] = stub
    project_id = client.post("/projects", json=_sample_project_payload()).get_json()["id"]
    assert stub.call_count == 1

    response = client.put(f"/projects/{project_id}", json={"name": "Full Kitchen Gut Remodel"})

    assert response.status_code == 200
    assert stub.call_count == 2


def test_update_project_status_only_does_not_rerun_enrichment(app, client):
    stub = CountingStubClient()
    app.config["ENRICHMENT_CLIENT"] = stub
    project_id = client.post("/projects", json=_sample_project_payload()).get_json()["id"]
    assert stub.call_count == 1

    response = client.put(f"/projects/{project_id}", json={"project_status": "in_progress"})

    assert response.status_code == 200
    assert stub.call_count == 1


def test_update_project_survives_enrichment_failure(app, client):
    app.config["ENRICHMENT_CLIENT"] = StubSuccessClient()
    project_id = client.post("/projects", json=_sample_project_payload()).get_json()["id"]

    app.config["ENRICHMENT_CLIENT"] = StubFailureClient()
    response = client.put(f"/projects/{project_id}", json={"budget": 700_000})

    assert response.status_code == 200  # update must still succeed
    assert response.get_json()["enrichment_status"] == "failed"