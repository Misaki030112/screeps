#!/usr/bin/env python3
"""Fetch just-published official history base 84370900 once game.time is safely past 84371040."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

# Reuse confirm helpers (tick_s loader, retry_one, db_range)
sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-20_1000")
import backfill_confirm as confirm

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
JUST_BASE = 84370900
WAIT_UNTIL_GT = JUST_BASE + 140
LIVE = Path("/workspace/screeps/metrics/live.json")
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_1000")
OUT = DIR / f"just_published_{JUST_BASE}.json"
HK = ZoneInfo("Asia/Hong_Kong")


def wait_for_publish(target=WAIT_UNTIL_GT, timeout_s=480, poll_s=10):
    """Wait on listener live.json (no extra game/time API) until the next base can be public."""
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout_s:
        try:
            d = json.loads(LIVE.read_text())
            st = d.get("stats") if isinstance(d.get("stats"), dict) else {}
            # Prefer stats.t: live.json gameTime can lag the already-published threshold.
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
    # Snapshot pre-counts at GET time so wrapup actual-inserted is not inflated by live rotation during the wait.
    pre = {}
    with db.connect() as c:
        for room in ROOMS:
            d, mn, mx, n = confirm.db_range(c, room, JUST_BASE)
            pre[room] = {"distinct": d or 0, "rows": n or 0, "min": mn, "max": mx}
    (DIR / "just_published_pre_counts.json").write_text(json.dumps(pre, indent=2) + "\n")
    print("wrote pre_counts at GET time", pre, flush=True)
    gets = []
    recovered, still_404 = [], []
    inserted = ts_realigned = 0
    for room in ROOMS:
        with db.connect() as c:
            d, mn, mx, n = confirm.db_range(c, room, JUST_BASE)
        print(f"  pre  {room}@{JUST_BASE} distinct={d} rows={n} range={mn}..{mx}", flush=True)
        res = confirm.retry_one(room, JUST_BASE, our, now_ts, gt, tick_s=tick_s, cm=cm)
        rec = {
            "t": res["at"], "room": room, "base": JUST_BASE, "code": res["status"],
            "ticks": res.get("ticks", 0), "ts": res.get("ts"), "game_time": gt,
            "ok": res["ok"], "inserted": res["inserted"], "nfix": res.get("nfix", 0),
            "db_distinct": res.get("db_distinct"), "db_min": res.get("db_min"),
            "db_max": res.get("db_max"), "db_rows": res.get("db_rows"),
        }
        gets.append(rec)
        if not res["ok"]:
            print(f"  still_404 {room}@{JUST_BASE} at {res['at']} game.time={gt}", flush=True)
            still_404.append(f"{room}@{JUST_BASE}")
            continue
        print(f"  recovered_or_ok {room}@{JUST_BASE} ticks={res['ticks']} ts={res['ts']} at {res['at']} inserted={res['inserted']}", flush=True)
        inserted += res["inserted"]
        ts_realigned += res.get("nfix") or 0
        recovered.append(f"{room}@{JUST_BASE}")
    print(f"recovered={recovered} still_404={still_404} inserted={inserted} ts_realigned={ts_realigned}", flush=True)
    payload = {
        "game_time": gt, "at": hk, "pass": "just_published",
        "base": JUST_BASE, "threshold": WAIT_UNTIL_GT, "tick_s": tick_s,
        "gets": gets, "recovered": recovered, "still_404": still_404,
        "inserted": inserted, "ts_realigned": ts_realigned,
        "waited_live_gt": waited,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print("finished", flush=True)


if __name__ == "__main__":
    main()
