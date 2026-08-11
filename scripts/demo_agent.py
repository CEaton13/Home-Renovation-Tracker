"""Standalone 'agent' that kicks off a project-creation task against the
Home Renovation Tracker API, for demoing distributed tracing end to end.

Run with auto-instrumentation so this script's own span is exported and
propagated to the API via the traceparent header. Run from the host while
the API container is already up (`docker compose up --build`):

    opentelemetry-instrument python scripts/demo_agent.py
"""
import sys
import time
from datetime import date, timedelta

import requests
from opentelemetry import trace

tracer = trace.get_tracer("renovation-tracker.agent")

API_URL = "http://localhost:5000/projects"

_today = date.today()

DEMO_PROJECT = {
    "name": "Kitchen Refresh",
    "room": "kitchen",
    "budget": 850000,
    "start_date": _today.isoformat(),
    "target_completion_date": (_today + timedelta(days=60)).isoformat(),
}


def main() -> int:
    with tracer.start_as_current_span("agent.create_project_task") as span:
        span.set_attribute("app.project.name", DEMO_PROJECT["name"])
        start = time.perf_counter()
        response = requests.post(API_URL, json=DEMO_PROJECT, timeout=30)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        span.set_attribute("app.request.duration_ms", duration_ms)

        print(f"Status: {response.status_code} ({duration_ms} ms)")
        print(response.json())

        if not response.ok:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
