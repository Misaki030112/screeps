#!/usr/bin/env python3
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import subprocess, shutil

d = Path("/workspace/screeps/state/_halfhour_2026-11-26_1100")
hk = ZoneInfo("Asia/Hong_Kong")

def stamp(step, kind):
    now = datetime.now(hk)
    d.joinpath(f"{step}_{kind}.txt").write_text(str(int(now.timestamp())) + "\n")
    d.joinpath(f"{step}_{kind}_human.txt").write_text(now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong") + "\n")
    print(now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), step, kind, flush=True)

stamp("just_published", "start")
out = open(d / "backfill_just_published.txt", "w")
err = open(d / "backfill_just_published.err", "w")
proc = subprocess.run(
    [".venv/bin/python", str(d / "backfill_just_published.py")],
    cwd="/workspace/screeps",
    stdout=out,
    stderr=err,
)
out.close(); err.close()
(d / "just_published.exit").write_text(str(proc.returncode) + "\n")
for src in sorted(d.glob("just_published_[0-9]*.json")):
    if src.name.endswith("_first.json"):
        continue
    dest = d / (src.stem + "_first.json")
    if not dest.exists():
        shutil.copyfile(src, dest)
stamp("just_published", "done")
print("exit", proc.returncode, flush=True)
