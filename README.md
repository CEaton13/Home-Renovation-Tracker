# Home Renovation Tracker

A backend service for tracking home renovation projects and their tasks — budgets, spend, trades, and status — with AI-assisted task-breakdown suggestions on project creation.

## Install & Run

```powershell
docker compose up --build
```

The API is then available at `http://localhost:5000`. Copy `.env.example` to `.env` and fill in your own Azure OpenAI credentials before starting — see **AI Enrichment** below for details.

## API Overview

| Endpoint | Method | Purpose |
|---|---|---|
| `/projects` | POST, GET | Create a project; list all projects with cost aggregates and filters |
| `/projects/<id>` | GET, PUT, DELETE | Fetch/update/delete a single project |
| `/projects/<id>/tasks` | POST, GET | Add a task; list tasks for a project, with filters |
| `/tasks/<id>` | PUT, DELETE | Update/delete a single task |
| `/tasks/<id>/complete` | POST | Mark a task done, record actual cost, recompute project totals |
| `/live`, `/ready` | GET | Liveness and readiness checks |

## AI Enrichment

On project creation, the service calls a deployed Azure OpenAI model to suggest a task breakdown, validated through a Pydantic schema before being persisted.

**Client choice:** `AzureEnrichmentClient` (`src/renovation_tracker/azure_client.py`) uses the plain `openai` SDK `OpenAI` client pointed at the Azure AI Foundry resource's unified `/openai/v1` endpoint via `base_url`, rather than the SDK's `AzureOpenAI` class. This is a deliberate choice, not an oversight: this project's Azure resource is provisioned through AI Foundry and only exposes the unified endpoint, which `AzureOpenAI` (built for the older per-deployment REST surface) cannot target — the Foundry portal's own sample code for this resource uses the plain `OpenAI` client for the same reason.

**Model & config parameters:** the deployed model is `gpt-5-mini`, a reasoning model, chosen for low cost/latency on a task that's really structured extraction rather than open-ended generation. Because it's a reasoning model, the Responses API does not accept `temperature` or `top_p` for it — `reasoning={"effort": "low"}` is the equivalent lever, and `"low"` is deliberately chosen over a higher effort level since this task is low-variance structured extraction that doesn't benefit from deeper reasoning, keeping the call cheaper and faster. `text={"format": {"type": "json_object"}}` enforces syntactically valid JSON at the API level rather than relying on prompt instructions alone (the response is still validated against the `EnrichmentPayload` Pydantic model after parsing). `max_output_tokens=2000` bounds cost/latency while leaving headroom for a multi-task breakdown.

**Responsible AI safeguards:**
1. **Scope-constraining system prompt** — explicitly forbids omitting permit/safety/building-code considerations and forbids underestimating costs to make a project look more affordable than realistic.
2. **PII minimization** — only project name, room, and budget are sent to the model; no owner name, address, or other identifying information.
3. **Explicit AI-generated marking** — `EnrichmentPayload.ai_generated` is a fixed `Literal[True]`, so every validated enrichment payload is self-documenting as AI-sourced.
4. **Graceful degradation** — enrichment failures (exceptions, malformed JSON, incomplete responses) never fail the underlying create/update; `enrichment_status` is set to `failed` and the failure is logged with the request's correlation id. See `tests/test_enrichment.py` for three distinct injected failure modes (raised exception, malformed JSON, no client configured).

## Edge Case Policies

**Task pushes a project over budget:** accepted, not rejected. `complete_task` records the actual cost unconditionally; the project's `over_budget` flag (computed live from `SUM(actual_cost) > budget` in `project_repository.list_projects_with_aggregates` / `get_project_totals`) flips to `true` and surfaces on the dashboard and in the `complete_task` response. Renovation costs legitimately run over during a project, and a hard rejection would block recording real spend — flagging is more useful than blocking here.

