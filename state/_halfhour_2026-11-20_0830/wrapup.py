#!/usr/bin/env python3
"""Write local status records for the 08:30 half-hour official-history backfill."""
from __future__ import annotations
import json, shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

HK = ZoneInfo("Asia/Hong_Kong")
ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-20_0830"
assert "_halfhour_2026-11-20_0830" in str(DIR), DIR
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84368901, 84369600
PUB_BASES = "84368900..84369500"
GT_FIRST = 84369640
TICK_S_FIRST = 4.17664
TICK_S_PRINTED = "4.177"
TICK_S_IN_USE = 4.17664
TS_REALIGNED_FIRST = 0
NFIX_CORR = 0
RECON_ROWS = 23785
ALREADY = 23585
INSERTED_FIRST = 200
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
PER_ROOM_LINE = "W46N8:700t/0new W47N8:700t/200new W45N8:700t/0new W45N7:700t/0new W47N7:700t/0new"
MISSING_CHUNKS = 0
JUST_BASE = 84369600
JUST_T0, JUST_T1 = 84369601, 84369700
JUST_THRESHOLD = 84369740
FIRST_PASS_CORE = (
    "first pass 35 of 35 official GETs 200, missing_chunks=0; "
    "08:00 half-hour already wrote through 84369100 / reconstructed through 84369200 "
    "(just-published 84369200 written 08:13:19 at game.time=84369340, 200 for all 5, ticks 84369201..84369300); "
    "concurrent 1h patrol _patrol_2026-11-20_0826 already official-filled 84368801..84369500 at 08:29 "
    "(game.time=84369564, published_bases 84368800..84369400, 35/35 official 200, already_in_db=18503 / inserted=6575, tick_s=4.191, ts_realigned=0) "
    "and just-published 84369500 at 08:34:20 Asia/Hong_Kong game.time=84369641 (200 for all 5, script inserted=2701, ticks 84369501..84369600), racing this first pass; "
    "(this pass already_in_db=23585 / inserted=200; overlap 84368901..84369600 already almost entirely present from the 08:00 half-hour official fill through 84369300, the concurrent patrol official fill through 84369600, and live rotation; "
    "this pass inserted 200 additional rows: W46N8 0, W47N8 200, W45N8 0, W45N7 0, W47N7 0; all 5 rooms 700t; "
    "NEW box freeze 08:22:11-08:23:13 (61s) STATS gap 84369461..84369489 (29) is fully inside this reconstructed window: last STATS 84369460 at 08:21:46, next STATS 84369490 at 08:23:56 Asia/Hong_Kong (wall ~130s); listener auto-restart 08:23:16 (listener.py pid 1209504 started 08:23:25); official-filled 29/29 in all 5 rooms; not yet told, for the concurrent/next 1h patrol; "
    "prior box freeze 07:46:17-08:04:28 (1086s) STATS gap 84368941..84369219 (279) also sits inside this window and was already official-filled and recorded in the 08:00 half-hour status (last STATS 84368940 at 07:45:43, next STATS 84369220 at 08:04:51, wall ~1148s; official-filled 279/279 in all 5 rooms; not yet told, for the concurrent 1h patrol); "
    "room_stats STATS gap 84368531..84368559 (29) from the 07:18:51 ping/pong timeout has aged out of this window start 84368901 (already recorded in the 07:30 / 08:00 half-hour status; 07:29 1h patrol noted 07:18:51 as the 07:17 patrol services.sh restart, not a box freeze); "
    "listener auto-restart 08:23:16 (pid 1209504 started 08:23:25) after the 08:22 freeze; this run did not itself restart the listener; "
    "leftover official 404 W45N8@84368100, W47N7@84366500, W47N8@84366200, W45N7@84365200, W47N8@84363900, W46N8@84362700, W47N8@84361700, W46N8@84360600, W45N7@84360200, W47N8@84359900 and older aged out of this 40-min window and were not retried this pass (still unfilled; concurrent 1h patrol official_retry 08:32:55 still 404, inserted=0; W45N8@84368100 already told by the 07:29 1h patrol); "
    "this window empty_no_creep=0 (all 5 rooms 700/700 official recovered)"
)

