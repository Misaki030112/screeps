#!/usr/bin/env python3
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import subprocess, time

d = Path("/workspace/screeps/state/_halfhour_2026-11-24_1400")
hk = ZoneInfo("Asia/Hong_Kong")
py = "/workspace/screeps/.venv/bin/python"

def stamp(step, kind):
    now = datetime.now(hk)
    d.joinpath(f"{step}_{kind}.txt").write_text(str(int(now.timestamp())) + "\n")
    d.joinpath(f"{step}_{kind}_human.txt").write_text(now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong") + "\n")
    print(now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), step, kind, flush=True)

def run(step, args, out_name, err_name, exit_name):
    stamp(step, "start")
    out = open(d / out_name, "w")
    err = open(d / err_name, "w")
    proc = subprocess.run(args, cwd="/workspace/screeps", stdout=out, stderr=err)
    out.close(); err.close()
    (d / exit_name).write_text(str(proc.returncode) + "\n")
    stamp(step, "done")
    print("exit", step, proc.returncode, flush=True)
    return proc.returncode

c1 = run("backfill_confirm", [py, str(d / "backfill_confirm.py"), "confirm"],
         "backfill_confirm.txt", "backfill_confirm.err", "backfill_confirm.exit")
time.sleep(20)
c2 = run("backfill_retry2", [py, str(d / "backfill_confirm.py"), "retry2"],
         "backfill_retry2.txt", "backfill_retry2.err", "backfill_retry2.exit")
time.sleep(15)
c3 = run("backfill_late_retry", [py, str(d / "backfill_late_retry.py")],
         "backfill_late_retry.txt", "backfill_late_retry.err", "backfill_late_retry.exit")
print("all_exits", c1, c2, c3, flush=True)
