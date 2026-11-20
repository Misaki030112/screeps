#!/usr/bin/env python3
"""Retry just-published 404 W47N8@84380300 after a short wait (not yet published at gt=84380440)."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-20_2100")
import backfill_confirm as confirm

ROOM, BASE = "W47N8", 84380300
LIVE = Path("/workspace/screeps/metrics/live.json")
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_2100")
HK = ZoneInfo("Asia/Hong_Kong")
WAIT_EXTRA = 60
TARGET_GT = BASE + 160  # a bit past the first just-published threshold of +140


def live_gt():
    d = json.loads(LIVE.read_text())
    st = d.get("stats") if isinstance(d.get("stats"), dict) else {}
    return int(st.get("t") or d.get("gameTime") or 0)


def main():
    confirm.load_tick_s()
    tick_s = confirm.TICK_S
    t0 = time.time()
    while time.time() - t0 < 300:
        gt = live_gt()
        if gt >= TARGET_GT and (time.time() - t0) >= 20:
            print(f"live game.time={gt} >= {TARGET_GT} after {time.time()-t0:.0f}s; proceeding", flush=True)
            break
        time.sleep(10)
    else:
        print(f"wait end last_live_gt={live_gt()}; trying anyway", flush=True)
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
        gt = live_gt()
        print(f"fell back to live game.time={gt}", flush=True)
    with db.connect() as c:
        cm = db.current_commit(c)
        d, mn, mx, n = confirm.db_range(c, ROOM, BASE)
    print(f"just_published_retry {hk} game.time={gt} tick_s={tick_s} pre {ROOM}@{BASE} distinct={d} rows={n} range={mn}..{mx}", flush=True)
    res = confirm.retry_one(ROOM, BASE, our, now_ts, gt, tick_s=tick_s, cm=cm)
    rec = {
        "t": res["at"], "room": ROOM, "base": BASE, "code": res["status"],
        "ticks": res.get("ticks", 0), "ts": res.get("ts"), "game_time": gt,
        "ok": res["ok"], "inserted": res["inserted"], "nfix": res.get("nfix", 0),
        "db_distinct": res.get("db_distinct"), "db_min": res.get("db_min"),
        "db_max": res.get("db_max"), "db_rows": res.get("db_rows"),
    }
    print(rec, flush=True)
    payload = {
        "game_time": gt, "at": hk, "pass": "just_published_retry",
        "base": BASE, "tick_s": tick_s, "get": rec,
        "inserted": res["inserted"], "still_404": [] if res["ok"] else [f"{ROOM}@{BASE}"],
    }
    (DIR / "just_published_retry_W47N8.json").write_text(json.dumps(payload, indent=2) + "\n")
    # merge into just_published json so post_counts sees the retry
    jp_path = DIR / f"just_published_{BASE}.json"
    jp = json.loads(jp_path.read_text())
    jp["retry"] = payload
    if res["ok"]:
        jp["inserted"] = int(jp.get("inserted") or 0) + int(res["inserted"] or 0)
        jp["ts_realigned"] = int(jp.get("ts_realigned") or 0) + int(res.get("nfix") or 0)
        if f"{ROOM}@{BASE}" in (jp.get("still_404") or []):
            jp["still_404"] = [x for x in jp["still_404"] if x != f"{ROOM}@{BASE}"]
        recs = jp.get("recovered") or []
        if f"{ROOM}@{BASE}" not in recs:
            recs.append(f"{ROOM}@{BASE}")
        jp["recovered"] = recs
        # update or append get record
        gets = jp.get("gets") or []
        replaced = False
        for i, g in enumerate(gets):
            if g.get("room") == ROOM and g.get("base") == BASE:
                gets[i] = rec
                replaced = True
                break
        if not replaced:
            gets.append(rec)
        jp["gets"] = gets
    jp_path.write_text(json.dumps(jp, indent=2) + "\n")
    print("finished", "ok" if res["ok"] else "still_404", "inserted", res["inserted"], flush=True)


if __name__ == "__main__":
    main()
