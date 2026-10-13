# Agentic Software Engineering System — URL Shortener

Interview assignment prototype: **functional Java URL shortener** plus **stateful, auditable engineering-workflow demonstrator**.

## Quick start (Docker)

Requirements: Docker Desktop / Docker Compose.

```bash
docker compose up --build
```

- URL shortener: http://localhost:8080/actuator/health
- Orchestrator API / Swagger UI: http://localhost:8000/docs
- PostgreSQL: localhost:5432 (local development only)

## Example: create a short URL

```bash
curl -X POST http://localhost:8080/api/urls -H 'Content-Type: application/json' -d '{"url":"https://example.com"}'
```

Copy the returned `code` and test:

```bash
curl -i http://localhost:8080/REPLACE_CODE
curl http://localhost:8080/api/urls/REPLACE_CODE/analytics
curl -X DELETE http://localhost:8080/api/urls/REPLACE_CODE
```

## Example: orchestrator

```bash
curl -X POST http://localhost:8000/workflows -H 'Content-Type: application/json' -d '{"requirement":"Add URL expiration to existing service","scenario":"brownfield"}'
```

Copy the returned `id`, then:

```bash
curl -X POST http://localhost:8000/workflows/REPLACE_ID/run
curl -X POST http://localhost:8000/workflows/REPLACE_ID/decisions -H 'Content-Type: application/json' -d '{"action":"design","decision":"approve"}'
curl -X POST http://localhost:8000/workflows/REPLACE_ID/decisions -H 'Content-Type: application/json' -d '{"action":"release","decision":"approve"}'
curl http://localhost:8000/workflows/REPLACE_ID/metrics
```

For ambiguous scenario, choose `scenario=ambiguous`, run, then submit `{"action":"clarification","decision":"approve","notes":"Reject invalid schemes and add per-client request limits"}` before design approval.

## Run tests

```bash
cd agentic-orchestrator
python -m pip install -r requirements.txt
python -m pytest -q
cd ../url-shortener-service
mvn test
```

JDK 21 and Maven are required for Java tests outside Docker. Alternatively, build the service using `docker compose build url-shortener` (build skips Java tests).

## Architecture and scope

See [architecture](docs/architecture.md), [demo script](docs/demo.md), and [scenario requirements](scenarios).

**Important limitation:** The orchestrator is a deterministic, stateful **agent-role simulation** with approvals, dependency checks, persistent audit events and artifact generation. It does **not** call an LLM, write production code, execute autonomous Maven builds, perform real Git rollback, or run parallel workers. These are explicitly identified as next-stage integrations. Do not present these features as implemented.

The URL shortener is a functional REST service with persistent URLs, redirect, expiry, deactivation and click count. For production it needs rate limiting, authentication for management APIs, durable migrations, more robust concurrency controls and privacy-aware analytics.


## Live agent execution (opt-in)

The original `/workflows` API is a deterministic offline orchestration demo. A separate `/live/workflows` API implements optional LLM-backed requirements, planning, code-change proposals, human approval, actual Maven test execution, parallel documentation, bounded retries and file snapshot rollback. It requires an LLM API key and an isolated workspace. See [Live agent demo](docs/live-agent-demo.md). **Do not represent offline simulations as actual AI code generation.**
