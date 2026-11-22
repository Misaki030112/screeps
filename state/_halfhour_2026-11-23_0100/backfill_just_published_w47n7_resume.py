#!/usr/bin/env python3
"""Resume just-published 84424800 for W47N7 after a transient SSL error; do not touch pre_counts."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

sys.path.insert(0, "/workspace/screeps/state/_halfhour_2026-11-23_0100")
import backfill_confirm as confirm

JUST_BASE = 84424800
DIR = Path("/workspace/screeps/state/_halfhour_2026-11-23_0100")
OUT = DIR / f"just_published_{JUST_BASE}.json"
HK = ZoneInfo("Asia/Hong_Kong")
ROOMS_DONE = [
    {"t": "01:08:38", "room": "W46N8", "base": JUST_BASE, "code": 200, "ticks": 100, "ts": 1795367164055, "game_time": 84424942, "ok": True, "inserted": 589, "nfix": 0},
    {"t": "01:08:42", "room": "W47N8", "base": JUST_BASE, "code": 200, "ticks": 100, "ts": 1795367197039, "game_time": 84424942, "ok": True, "inserted": 392, "nfix": 0},
    {"t": "01:08:47", "room": "W45N8", "base": JUST_BASE, "code": 200, "ticks": 100, "ts": 1795367195519, "game_time": 84424942, "ok": True, "inserted": 442, "nfix": 0},
    {"t": "01:08:50", "room": "W45N7", "base": JUST_BASE, "code": 200, "ticks": 100, "ts": 1795367166048, "game_time": 84424942, "ok": True, "inserted": 312, "nfix": 0},
]

def main():
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
        live = json.loads(Path("/workspace/screeps/metrics/live.json").read_text())
        st = live.get("stats") if isinstance(live.get("stats"), dict) else {}
        gt = live.get("gameTime") or st.get("t")
        print(f"fell back to live game.time={gt}", flush=True)
    with db.connect() as c:
        cm = db.current_commit(c)
    with db.connect() as c:
        d, mn, mx, n = confirm.db_range(c, "W47N7", JUST_BASE)
    print(f"W47N7 resume start {hk} game.time={gt} tick_s={tick_s} pre distinct={d} rows={n} range={mn}..{mx}", flush=True)
    res = None
    last_err = None
    for attempt in range(4):
        try:
            res = confirm.retry_one("W47N7", JUST_BASE, our, now_ts, gt, tick_s=tick_s, cm=cm)
            break
        except Exception as e:
            last_err = e
            print(f"  W47N7 attempt {attempt+1} failed: {e!r}", flush=True)
            time.sleep(5 * (attempt + 1))
    if res is None:
        raise SystemExit(f"W47N7 retry failed after 4 attempts: {last_err!r}")
    rec = {
        "t": res["at"], "room": "W47N7", "base": JUST_BASE, "code": res["status"],
        "ticks": res.get("ticks", 0), "ts": res.get("ts"), "game_time": gt,
        "ok": res["ok"], "inserted": res["inserted"], "nfix": res.get("nfix", 0),
        "db_distinct": res.get("db_distinct"), "db_min": res.get("db_min"),
        "db_max": res.get("db_max"), "db_rows": res.get("db_rows"),
    }
    print(f"  W47N7 ok={res['ok']} status={res['status']} ticks={res.get('ticks')} ts={res.get('ts')} inserted={res['inserted']} nfix={res.get('nfix', 0)}", flush=True)

    # fill db_* for the already-successful rooms from current DB (do not change pre_counts)
    gets = []
    with db.connect() as c:
        for g in ROOMS_DONE:
            d, mn, mx, n = confirm.db_range(c, g["room"], JUST_BASE)
            g = dict(g)
            g.update({"db_distinct": d, "db_min": mn, "db_max": mx, "db_rows": n})
            gets.append(g)
    gets.append(rec)
    recovered = [f"{g['room']}@{JUST_BASE}" for g in gets if g.get("ok")]
    still_404 = [f"{g['room']}@{JUST_BASE}" for g in gets if not g.get("ok")]
    inserted = sum(int(g.get("inserted") or 0) for g in gets)
    ts_realigned = sum(int(g.get("nfix") or 0) for g in gets)
    payload = {
        "game_time": 84424942,
        "at": "2026-11-23 01:08:36 Asia/Hong_Kong",
        "pass": "just_published",
        "base": JUST_BASE,
        "threshold": 84424940,
        "tick_s": tick_s,
        "gets": gets,
        "recovered": recovered,
        "still_404": still_404,
        "inserted": inserted,
        "ts_realigned": ts_realigned,
        "waited_live_gt": 84424940,
        "w47n7_ssl_resume": {"at": hk, "game_time": gt, "attempts": "retried after SSL EOF on first pass"},
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {OUT} recovered={recovered} still_404={still_404} inserted={inserted}", flush=True)
    # append note to JP log without rewriting the first-pass story
    with (DIR / "backfill_just_published.txt").open("a") as f:
        f.write(f"W47N7 SSL resume at {hk} gt={gt} ok={res['ok']} status={res['status']} inserted={res['inserted']} ticks={res.get('ticks')} ts={res.get('ts')}\n")
        f.write(f"recovered={recovered} still_404={still_404} inserted={inserted} ts_realigned={ts_realigned}\n")
        f.write("finished after W47N7 SSL resume\n")

if __name__ == "__main__":
    main()
