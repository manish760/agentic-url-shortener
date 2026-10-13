import os, tempfile, importlib
from pathlib import Path

def test_human_gates_and_completion(monkeypatch):
 with tempfile.TemporaryDirectory() as tmp:
  monkeypatch.setenv('WORKSPACE_ROOT',tmp)
  from app import engine
  importlib.reload(engine)
  w=engine.create('Build a URL shortener','greenfield')
  w=engine.advance(w['id'])
  assert w['status']=='WAITING_APPROVAL'
  assert w['completed']==['REQUIREMENTS','PLANNING']
  w=engine.approve(w['id'],'design','approve')
  assert w['status']=='WAITING_RELEASE_APPROVAL'
  assert 'TESTING' in w['completed'] and 'DOCUMENTATION' in w['completed']
  w=engine.approve(w['id'],'release','approve')
  assert w['status']=='COMPLETED'

def test_ambiguous_requires_clarification(monkeypatch):
 with tempfile.TemporaryDirectory() as tmp:
  monkeypatch.setenv('WORKSPACE_ROOT',tmp)
  from app import engine
  importlib.reload(engine)
  w=engine.create('Make the service more secure','ambiguous')
  w=engine.advance(w['id'])
  assert w['status']=='WAITING_CLARIFICATION'
  w=engine.approve(w['id'],'clarification','approve','Reject non-http URLs and add rate limiting')
  assert w['status']=='WAITING_APPROVAL'

def test_rejection_safe_stops(monkeypatch):
 with tempfile.TemporaryDirectory() as tmp:
  monkeypatch.setenv('WORKSPACE_ROOT',tmp)
  from app import engine
  importlib.reload(engine)
  w=engine.create('Add URL expiration to existing service','brownfield')
  w=engine.advance(w['id'])
  w=engine.approve(w['id'],'design','reject','Need schema review')
  assert w['status']=='STOPPED'
