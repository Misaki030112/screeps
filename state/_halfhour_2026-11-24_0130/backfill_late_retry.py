#!/usr/bin/env python3
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api
sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-24_0130")
import backfill_confirm as confirm

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-24_0130")
HK = ZoneInfo("Asia/Hong_Kong")
TARGETS = [
    ("W45N7", 84444900),  # NOT YET TOLD leftover from quiet 0100 first-pass; still in window start 84444801; still 404 at this 0130 first pass; listener 0/100; do not relabel NEW
    ("W47N8", 84445100),  # NOT YET TOLD leftover from quiet 0100 JP; still in window start 84444801; still 404 at this 0130 first pass; listener 3/100; do not relabel NEW
    ("W46N8", 84444500),  # NOT YET TOLD leftover from quiet 0030; aged out of window start 84444801; retry as near-window; listener 0/100; do not relabel NEW
    ("W46N8", 84444200),  # NOT YET TOLD leftover from quiet 0000 JP; aged out of window start 84444801; retry as near-window; listener 0/100; do not relabel NEW
    ("W47N8", 84443800),  # NOT YET TOLD leftover from quiet 2330 JP; aged out of window start 84444801; retry as near-window; listener already 100/100; do not relabel NEW
    ("W47N7", 84443300),  # already told in 23:33 2321 patrol; aged out of window start 84444801; retry as near-window; do not relabel NEW
    ("W45N7", 84441900),  # already told in 23:33 2321 patrol; aged out of window start 84444801; retry as near-window; do not relabel NEW
    ("W47N7", 84440900),  # already told in 20:44 2028 patrol (also mentioned in 23:33 2321); aged out of window start 84444801; retry as near-window; do not relabel NEW
    ("W45N8", 84439200),  # already told in 20:44 2028 patrol; aged out of window start 84444801; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # already told in 20:44 2028 patrol; aged out of window start 84444801; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # already told in 20:44 2028 patrol; aged out of window start 84444801; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # already told in 20:44 2028 patrol; aged out of window start 84444801; retry as near-window; do not relabel NEW
]  # W45N8@84437100 and W47N7@84436400 already told in 17:46 1728 patrol; not retried

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
