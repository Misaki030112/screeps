#!/usr/bin/env python3
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import subprocess

d = Path("/workspace/screeps/state/_halfhour_2026-11-24_0900")
hk = ZoneInfo("Asia/Hong_Kong")

def stamp(step, kind):
    now = datetime.now(hk)
    d.joinpath(f"{step}_{kind}.txt").write_text(str(int(now.timestamp())) + "\n")
    d.joinpath(f"{step}_{kind}_human.txt").write_text(
        now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong") + "\n"
    )
    print(now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), step, kind, flush=True)

stamp("backfill_postjp", "start")
out = open(d / "backfill_postjp_retry.txt", "w")
err = open(d / "backfill_postjp_retry.err", "w")
proc = subprocess.run(
    [".venv/bin/python", str(d / "backfill_postjp_retry.py")],
    cwd="/workspace/screeps",
    stdout=out,
    stderr=err,
)
out.close()
err.close()
(d / "backfill_postjp_retry.exit").write_text(str(proc.returncode) + "\n")
stamp("backfill_postjp", "done")
print("exit", proc.returncode, flush=True)
