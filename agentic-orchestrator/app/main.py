from fastapi import FastAPI,HTTPException
from pydantic import BaseModel,Field
from . import engine
app=FastAPI(title='Agentic Engineering Orchestrator',version='0.1.0')
class NewWorkflow(BaseModel):
 requirement:str=Field(min_length=5,max_length=3000)
 scenario:str='greenfield'
class Decision(BaseModel):
 action:str
 decision:str
 notes:str=''
def safe_call(fn,*args):
 try:return fn(*args)
 except KeyError as e:raise HTTPException(404,str(e)) from e
 except ValueError as e:raise HTTPException(400,str(e)) from e
@app.get('/health')
def health():return {'status':'UP'}
@app.post('/workflows',status_code=201)
def create(body:NewWorkflow):return safe_call(engine.create,body.requirement,body.scenario)
@app.post('/workflows/{workflow_id}/run')
def run(workflow_id:str):return safe_call(engine.advance,workflow_id)
@app.get('/workflows/{workflow_id}')
def get(workflow_id:str):return safe_call(engine.load,workflow_id)
@app.get('/workflows/{workflow_id}/metrics')
def metrics(workflow_id:str):return engine.metrics(safe_call(engine.load,workflow_id))
@app.post('/workflows/{workflow_id}/decisions')
def decide(workflow_id:str,body:Decision):return safe_call(engine.approve,workflow_id,body.action,body.decision,body.notes)
@app.post('/workflows/{workflow_id}/stop')
def stop(workflow_id:str):return safe_call(engine.stop,workflow_id)


# Live LLM-backed workflow endpoints. The deterministic /workflows API remains available for offline demonstrations.
from . import advanced
@app.post('/live/workflows',status_code=201)
def live_create(body:NewWorkflow):return safe_call(advanced.start,body.requirement,body.scenario)
@app.post('/live/workflows/{workflow_id}/decisions')
def live_decide(workflow_id:str,body:Decision):return safe_call(advanced.decide,workflow_id,body.action,body.decision,body.notes)
@app.post('/live/workflows/{workflow_id}/stop')
def live_stop(workflow_id:str):return safe_call(advanced.stop,workflow_id)
