#!/usr/bin/env python3
"""Late retry of first-pass official 404 W47N7@84395600. Does not overwrite confirm JSON."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, "/workspace/screeps/tools")
sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-21_1530")
import history_backfill as hb
import db, api
import backfill_confirm as confirm

confirm.load_tick_s()
room, base = "W47N7", 84395600
our = hb.uid()
now_ts = datetime.now(timezone.utc)
hk = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
gt = None
for attempt in range(3):
    try:
        gt = api.req("game/time?shard=" + hb.SHARD)["time"]
        break
    except Exception as e:
        print("game/time attempt %s failed: %r" % (attempt+1, e))
        time.sleep(3 * (attempt + 1))
if gt is None:
    raise SystemExit("game/time failed")
with db.connect() as c:
    cm = db.current_commit(c)
    d, mn, mx, n = confirm.db_range(c, room, base)
print("late retry start %s game.time=%s tick_s=%s pre distinct=%s rows=%s range=%s..%s" % (hk, gt, confirm.TICK_S, d, n, mn, mx))
res = confirm.retry_one(room, base, our, now_ts, gt, tick_s=confirm.TICK_S, cm=cm)
still = [] if res["ok"] else ["%s@%s" % (room, base)]
recovered = ["%s@%s" % (room, base)] if res["ok"] and res["inserted"] > 0 else []
print("  code=%s inserted=%s still_404=%s recovered=%s db_distinct=%s range=%s..%s" % (res["status"], res["inserted"], still, recovered, res.get("db_distinct"), res.get("db_min"), res.get("db_max")))
payload = {
    "at": hk,
    "game_time": gt,
    "tick_s": confirm.TICK_S,
    "room": room,
    "base": base,
    "code": res["status"],
    "ok": res["ok"],
    "inserted": res["inserted"],
    "nfix": res.get("nfix", 0),
    "still_404": still,
    "recovered": recovered,
    "db_distinct": res.get("db_distinct"),
    "db_min": res.get("db_min"),
    "db_max": res.get("db_max"),
    "db_rows": res.get("db_rows"),
}
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-21_1530")
(DIR / "backfill_late_retry_W47N7_84395600.json").write_text(json.dumps(payload, indent=2) + chr(10))
(DIR / "backfill_late_retry_W47N7_84395600.txt").write_text("%s gt=%s %s@%s code=%s inserted=%s still_404=%s%s" % (hk, gt, room, base, res["status"], res["inserted"], still, chr(10)))
print("finished")
