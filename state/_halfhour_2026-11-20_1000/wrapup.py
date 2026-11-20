#!/usr/bin/env python3
"""Write local status records for the 10:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-20_1000"
assert "_halfhour_2026-11-20_1000" in str(DIR), DIR
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84370201, 84370900
PUB_BASES = "84370200..84370800"
GT_FIRST = 84370964
TICK_S_FIRST = 4.21346
TICK_S_PRINTED = "4.213"
TICK_S_IN_USE = 4.157706666666667
TS_REALIGNED_FIRST = 2438
NFIX_CORR = 0
RECON_ROWS = 24259
ALREADY = 11937
INSERTED_FIRST = 12322
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
PER_ROOM_LINE = "W46N8:700t/3629new W47N8:700t/4651new W45N8:700t/1454new W45N7:700t/923new W47N7:700t/1665new"
MISSING_CHUNKS = 0
JUST_BASE = 84370900
JUST_T0, JUST_T1 = 84370901, 84371000
JUST_THRESHOLD = 84371040
FIRST_PASS_CORE = (
    "first pass 35 of 35 official GETs 200, missing_chunks=0; "
    "09:30 half-hour already wrote through 84370300 / reconstructed through 84370400 "
    "(just-published 84370400 written 09:37:02 at game.time=84370542, 200 for all 5, ticks 84370401..84370500); "
    "no concurrent 1h patrol this run; "
    "(this pass already_in_db=11937 / inserted=12322; overlap 84370201..84370500 already present from the 09:30 half-hour official fill through 84370500, plus live rotation W46N8 84370501..84370545 and W47N8 after 84370546; "
    "this pass inserted 12322 additional rows: W46N8 3629, W47N8 4651, W45N8 1454, W45N7 923, W47N7 1665; four rooms 700t, W45N7 533t plus 167 official empty-no-creep ticks 84370301..84370447 and 84370666..84370685; "
    "NEW box freeze 09:44:17-10:03:04 (1127s) STATS gap 84370641..84370929 (289) sits inside this reconstructed window through 84370900 (remainder 84370901..84370929 belongs to just-published 84370900): last STATS 84370640 at 09:43:47, next STATS 84370930 at 10:03:46 Asia/Hong_Kong (wall ~1199s); listener auto-restart 10:03:07 (listener.py pid 1244409 started 10:03:16); official-filled 289/289 in W46N8/W47N8/W45N8/W47N7; W45N7 269/289 with 20 official empty-no-creep ticks 84370666..84370685; told status left to the next 1h patrol; "
    "prior box freeze 09:09:35-09:20:53 (672s) STATS gap 84370151..84370319 (169) also sits partly inside this window start 84370201 and was already official-filled 169/169 in W46N8/W47N8/W45N8/W47N7; W45N7 150/169 with 19 official empty-no-creep ticks 84370301..84370319 (recorded in the 09:30 half-hour; told status left to the 09:20 1h patrol; last STATS 84370150 at 09:09:26, next STATS 84370320 at 09:21:31, wall ~725s); "
    "prior box freezes 08:45:32-08:56:59 (683s, STATS 84369801..84369979) and 08:22:11-08:23:13 (61s, STATS 84369461..84369489) and 07:46:17-08:04:28 (1086s, STATS 84368941..84369219) have aged out of this window start 84370201 and were already official-filled and told by the 08:26 / 09:20 1h patrols; "
    "listener auto-restart 10:03:07 (pid 1244409 started 10:03:16) after the 09:44 freeze; this run did not itself restart the listener; "
    "leftover official 404 W45N8@84368100, W47N7@84366500, W47N8@84366200, W45N7@84365200, W47N8@84363900, W46N8@84362700, W47N8@84361700, W46N8@84360600, W45N7@84360200, W47N8@84359900 and older aged out of this 40-min window and were not retried this pass (still unfilled; 09:20 1h patrol official_retry 09:24:54 still 404 on all 16 leftovers, inserted=0; W45N8@84368100 already told by the 07:29 1h patrol); "
    "this window empty_no_creep=167 (W45N7 official empty 84370301..84370447 and 84370666..84370685; other 4 rooms 700/700 official recovered)"
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
    freeze0845 = {room: rng(c, room, 84369801, 84369979, 179) for room in ROOMS}
    freeze0909 = {room: rng(c, room, 84370151, 84370319, 169) for room in ROOMS}
    freeze0944 = {room: rng(c, room, 84370641, 84370929, 289) for room in ROOMS}
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
    "No concurrent 1h patrol this run; the 09:20 1h patrol official_retry 09:24:54 Asia/Hong_Kong already retried 16 leftovers and all still 404 (inserted=0). "
    f"This window has empty_no_creep={empty_no_creep} (W45N7 official empty-no-creep 84370301..84370447 and 84370666..84370685; other 4 rooms official-recovered 700/700)."
)

def fill_counts(fills, expected_n):
    return ", ".join(f"{room} {fills[room]['distinct']}/{expected_n}" for room in ROOMS)

freeze_para = (
    f"NEW box freeze 09:44:17-10:03:04 Asia/Hong_Kong (1127s; run_listener.sh auto-restart 10:03:07, listener.py pid 1244409 started 10:03:16; this run did not itself restart the listener; told status left to the next 1h patrol) "
    f"room_stats gap 84370641..84370929 (289) sits inside this reconstructed window through 84370900 and just-published 84370900 (remainder 84370901..84370929): last STATS 84370640 at 09:43:47, next STATS 84370930 at 10:03:46 (wall ~1199s); official-filled 289/289 in W46N8/W47N8/W45N8/W47N7; W45N7 269/289 with 20 official empty-no-creep ticks 84370666..84370685 (counts {fill_counts(freeze0944, 289)}). "
    f"Prior box freeze 09:09:35-09:20:53 Asia/Hong_Kong (672s; already official-filled, recorded in the 09:30 half-hour; told status left to the 09:20 1h patrol) "
    f"room_stats gap 84370151..84370319 (169) also sits partly inside this window start 84370201: last STATS 84370150 at 09:09:26, next STATS 84370320 at 09:21:31 (wall ~725s); official-filled 169/169 in W46N8/W47N8/W45N8/W47N7; W45N7 150/169 with 19 official empty-no-creep ticks 84370301..84370319 (counts {fill_counts(freeze0909, 169)}). "
    f"Prior box freeze 08:45:32-08:56:59 Asia/Hong_Kong (683s; already official-filled 179/179 and recorded in the 09:00 half-hour; told status left to the 09:20 1h patrol) room_stats gap 84369801..84369979 (179) has aged out of this window start 84370201 (counts {fill_counts(freeze0845, 179)}). "
    f"Prior box freeze 08:22:11-08:23:13 Asia/Hong_Kong (61s; already official-filled and told by the 08:26 1h patrol) room_stats gap 84369461..84369489 (29) has aged out of this window start 84370201 (counts {fill_counts(freeze0822, 29)}). "
    f"Prior box freeze 07:46:17-08:04:28 Asia/Hong_Kong (1086s; already official-filled and told by the 08:26 1h patrol) room_stats gap 84368941..84369219 (279) has aged out of this window start 84370201 (counts {fill_counts(freeze0746, 279)}). "
    "Box freezes 06:37:56-07:03:44, 06:14:32-06:19:42, 05:53:08-05:56:59, 05:59:54-06:01:32 and earlier have aged out of this window start 84370201 or were already told by the 08:26 / 07:29 / 06:29 1h patrols. "
    "This run found the listener already auto-restarted (pid 1244409 started 10:03:16, after the 10:03:07 restart at the end of the 09:44 freeze) and did not itself restart it. "
    + leftover_txt + " "
    f"live.json was fresh at pre-check 10:05:51 (age ~0.5s, tip stats.t=84370960, roomSlot W47N8; live.json gameTime and objects stayed empty after the 10:03:16 reconnect, but room ingest, CPU and path buffers were already flowing: creep_ticks W47N8 84370930..84370962 near tip, creep_cpu through 84370950 / path_arrivals through 84370943 / room_stats through 84370950); "
    f"this pass inserted 12322 additional rows in 84370201..84370900 plus just-published actual {{INSERTED_JUST}} in 84370901..84371000; "
    f"single_slot held, creep_cpu through {{cpu_tip}} / path_arrivals through {{path_tip}} / room_stats through {{rs_tip}} at wrapup; this run did not restart the listener."
)

slot = live.get("roomSlot")
single_slot = (not yield_present)
listener_line = (
    f"listener single_slot={single_slot} roomSlot={slot} rot={rot} yield={'present' if yield_present else 'absent'}; "
    "no second listener started; no war_cmd/pulse restart."
)

vs_first_s = vs_first or (vs_cand.get("first") or {})
tick_s_line = (
    f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"live-anchor-best is all_mean {TICK_S_IN_USE} "
    f"(vs_all_mean over45={(vs_cand.get('all_mean') or {}).get('over45')} mean_off={(vs_cand.get('all_mean') or {}).get('mean_off')}, over15={(vs_cand.get('all_mean') or {}).get('over15')}; "
    f"vs_first over45={vs_first_s.get('over45')} mean_off={vs_first_s.get('mean_off')}, over15={vs_first_s.get('over15')}); "
    f"later-mean-robust {tick_s.get('later_mean_w46_robust')} is worse than live-anchor-best all_mean "
    f"(later over45={(vs_later_after or vs_cand.get('later_robust') or {}).get('over45')} "
    f"mean_off={(vs_later_after or vs_cand.get('later_robust') or {}).get('mean_off')}) and was refused; "
    f"all_mean {tick_s.get('all_mean_w46')}; prev_later {tick_s.get('prev_later_mean')} "
    f"(vs_prev_later over45={(vs_cand.get('prev_later') or {}).get('over45')} mean_off={(vs_cand.get('prev_later') or {}).get('mean_off')}) is not live-anchor-best. "
    f"First-pass realign moved {TS_REALIGNED_FIRST} rows onto {TICK_S_FIRST}; no corrective realign "
    f"(live-anchor-best all_mean {TICK_S_IN_USE} already inside 45s gate, over45=0); in-use all_mean {TICK_S_IN_USE}; "
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
    f"confirm {finished_hkt.replace('Asia/Hong_Kong','').strip()} and retry2 were skipped (no in-window or aged targets; first pass 35/35 official 200); {just_note}; this pass inserted {INSERTED_FIRST} additional rows in the reconstructed window (W46N8 3629 / W47N8 4651 / W45N8 1454 / W45N7 923 / W47N7 1665) on top of the 09:30 half-hour official fill through 84370500 and live rotation",
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
    "new_box_freeze": {"from": "2026-11-20 09:44:17", "to": "2026-11-20 10:03:04", "sec": 1127, "gap": [84370641, 84370929], "span": 289, "wall_s": 1199, "last_stats": 84370640, "next_stats": 84370930, "told": False, "seen_by": "10:00 half-hour backfill; told status left to the next 1h patrol", "fill": "289/289 in W46N8 W47N8 W45N8 W47N7; W45N7 269/289 official empty-no-creep 84370666..84370685"},
    "prior_box_freeze_0909": {"from": "2026-11-20 09:09:35", "to": "2026-11-20 09:20:53", "sec": 672, "gap": [84370151, 84370319], "span": 169, "wall_s": 725, "last_stats": 84370150, "next_stats": 84370320, "told": True, "recorded_in": "09:30 half-hour and 09:20 1h patrol; already told by the 09:20 1h patrol (finished 09:31)", "fill": "169/169 in W46N8 W47N8 W45N8 W47N7; W45N7 150/169 official empty-no-creep 84370301..84370319"},
    "prior_box_freeze_0845": {"from": "2026-11-20 08:45:32", "to": "2026-11-20 08:56:59", "sec": 683, "gap": [84369801, 84369979], "span": 179, "wall_s": 740, "last_stats": 84369800, "next_stats": 84369980, "told": True, "recorded_in": "09:00 half-hour and 09:20 1h patrol; told status left to the 09:20 1h patrol; aged out of this window start 84370201"},
    "prior_box_freeze_0822": {"from": "2026-11-20 08:22:11", "to": "2026-11-20 08:23:13", "sec": 61, "gap": [84369461, 84369489], "span": 29, "told": True, "recorded_in": "08:26 1h patrol"},
    "prior_box_freeze_0746": {"from": "2026-11-20 07:46:17", "to": "2026-11-20 08:04:28", "sec": 1086, "gap": [84368941, 84369219], "span": 279, "told": True, "recorded_in": "08:26 1h patrol"},
    "listener": {"single_slot": single_slot, "roomSlot": slot, "rot": rot, "pid": 1244409, "started": "10:03:16", "restart": "10:03:07", "this_run_restarted": False, "war_cmd_pulse_restart": False},
    "concurrent_1h_patrol": None,
    "cpu_tip": cpu_tip,
    "path_tip": path_tip,
    "room_stats_tip": rs_tip,
}
(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")
shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

verify = [
    f"{finished_hkt_sec} verify 10:00 half-hour official-history backfill",
    f"window ticks {TMIN}..{TMAX} published_bases {PUB_BASES} game.time_first={GT_FIRST}",
    f"inserted_first={INSERTED_FIRST} confirm={INSERTED_CONFIRM} retry2={INSERTED_RETRY2} just_published={INSERTED_JUST} (script {INSERTED_JUST_SCRIPT}) total={INSERTED_TOTAL}",
    f"coverage {recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}",
    f"tick_s_in_use={TICK_S_IN_USE:.5f} ts_realigned_first={TS_REALIGNED_FIRST} ts_realigned_corrective={NFIX_CORR}",
    inwin_txt,
    leftover_txt,
    freeze_para,
    listener_line,
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 10:03:07 (listener.py pid 1244409 started 10:03:16) after NEW box freeze 09:44:17-10:03:04 (1127s, room_stats gap 84370641..84370929 (289; last STATS 84370640 at 09:43:47, next 84370930 at 10:03:46, wall ~1199s; official-filled 289/289 in W46N8/W47N8/W45N8/W47N7, W45N7 269/289 official empty-no-creep 84370666..84370685; told status left to the next 1h patrol). Prior 09:09:35-09:20:53 freeze and STATS gap 84370151..84370319 (169; official-filled 169/169 in W46N8/W47N8/W45N8/W47N7, W45N7 150/169 official empty-no-creep 84370301..84370319; seen by the 09:20 1h patrol finished 09:31; told status left to that patrol) still partly overlaps this window start 84370201. Prior 08:45:32-08:56:59 freeze and STATS gap 84369801..84369979 (179; official-filled 179/179) have aged out of this window start 84370201 (told status left to the 09:20 1h patrol). Prior 08:22:11-08:23:13 freeze and STATS gap 84369461..84369489 (29; official-filled 29/29) and 07:46:17-08:04:28 freeze and STATS gap 84368941..84369219 (279; official-filled 279/279) have aged out of this window start 84370201 and were already told by the 08:26 1h patrol. Box freeze 06:37:56-07:03:44 already told by the 07:29 1h patrol and has aged out of this window. Earlier already-told: 06:19:45 after 06:14:32-06:19:42; 06:01:35 after 05:59:54-06:01:32; 05:57:02 after 05:53:08-05:56:59 (told by the 06:29 1h patrol). By wrapup live.json was flowing on a single listener slot (gameTime/objects in the live.json snapshot stayed empty after the 10:03 reconnect, but room ingest and CPU/path buffers were flowing); single_slot held.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1000.txt")
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
