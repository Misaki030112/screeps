#!/usr/bin/env python3
"""Fetch just-published official history base 84369500 once game.time is safely past 84369640."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-20_0900")
import backfill_confirm as confirm

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
JUST_BASE = 84370300
WAIT_UNTIL_GT = JUST_BASE + 140
LIVE = Path("/workspace/screeps/metrics/live.json")
DIR = Path("/workspace/screeps/state/_patrol_2026-11-20_0920")
OUT = DIR / f"just_published_{JUST_BASE}.json"
HK = ZoneInfo("Asia/Hong_Kong")


def wait_for_publish(target=WAIT_UNTIL_GT, timeout_s=480, poll_s=8):
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout_s:
        try:
            d = json.loads(LIVE.read_text())
            st = d.get("stats") if isinstance(d.get("stats"), dict) else {}
            gt = st.get("t") or d.get("gameTime")
            last = gt
            if gt and int(gt) >= target:
                print(f"live game.time={gt} >= {target} after {time.time()-t0:.0f}s; proceeding", flush=True)
                return int(gt)
        except Exception as e:
            print(f"  live.json read failed: {e!r}", flush=True)
        time.sleep(poll_s)
    print(f"wait timeout after {timeout_s}s last_live_gt={last}; will try anyway", flush=True)
    return last


def main():
    confirm.load_tick_s()
    tick_s = confirm.TICK_S
    waited = wait_for_publish()
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
        gt = live.get("gameTime") or st.get("t") or waited
        print(f"fell back to live game.time={gt}", flush=True)
    with db.connect() as c:
        cm = db.current_commit(c)
    print(f"just_published GET start {hk} game.time={gt} tick_s={tick_s} base={JUST_BASE} threshold>={WAIT_UNTIL_GT}", flush=True)
    recovered, still_404 = [], []
    inserted = ts_realigned = 0
    gets = []
    for room in ROOMS:
        with db.connect() as c:
            d, mn, mx, n = confirm.db_range(c, room, JUST_BASE)
        print(f"  pre  {room}@{JUST_BASE} distinct={d} rows={n} range={mn}..{mx}", flush=True)
        res = confirm.retry_one(room, JUST_BASE, our, now_ts, gt, tick_s=tick_s, cm=cm)
        rec = {
            "t": res["at"], "room": room, "base": JUST_BASE, "code": res["status"],
            "ticks": res.get("ticks", 0), "ts": res.get("ts"), "game_time": gt,
            "inserted": res.get("inserted", 0), "ts_realigned": res.get("ts_realigned", 0),
        }
        gets.append(rec)
        if res["status"] == 200:
            recovered.append(f"{room}@{JUST_BASE}")
            inserted += res.get("inserted", 0) or 0
            ts_realigned += res.get("ts_realigned", 0) or 0
            print(f"  recovered_or_ok {room}@{JUST_BASE} ticks={res.get('ticks')} inserted={res.get('inserted')}", flush=True)
        else:
            still_404.append(f"{room}@{JUST_BASE}")
            print(f"  still_{res['status']} {room}@{JUST_BASE}", flush=True)
        time.sleep(hb.GAP_S)
    # post counts
    post = {}
    with db.connect() as c:
        for room in ROOMS:
            d, mn, mx, n = confirm.db_range(c, room, JUST_BASE)
            post[room] = {"distinct": d, "min": mn, "max": mx, "rows": n}
    out = {
        "at": hk, "game_time": gt, "tick_s": tick_s, "base": JUST_BASE,
        "recovered": recovered, "still_404": still_404,
        "inserted": inserted, "ts_realigned": ts_realigned,
        "gets": gets, "post": post,
    }
    OUT.write_text(json.dumps(out, indent=2, default=str))
    print(f"recovered={recovered} still_404={still_404} inserted={inserted} ts_realigned={ts_realigned}")
    print(f"wrote {OUT}")
    print("finished")


if __name__ == "__main__":
    main()
