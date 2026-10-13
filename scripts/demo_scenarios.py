"""Offline scenario demonstration using FastAPI test client. Run from orchestrator directory with PYTHONPATH=."""
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
for scenario,requirement in [
    ("greenfield","Build a URL shortener with redirects and click analytics"),
    ("brownfield","Add URL expiration behavior to the existing URL shortener"),
    ("ambiguous","Make the URL shortener more secure")]:
    response=client.post("/workflows",json={"requirement":requirement,"scenario":scenario})
    response.raise_for_status();id=response.json()["id"]
    current=client.post(f"/workflows/{id}/run").json()
    while current["status"].startswith("WAITING"):
        action={"WAITING_CLARIFICATION":"clarification","WAITING_APPROVAL":"design","WAITING_RELEASE_APPROVAL":"release"}[current["status"]]
        current=client.post(f"/workflows/{id}/decisions",json={"action":action,"decision":"approve","notes":"Use HTTP(S) URL validation, error handling, test coverage and documented acceptance criteria"}).json()
    print(scenario, current["status"], client.get(f"/workflows/{id}/metrics").json())
