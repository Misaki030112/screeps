#!/usr/bin/env python3
from pathlib import Path

print("----- model_1h key -----")
for line in Path("state/_patrol_2026-11-20_1923/model_1h.txt").read_text().splitlines():
    if any(k in line.lower() for k in ("upgrade", "storage", "alloc", "income", "overhead", "ideal", "harvest", "waste", "delivered", "spawn", "e/t", "window", "rcl", "cpu", "idle")):
        print(line)

print("\n----- official_retry key -----")
for line in Path("state/_patrol_2026-11-20_1923/official_retry.out").read_text().splitlines():
    if any(k in line for k in ("game.time", "404", "200", "retry", "just-pub", "just_pub", "IN_WINDOW", "LEFTOVER", "pre ", "post ", "hour-window", "STATS", "fill ", "wrote", "inserted", "empty", "skip", "distinct", "status=")):
        print(line)

print("\n----- audit full -----")
print(Path("state/_patrol_2026-11-20_1923/audit_patrol.txt").read_text())

print("\n----- motion 1h -----")
print(Path("state/_patrol_2026-11-20_1923/motion_1h.txt").read_text())
