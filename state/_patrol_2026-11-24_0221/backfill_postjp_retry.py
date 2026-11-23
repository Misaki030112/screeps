#!/usr/bin/env python3
from pathlib import Path
import json, sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api
sys.path.insert(0, "/workspace/screeps/state/_patrol_2026-11-24_0221")
import backfill_confirm as confirm

DIR = Path("/workspace/screeps/state/_patrol_2026-11-24_0221")
TARGETS = [
    ("W45N8", 84433100),  # already told 1129; retry; do not label NEW
    ("W47N8", 84433300),  # already told 1129; retry; do not label NEW
    ("W47N7", 84434000),  # still-untold from quiet 1200; retry; do not relabel NEW
    ("W45N7", 84434800),  # still-untold from quiet 1300 JP; retry; do not relabel NEW
    ("W45N7", 84435400),  # still-untold NEW from quiet 1400; retry; do not relabel NEW
    ("W47N8", 84435500),  # still-untold NEW from quiet 1400; retry; do not relabel NEW
]  # still 404 after confirm; JP 84433600 TBD
NL = chr(10)

def main():
    confirm.load_tick_s()
    tick_s = confirm.TICK_S
    hk = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    if not TARGETS:
        print(f"postjp_retry skipped no targets at {hk}")
        (DIR / "backfill_postjp_retry.json").write_text(
            json.dumps({
                "at": hk, "skipped": True, "reason": "no targets",
                "targets": [], "still_404": [], "inserted": 0,
                "recovered": [], "game_time": None, "tick_s": tick_s,
            }, indent=2) + NL
        )
        return
    our = hb.uid()
    now_ts = datetime.now(timezone.utc)
    gt = api.req("game/time?shard=%s" % hb.SHARD)["time"]
    with db.connect() as c:
        cm = db.current_commit(c)
    print(f"postjp_retry start {hk} game.time={gt} tick_s={tick_s} targets={TARGETS}")
    results = []
    inserted = 0
    still_404 = []
    recovered = []
    for room, base in TARGETS:
        with db.connect() as c:
            d, mn, mx, n = confirm.db_range(c, room, base)
        print(f"  pre  {room}@{base} distinct={d} rows={n} range={mn}..{mx}")
        res = confirm.retry_one(room, base, our, now_ts, gt, tick_s=tick_s, cm=cm)
        if not res.get("ok"):
            still_404.append(f"{room}@{base}")
            print(f"  still_404 {room}@{base} at {res.get('at')} game.time={gt}")
        else:
            recovered.append(f"{room}@{base}")
            print(f"  recovered_or_ok {room}@{base} inserted={res.get('inserted')}")
        inserted += int(res.get("inserted") or 0)
        results.append({
            "room": room, "base": base, "status": res.get("status"),
            "inserted": res.get("inserted"), "db_distinct": res.get("db_distinct"),
        })
    payload = {
        "at": hk, "game_time": gt, "tick_s": tick_s,
        "targets": ["%s@%s" % (r, b) for r, b in TARGETS],
        "results": results, "inserted": inserted,
        "still_404": still_404, "recovered": recovered,
        "at_finish": datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"),
    }
    (DIR / "backfill_postjp_retry.json").write_text(json.dumps(payload, indent=2, default=str) + NL)
    print(f"recovered={recovered} still_404={still_404} inserted={inserted}")
    print("finished", payload["at_finish"])

if __name__ == "__main__":
    main()