**Completing a project with open tasks:** blocked, not auto-closed. Setting `project_status="completed"` while any task isn't `done` returns `409 Conflict` listing the offending task ids (`project_repository.update_project`, `_get_open_task_ids`). Auto-closing tasks would silently misrepresent work that was never actually finished; blocking keeps "completed" a meaningful, trustworthy status.

**Deleting a project that still has tasks:** blocked, not cascaded. The `tasks.project_id` foreign key uses `ON DELETE RESTRICT` (`storage/schema.sql`), so `DELETE /projects/<id>` fails with `409 Conflict` if any tasks remain — the caller must delete the project's tasks first. This avoids silent, irreversible bulk data loss from a single project delete.

**Concurrent mutations:** each request opens its own SQLite connection (`storage/db.py::get_db`), and SQLite serializes writers at the file level — only one write transaction can commit at a time, so concurrent writes can never physically corrupt a row or produce a torn read. That said, a couple of endpoints do a read-then-decide-then-write sequence that isn't atomic at the SQL level, which matters under true concurrency:

- **Two clients completing the same task at once:** `complete_task` reads the task, checks `task_status != "done"`, then writes. If both requests read the row while it's still `todo` before either commits, both pass the guard — the first `UPDATE` commits, the second then runs (after waiting on SQLite's write lock) and silently overwrites the first `actual_cost`/status instead of hitting the expected `409 "already completed"`. This is a known limitation of the current implementation, not by-design behavior; a proper fix would move the guard into the `UPDATE ... WHERE task_status != 'done'` clause and check `cursor.rowcount` to detect the lost race, rather than relying on a prior `SELECT`.

- **Deleting a task while its project's total is being recomputed:** `complete_task` performs its `UPDATE` and the totals `SELECT` within the same connection before committing, so a concurrent `DELETE` of that task from another connection blocks behind that write lock until the completing transaction commits — the totals returned reflect a consistent pre-delete-or-post-complete snapshot, never a half-applied state.
- No optimistic locking (a `version` column or `updated_at` compare-and-swap) or application-level row locking is implemented; SQLite's own writer serialization is the only concurrency guard currently in place.

**Testability:** the enrichment client is a `Protocol` (`EnrichmentClient`), not a concrete dependency — route code depends on the interface, not on `AzureEnrichmentClient` directly. Tests inject plain stub objects (`tests/stubs.py`) satisfying that one-method interface, so the full test suite runs without any network call, in ~13 seconds for 33 tests.

## Structured Logging

Every request emits one JSON log line (method, path, status code, duration, correlation id) via structlog. The same correlation id appears in every error response body under `request_id`, so a client-reported error can be traced directly to its server-side log line.

## Tracing (demo)

`docker compose up --build` also starts Jaeger, with its UI at `http://localhost:16686`. The API container runs under `opentelemetry-instrument` (see `Dockerfile`), so every request is traced automatically — no manual span code inside application logic beyond a single `app.request_id` attribute set in `app.py` for log/trace correlation. Traces are exported over OTLP/HTTP to the `jaeger` service; the `OTEL_*` env vars controlling this live in `.env.example`.

**Generating a trace:** with the API container running, from the host machine (not inside Docker):

```powershell
opentelemetry-instrument python scripts/demo_agent.py
```

This script is a standalone "agent" that POSTs a demo project to `http://localhost:5000/projects`, with its own root span propagated to the API via the `traceparent` header. It's run from the host rather than as a compose service — simplest option for a demo script that only needs to reach the API's already-published port.

**What to look for in the Jaeger UI:** search for service `renovation-tracker-api`, open the latest trace, and expect to see nested spans for the Flask request, the SQLite insert, the outbound Azure OpenAI call, and the SQLite enrichment update, all under the agent's root span (`agent.create_project_task`). If Azure OpenAI isn't configured, the httpx span is simply absent — the trace still completes since enrichment fails gracefully (see **AI Enrichment** above).

## Running Tests

```powershell
pytest tests/ -v
```