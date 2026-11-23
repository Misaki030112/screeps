#!/usr/bin/env python3
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import subprocess, sys

d = Path("/workspace/screeps/state/_halfhour_2026-11-23_2330")
hk = ZoneInfo("Asia/Hong_Kong")
now = datetime.now(hk)
epoch = str(int(now.timestamp())) + "\n"
human = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong") + "\n"
d.joinpath("started_at.txt").write_text(epoch)
d.joinpath("started_at.epoch.txt").write_text(epoch)
d.joinpath("started_at_human.txt").write_text(human)
print("started_at", human.strip())

def stamp(step, kind):
    now = datetime.now(hk)
    d.joinpath(f"{step}_{kind}.txt").write_text(str(int(now.timestamp())) + "\n")
    d.joinpath(f"{step}_{kind}_human.txt").write_text(now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong") + "\n")
    print(now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), step, kind)

stamp("pre_run", "start")
proc = subprocess.run(
    [".venv/bin/python", str(d / "pre_run.py")],
    cwd="/workspace/screeps",
    stdout=open(d / "pre_run.txt", "w"),
    stderr=open(d / "pre_run.err", "w"),
)
(d / "pre_run.exit").write_text(str(proc.returncode) + "\n")
stamp("pre_run", "done")
print("exit", proc.returncode)
