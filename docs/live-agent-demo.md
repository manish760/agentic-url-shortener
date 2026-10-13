# Live AI engineering workflow (optional)

The deterministic workflow API works without a model key, and provides a reproducible demonstration of approvals and state transitions. It **does not modify source code**.

The `/live/workflows` API uses an OpenAI-compatible chat completion API to analyze requirements, plan code changes, inspect a restricted source tree, generate proposed replacement files, request approval, run real Maven tests and documentation generation in parallel, and rollback changed files if validation fails. **Use only in a disposable development checkout.** Never point SOURCE_REPO at a production checkout or sensitive repository.

```bash
export LLM_API_KEY=your_key
export LLM_MODEL=gpt-4.1-mini
# optional: export LLM_BASE_URL=https://your-compatible-provider/v1
uvicorn app.main:app --reload --port 8000
```

Create live workflow:

```bash
curl -X POST http://localhost:8000/live/workflows -H 'Content-Type: application/json' -d '{"requirement":"Add an endpoint to list active URLs with pagination","scenario":"brownfield"}'
```

Read its `id` and status; approve each gate (or reject). Example:

```bash
curl -X POST http://localhost:8000/live/workflows/WORKFLOW_ID/decisions -H 'Content-Type: application/json' -d '{"action":"design","decision":"approve","notes":"Reviewed"}'
```

Next approve `change` only after reviewing the proposed file contents from GET `/workflows/WORKFLOW_ID`. The workflow runs real Maven tests, captures output, then pauses for `release` approval. A release approval means **reviewed and ready**, not deployed.

## Security / limits

This is a controlled **prototype**, not a hardened multi-tenant sandbox. It uses extension/path checks and restricted Maven invocation, but Maven plugins and generated Java code can execute arbitrary code during tests. Run inside an isolated container with no production secrets, minimal privileges and no access to internal services. The orchestrator does not perform real deployment, policy-as-code evaluation, vulnerability scanning, git merge or production database rollback. A human must review changes and test evidence.
