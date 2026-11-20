#!/usr/bin/env python3
"""Retry just-published 404 W47N7@84378000 after a short interval."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api
sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-20_1900")
import backfill_confirm as confirm

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_1900")
HK = ZoneInfo("Asia/Hong_Kong")
TARGET = ("W47N7", 84378000)

def main():
    confirm.load_tick_s()
    tick_s = confirm.TICK_S
    hk = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    gt = None
    for attempt in range(3):
        try:
            gt = api.req("game/time?shard=" + hb.SHARD)["time"]
            break
        except Exception as e:
            print("game/time attempt", attempt + 1, "failed:", repr(e), flush=True)
            time.sleep(3 * (attempt + 1))
    if gt is None:
        live = json.loads(Path("/workspace/screeps/metrics/live.json").read_text())
        st = live.get("stats") if isinstance(live.get("stats"), dict) else {}
        gt = live.get("gameTime") or st.get("t")
    our = hb.uid()
    now_ts = datetime.now(timezone.utc)
    with db.connect() as c:
        cm = db.current_commit(c)
    room, base = TARGET
    print("retry_just404 start", hk, "game.time=", gt, "tick_s=", tick_s, "target=", f"{room}@{base}", flush=True)
    with db.connect() as c:
        d, mn, mx, n = confirm.db_range(c, room, base)
    print("  pre ", f"{room}@{base}", "distinct=", d, "rows=", n, "range=", mn, "..", mx, flush=True)
    res = confirm.retry_one(room, base, our, now_ts, gt, tick_s, cm)
    if not res["ok"]:
        print("  still_404", f"{room}@{base}", "at", res["at"], "game.time=", gt, flush=True)
        recovered, still_404 = [], [f"{room}@{base}"]
    else:
        print("  recovered_or_ok", f"{room}@{base}", "ticks=", res["ticks"], "ts=", res["ts"], "at", res["at"], "inserted=", res["inserted"], flush=True)
        recovered, still_404 = [f"{room}@{base}"], []
    payload = {
        "game_time": gt,
        "at": hk,
        "pass": "retry_just404",
        "target": f"{room}@{base}",
        "tick_s": tick_s,
        "get": res,
        "recovered": recovered,
        "still_404": still_404,
        "inserted": res.get("inserted") or 0,
        "ts_realigned": res.get("nfix") or 0,
    }
    out = DIR / "backfill_retry_just404.json"
    out.write_text(json.dumps(payload, indent=2, default=str) + chr(10))
    print("wrote", out, flush=True)
    print("recovered=", recovered, "still_404=", still_404, "inserted=", payload["inserted"], flush=True)

if __name__ == "__main__":
    main()
