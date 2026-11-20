#!/usr/bin/env python3
import sys, json, time
from pathlib import Path
sys.path.insert(0, "/workspace/screeps/tools")
import db, history_backfill as hb

c = db.connect()

print("=== events since 84377350 ===")
cols = c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='events' ORDER BY ordinal_position").fetchall()
print("event cols", [x[0] for x in cols])
rows = c.execute("SELECT * FROM events WHERE tick>=84377350 ORDER BY tick LIMIT 80").fetchall()
print("n", len(rows))
for r in rows:
    print(str(r)[:400])

print("=== defenders creep traces ===")
rows = c.execute("""
SELECT creep, role, min(tick), max(tick), count(*),
       (array_agg(room ORDER BY tick))[1] as first_room,
       (array_agg(room ORDER BY tick DESC))[1] as last_room,
       (array_agg(x ORDER BY tick DESC))[1],
       (array_agg(y ORDER BY tick DESC))[1],
       max(hits)
FROM creep_ticks
WHERE tick>=84377350 AND (role ILIKE '%def%' OR creep ILIKE '%def%' OR creep ILIKE '%guard%')
GROUP BY creep, role
ORDER BY min(tick)
""").fetchall()
for r in rows:
    print(r)

print("=== W45N7 names 84377800..now ===")
rows = c.execute("""
SELECT creep, role, min(tick), max(tick), count(*)
FROM creep_ticks
WHERE room='W45N7' AND tick BETWEEN 84377800 AND 84378200
GROUP BY creep, role
ORDER BY min(tick)
""").fetchall()
for r in rows:
    print(r)

print("=== W45N7 ticks around core ===")
print(c.execute("SELECT count(DISTINCT tick), min(tick), max(tick) FROM creep_ticks WHERE room='W45N7' AND tick BETWEEN 84377900 AND 84378180").fetchone())

gt = c.execute("SELECT max(tick) FROM room_stats").fetchone()[0]
print("=== just-published 84378000 gt", gt, "===")
results = []
if gt >= 84378100:
    for room in ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7"):
        j = hb.history_get(room, 84378000)
        time.sleep(getattr(hb, "GAP_S", 0.35))
        rec = {"room": room, "base": 84378000, "status": 404 if not j else 200}
        if not j:
            print("  404", room)
            rec["inserted"] = 0
        else:
            rec["nticks"] = len(j.get("ticks") or {})
            print("  200", room, "ticks", rec["nticks"])
        results.append(rec)
    Path("/workspace/screeps/state/_patrol_2026-11-20_1819/justpub_84378000.json").write_text(json.dumps(results, indent=2))
else:
    print("not yet published")

for fn in ("model_1h.txt", "model_2h.txt"):
    t = Path("/workspace/screeps/state/_patrol_2026-11-20_1819/" + fn).read_text()
    for line in t.splitlines():
        if line.strip().startswith("actual:"):
            s = line.strip()[7:].strip()
            try:
                d = json.loads(s)
                keys = ["ticks", "tick_s", "storage_delta", "upgrade_per_tick", "upgrade_per_tick_1h", "cpu", "income"]
                print(fn, {k: d.get(k) for k in keys})
            except Exception as e:
                print(fn, "parse", e, s[:200])
        elif "upgrader_work" in line or line.strip().startswith("spawn_util"):
            print(fn, line.strip())

print("======= AUDIT =======")
t = Path("/workspace/screeps/state/_patrol_2026-11-20_1819/audit_patrol.txt").read_text()
for l in t.splitlines():
    if l.startswith("images:"):
        break
    print(l[:400])
print("======= MOTION 1h =======")
lines = Path("/workspace/screeps/state/_patrol_2026-11-20_1819/motion_1h.txt").read_text().splitlines()
print(chr(10).join(lines[:22]))
