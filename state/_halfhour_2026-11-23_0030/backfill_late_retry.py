#!/usr/bin/env python3
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api
sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-23_0030")
import backfill_confirm as confirm

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-23_0030")
HK = ZoneInfo("Asia/Hong_Kong")
TARGETS = []  # first-pass 404 W47N7@84424400 recovered on confirm; aged-out leftovers not retried

def main():
    confirm.load_tick_s()
    tick_s = confirm.TICK_S
    hk = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    if not TARGETS:
        print(f"late retry skipped no targets at {hk}")
        (DIR / "backfill_late_retry.json").write_text(
            json.dumps({
                "at": hk, "skipped": True, "reason": "no targets",
                "targets": [], "still_404": [], "inserted": 0,
                "recovered": [], "game_time": None, "tick_s": tick_s,
            }, indent=2) + chr(10)
        )
        return
    our = hb.uid()
    now_ts = datetime.now(timezone.utc)
    gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
    with db.connect() as c:
        cm = db.current_commit(c)
    print(f"late_retry start {hk} game.time={gt} tick_s={tick_s} targets={TARGETS}")
    results = []
    inserted = 0
    still_404 = []
    recovered = []
    for room, base in TARGETS:
        with db.connect() as c:
            d, mn, mx, n = confirm.db_range(c, room, base)
        print(f"  pre  {room}@{base} distinct={d} rows={n} range={mn}..{mx}")
        res = confirm.retry_one(room, base, our, now_ts, gt, tick_s=tick_s, cm=cm)
        item = {
            "room": room, "base": base,
            "pre": {"distinct": d or 0, "rows": n or 0, "min": mn, "max": mx},
            "status": res.get("status"), "ok": res.get("ok"),
            "inserted": res.get("inserted") or 0, "nfix": res.get("nfix") or 0,
            "ticks": res.get("ticks") or 0, "ts": res.get("ts"),
            "at": res.get("at"),
            "db_distinct": res.get("db_distinct"), "db_min": res.get("db_min"),
            "db_max": res.get("db_max"), "db_rows": res.get("db_rows"),
        }
        if not res.get("ok"):
            item["still_404"] = True
            still_404.append(f"{room}@{base}")
            print(f"  still_404 {room}@{base} at {res.get('at')} game.time={gt}")
        else:
            item["still_404"] = False
            recovered.append(f"{room}@{base}")
            print(f"  recovered_or_ok {room}@{base} inserted={res.get('inserted')}")
        inserted += int(res.get("inserted") or 0)
        results.append(item)
        time.sleep(hb.GAP_S)
    payload = {
        "at": hk, "game_time": gt, "tick_s": tick_s,
        "targets": [f"{r}@{b}" for r,b in TARGETS],
        "results": results, "inserted": inserted,
        "still_404": still_404, "recovered": recovered,
        "at_finish": datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"),
    }
    (DIR / "backfill_late_retry.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(f"recovered={recovered} still_404={still_404} inserted={inserted}")
    print("finished", payload["at_finish"])

if __name__ == "__main__":
    main()
