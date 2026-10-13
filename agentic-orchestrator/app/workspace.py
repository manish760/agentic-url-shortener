"""Constrained source inspection, patch proposal, build and rollback tooling."""
import os, subprocess, shutil
from pathlib import Path

REPO=Path(os.getenv("SOURCE_REPO",str(Path(__file__).resolve().parents[2]/"url-shortener-service"))).resolve()
ALLOWED={".java",".xml",".yml",".yaml",".md",".properties"}
MAX_BYTES=150_000

def file_path(relative):
    if not isinstance(relative,str) or relative.startswith("/") or "\\" in relative:raise ValueError("Unsafe path")
    target=(REPO/relative).resolve()
    if not target.is_relative_to(REPO) or target.suffix not in ALLOWED or any(s in relative.lower() for s in ("secret","password","credential",".env")):
        raise ValueError("File not permitted")
    return target

def inspect(max_files=40):
    result=[]
    for f in sorted(REPO.rglob("*")):
        if f.is_file() and f.suffix in ALLOWED and not any(x in f.parts for x in ("target",".git","build")) and f.stat().st_size<=MAX_BYTES:
            result.append(str(f.relative_to(REPO)))
        if len(result)>=max_files:break
    return result

def read(relative):
    f=file_path(relative)
    if f.stat().st_size>MAX_BYTES:raise ValueError("File too large")
    return f.read_text(encoding="utf-8")

def apply_changes(changes):
    if not isinstance(changes,list) or not 1<=len(changes)<=8:raise ValueError("Expected 1-8 changes")
    verified=[]
    for item in changes:
        f=file_path(item["path"])
        content=item["content"]
        if not isinstance(content,str) or len(content.encode())>MAX_BYTES:raise ValueError("Oversized content")
        verified.append((f,content))
    originals={str(f):(f.read_bytes() if f.exists() else None) for f,_ in verified}
    try:
        for f,content in verified:
            f.parent.mkdir(parents=True,exist_ok=True)
            f.write_text(content,encoding="utf-8")
    except Exception:
        rollback(originals)
        raise
    return originals

def rollback(originals):
    for name,contents in originals.items():
        f=Path(name)
        if contents is None:f.unlink(missing_ok=True)
        else:f.write_bytes(contents)

def run_tests(timeout=180):
    mvn=shutil.which("mvn")
    if not mvn:return {"passed":False,"error":"Maven not installed","output":""}
    try:
        p=subprocess.run([mvn,"-B","test"],cwd=REPO,capture_output=True,text=True,timeout=timeout,env={**os.environ,"MAVEN_OPTS":"-Xmx512m"})
        return {"passed":p.returncode==0,"exit_code":p.returncode,"output":(p.stdout+"\n"+p.stderr)[-12000:]}
    except subprocess.TimeoutExpired:return {"passed":False,"error":"Test timeout","output":""}
