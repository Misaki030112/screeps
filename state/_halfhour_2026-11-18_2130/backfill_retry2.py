#!/usr/bin/env python3
"""Focused retry of remaining in-window official 404 W45N8@84341100."""
from __future__ import annotations
import sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

ROOM, BASE = "W45N8", 84341100
TICK_S = 4.68880

def main():
    hk = datetime.now(ZoneInfo("Asia/Hong_Kong"))
    gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
    print(f"retry2 {ROOM}@{BASE} start {hk.strftime('%Y-%m-%d %H:%M:%S')} Asia/Hong_Kong game.time={gt} tick_s={TICK_S}", flush=True)
    with db.connect() as c:
        t0, t1 = BASE + 1, BASE + 100
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (ROOM, t0, t1),
        ).fetchone()
        print(f"  pre distinct={d or 0} rows={n or 0} range={mn}..{mx}", flush=True)
    prev = hb.history_get(ROOM, BASE - 100)
    time.sleep(hb.GAP_S)
    print(f"  seed prev {BASE-100} {'ok' if prev else 'missing'}", flush=True)
    j = hb.history_get(ROOM, BASE)
    time.sleep(hb.GAP_S)
    now = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%H:%M:%S")
    if not j:
        print(f"  still_404 {ROOM}@{BASE} at {now} game.time={gt}", flush=True)
        return 0
    print(f"  ok  {ROOM}@{j.get('base')} ticks={len(j.get('ticks') or {})} ts={j.get('timestamp')}", flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
