# Architecture and governance

## Context

Two independently runnable APIs: Java Spring Boot URL shortener (port 8080) and Python FastAPI orchestration prototype (port 8000). PostgreSQL backs the Java service in Docker; the orchestrator uses SQLite inside a mounted local workspace for persistent workflow records and audit events.

## Explicit task dependency graph

`REQUIREMENTS -> PLANNING -> ARCHITECTURE -> IMPLEMENTATION -> (TESTING || DOCUMENTATION) -> REVIEW`

The testing and documentation stages are sibling dependencies of REVIEW; the current demonstration engine evaluates ready nodes sequentially in a deterministic loop, **not in parallel**. The graph and synchronization semantics are represented, but true concurrent scheduling remains future work.

## Approval and control

- Ambiguous requirements pause for clarification.
- Design changes pause for explicit human approval.
- Final readiness pauses for explicit human approval.
- Rejection stops workflow and preserves trace.
- Generated artifacts are written only inside a workflow-specific workspace directory.
- No arbitrary shell execution, autonomous source changes, production deployment or secret access is permitted.
- Retry counter is bounded, but currently exercises artifact validation only; automated code repair is not implemented.

## Key trade-offs and limitations

The deterministic orchestration engine is an executable **agent-role simulation**, not a production AI coding agent system. It demonstrates graph state, persistence, approvals, traceability, and reviewable artifacts. It does not invoke an LLM, modify source code, execute Java tests, dynamically replan, perform real rollbacks, or calculate MTTR. These require controlled tool adapters and real agent integrations. The URL shortener is independently functional.

For production: use isolated workers, transactional outbox/event processing for analytics, real migration tooling, stronger authentication and authorization, API rate limits, SSRF-safe link previews, managed secrets, distributed tracing, and robust concurrent code allocation.