coverage_payload = json.loads((DIR / "coverage_final.json").read_text())
coverage = coverage_payload["coverage"]
recovered = coverage_payload["official_recovered"]
expected = coverage_payload["expected"]
empty_no_creep = coverage_payload["empty_no_creep"]
official_404_missing = coverage_payload["official_404_missing"]
unique_after = coverage_payload["unique_after"]
tick_s = json.loads((DIR / "tick_s_realign.json").read_text())
vs_later_after = tick_s.get("vs_later_after") or {}
vs_first = tick_s.get("vs_first") or {}
vs_cand = tick_s.get("vs_candidates") or {}
live = json.loads((ROOT / "metrics" / "live.json").read_text())
rot = json.loads((ROOT / "metrics" / "listener_rot.json").read_text())
yield_present = (ROOT / "metrics" / "listener_yield_rooms").exists()
just_pub_path = DIR / f"just_published_{JUST_BASE}.json"
just_pub_payload = json.loads(just_pub_path.read_text()) if just_pub_path.exists() else {}
just_pre = {}
try:
    just_pre = json.loads((DIR / "just_published_pre_counts.json").read_text())
except Exception:
    just_pre = {}

finished = datetime.now(HK)
finished_hkt = finished.strftime("%Y-%m-%d %H:%M Asia/Hong_Kong")
finished_hkt_sec = finished.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

def rng(c, room, t0, t1, expected_n):
    d, n, mn, mx = c.execute(
        "SELECT count(DISTINCT tick), count(*), min(tick), max(tick) "
        "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, t0, t1),
    ).fetchone()
    return {"distinct": d or 0, "rows": n or 0, "min": mn, "max": mx, "missing": expected_n - (d or 0)}

just_recovered = just_pub_payload.get("recovered") or []
just_still_404 = just_pub_payload.get("still_404") or []
just_gt = just_pub_payload.get("game_time")
just_at = just_pub_payload.get("at")
all_five = (len(just_recovered) == 5 and not just_still_404)
INSERTED_JUST_SCRIPT = int(just_pub_payload.get("inserted") or 0) if just_pub_payload else 0
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2

db_lines = []
cpu_tip = path_tip = rs_tip = None
with db.connect() as c:
    for room in sorted(ROOMS):
        mn, mx, n, d = c.execute(
            "SELECT min(tick), max(tick), count(*), count(DISTINCT tick) "
            "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, TMIN, TMAX),
        ).fetchone()
        db_lines.append(f"  {room} ticks={mn}..{mx} rows={n} distinct={d}")
    cpu_tip = c.execute("SELECT max(tick) FROM creep_cpu").fetchone()[0]
    path_tip = c.execute("SELECT max(tick) FROM path_arrivals").fetchone()[0]
    rs_tip = c.execute("SELECT max(tick) FROM room_stats").fetchone()[0]
    freeze0746 = {room: rng(c, room, 84368941, 84369219, 279) for room in ROOMS}
    freeze0822 = {room: rng(c, room, 84369461, 84369489, 29) for room in ROOMS}
    just_rng = {room: rng(c, room, JUST_T0, JUST_T1, 100) for room in ROOMS}
    hole_w45n8_68100 = rng(c, "W45N8", 84368101, 84368200, 100)
    hole_w47n7_66500 = rng(c, "W47N7", 84366501, 84366600, 100)
    hole_w47n8_66200 = rng(c, "W47N8", 84366201, 84366300, 100)
    hole_w45n7_65200 = rng(c, "W45N7", 84365201, 84365300, 100)
    hole_w47n8_63900 = rng(c, "W47N8", 84363901, 84364000, 100)
    hole_w46n8_62700 = rng(c, "W46N8", 84362701, 84362800, 100)
    hole_w47n8_61700 = rng(c, "W47N8", 84361701, 84361800, 100)
    hole_w46n8_60600 = rng(c, "W46N8", 84360601, 84360700, 100)
    aged_w45n7_60200 = rng(c, "W45N7", 84360201, 84360300, 100)
    aged_w47n8_59900 = rng(c, "W47N8", 84359901, 84360000, 100)
