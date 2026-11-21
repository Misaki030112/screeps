#!/usr/bin/env python3
"""Resume just-published 84406200 after SSL failure on W47N7 only. Do not rewrite pre_counts."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api
sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-22_0330")
import backfill_confirm as confirm

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
JUST_BASE = 84406200
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-22_0330")
HK = ZoneInfo("Asia/Hong_Kong")
OUT = DIR / f"just_published_{JUST_BASE}.json"

# First four rooms already succeeded before the SSL crash; keep script inserted counts.
PRIOR = [
    {"t": "03:41:09", "room": "W46N8", "base": JUST_BASE, "code": 200,
     "ticks": 100, "ts": 1795289933637, "game_time": 84406341,
     "ok": True, "inserted": 853, "nfix": 0},
    {"t": "03:41:14", "room": "W47N8", "base": JUST_BASE, "code": 200,
     "ticks": 100, "ts": 1795289969923, "game_time": 84406341,
     "ok": True, "inserted": 293, "nfix": 0},
    {"t": "03:41:18", "room": "W45N8", "base": JUST_BASE, "code": 200,
     "ticks": 100, "ts": 1795289966424, "game_time": 84406341,
     "ok": True, "inserted": 158, "nfix": 0},
    {"t": "03:41:20", "room": "W45N7", "base": JUST_BASE, "code": 200,
     "ticks": 100, "ts": 1795289935726, "game_time": 84406341,
     "ok": True, "inserted": 452, "nfix": 0},
]


def main():
    confirm.load_tick_s()
    tick_s = confirm.TICK_S
    time.sleep(5)
    our = hb.uid()
    now_ts = datetime.now(timezone.utc)
    hk = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    gt = None
    for attempt in range(3):
        try:
            gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
            break
        except Exception as e:
            print(f"game/time attempt {attempt+1} failed: {e!r}", flush=True)
            time.sleep(3 * (attempt + 1))
    if gt is None:
        raise SystemExit("game/time failed")
    with db.connect() as c:
        cm = db.current_commit(c)
        d, mn, mx, n = confirm.db_range(c, "W47N7", JUST_BASE)
    print(f"resume W47N7@{JUST_BASE} start {hk} game.time={gt} tick_s={tick_s} pre distinct={d} rows={n} range={mn}..{mx}", flush=True)

    last_err = None
    res = None
    for attempt in range(4):
        try:
            res = confirm.retry_one("W47N7", JUST_BASE, our, now_ts, gt, tick_s=tick_s, cm=cm)
            last_err = None
            break
        except Exception as e:
            last_err = e
            print(f"  transient W47N7@{JUST_BASE} resume attempt {attempt+1}: {e!r}", flush=True)
            time.sleep(5 * (attempt + 1))
    if res is None:
        raise SystemExit(f"W47N7 retry failed: {last_err!r}")

    rec = {
        "t": res["at"], "room": "W47N7", "base": JUST_BASE, "code": res["status"],
        "ticks": res.get("ticks", 0), "ts": res.get("ts"), "game_time": gt,
        "ok": res["ok"], "inserted": res["inserted"], "nfix": res.get("nfix", 0),
        "db_distinct": res.get("db_distinct"), "db_min": res.get("db_min"),
        "db_max": res.get("db_max"), "db_rows": res.get("db_rows"),
        "resumed_after_ssl": True, "resume_gt": gt,
    }
    if not res["ok"]:
        print(f"  still_404 W47N7@{JUST_BASE} at {res['at']} game.time={gt}", flush=True)
    else:
        print(f"  recovered_or_ok W47N7@{JUST_BASE} ticks={res['ticks']} ts={res['ts']} at {res['at']} inserted={res['inserted']}", flush=True)

    # Fill db_* on prior rooms from current DB (post-insert).
    gets = []
    with db.connect() as c:
        for rec0 in PRIOR:
            d, mn, mx, n = confirm.db_range(c, rec0["room"], JUST_BASE)
            rec0 = dict(rec0)
            rec0.update({"db_distinct": d, "db_min": mn, "db_max": mx, "db_rows": n})
            gets.append(rec0)
    gets.append(rec)

    recovered = [f"{g['room']}@{JUST_BASE}" for g in gets if g.get("ok")]
    still_404 = [f"{g['room']}@{JUST_BASE}" for g in gets if not g.get("ok")]
    inserted = sum(int(g.get("inserted") or 0) for g in gets)
    ts_realigned = sum(int(g.get("nfix") or 0) for g in gets)
    print(f"recovered={recovered} still_404={still_404} inserted={inserted} ts_realigned={ts_realigned}", flush=True)

    payload = {
        "game_time": 84406341,
        "resume_game_time": gt,
        "at": "2026-11-22 03:41:08 Asia/Hong_Kong",
        "resume_at": hk,
        "pass": "just_published",
        "base": JUST_BASE,
        "threshold": JUST_BASE + 140,
        "tick_s": tick_s,
        "gets": gets,
        "recovered": recovered,
        "still_404": still_404,
        "inserted": inserted,
        "ts_realigned": ts_realigned,
        "waited_live_gt": 84406340,
        "w47n7_resumed_after_ssl": True,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    with (DIR / "backfill_just_published.txt").open("a") as f:
        f.write(f"resume W47N7 after SSL at {hk} game.time={gt}\n")
        if res["ok"]:
            f.write(f"  recovered_or_ok W47N7@{JUST_BASE} ticks={res['ticks']} ts={res['ts']} at {res['at']} inserted={res['inserted']}\n")
        else:
            f.write(f"  still_404 W47N7@{JUST_BASE} at {res['at']} game.time={gt}\n")
        f.write(f"recovered={recovered} still_404={still_404} inserted={inserted} ts_realigned={ts_realigned}\n")
        f.write("finished\n")
    print("finished", flush=True)


if __name__ == "__main__":
    main()
