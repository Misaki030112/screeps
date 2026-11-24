#!/usr/bin/env python3
from pathlib import Path
NL = chr(10)
import json, sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api
sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-24_0730")
import backfill_confirm as confirm

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-24_0730")
TARGETS = [
    ("W46N8", 84450500),  # NEW just-published official 404 this 0730 pass; first JP GET 07:44:54 gt=84450643 / retry 07:48:57 gt=84450700 / retry2 07:56:04 gt=84450800 still 404 official inserted=0; other four rooms already 200 at first JP +143; 200 ticks past chunk close 84450600 at retry2, not mere publish lag; outside TMAX=84450500; retry
    ("W46N8", 84448500),  # NEW first-pass in-window official 404 at this 0530 first pass gt=84448834; other four rooms already 200 on 84448500; hole 84448501..84448600; retry
    ("W45N8", 84448600),  # NEW first-pass in-window official 404 at this 0530 first pass gt=84448834; other four rooms already 200 on 84448600; hole 84448601..84448700; retry
    ("W47N8", 84448400),  # NOT YET TOLD leftover from quiet 0500 JP; still in window start 84448101; still 404 at this 0530 first pass gt=84448834 (~334 ticks past chunk close 84448500); listener 0/100; other four rooms already 200 at 0500 JP +141; do not relabel NEW
    ("W47N8", 84447700),  # NOT YET TOLD leftover from quiet 0430 first-pass; aged out of window start 84448101; still 404 through 0500 postjp; listener 0/100; other four rooms already 200 at 0430 first pass; do not relabel NEW
    ("W45N8", 84447400),  # NOT YET TOLD leftover from quiet 0400 first-pass; aged out of window start 84447701; still 404 through 0430 postjp; listener 0/100; other four rooms already 200 at 0400 first pass; retry as near-window; do not relabel NEW
    ("W47N7", 84446600),  # NOT YET TOLD leftover from quiet 0300 first-pass; aged out of window start 84447701; still 404 through 0430 postjp; listener 0/100; other four rooms already 200 at 0300 confirm or later first pass; retry as near-window; do not relabel NEW
    ("W46N8", 84445500),  # already told in 02:34 0221 patrol; leftover from quiet 0130 JP; aged out of window start 84446401; listener already 100/100; retry as near-window; do not relabel NEW
    ("W45N7", 84444900),  # already told in 02:34 0221 patrol; leftover from quiet 0100 first-pass; aged out of window start 84446401; listener 0/100; retry as near-window; do not relabel NEW
    ("W47N8", 84445100),  # already told in 02:34 0221 patrol; leftover from quiet 0100 JP; aged out of window start 84446401; listener 3/100; retry as near-window; do not relabel NEW
    ("W46N8", 84444500),  # already told in 02:34 0221 patrol; leftover from quiet 0030; aged out of window start 84446401; listener 0/100; retry as near-window; do not relabel NEW
    ("W46N8", 84444200),  # already told in 02:34 0221 patrol; leftover from quiet 0000 JP; aged out of window start 84446401; listener 0/100; retry as near-window; do not relabel NEW
    ("W47N8", 84443800),  # already told in 02:34 0221 patrol; leftover from quiet 2330 JP; aged out of window start 84446401; listener already 100/100; retry as near-window; do not relabel NEW
    ("W47N7", 84443300),  # already told in 23:33 2321 / 02:34 0221 patrols; aged out of window start 84446401; retry as near-window; do not relabel NEW
    ("W45N7", 84441900),  # already told in 23:33 2321 / 02:34 0221 patrols; aged out of window start 84446401; retry as near-window; do not relabel NEW
    ("W47N7", 84440900),  # already told in 20:44 2028 patrol; aged out of window start 84446401; retry as near-window; do not relabel NEW
    ("W45N8", 84439200),  # already told in 20:44 2028 patrol; aged out of window start 84446401; retry as near-window; do not relabel NEW
    ("W45N8", 84439300),  # already told in 20:44 2028 patrol; aged out of window start 84446401; retry as near-window; do not relabel NEW
    ("W45N8", 84439500),  # already told in 20:44 2028 patrol; aged out of window start 84446401; retry as near-window; do not relabel NEW
    ("W47N7", 84438700),  # already told in 20:44 2028 patrol; aged out of window start 84446401; retry as near-window; do not relabel NEW
]  # W45N8@84437100 and W47N7@84436400 already told in 17:46 1728 patrol; not retried

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
