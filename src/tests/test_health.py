"""Tests for liveness and readiness endpoints."""

def test_live_returns_200(client):
    response = client.get("/live")

    assert response.status_code == 200
    assert response.get_json()["status"] == "live"


def test_ready_returns_200_when_db_reachable(client):
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.get_json()["status"] == "ready"