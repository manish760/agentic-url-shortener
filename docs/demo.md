# Interview demonstration

Start: `docker compose up --build`.

## URL shortener

`curl -s -X POST http://localhost:8080/api/urls -H 'Content-Type: application/json' -d '{"url":"https://example.com"}'`

Copy the returned code and open `http://localhost:8080/<code>`. Then GET `/api/urls/<code>/analytics`.

## Orchestration

1. POST `/workflows` with `{"requirement":"Build a URL shortener","scenario":"greenfield"}`.
2. POST `/workflows/<id>/run`: see `WAITING_APPROVAL`.
3. POST `/workflows/<id>/decisions` with `{"action":"design","decision":"approve"}`: see `WAITING_RELEASE_APPROVAL`.
4. POST another decision with `{"action":"release","decision":"approve"}`: see `COMPLETED`.
5. GET `/workflows/<id>` to inspect trace and artifacts; GET `/workflows/<id>/metrics`.
6. Repeat for `brownfield`, or for `ambiguous` to demonstrate `WAITING_CLARIFICATION` and human notes.
7. Reject a design to demonstrate safe-stop.

FastAPI interactive docs: http://localhost:8000/docs.

**Disclosure for interview:** Orchestrator agents currently generate deterministic engineering proposals, not actual source edits or AI-generated code. The Java application is the runnable engineering output; the orchestrator is an executable governance proof of concept.
