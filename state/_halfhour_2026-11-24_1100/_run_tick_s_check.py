#!/usr/bin/env python3
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import subprocess

d = Path("/workspace/screeps/state/_halfhour_2026-11-24_1100")
hk = ZoneInfo("Asia/Hong_Kong")

def stamp(step, kind):
    now = datetime.now(hk)
    d.joinpath(f"{step}_{kind}.txt").write_text(str(int(now.timestamp())) + "\n")
    d.joinpath(f"{step}_{kind}_human.txt").write_text(now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong") + "\n")
    print(now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), step, kind, flush=True)

stamp("tick_s_check", "start")
out = open(d / "tick_s_check.txt", "w")
err = open(d / "tick_s_check.err", "w")
proc = subprocess.run(
    [".venv/bin/python", str(d / "tick_s_check.py")],
    cwd="/workspace/screeps",
    stdout=out,
    stderr=err,
)
out.close(); err.close()
(d / "tick_s_check.exit").write_text(str(proc.returncode) + "\n")
stamp("tick_s_check", "done")
print("exit", proc.returncode, flush=True)
