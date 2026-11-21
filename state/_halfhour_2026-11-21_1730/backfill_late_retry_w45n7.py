#!/usr/bin/env python3
import sys, json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

sys.path.insert(0, "/workspace/screeps/tools")
sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-21_1730")
import history_backfill as hb
import db, api
import backfill_confirm as confirm

confirm.load_tick_s()
room, base = "W45N7", 84397400
hk = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
our = hb.uid()
now_ts = datetime.now(timezone.utc)
with db.connect() as c:
    cm = db.current_commit(c)
    d, mn, mx, n = confirm.db_range(c, room, base)
print(f"late_retry start {hk} game.time={gt} tick_s={confirm.TICK_S} target={room}@{base}")
print(f"  pre  {room}@{base} distinct={d} rows={n} range={mn}..{mx}")
res = confirm.retry_one(room, base, our, now_ts, gt, tick_s=confirm.TICK_S, cm=cm)
print(f"  status={res['status']} inserted={res['inserted']} ticks={res.get('ticks')} nfix={res.get('nfix')} at={res['at']}")
print(f"  db_after distinct={res.get('db_distinct')} rows={res.get('db_rows')} range={res.get('db_min')}..{res.get('db_max')}")
payload = {
    "at": hk,
    "game_time": gt,
    "pass": "late_retry",
    "room": room,
    "base": base,
    "tick_s": confirm.TICK_S,
}
payload.update(res)
out = Path("/workspace/screeps/state/_halfhour_2026-11-21_1730/backfill_late_retry_w45n7.json")
out.write_text(json.dumps(payload, indent=2, default=str) + chr(10))
print("finished")
