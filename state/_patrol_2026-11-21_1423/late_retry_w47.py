#!/usr/bin/env python3
import sys, json
from datetime import datetime
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb, api
HK = ZoneInfo("Asia/Hong_Kong")
gt = api.req("game/time?shard=%s" % hb.SHARD)["time"]
j = hb.history_get("W47N8", 84395100)
rec = {
    "gt": gt,
    "status": 200 if j else 404,
    "nticks": len((j or {}).get("ticks") or {}),
    "at": datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"),
}
print(rec)
path = "state/_patrol_2026-11-21_1423/backfill_late_retry_W47N8_84395100.json"
open(path, "w").write(json.dumps(rec, indent=2) + "
")
print("wrote", path)
