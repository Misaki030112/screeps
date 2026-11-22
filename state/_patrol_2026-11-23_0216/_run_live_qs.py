#!/usr/bin/env python3
import subprocess, sys
from pathlib import Path
D = Path("/workspace/screeps/state/_patrol_2026-11-23_0216")
scripts = ["q_live1.py", "q_live2.py", "q_live3.py", "q_extra.py", "q_threat.py"]
for name in scripts:
    p = D / name
    if not p.exists():
        print("SKIP missing", name)
        continue
    print("-----", name, "-----", flush=True)
    out = D / (p.stem + ".txt")
    err = D / (p.stem + ".err")
    r = subprocess.run(
        ["/workspace/screeps/.venv/bin/python", str(p)],
        cwd="/workspace/screeps",
        capture_output=True,
        text=True,
        timeout=180,
    )
    out.write_text(r.stdout)
    err.write_text(r.stderr)
    print("rc", r.returncode)
    print(r.stdout[-4000:] if r.stdout else "")
    if r.stderr:
        print("ERR", r.stderr[-2000:])
