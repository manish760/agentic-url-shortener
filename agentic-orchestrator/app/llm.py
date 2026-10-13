"""Optional OpenAI-compatible LLM integration. Never execute returned text directly."""
import json, os, urllib.request

def complete(system: str, user: str) -> str:
    key=os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("LLM_API_KEY is required for live agent execution")
    base=os.getenv("LLM_BASE_URL","https://api.openai.com/v1").rstrip("/")
    if not base.startswith("https://") and not (base.startswith("http://localhost:") or base.startswith("http://127.0.0.1:")):
        raise ValueError("LLM_BASE_URL must use HTTPS (or localhost for development)")
    payload=json.dumps({"model":os.getenv("LLM_MODEL","gpt-4.1-mini"),"temperature":0,"messages":[{"role":"system","content":system},{"role":"user","content":user}]}).encode()
    req=urllib.request.Request(base+"/chat/completions",payload,headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=45) as resp:
        data=json.load(resp)
    return data["choices"][0]["message"]["content"]

def json_response(system,user):
    raw=complete(system+" Respond with a single valid JSON object; no markdown fences.",user).strip()
    if raw.startswith("```"):
        raw=raw.split("\n",1)[1].rsplit("```",1)[0].strip()
    result=json.loads(raw)
    if not isinstance(result,dict):raise ValueError("Expected JSON object")
    return result