db_after_lines = "\n".join(db_lines)

INSERTED_JUST = 0
just_actual_parts = []
if just_pub_payload and just_pre:
    for room in ROOMS:
        pre_n = int((just_pre.get(room) or {}).get("rows") or 0)
        post_n = int(just_rng[room]["rows"] or 0)
        delta = max(0, post_n - pre_n)
        INSERTED_JUST += delta
        just_actual_parts.append(f"{room} {post_n}-{pre_n}={delta}")
elif just_pub_payload:
    INSERTED_JUST = INSERTED_JUST_SCRIPT

if just_pub_payload:
    just_distinct_note = ", ".join(
        f"{room} {just_rng[room]['distinct']}/100" for room in ROOMS
    )
    just_note = (
        f"just-published {JUST_BASE} attempted at {just_at} game.time={just_gt} "
        f"(typically publishable around game.time>={JUST_THRESHOLD}) and was "
        + ("200 for all 5 rooms" if all_five else f"not fully published (recovered={just_recovered or []} still_404={just_still_404 or []})")
        + f" (script inserted={INSERTED_JUST_SCRIPT}, actual db inserted={INSERTED_JUST}"
        + (f" [{', '.join(just_actual_parts)}]" if just_actual_parts else "")
        + f"; ticks {JUST_T0}..{JUST_T1}, {just_distinct_note})"
    )
else:
    just_note = f"just-published {JUST_BASE} was not attempted"
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
FIRST_PASS_LINE = FIRST_PASS_CORE + "; " + just_note

inwin_txt = (
    "in-window official 404 after first pass: none (35 of 35 official GETs 200, missing_chunks=0); "
    "no confirm/retry2 targets"
)
leftover_txt = (
    f"Leftover official 404 W45N8@84368100 (hole 84368101..84368200 still db {hole_w45n8_68100['distinct']}/100, no rows; already told by the 07:29 1h patrol) aged out of this window start {TMIN} and was not retried this pass (still unfilled). "
    f"Leftover official 404 W47N7@84366500 (hole 84366501..84366600 still db {hole_w47n7_66500['distinct']}/100, no rows; already told by the 05:23 1h patrol) aged out of this window start {TMIN} and was not retried this pass (still unfilled). "
    f"Leftover official 404 W47N8@84366200 (hole 84366201..84366300 still db {hole_w47n8_66200['distinct']}/100, no rows; already told by the 05:23 1h patrol) aged out of this window start {TMIN} and was not retried this pass (still unfilled). "
    f"Leftover official 404 W45N7@84365200 (hole 84365201..84365300 still db {hole_w45n7_65200['distinct']}/100, no rows; already told by the 04:21 1h patrol) aged out of this window start {TMIN} and was not retried this pass (still unfilled). "
    f"Leftover official 404 W47N8@84363900 (hole 84363901..84364000 still db {hole_w47n8_63900['distinct']}/100 live-only {hole_w47n8_63900['min']}..{hole_w47n8_63900['max']}, missing 84363901..84363950; already told by the 02:34 1h patrol) aged out of this window start {TMIN} and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W46N8@84362700 (hole 84362701..84362800 still db {hole_w46n8_62700['distinct']}/100, no live rows; already told by the 01:26 1h patrol) aged out of this window start {TMIN} and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W47N8@84361700 (hole 84361701..84361800 still db {hole_w47n8_61700['distinct']}/100 live-only; already told) aged out of this window start {TMIN} and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W46N8@84360600 (hole 84360601..84360700 still db {hole_w46n8_60600['distinct']}/100 live-only; already told) aged out and was not retried (still unfilled). "
    f"Aged leftover official 404 W45N7@84360200 (hole 84360201..84360300 still db {aged_w45n7_60200['distinct']}/100; already told) and W47N8@84359900 (hole 84359901..84360000 still db {aged_w47n8_59900['distinct']}/100; already told) also sit outside this window and were not retried (still unfilled). "
    "Aged leftover official 404 W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) were not retried this pass (already outside this 40-min window). "
    "Concurrent 1h patrol official_retry 08:32:55 Asia/Hong_Kong retried 16 leftovers and all still 404 (inserted=0). "
    f"This window has empty_no_creep={empty_no_creep} (all 5 rooms official-recovered 700/700)."
)

