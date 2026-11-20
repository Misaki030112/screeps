#!/usr/bin/env python3
"""Retry just-published W45N7@84376800 which 404'd at the first threshold GET."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api
sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-20_1700")
import backfill_confirm as confirm

ROOM, BASE = "W45N7", 84376800
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_1700")
HK = ZoneInfo("Asia/Hong_Kong")

def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "retry"
    out = DIR / f"just_published_retry_W45N7_84376800_{tag}.json"
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
        raise SystemExit("game/time failed")
    with db.connect() as c:
        cm = db.current_commit(c)
        d, mn, mx, n = confirm.db_range(c, ROOM, BASE)
    print(f"retry W45N7@84376800 {tag} start {hk} game.time={gt} tick_s={tick_s} pre distinct={d} rows={n} range={mn}..{mx}", flush=True)
    res = confirm.retry_one(ROOM, BASE, our, now_ts, gt, tick_s=tick_s, cm=cm)
    print(f"  result ok={res['ok']} status={res['status']} ticks={res.get('ticks')} inserted={res['inserted']} nfix={res.get('nfix')} db_distinct={res.get('db_distinct')} range={res.get('db_min')}..{res.get('db_max')} rows={res.get('db_rows')}", flush=True)
    payload = {
        "at": hk, "game_time": gt, "tick_s": tick_s, "room": ROOM, "base": BASE, "tag": tag,
        "pre": {"distinct": d, "rows": n, "min": mn, "max": mx},
        "result": res,
    }
    out.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print("wrote", out, flush=True)

if __name__ == "__main__":
    main()
