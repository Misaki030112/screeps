#!/usr/bin/env python3
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import subprocess, json

d = Path("/workspace/screeps/state/_halfhour_2026-11-23_2230")
hk = ZoneInfo("Asia/Hong_Kong")
py = "/workspace/screeps/.venv/bin/python"

def stamp(step, kind):
    now = datetime.now(hk)
    d.joinpath(f"{step}_{kind}.txt").write_text(str(int(now.timestamp())) + "\n")
    d.joinpath(f"{step}_{kind}_human.txt").write_text(now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong") + "\n")
    print(now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), step, kind, flush=True)

# skip JP retry
now = datetime.now(hk)
(d / "just_published_retry_skipped.txt").write_text(
    f"skipped JP retry/retry2 at {now.strftime('%Y-%m-%d %H:%M:%S Asia/Hong_Kong')}: all_five_200, no JP-base 404s\n"
)
print("wrote skip retry", flush=True)

# postjp leftover retry
stamp("backfill_postjp_retry", "start")
out = open(d / "backfill_postjp_retry.txt", "w")
err = open(d / "backfill_postjp_retry.err", "w")
proc = subprocess.run([py, str(d / "backfill_postjp_retry.py")], cwd="/workspace/screeps", stdout=out, stderr=err)
out.close(); err.close()
(d / "backfill_postjp_retry.exit").write_text(str(proc.returncode) + "\n")
stamp("backfill_postjp_retry", "done")
print("postjp exit", proc.returncode, flush=True)

# patch and run post counts
pc = d / "_jp_post_counts.py"
t = pc.read_text()
t = t.replace("base = 84442500", "base = 84443000", 1)
old = 'script = {"W46N8": 561, "W47N8": 1429, "W45N8": 322, "W45N7": 342, "W47N7": 424}'
new = 'script = {"W46N8": 1019, "W47N8": 280, "W45N8": 355, "W45N7": 248, "W47N7": 448}'
if old not in t:
    raise SystemExit("script counts not found in _jp_post_counts.py")
pc.write_text(t.replace(old, new, 1))
out = open(d / "just_published_post_counts_run.txt", "w")
err = open(d / "just_published_post_counts.err", "w")
proc = subprocess.run([py, str(pc)], cwd="/workspace/screeps", stdout=out, stderr=err)
out.close(); err.close()
print("post_counts exit", proc.returncode, flush=True)

# coverage (run + final, same as 2200)
for step, outn in (("coverage_run", "coverage_run.txt"), ("coverage_final", "coverage_final.txt")):
    stamp(step, "start")
    out = open(d / outn, "w")
    err = open(d / (step + ".err"), "w")
    proc = subprocess.run([py, str(d / "coverage.py")], cwd="/workspace/screeps", stdout=out, stderr=err)
    out.close(); err.close()
    (d / (step + ".exit")).write_text(str(proc.returncode) + "\n")
    # coverage.py also writes coverage_run.json? check - we'll copy if needed
    stamp(step, "done")
    print(step, "exit", proc.returncode, flush=True)

# wrapup snap
stamp("wrapup_snap", "start")
out = open(d / "wrapup_snap.txt", "w")
err = open(d / "wrapup_snap.err", "w")
proc = subprocess.run([py, str(d / "wrapup_snap.py")], cwd="/workspace/screeps", stdout=out, stderr=err)
out.close(); err.close()
(d / "wrapup_snap.exit").write_text(str(proc.returncode) + "\n")
stamp("wrapup_snap", "done")
print("wrapup_snap exit", proc.returncode, flush=True)