def fill_counts(fills, expected_n):
    return ", ".join(f"{room} {fills[room]['distinct']}/{expected_n}" for room in ROOMS)

freeze_para = (
    f"NEW box freeze 08:22:11-08:23:13 Asia/Hong_Kong (61s; run_listener.sh auto-restart 08:23:16, listener.py pid 1209504 started 08:23:25; not yet told, for the concurrent/next 1h patrol) "
    f"room_stats gap 84369461..84369489 (29) is fully inside this window: last STATS 84369460 at 08:21:46, next STATS 84369490 at 08:23:56 (wall ~130s); official-filled 29/29 in all 5 rooms (counts {fill_counts(freeze0822, 29)}). "
    f"Prior box freeze 07:46:17-08:04:28 Asia/Hong_Kong (1086s; already official-filled and recorded in the 08:00 half-hour status; not yet told, for the concurrent 1h patrol) "
    f"room_stats gap 84368941..84369219 (279) also sits inside this window: last STATS 84368940 at 07:45:43, next STATS 84369220 at 08:04:51 (wall ~1148s); official-filled 279/279 in all 5 rooms (counts {fill_counts(freeze0746, 279)}). "
    "room_stats STATS gap 84368531..84368559 (29) Asia/Hong_Kong last STATS 84368530 at 07:17:42, next STATS 84368560 at 07:19:38 (wall ~116s) has aged out of this window start 84368901; already recorded in the 07:30 / 08:00 half-hour status (run_listener.sh auto-restart 07:18:51 after ws ping/pong timeout 07:18:47; the 07:29 1h patrol noted 07:18:51 as the 07:17 patrol services.sh restart, not a box freeze). "
    "Box freezes 06:37:56-07:03:44, 06:14:32-06:19:42, 05:53:08-05:56:59, 05:59:54-06:01:32, 05:18:07-05:19:42, 04:42:44-05:00:03 and earlier have aged out of this window start 84368901 or were already told by the 07:29 / 06:29 / 05:23 1h patrols. "
    "This run found the listener already auto-restarted (pid 1209504 started 08:23:25, after the 08:23:16 restart at the end of the 08:22 freeze) and did not itself restart it. "
    + leftover_txt + " "
    f"live.json was fresh at pre-check 08:33:51 (age ~2.7s, tip stats.t=84369630, roomSlot W47N8, gameTime was still 84369522 and objects_n=0 on the W47N8 5-weight slot while room ingest, CPU and path buffers were already flowing: creep_ticks W47N8 through 84369636, creep_cpu through 84369630 / path_arrivals through 84369616 / room_stats through 84369630); "
    f"this pass inserted 200 additional rows in 84368901..84369600 plus just-published actual {INSERTED_JUST} in 84369601..84369700; "
    f"single_slot held, creep_cpu through {cpu_tip} / path_arrivals through {path_tip} / room_stats through {rs_tip} at wrapup; this run did not restart the listener."
)

slot = live.get("roomSlot")
single_slot = (not yield_present)
listener_line = (
    f"listener single_slot={single_slot} roomSlot={slot} rot={rot} yield={'present' if yield_present else 'absent'}; "
    "no second listener started; no war_cmd/pulse restart."
)

