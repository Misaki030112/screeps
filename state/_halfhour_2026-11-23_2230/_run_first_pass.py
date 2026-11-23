#!/usr/bin/env python3
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import subprocess, shutil

d = Path("/workspace/screeps/state/_halfhour_2026-11-23_2230")
hk = ZoneInfo("Asia/Hong_Kong")

def stamp(step, kind):
    now = datetime.now(hk)
    d.joinpath(f"{step}_{kind}.txt").write_text(str(int(now.timestamp())) + "\n")
    d.joinpath(f"{step}_{kind}_human.txt").write_text(now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong") + "\n")
    print(now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), step, kind, flush=True)

stamp("history_backfill", "start")
out = open(d / "history_backfill_first_attempt.txt", "w")
err = open(d / "history_backfill_first_attempt.err", "w")
proc = subprocess.run(
    [".venv/bin/python", "tools/history_backfill.py", "--minutes", "40"],
    cwd="/workspace/screeps",
    stdout=out,
    stderr=err,
)
out.close(); err.close()
(d / "history_backfill_first_attempt.exit").write_text(str(proc.returncode) + "\n")
shutil.copyfile(d / "history_backfill_first_attempt.txt", d / "history_backfill.txt")
shutil.copyfile(d / "history_backfill_first_attempt.err", d / "history_backfill.err")
(d / "history_backfill.exit").write_text(str(proc.returncode) + "\n")
stamp("history_backfill", "done")
print("exit", proc.returncode, flush=True)
