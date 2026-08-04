"""Tests confirming requests emit structured log output."""

import json


def test_request_emits_json_log_with_expected_fields(client, capsys):
    client.get("/live")

    captured = capsys.readouterr()
    log_lines = [line for line in captured.out.strip().split("\n") if line]
    assert len(log_lines) >= 1

    last_log = json.loads(log_lines[-1])
    assert last_log["event"] == "request_completed"
    assert last_log["method"] == "GET"
    assert last_log["path"] == "/live"
    assert last_log["status_code"] == 200
    assert "duration_ms" in last_log
    assert "request_id" in last_log