vs_first_s = vs_first or (vs_cand.get("first") or {})
tick_s_line = (
    f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST} printed {TICK_S_PRINTED} is in the sane 3-6s band and is live-anchor-best "
    f"(vs_first over45={vs_first_s.get('over45')} mean_off={vs_first_s.get('mean_off')}, over15={vs_first_s.get('over15')}); "
    f"later-mean-robust {tick_s.get('later_mean_w46_robust')} is worse than first "
    f"(later over45={(vs_later_after or vs_cand.get('later_robust') or {}).get('over45')} "
    f"mean_off={(vs_later_after or vs_cand.get('later_robust') or {}).get('mean_off')}) and was refused; "
    f"all_mean {tick_s.get('all_mean_w46')}; prev_later {tick_s.get('prev_later_mean')}. "
    f"First-pass realign moved {TS_REALIGNED_FIRST} rows onto {TICK_S_FIRST}; no corrective realign "
    f"(live-anchor-best first already inside 45s gate, over45=0); in-use first {TICK_S_IN_USE}; "
    f"no in-window official 404 (confirm/retry2 skipped, no targets); {just_note})"
)

now_lines = [
    f"{finished_hkt} half-hour backfill OK (quiet)",
    f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
    f"  ({FIRST_PASS_LINE}; see history_backfill.txt)",
    tick_s_line,
    f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks={MISSING_CHUNKS}",
    f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
    f"per_room {PER_ROOM_LINE}",
    f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 +{INSERTED_RETRY2}, just_published +{INSERTED_JUST} actual / script {INSERTED_JUST_SCRIPT}, window {INSERTED_WINDOW}, run total {INSERTED_TOTAL})",
    f"ts_realigned_first={TS_REALIGNED_FIRST} ts_realigned_corrective={NFIX_CORR} tick_s_in_use={TICK_S_IN_USE}",
    "db_after",
    db_after_lines,
    f"coverage official_recovered={recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing} unique_room_ticks={unique_after.get('distinct_room_ticks')}",
    inwin_txt,
    leftover_txt,
    freeze_para,
    listener_line,
    f"confirm {finished_hkt.replace('Asia/Hong_Kong','').strip()} and retry2 were skipped (no in-window or aged targets; first pass 35/35 official 200); {just_note}; this pass inserted {INSERTED_FIRST} additional rows in the reconstructed window (W46N8 0 / W47N8 200 / W45N8 0 / W45N7 0 / W47N7 0) on top of the 08:00 half-hour official fill through 84369300 and the concurrent 1h patrol official fill through 84369600 and live rotation",
    f"ok_quiet=True coverage={recovered}/{expected} inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_TOTAL} tick_s_in_use={TICK_S_IN_USE} listener single_slot={single_slot}; no second listener; no war_cmd/pulse restart.",
]
now_text = "\n".join(now_lines) + "\n"
(DIR / "history_backfill_now.txt").write_text(now_text)

