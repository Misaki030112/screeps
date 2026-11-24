#!/usr/bin/env python3
from pathlib import Path

D = Path("/workspace/screeps/state/_patrol_2026-11-24_0820")
OLD = "state/_patrol_2026-11-24_0820"
NEW = "state/_patrol_2026-11-24_0820"

for p in D.glob("*.py"):
    t = p.read_text()
    n = t.replace(OLD, NEW).replace(
        "/workspace/screeps/state/_patrol_2026-11-24_0820", str(D)
    )
    if n != t:
        p.write_text(n)
        print("path-updated", p.name)

p = D / "exact2h.py"
t = p.read_text()
repls = [
    (
        "LAST_TIP = 84441290  # previous 3h patrol analysis tip (20:35:06 Asia/Hong_Kong room_stats)",
        "LAST_TIP = 84443730  # previous 3h patrol analysis tip (23:28:56 Asia/Hong_Kong room_stats)",
    ),
    (
        "BF_LO, BF_HI = 84440401, 84443600  # first-pass official window this 3h, missing_chunks=3",
        "BF_LO, BF_HI = 84442901, 84446000  # first-pass official window this 3h (update after backfill)",
    ),
]
for a, b in repls:
    if a not in t:
        print("MISSING exact2h needle:", a)
    else:
        t = t.replace(a, b)
        print("replaced exact2h:", a[:50])
p.write_text(t)

p = D / "freeze_clock.py"
t = p.read_text()
repls = [
    (
        "Console silences and listener restarts since last 3h patrol (delivered 20:43:58).",
        "Console silences and listener restarts since last 3h patrol (delivered 23:33:16).",
    ),
    (
        "# last 3h patrol already told freezes through 20:14:37-20:28:31 and short gap 20:01:56.",
        "# last 3h patrol already told freezes through 22:59:15-23:05:47.",
    ),
    (
        "# Fold still-untold after that plus any newer than the 23:00 half-hour wrap.",
        "# Fold still-untold short gaps 00:34:41 and 01:02:38 plus any newer.",
    ),
    (
        "CUT = datetime(2026, 11, 23, 20, 28, 31, tzinfo=HK)",
        "CUT = datetime(2026, 11, 23, 23, 5, 47, tzinfo=HK)",
    ),
    (
        "DELIVERED = datetime(2026, 11, 23, 20, 43, 58, tzinfo=HK)",
        "DELIVERED = datetime(2026, 11, 23, 23, 33, 16, tzinfo=HK)",
    ),
    (
        'if fr >= "2026-11-23 17:27:43":',
        'if fr >= "2026-11-23 23:05:47":',
    ),
    (
        'if m and m.group(1) >= "2026-11-23 17:27:43"',
        'if m and m.group(1) >= "2026-11-23 23:05:47"',
    ),
    (
        "if t >= datetime(2026, 11, 23, 20, 0, tzinfo=HK):",
        "if t >= datetime(2026, 11, 23, 23, 0, tzinfo=HK):",
    ),
    (
        "=== box_pauses after 20:28:31 (already-told end) ===",
        "=== box_pauses after 23:05:47 (already-told end) ===",
    ),
    (
        "=== listener restarts after 20:28:31 ===",
        "=== listener restarts after 23:05:47 ===",
    ),
    (
        "=== console silences >=60s after 20:28:31 ===",
        "=== console silences >=60s after 23:05:47 ===",
    ),
    (
        "=== short console gaps 3-59s after 20:28:31 (possible WS) ===",
        "=== short console gaps 3-59s after 23:05:47 (possible WS) ===",
    ),
]
for a, b in repls:
    if a not in t:
        print("MISSING freeze_clock needle:", a)
    else:
        t = t.replace(a, b)
        print("replaced freeze_clock:", a[:70])
p.write_text(t)
print("done")
