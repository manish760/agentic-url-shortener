"""Real opt-in agent execution with review gates, parallel validation and bounded recovery.
This is a controlled prototype, not a production-grade autonomous deployment system.
"""
import concurrent.futures, json, os, time
from . import engine, llm, workspace

SYSTEM="You are a senior software engineer. Respect requirements, safety, testability, backward compatibility. Never output secrets."

def _record(w,kind,detail):
    engine.event(w,kind,detail)
    engine.store(w)

def _generate(w,role,request):
    result=llm.json_response(SYSTEM+" Your role: "+role,request)
    _record(w,"agent_output",{"role":role,"keys":list(result.keys())})
    return result

def _plan(w):
    r=_generate(w,"Requirements",json.dumps({"requirement":w["requirement"],"scenario":w["scenario"],"instruction":"Return JSON with acceptance_criteria array, ambiguities array, risk_level string"}))
    w["analysis"]=r
    if r.get("ambiguities") and not w.get("clarification"):
        w["status"]="WAITING_CLARIFICATION";_record(w,"approval_required","Clarify ambiguous requirement");return False
    files=workspace.inspect()
    plan=_generate(w,"Architecture and Planning",json.dumps({"requirement":w["requirement"],"acceptance":r.get("acceptance_criteria"),"available_files":files,"instruction":"Return JSON with tasks array, impacted_files array, design string, risks array"}))
    w["plan"]=plan;w["status"]="WAITING_APPROVAL";_record(w,"approval_required","Approve plan and file changes before implementation");return False

def _propose(w):
    impacted=w["plan"].get("impacted_files",[])[:10]
    sources={}
    for name in impacted:
        try:sources[name]=workspace.read(name)
        except (ValueError,FileNotFoundError):pass
    proposal=_generate(w,"Coding",json.dumps({"requirement":w["requirement"],"plan":w["plan"],"source_files":sources,"instruction":"Return JSON with changes array of {path,content}, each content is the entire replacement file. Keep changes small, preserve compatibility, include tests where possible."}))
    changes=proposal.get("changes",[])
    # Validate every path before writing any file.
    for item in changes:workspace.file_path(item["path"])
    w["proposed_changes"]=changes;w["status"]="WAITING_CHANGE_APPROVAL";_record(w,"approval_required",{"change_count":len(changes),"files":[c["path"] for c in changes]})

def _validate(w):
    w["status"]="VALIDATING";_record(w,"stage","parallel testing and documentation")
    def docs():
        return _generate(w,"Documentation",json.dumps({"requirement":w["requirement"],"plan":w["plan"],"instruction":"Return JSON with summary, setup, risks, limitations strings"}))
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        tf=pool.submit(workspace.run_tests)
        df=pool.submit(docs)
        tests=tf.result();documentation=df.result()
    w["validation"]=tests;w["documentation"]=documentation
    w["metrics"]["test_attempts"]+=1
    _record(w,"validation",{"passed":tests["passed"],"test_attempts":w["metrics"]["test_attempts"]})
    if tests["passed"]:
        w["status"]="WAITING_RELEASE_APPROVAL";_record(w,"approval_required","Review successful tests and final diff");return
    if w["retry_count"]>=w["max_retries"]:
        _rollback(w);w["status"]="STOPPED";_record(w,"safe_stop","Test failure; retry budget exhausted");return
    w["retry_count"]+=1
    _rollback(w)
    w["plan"]["test_feedback"]=tests.get("output",tests.get("error",""))[-3000:]
    w["status"]="REPLANNING";_record(w,"replan",{"retry":w["retry_count"]})
    _propose(w)

def _rollback(w):
    backups=w.pop("_backups",{})
    if backups:
        workspace.rollback({k:(bytes.fromhex(v) if v is not None else None) for k,v in backups.items()})
        w["metrics"]["rollbacks"]+=1
        _record(w,"rollback","Restored files from pre-change snapshots")

def start(requirement,scenario):
    if not (os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")):
        raise ValueError("Configure LLM_API_KEY or OPENAI_API_KEY to run live agents")
    w=engine.create(requirement,scenario)
    w["mode"]="live";engine.store(w)
    try:_plan(w)
    except Exception as exc:w["status"]="STOPPED";_record(w,"error",str(exc))
    return engine.store(w)

def decide(wid,action,decision,notes=""):
    w=engine.load(wid)
    if w.get("mode")!="live":raise ValueError("Not a live workflow")
    allowed={"clarification":"WAITING_CLARIFICATION","design":"WAITING_APPROVAL","change":"WAITING_CHANGE_APPROVAL","release":"WAITING_RELEASE_APPROVAL"}
    if action not in allowed or w["status"]!=allowed[action]:raise ValueError("No matching pending approval")
    if decision not in ("approve","reject"):raise ValueError("Decision must be approve/reject")
    _record(w,"human_decision",{"action":action,"decision":decision,"notes":notes})
    if decision=="reject":
        _rollback(w);w["status"]="STOPPED";return engine.store(w)
    try:
        if action=="clarification":
            if len(notes.strip())<10:raise ValueError("Please provide specific acceptance criteria")
            w["clarification"]=notes;w["requirement"]+="\nClarification: "+notes
            _plan(w)
        elif action=="design":_propose(w)
        elif action=="change":
            originals=workspace.apply_changes(w["proposed_changes"])
            w["_backups"]={k:(v.hex() if v is not None else None) for k,v in originals.items()}
            _record(w,"source_modified",[c["path"] for c in w["proposed_changes"]])
            _validate(w)
        else:
            w.pop("_backups",None);w["status"]="COMPLETED";_record(w,"completed","Release-ready, not deployed")
    except Exception as exc:
        _rollback(w);w["status"]="STOPPED";_record(w,"error",str(exc))
    return engine.store(w)

def stop(wid):
    w=engine.load(wid)
    if w.get("mode")!="live":raise ValueError("Not a live workflow")
    if w["status"]!="COMPLETED":_rollback(w);w["status"]="STOPPED";_record(w,"safe_stop","User stopped workflow")
    return engine.store(w)
