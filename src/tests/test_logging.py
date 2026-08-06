"""Tests confirming requests emit structured log output."""

import json
import logging


def test_request_emits_json_log_with_expected_fields(client, caplog):
    caplog.set_level(logging.INFO)

    client.get("/live")

    assert len(caplog.records) >= 1
    last_record = caplog.records[-1]
    last_log = json.loads(last_record.getMessage())

    assert last_log["event"] == "request_completed"
    assert last_log["method"] == "GET"
    assert last_log["path"] == "/live"
    assert last_log["status_code"] == 200
    assert "duration_ms" in last_log
    assert "request_id" in last_log