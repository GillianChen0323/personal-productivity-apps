import json, os, time, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent/'progress-store'
def read():
 p=ROOT/'current.json'
 return json.loads(p.read_text()) if p.exists() else None
def revision(data):
 return hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False).encode()).hexdigest() if data else 'none'
def write(data,expected):
 current=read()
 if expected!=revision(current):raise ValueError('stale')
 if current and current.get('done') and not data.get('done'):raise ValueError('empty')
 ROOT.mkdir(exist_ok=True)
 if current:
  archive=ROOT/'history';archive.mkdir(exist_ok=True)
  (archive/(str(time.time_ns())+'.json')).write_text(json.dumps(current,ensure_ascii=False))
 tmp=ROOT/'pending.tmp';tmp.write_text(json.dumps(data,ensure_ascii=False));os.replace(tmp,ROOT/'current.json')
 return revision(data)