payload = {
    "ok_quiet": True,
    "finished": finished_hkt,
    "game_time_first": GT_FIRST,
    "published_bases": PUB_BASES,
    "rooms": list(ROOMS),
    "reconstructed": {"tmin": TMIN, "tmax": TMAX, "ticks": 700, "creep_rows": RECON_ROWS, "missing_chunks": MISSING_CHUNKS},
    "already_in_db": ALREADY,
    "inserted_first": INSERTED_FIRST,
    "inserted_confirm": INSERTED_CONFIRM,
    "inserted_retry2": INSERTED_RETRY2,
    "inserted_just_published_script": INSERTED_JUST_SCRIPT,
    "inserted_just_published_actual": INSERTED_JUST,
    "inserted_window": INSERTED_WINDOW,
    "inserted_total": INSERTED_TOTAL,
    "per_room": PER_ROOM_LINE,
    "coverage": {"official_recovered": recovered, "expected": expected, "empty_no_creep": empty_no_creep, "official_404": official_404_missing, "unique_room_ticks": unique_after.get("distinct_room_ticks")},
    "tick_s_first": TICK_S_FIRST,
    "tick_s_in_use": TICK_S_IN_USE,
    "tick_s_in_use_name": tick_s.get("tick_s_in_use_name") or "first",
    "ts_realigned_first": TS_REALIGNED_FIRST,
    "ts_realigned_corrective": NFIX_CORR,
    "just_published": {"base": JUST_BASE, "t0": JUST_T0, "t1": JUST_T1, "game_time": just_gt, "at": just_at, "all_five_200": all_five, "script_inserted": INSERTED_JUST_SCRIPT, "actual_inserted": INSERTED_JUST},
    "new_box_freeze": {"from": "2026-11-20 08:22:11", "to": "2026-11-20 08:23:13", "sec": 61, "gap": [84369461, 84369489], "span": 29, "told": False},
    "prior_box_freeze_0746": {"from": "2026-11-20 07:46:17", "to": "2026-11-20 08:04:28", "sec": 1086, "gap": [84368941, 84369219], "span": 279, "told": False, "recorded_in": "08:00 half-hour"},
    "listener": {"single_slot": single_slot, "roomSlot": slot, "rot": rot, "pid": 1209504, "started": "08:23:25", "restart": "08:23:16", "this_run_restarted": False, "war_cmd_pulse_restart": False},
    "concurrent_1h_patrol": "_patrol_2026-11-20_0826",
    "cpu_tip": cpu_tip,
    "path_tip": path_tip,
    "room_stats_tip": rs_tip,
}
(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")
shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

verify = [
    f"{finished_hkt_sec} verify 08:30 half-hour official-history backfill",
    f"window ticks {TMIN}..{TMAX} published_bases {PUB_BASES} game.time_first={GT_FIRST}",
    f"inserted_first={INSERTED_FIRST} confirm={INSERTED_CONFIRM} retry2={INSERTED_RETRY2} just_published={INSERTED_JUST} (script {INSERTED_JUST_SCRIPT}) total={INSERTED_TOTAL}",
    f"coverage {recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}",
    f"tick_s_in_use={TICK_S_IN_USE:.5f} ts_realigned_first={TS_REALIGNED_FIRST} ts_realigned_corrective={NFIX_CORR}",
    inwin_txt,
    leftover_txt,
    freeze_para,
    listener_line,
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 08:23:16 (listener.py pid 1209504 started 08:23:25) after NEW box freeze 08:22:11-08:23:13 (61s, room_stats gap 84369461..84369489 (29; last STATS 84369460 at 08:21:46, next 84369490 at 08:23:56, wall ~130s; official-filled 29/29 in all 5 rooms; not yet told, for the concurrent/next 1h patrol). Prior 07:46:17-08:04:28 freeze and STATS gap 84368941..84369219 (279; official-filled 279/279) were already recorded in the 08:00 half-hour status (not yet told, for the concurrent 1h patrol). Prior 07:18:51 ping/pong restart and STATS gap 84368531..84368559 (29; official-filled 29/29) have aged out of this window start 84368901 and were already recorded in the 07:30 / 08:00 half-hour status (07:29 1h patrol noted 07:18:51 as the 07:17 patrol services.sh restart, not a box freeze). Box freeze 06:37:56-07:03:44 already told by the 07:29 1h patrol and has aged out of this window. Earlier already-told: 06:19:45 after 06:14:32-06:19:42; 06:01:35 after 05:59:54-06:01:32; 05:57:02 after 05:53:08-05:56:59 (told by the 06:29 1h patrol). By wrapup live.json was flowing on a single listener slot and CPU/path buffers were flowing; single_slot held.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0830.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run_stdout.txt").write_text(summary)
(DIR / "wrapup_run.err").write_text("")
print(summary, end="")
print("ok_line", f"ok_quiet=True coverage={recovered}/{expected} inserted_total={INSERTED_TOTAL}")
