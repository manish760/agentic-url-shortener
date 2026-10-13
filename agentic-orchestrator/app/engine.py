"""Auditable, bounded orchestration prototype. Agents are deterministic by default.
An LLM can be added behind the same interfaces; no untrusted model text is executed.
"""
import json, os, re, sqlite3, time, uuid
from pathlib import Path
from threading import RLock

ROOT=Path(os.getenv('WORKSPACE_ROOT',str(Path(__file__).resolve().parents[2]/'workspace'))).resolve()
ROOT.mkdir(parents=True,exist_ok=True)
DB=ROOT/'workflows.sqlite3'
LOCK=RLock()
STAGES=['REQUIREMENTS','PLANNING','ARCHITECTURE','IMPLEMENTATION','TESTING','DOCUMENTATION','REVIEW']
GRAPH={'REQUIREMENTS':[], 'PLANNING':['REQUIREMENTS'], 'ARCHITECTURE':['PLANNING'],
       'IMPLEMENTATION':['ARCHITECTURE'], 'TESTING':['IMPLEMENTATION'],
       'DOCUMENTATION':['IMPLEMENTATION'], 'REVIEW':['TESTING','DOCUMENTATION']}

def connection():
 c=sqlite3.connect(DB);c.row_factory=sqlite3.Row
 c.execute('CREATE TABLE IF NOT EXISTS workflows (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
 return c

def store(w):
 w['updated_at']=time.time()
 with LOCK, connection() as c:c.execute('INSERT OR REPLACE INTO workflows VALUES (?,?)',(w['id'],json.dumps(w)))
 return w

def load(workflow_id):
 with LOCK, connection() as c:r=c.execute('SELECT payload FROM workflows WHERE id=?',(workflow_id,)).fetchone()
 if not r:raise KeyError('Unknown workflow')
 return json.loads(r['payload'])

def event(w,kind,detail):w['events'].append({'time':time.time(),'type':kind,'detail':detail})

def create(requirement,scenario):
 if not isinstance(requirement,str) or not 5<=len(requirement)<=3000:raise ValueError('Requirement must be 5-3000 characters')
 if scenario not in ('greenfield','brownfield','ambiguous'):raise ValueError('Invalid scenario')
 w={'id':str(uuid.uuid4()),'requirement':requirement,'scenario':scenario,'status':'CREATED',
    'completed':[],'artifacts':{},'events':[],'retry_count':0,'max_retries':2,
    'approval':None,'created_at':time.time(),'updated_at':time.time(),'graph':GRAPH,
    'metrics':{'test_attempts':0,'rollbacks':0},'decisions':[]}
 event(w,'created',scenario);return store(w)

def artifact(w,name,content):
 folder=ROOT/w['id'];folder.mkdir(parents=True,exist_ok=True)
 safe=re.sub('[^a-z0-9_-]','',name.lower())+'.md'
 target=(folder/safe).resolve()
 if target.parent!=folder.resolve():raise ValueError('Unsafe path')
 target.write_text(content,encoding='utf-8');w['artifacts'][name]=str(target.relative_to(ROOT))

def execute_stage(w,stage):
 if stage=='REQUIREMENTS':
  ambiguous=w['scenario']=='ambiguous' or bool(re.search(r'\b(better|faster|secure|improve)\b',w['requirement'],re.I))
  artifact(w,'requirements',f"# Normalized requirement\n\n{w['requirement']}\n\nScenario: {w['scenario']}\n\nAcceptance: document behavior, validate APIs, record test evidence.\n")
  if ambiguous and not w.get('clarified'):
   w['status']='WAITING_CLARIFICATION';event(w,'gate','Clarification required: specify measurable acceptance criteria');return False
 elif stage=='PLANNING':
  artifact(w,'plan','# Task dependency graph\n\n'+ '\n'.join(f'- {k}: depends on {", ".join(v) or "none"}' for k,v in GRAPH.items()))
 elif stage=='ARCHITECTURE':
  artifact(w,'architecture',f"# Impact analysis\n\nScenario: {w['scenario']}\n\nReview controller, service, repository, entity, tests, and API compatibility.\n\nRisk: changing persisted schemas requires human approval.\n")
  if not w.get('design_approved'):
   w['status']='WAITING_APPROVAL';event(w,'gate','Design approval required before implementation');return False
 elif stage=='IMPLEMENTATION':
  # Intentionally generate a reviewable proposal rather than execute arbitrary LLM-authored code.
  artifact(w,'change-proposal',f"# Proposed engineering change\n\nRequirement: {w['requirement']}\n\n1. Review API and persistence changes.\n2. Implement on an isolated Git branch.\n3. Add unit and integration tests.\n4. Require review before merge.\n\nNo source files were modified automatically in this demo.\n")
 elif stage=='TESTING':
  w['metrics']['test_attempts']+=1
  # deterministic validation of generated artifacts and task dependencies; not a Java build
  valid=all(x in w['artifacts'] for x in ('requirements','plan','architecture','change-proposal'))
  artifact(w,'validation',f"# Workflow validation\n\nArtifact checks: {'PASS' if valid else 'FAIL'}\n\nNote: Java Maven tests must be run separately.\n")
  if not valid:
   w['retry_count']+=1;event(w,'retry','Missing artifacts')
   if w['retry_count']>w['max_retries']:
    w['status']='STOPPED';return False
   w['completed']=[x for x in w['completed'] if x not in ('IMPLEMENTATION','TESTING')]
   return False
 elif stage=='DOCUMENTATION':
  artifact(w,'documentation',f"# Release notes\n\n{w['requirement']}\n\nSee validation.md and change-proposal.md.\n")
 elif stage=='REVIEW':
  if not w.get('release_approved'):
   w['status']='WAITING_RELEASE_APPROVAL';event(w,'gate','Final human approval required');return False
  artifact(w,'summary','# Final summary\n\nWorkflow proposal reviewed and approved.\n\nThis is not evidence of an actual deployment.\n')
 w['completed'].append(stage);event(w,'completed',stage);return True

def advance(workflow_id):
 with LOCK:
  w=load(workflow_id)
  if w['status'] in ('COMPLETED','STOPPED'):return w
  w['status']='RUNNING'
  for stage in STAGES:
   if stage in w['completed']:continue
   if not all(dep in w['completed'] for dep in GRAPH[stage]):break
   if not execute_stage(w,stage):break
  else:w['status']='COMPLETED';event(w,'completed','workflow')
  return store(w)

def approve(workflow_id,action,decision,notes=''):
 if action not in ('clarification','design','release') or decision not in ('approve','reject'):raise ValueError('Invalid approval action')
 w=load(workflow_id)
 expected={'clarification':'WAITING_CLARIFICATION','design':'WAITING_APPROVAL','release':'WAITING_RELEASE_APPROVAL'}[action]
 if w['status']!=expected:raise ValueError('No matching pending approval')
 w['decisions'].append({'action':action,'decision':decision,'notes':notes,'time':time.time()})
 event(w,'human_decision',f'{action}: {decision}')
 if decision=='reject':w['status']='STOPPED';event(w,'safe_stop','Rejected by human');return store(w)
 if action=='clarification':
  if len(notes.strip())<10:raise ValueError('Clarification needs at least 10 characters')
  w['clarified']=notes;artifact(w,'clarification','# Human clarification\n\n'+notes)
 elif action=='design':w['design_approved']=True
 else:w['release_approved']=True
 store(w);return advance(workflow_id)

def stop(workflow_id):
 w=load(workflow_id)
 if w['status']!='COMPLETED':w['status']='STOPPED';event(w,'safe_stop','Stopped by user')
 return store(w)

def metrics(w):
 return {'workflow_id':w['id'],'status':w['status'],'latency_seconds':round(w['updated_at']-w['created_at'],3),
         'retry_count':w['retry_count'],'rollback_count':w['metrics']['rollbacks'],
         'completed_stages':len(w['completed']),'total_stages':len(STAGES)}
