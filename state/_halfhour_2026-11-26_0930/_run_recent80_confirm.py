#!/usr/bin/env python3
"""Confirm only the two official 404s from the 80-min top-up. Writes recent80_confirm.json, does not overwrite the 42h confirm.json."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-26_0930")
sys.path.insert(0, "/workspace/screeps/tools")
sys.path.insert(0, str(DIR))
import history_backfill as hb
import db, api
import backfill_confirm as confirm

TARGETS = [("W47N7", 84492300), ("W47N8", 84492600)]
OUT = DIR / "recent80_confirm.json"
HK = ZoneInfo("Asia/Hong_Kong")


def main():
    confirm.load_tick_s()
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
        raise SystemExit("game/time failed after 3 attempts")
    with db.connect() as c:
        cm = db.current_commit(c)
    print(f"recent80_confirm GET start {hk} game.time={gt} tick_s={confirm.TICK_S} targets={len(TARGETS)}", flush=True)
    recovered, still_404 = [], []
    inserted = ts_realigned = 0
    gets = []
    for room, base in TARGETS:
        with db.connect() as c:
            d, mn, mx, n = confirm.db_range(c, room, base)
        print(f"  pre  {room}@{base} distinct={d} rows={n} range={mn}..{mx}", flush=True)
        res = confirm.retry_one(room, base, our, now_ts, gt, tick_s=confirm.TICK_S, cm=cm)
        rec = {
            "t": res["at"], "room": room, "base": base, "code": res["status"],
            "ticks": res.get("ticks", 0), "ts": res.get("ts"), "game_time": gt,
            "ok": res["ok"], "inserted": res["inserted"], "nfix": res.get("nfix", 0),
            "db_distinct": res.get("db_distinct"), "db_min": res.get("db_min"),
            "db_max": res.get("db_max"), "db_rows": res.get("db_rows"),
        }
        gets.append(rec)
        if not res["ok"]:
            print(f"  still_404 {room}@{base} at {res['at']} game.time={gt}", flush=True)
            still_404.append(f"{room}@{base}")
            continue
        print(f"  recovered_or_ok {room}@{base} ticks={res['ticks']} ts={res['ts']} at {res['at']} inserted={res['inserted']}", flush=True)
        inserted += res["inserted"]
        ts_realigned += res.get("nfix") or 0
        if res["inserted"] > 0:
            recovered.append(f"{room}@{base}")
        else:
            recovered.append(f"{room}@{base}#already")
        time.sleep(1.2)
    payload = {
        "game_time": gt, "at": hk, "pass": "recent80_confirm", "gets": gets,
        "recovered": recovered, "still_404": still_404,
        "inserted": inserted, "ts_realigned": ts_realigned, "tick_s": confirm.TICK_S,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"recovered={recovered} still_404={still_404} inserted={inserted} ts_realigned={ts_realigned}", flush=True)
    print("finished", flush=True)


if __name__ == "__main__":
    main()
