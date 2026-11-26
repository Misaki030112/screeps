#!/usr/bin/env python3
from pathlib import Path
NL = chr(10)
import json, sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api
sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-24_1230")
import backfill_confirm as confirm

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-24_1230")
TARGETS = [
    ("W46N8", 84454300),  # first-pass in-window official 404 this 1230 pass at gt=84454741; still 404 through confirm 12:41:22 / retry2 12:42:25 / late 12:43:xx official inserted=0; other four rooms already 200; +409 past chunk close 84454400 at late gt=84454809; retry in postjp; do not label leftover official 404 or NEW until postjp stays 404
    ("W47N7", 84454200),  # just-published official 404 this 1200 pass; still 404 through JP GET 12:10:48 gt=84454354 / retry 12:14:18 gt=84454400 / retry2 12:21:30 gt=84454500 official inserted=0; other four rooms already 200 at first JP; retry in postjp
    ("W46N8", 84454100),  # first-pass in-window official 404 this 1200 pass at gt=84454245; other four rooms already 200 on 84454100; may still be publish lag (only +45 past chunk close 84454200 at first pass); retry; do not label leftover official 404 or NEW until later retries stay 404 well past close
    ("W47N7", 84452600),  # first-pass in-window official 404 this 1030 pass at gt=84452986; other four rooms already 200 on 84452600; retry; do not label leftover official 404 or NEW until later retries stay 404 well past close
    ("W47N7", 84451700),  # first-pass in-window official 404 this 0900 pass at gt=84451819; other four rooms already 200 on 84451700; may still be publish lag (only +19 past chunk close 84451800); retry; do not label leftover official 404 or NEW until later retries stay 404 well past close
    ("W46N8", 84450800),  # already told in ~08:31 0820; in-window official 404 this 0830 first pass; retry; do not relabel NEW
    ("W46N8", 84450500),  # already told in ~08:31 0820; leftover from quiet 0730 JP; retry as near-window; do not relabel NEW
    ("W46N8", 84448500),  # already told in ~05:38 0522 / ~08:31 0820; aged out; retry as near-window; do not relabel NEW
    ("W45N8", 84448600),  # already told in ~05:38 0522 / ~08:31 0820; aged out; retry as near-window; do not relabel NEW
    ("W47N8", 84448400),  # already told in ~05:38 0522 / ~08:31 0820; aged out; retry as near-window; do not relabel NEW
    ("W47N8", 84447700),  # already told in ~05:38 0522 / ~08:31 0820; aged out; retry as near-window; do not relabel NEW
    ("W45N8", 84447400),  # already told in ~05:38 0522 / ~08:31 0820; aged out; retry as near-window; do not relabel NEW
    ("W47N7", 84446600),  # already told in ~05:38 0522 / ~08:31 0820; aged out; retry as near-window; do not relabel NEW
    ("W46N8", 84445500),  # already told in ~02:34 0221; aged out; retry as near-window; do not relabel NEW
    ("W45N7", 84444900),  # already told in ~02:34 0221; aged out; retry as near-window; do not relabel NEW
    ("W47N8", 84445100),  # already told in ~02:34 0221; aged out; retry as near-window; do not relabel NEW
    ("W46N8", 84444500),  # already told in ~02:34 0221; aged out; retry as near-window; do not relabel NEW
    ("W46N8", 84444200),  # already told in ~02:34 0221; aged out; retry as near-window; do not relabel NEW
    ("W47N8", 84443800),  # already told in ~02:34 0221; aged out; retry as near-window; do not relabel NEW
    ("W47N7", 84443300),  # already told in ~23:33 2321 / 0221; aged out; retry as near-window; do not relabel NEW
    ("W45N7", 84441900),  # already told in ~23:33 2321 / 0221; aged out; retry as near-window; do not relabel NEW
    ("W47N7", 84440900),  # already told in ~20:44 2028; aged out; retry as near-window; do not relabel NEW
    ("W45N8", 84439200),  # already told in ~20:44 2028; aged out; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # already told in ~20:44 2028; aged out; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # already told in ~20:44 2028; aged out; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # already told in ~20:44 2028; aged out; retry as near-window; do not relabel NEW
]  # older already-told leftovers aged out; not relabeled NEW

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
