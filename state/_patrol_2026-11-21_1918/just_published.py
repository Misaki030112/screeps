#!/usr/bin/env python3
import sys, json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
sys.path.insert(0, "/workspace/screeps/state/_patrol_2026-11-21_1918")
import official_retry2 as r
import db

HK = ZoneInfo("Asia/Hong_Kong")
with db.connect() as c:
    gt = c.execute("SELECT max(tick) FROM room_stats").fetchone()[0]
print("db max room_stats tick as gt proxy", gt, flush=True)
if gt < 84399400:
    print("still too early, skip")
    raise SystemExit(0)
now_ts = datetime.now(timezone.utc)
results = []
for room in r.ROOMS:
    rec = r.insert_chunk(room, 84399300, now_ts, gt, r.TICK_S)
    rec["kind"] = "just_published_late"
    results.append(rec)
    print("JP", room, rec.get("status"), "inserted", rec.get("inserted"), "nticks", rec.get("nticks"), "range", rec.get("tmin"), rec.get("tmax"), flush=True)

print("=== post counts 84399301..84399400 ===", flush=True)
with db.connect() as c:
    for room in r.ROOMS:
        row = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, 84399301, 84399400),
        ).fetchone()
        print(room, "distinct", row[0], "min", row[1], "max", row[2], "rows", row[3])
    print("=== 19:10 freeze fill 84399191..84399309 ===")
    for room in r.ROOMS:
        row = c.execute(
            "SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, 84399191, 84399309),
        ).fetchone()
        print(room, "%s/119" % row[0])
    print("=== 18:47 freeze fill 84398871..84399029 ===")
    for room in r.ROOMS:
        row = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, 84398871, 84399029),
        ).fetchone()
        print(room, "%s/159" % row[0], "min", row[1], "max", row[2])

out = "/workspace/screeps/state/_patrol_2026-11-21_1918/just_published.json"
with open(out, "w") as f:
    json.dump(results, f, indent=2, default=str)
    f.write("\n")
print("done", datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"))
