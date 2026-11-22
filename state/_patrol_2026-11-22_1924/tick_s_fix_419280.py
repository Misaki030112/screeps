#!/usr/bin/env python3
import json, sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
sys.path.insert(0, "/workspace/screeps/scripts")
sys.path.insert(0, "/workspace/screeps/state/_patrol_2026-11-22_1924")
import db, api
import history_backfill as hb
import tick_s_check as tsc

TMIN, TMAX = 84419301, 84420000
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TARGET = 4.19280
DIR = Path("/workspace/screeps/state/_patrol_2026-11-22_1924")

def vs(c, tick_s, gt, now):
    row = c.execute(
        """SELECT count(*) FILTER (WHERE abs(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) > 45) AS over45,
                  count(*) FILTER (WHERE abs(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) > 15) AS over15,
                  count(*) AS n,
                  avg(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) AS mean_off,
                  min(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) AS min_off,
                  max(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) AS max_off
             FROM creep_ticks
            WHERE tick BETWEEN %(t0)s AND %(t1)s AND room = ANY(%(rooms)s)""",
        {"now": now, "gt": gt, "tick_s": tick_s, "t0": TMIN, "t1": TMAX, "rooms": list(ROOMS)},
    ).fetchone()
    return {
        "over45": row[0], "over15": row[1], "n": row[2],
        "mean_off": float(row[3] or 0), "min_off": float(row[4] or 0), "max_off": float(row[5] or 0),
    }

def main():
    gt = api.req("game/time?shard=shard3")["time"]
    now = datetime.now(timezone.utc)
    print(f"before realign game.time={gt} now={now.isoformat()} target={TARGET}", flush=True)
    with db.connect() as c:
        print("before vs 4.19280", vs(c, 4.19280, gt, now), flush=True)
        print("before vs 4.08344", vs(c, 4.08344, gt, now), flush=True)

    with db.connect(autocommit=False) as c:
        nfix, skipped = tsc.realign_chunk_safe(c, TMIN, TMAX, ROOMS, now, gt, TARGET)
        c.commit()
    print(f"chunk-safe nfix={nfix} skipped={skipped}", flush=True)
    n2 = 0
    if skipped:
        with db.connect(autocommit=False) as c:
            n2 = hb.realign_ts(c, TMIN, TMAX, ROOMS, now, gt, TARGET)
            c.commit()
        print(f"full realign extra n2={n2}", flush=True)

    now2 = datetime.now(timezone.utc)
    gt2 = api.req("game/time?shard=shard3")["time"]
    with db.connect() as c:
        for name, ts in [("prev_4.19280", 4.19280), ("first_4.08344", 4.08344), ("later_4.23830", 4.23830), ("all_4.21249", 4.21249)]:
            print(name, vs(c, ts, gt2, now2), flush=True)

    j = json.loads((DIR / "tick_s_realign.json").read_text())
    j["manual_revert_from_first_4.08344_to_prev_4.19280"] = {
        "why": "first-interval 4.08344 is the short 84419300..84419400 span artifact; 19:00 halfhour tick_s_in_use 4.19280 had over45=0 on overlapping data before this first-pass mass-realigned 15230 rows to 4.083. tick_s_check then doubled down on first. Realigned window to proven 4.19280.",
        "nfix": nfix,
        "skipped": skipped,
        "n2": n2,
        "gt": gt,
        "gt2": gt2,
        "at": datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"),
    }
    j["tick_s_in_use"] = 4.19280
    j["tick_s_in_use_name"] = "prev_later_manual"
    j["corrective_applied"] = True
    (DIR / "tick_s_realign.json").write_text(json.dumps(j, indent=2, default=str) + "\n")
    print("updated tick_s_realign.json tick_s_in_use=4.19280", flush=True)

if __name__ == "__main__":
    main()
