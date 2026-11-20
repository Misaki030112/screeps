#!/usr/bin/env python3
import json, sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api
import importlib.util
spec = importlib.util.spec_from_file_location(
    "official_retry",
    "/workspace/screeps/state/_patrol_2026-11-21_0124/official_retry.py",
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
HK = ZoneInfo("Asia/Hong_Kong")
now_ts = datetime.now(timezone.utc)
gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
print("jp game.time", gt, "at", datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), flush=True)
recs = []
jp_base = 84384100
if gt >= jp_base + 100:
    for room in mod.ROOMS:
        rec = mod.insert_chunk(room, jp_base, now_ts, gt, 4.172)
        recs.append(rec)
else:
    print("still unpublished", gt, flush=True)
print("=== retry2 W45N7 404s ===", flush=True)
for room, base in [("W45N7", 84383900), ("W45N7", 84383500)]:
    rec = mod.insert_chunk(room, base, now_ts, gt, 4.172)
    recs.append(rec)
path = "/workspace/screeps/state/_patrol_2026-11-21_0124/jp_and_retry2.json"
with open(path, "w") as f:
    json.dump({"gt": gt, "recs": recs}, f, indent=2, default=str)
    f.write("\n")
print("wrote", path, flush=True)
with db.connect() as c:
    for room, base in [(r, 84384100) for r in mod.ROOMS] + [("W45N7", 84383900), ("W45N7", 84383500)]:
        d, mn, mx, n = mod.db_range(c, room, base)
        print(f"  post {room}@{base} distinct={d} min={mn} max={mx} rows={n}", flush=True)
