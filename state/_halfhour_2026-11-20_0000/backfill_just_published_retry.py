#!/usr/bin/env python3
"""Retry just-published official 404 W47N8@84361700 (other four rooms were 200 at 23:40)."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-19_2330")
import backfill_confirm as confirm

ROOMS_RETRY = (("W47N8", 84361700),)
LIVE = Path("/workspace/screeps/metrics/live.json")
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-19_2330")
OUT = DIR / "just_published_84361700_retry.json"
HK = ZoneInfo("Asia/Hong_Kong")

def main():
    confirm.load_tick_s()
    tick_s = confirm.TICK_S
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
        live = json.loads(LIVE.read_text())
        st = live.get("stats") if isinstance(live.get("stats"), dict) else {}
        gt = live.get("gameTime") or st.get("t")
        print(f"fell back to live game.time={gt}", flush=True)
    with db.connect() as c:
        cm = db.current_commit(c)
    print(f"just_published_retry GET start {hk} game.time={gt} tick_s={tick_s}", flush=True)
    gets = []
    recovered, still_404 = [], []
    inserted = ts_realigned = 0
    for room, base in ROOMS_RETRY:
        with db.connect() as c:
            d, mn, mx, n = confirm.db_range(c, room, base)
        print(f"  pre  {room}@{base} distinct={d} rows={n} range={mn}..{mx}", flush=True)
        res = confirm.retry_one(room, base, our, now_ts, gt, tick_s=tick_s, cm=cm)
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
        recovered.append(f"{room}@{base}")
    print(f"recovered={recovered} still_404={still_404} inserted={inserted} ts_realigned={ts_realigned}", flush=True)
    payload = {
        "game_time": gt, "at": hk, "pass": "just_published_retry",
        "tick_s": tick_s, "gets": gets, "recovered": recovered,
        "still_404": still_404, "inserted": inserted, "ts_realigned": ts_realigned,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print("finished", flush=True)

if __name__ == "__main__":
    main()
