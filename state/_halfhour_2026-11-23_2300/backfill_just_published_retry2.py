#!/usr/bin/env python3
"""Retry2 just-published official history base 84443400 at +300 after +140 and +200 if any 404 remains."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db

sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-23_2300")
import backfill_confirm as confirm

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
JUST_BASE = 84443400
WAIT_UNTIL_GT = JUST_BASE + 300
LIVE = Path("/workspace/screeps/metrics/live.json")
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-23_2300")
OUT = DIR / f"just_published_{JUST_BASE}.json"
HK = ZoneInfo("Asia/Hong_Kong")


def wait_for_publish(target=WAIT_UNTIL_GT, timeout_s=600, poll_s=10):
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout_s:
        try:
            d = json.loads(LIVE.read_text())
            st = d.get("stats") if isinstance(d.get("stats"), dict) else {}
            gt = st.get("t") or d.get("gameTime")
            last = gt
            if gt and int(gt) >= target:
                print(f"retry2 live game.time={gt} >= {target} after {time.time()-t0:.0f}s; proceeding", flush=True)
                return int(gt)
        except Exception as e:
            print(f"  live.json read failed: {e!r}", flush=True)
        time.sleep(poll_s)
    print(f"retry2 wait timeout after {timeout_s}s last_live_gt={last}; will try anyway", flush=True)
    return last


def main():
    confirm.load_tick_s()
    tick_s = confirm.TICK_S
    waited = wait_for_publish()
    our = hb.uid()
    now_ts = datetime.now(timezone.utc)
    hk = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    live = json.loads(LIVE.read_text())
    st = live.get("stats") if isinstance(live.get("stats"), dict) else {}
    gt = st.get("t") or live.get("gameTime") or waited
    print(f"just_published RETRY2 GET start {hk} live_gt={gt} tick_s={tick_s} base={JUST_BASE} threshold>={WAIT_UNTIL_GT}", flush=True)
    pre = {}
    with db.connect() as c:
        cm = db.current_commit(c)
        for room in ROOMS:
            d, mn, mx, n = confirm.db_range(c, room, JUST_BASE)
            pre[room] = {"distinct": d or 0, "rows": n or 0, "min": mn, "max": mx}
    (DIR / "just_published_pre_counts_retry2.json").write_text(json.dumps(pre, indent=2) + "\n")
    print("wrote pre_counts at retry2 GET time", pre, flush=True)
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
            time.sleep(1.2)
            continue
        print(f"  recovered_or_ok {room}@{JUST_BASE} ticks={res['ticks']} ts={res['ts']} at {res['at']} inserted={res['inserted']}", flush=True)
        inserted += res["inserted"]
        ts_realigned += res.get("nfix") or 0
        recovered.append(f"{room}@{JUST_BASE}")
        time.sleep(1.2)
    print(f"retry2 recovered={recovered} still_404={still_404} inserted={inserted} ts_realigned={ts_realigned}", flush=True)
    payload = {
        "game_time": gt, "at": hk, "pass": "just_published_retry2",
        "base": JUST_BASE, "threshold": WAIT_UNTIL_GT, "tick_s": tick_s,
        "gets": gets, "recovered": recovered, "still_404": still_404,
        "inserted": inserted, "ts_realigned": ts_realigned,
        "waited_live_gt": waited,
        "first_attempt": "all_five_404 at +140 (84420140) and +200 (84420200); this pass +300",
    }
    (DIR / f"just_published_{JUST_BASE}_retry2.json").write_text(json.dumps(payload, indent=2) + "\n")
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print("finished retry2", flush=True)


if __name__ == "__main__":
    main()
