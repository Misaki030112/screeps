#!/usr/bin/env python3
from pathlib import Path
import json, sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-21_0000")
import history_backfill as hb
import backfill_confirm as confirm
import db

HK = ZoneInfo("Asia/Hong_Kong")
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-21_0000")
JUST_BASE = 84382900
ROOM = "W46N8"
hk = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

confirm.load_tick_s()
tick_s = confirm.TICK_S
live = json.loads(Path("/workspace/screeps/metrics/live.json").read_text())
st = live.get("stats") if isinstance(live.get("stats"), dict) else {}
gt = live.get("gameTime") or st.get("t")
print(f"retry_just {ROOM}@{JUST_BASE} start {hk} live.gameTime={gt} tick_s={tick_s}", flush=True)

cm = {}
with db.connect() as c:
    cm = db.current_commit(c)
    d, mn, mx, n = confirm.db_range(c, ROOM, JUST_BASE)
print(f"  pre  {ROOM}@{JUST_BASE} distinct={d} rows={n} range={mn}..{mx}", flush=True)
our = hb.uid()
now_ts = datetime.now(timezone.utc)
res = confirm.retry_one(ROOM, JUST_BASE, our, now_ts, gt, tick_s=tick_s, cm=cm)
print(
    f"  status={res.get('status')} ticks={res.get('ticks')} ts={res.get('ts')} "
    f"at={res.get('at')} inserted={res.get('inserted')}",
    flush=True,
)

jp_path = DIR / f"just_published_{JUST_BASE}.json"
jp = json.loads(jp_path.read_text())
retry = {
    "t": res.get("at"),
    "room": ROOM,
    "base": JUST_BASE,
    "code": res.get("status"),
    "ticks": res.get("ticks", 0),
    "ts": res.get("ts"),
    "game_time": gt,
    "inserted": res.get("inserted", 0),
    "at": datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"),
    "pass": "just_published_retry",
}
jp.setdefault("retries", []).append(retry)
key = f"{ROOM}@{JUST_BASE}"
if res.get("status") == 200 or (res.get("ticks") or 0) > 0:
    still = jp.get("still_404") or []
    jp["still_404"] = [x for x in still if x != key]
    rec = jp.get("recovered") or []
    if key not in rec:
        rec.append(key)
    jp["recovered"] = rec
    jp["inserted"] = int(jp.get("inserted") or 0) + int(res.get("inserted") or 0)
    jp["retry_recovered"] = [key]
else:
    jp["retry_still_404"] = [key]
jp_path.write_text(json.dumps(jp, indent=2) + chr(10))
print("wrote", jp_path)
print("still_404", jp.get("still_404"), "recovered", jp.get("recovered"), "inserted", jp.get("inserted"))

with db.connect() as c:
    d, mn, mx, n = confirm.db_range(c, ROOM, JUST_BASE)
print(f"  post {ROOM}@{JUST_BASE} distinct={d} rows={n} range={mn}..{mx}")
