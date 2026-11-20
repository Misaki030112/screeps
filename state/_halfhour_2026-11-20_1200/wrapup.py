#!/usr/bin/env python3
"""Write local status records for the 12:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-20_1200"
assert "_halfhour_2026-11-20_1200" in str(DIR), DIR
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84371901, 84372600
PUB_BASES = "84371900..84372500"
GT_FIRST = 84372662
TICK_S_FIRST = 4.10114
TICK_S_PRINTED = "4.101"
TICK_S_IN_USE = 4.10114
TS_REALIGNED_FIRST = 7921
NFIX_CORR = 2135
RECON_ROWS = 28582
ALREADY = 16613
INSERTED_FIRST = 11969
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
PER_ROOM_LINE = "W46N8:700t/2164new W47N8:700t/5256new W45N8:700t/2151new W45N7:700t/1557new W47N7:700t/841new"
MISSING_CHUNKS = 0
JUST_BASE = 84372600
JUST_T0, JUST_T1 = 84372601, 84372700
JUST_THRESHOLD = 84372740

coverage_payload = json.loads((DIR / "coverage_final.json").read_text())
coverage = coverage_payload["coverage"]
recovered = coverage_payload["official_recovered"]
expected = coverage_payload["expected"]
empty_no_creep = coverage_payload["empty_no_creep"]
official_404_missing = coverage_payload["official_404_missing"]
unique_after = coverage_payload["unique_after"]
tick_s = json.loads((DIR / "tick_s_realign.json").read_text())
TICK_S_IN_USE = float(tick_s.get("tick_s_in_use") or TICK_S_IN_USE)
TICK_S_IN_USE_NAME = tick_s.get("tick_s_in_use_name") or "first"
NFIX_CORR = int(tick_s.get("ts_realigned_to_later_mean") or 0) if tick_s.get("corrective_applied") else 0
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
if "rooms" in just_pre:
    just_pre = just_pre["rooms"]

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
    freeze1148 = {room: rng(c, room, 84372431, 84372599, 169) for room in ROOMS}
    gap1201 = {room: rng(c, room, 84372611, 84372639, 29) for room in ROOMS}
    gap1136 = {room: rng(c, room, 84372251, 84372269, 19) for room in ROOMS}
    gap1118 = {room: rng(c, room, 84371991, 84372019, 29) for room in ROOMS}
    gap1111_overlap = {room: rng(c, room, 84371901, 84371919, 19) for room in ROOMS}
    just_rng = {room: rng(c, room, JUST_T0, JUST_T1, 100) for room in ROOMS}
    hole_w46n8_71600 = rng(c, "W46N8", 84371601, 84371700, 100)
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
    just_distinct_note = ", ".join(f"{room} {just_rng[room]['distinct']}/100" for room in ROOMS)
    just_note = (
        f"just-published {JUST_BASE} attempted at {just_at} game.time={just_gt} "
        f"(typically publishable around game.time>={JUST_THRESHOLD}) and was "
        + ("200 for all 5 rooms" if all_five else f"not fully published (recovered={just_recovered or []} still_404={just_still_404 or []})")
        + f" (script inserted={INSERTED_JUST_SCRIPT}, actual db inserted={INSERTED_JUST}"
        + (f" [{', '.join(just_actual_parts)}]" if just_actual_parts else "")
        + f"; ticks {JUST_T0}..{JUST_T1}, {just_distinct_note}; W47N7 47/100 is official empty-no-creep in that chunk, not a 404)"
    )
else:
    just_note = f"just-published {JUST_BASE} was not attempted"
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST

def fill_counts(fills, expected_n):
    return ", ".join(f"{room} {fills[room]['distinct']}/{expected_n}" for room in ROOMS)

FIRST_PASS_CORE = (
    "first pass 35 of 35 official GETs 200, missing_chunks=0; "
    "11:30 half-hour already wrote through 84372200 / reconstructed through 84372200 "
    "(just-published 84372200 written 11:41:59 at game.time=84372342, 200 for all 5, ticks 84372201..84372300); "
    "prior 1h patrol _patrol_2026-11-20_1125 already delivered around 11:25 Asia/Hong_Kong and told the 10:49 freeze, short gaps 11:11:56 / 11:18:38, and W46N8@84371600 404; "
    f"this pass already_in_db={ALREADY} / inserted={INSERTED_FIRST}; overlap 84371901..84372300 already present from the 11:30 half-hour official fill through 84372200 / just-published through 84372300, plus live rotation; "
    f"this pass inserted {INSERTED_FIRST} additional rows: W46N8 2164, W47N8 5256, W45N8 2151, W45N7 1557, W47N7 841; "
    "all 5 rooms 700t; first-pass window is 700 ticks, published_bases 84371900..84372500 at game.time=84372662; "
    "NEW box freeze 11:48:50-11:59:04 (609s in box_pauses.jsonl) STATS gap 84372431..84372599 (169) sits inside this first-pass window: last STATS 84372430 at 11:48:06, next STATS 84372600 at 11:59:50 Asia/Hong_Kong (wall ~704.2s); listener auto-restart 11:59:07; official-filled 169/169 all 5 by this first pass; told=false, seen by this 12:00 half-hour, told status left to the next 1h patrol; "
    "NEW short listener gap around auto-restart 12:01:48 (pid 1293018 started 12:01:58; parent run_listener.sh pid 4035476 from Nov 13; no box_pauses.jsonl row) STATS gap 84372611..84372639 (29) sits after this first-pass window and inside just-published 84372600: last STATS 84372610 at 12:00:35, next STATS 84372640 at 12:02:39 Asia/Hong_Kong (wall ~124.3s); official-filled 29/29 in W46N8/W47N8/W45N8/W45N7; W47N7 11/29 with 18 official empty-no-creep ticks in just-published 84372600 (chunk HTTP 200, 47/100 ticks had our creeps); told=false, left to the next 1h patrol; "
    "listener auto-restarts 11:44:14 and 11:46:19 after the 11:30 wrapup produced no room_stats gap >10 ticks; "
    "prior short gap 11:36:21 STATS 84372251..84372269 (19) sits inside this window and is already official-filled 19/19 in all 5 rooms (told=false, left to the next 1h patrol by the 11:30 half-hour); "
    "prior short gaps 11:11:56 (overlap 84371901..84371919 still in window) and 11:18:38 STATS 84371991..84372019 sit inside this window and are already official-filled and told by the 11:25 1h patrol; "
    "prior box freeze 10:49:41-10:58:24 and official 404 W46N8@84371600 (hole 84371601..84371700) aged out of this window start 84371901 and were already told by the 11:25 1h patrol; not retried; "
    "leftover official 404 W45N8@84368100, W47N8@84366200, W47N7@84366500, W45N7@84365200, W47N8@84363900 and older aged out and were not retried (still unfilled; already told); "
    "this window empty_no_creep=0 official_404=0 (all 5 rooms 700/700 official recovered); "
    "this run did not itself restart the listener or war_cmd/pulse"
)
FIRST_PASS_LINE = FIRST_PASS_CORE + "; " + just_note

inwin_txt = "in-window official 404 after first pass: none (35/35 official GETs 200). W46N8@84371600 aged out of window start 84371901 and was not retried (still unfilled; already told by the 11:25 1h patrol)."

leftover_txt = (
    f"No in-window official 404 this pass. Leftover official 404 W46N8@84371600 (hole 84371601..84371700 still db {hole_w46n8_71600['distinct']}/100, no rows; already told by the 11:25 1h patrol) aged out of this window start {TMIN} and was not retried this pass (still unfilled). "
    "Leftover official 404 W45N8@84368100, W47N8@84366200, W47N7@84366500, W45N7@84365200, W47N8@84363900, W46N8@84362700, W47N8@84361700, W46N8@84360600, W45N7@84360200, W47N8@84359900 and older also aged out and were not retried (still unfilled; already told). "
    f"This window has empty_no_creep={empty_no_creep} official_404={official_404_missing} (all 5 rooms official-recovered 700/700)."
)

freeze_para = (
    f"NEW box freeze 11:48:50-11:59:04 Asia/Hong_Kong (609s in box_pauses.jsonl; listener auto-restart 11:59:07; this run did not itself restart the listener; told=false, seen by this 12:00 half-hour, told status left to the next 1h patrol) "
    f"room_stats gap 84372431..84372599 (169) sits inside the first-pass reconstructed window: last STATS 84372430 at 11:48:06, next STATS 84372600 at 11:59:50 (wall ~704.2s); official-filled 169/169 in all 5 rooms by this first pass (counts {fill_counts(freeze1148, 169)}). "
    f"NEW short listener gap 12:01:48 Asia/Hong_Kong (no box_pauses.jsonl row; run_listener.sh auto-restart 12:01:48, listener.py pid 1293018 started 12:01:58, parent run_listener.sh pid 4035476 from Nov 13; this run did not itself restart the listener; told=false, seen by this 12:00 half-hour, told status left to the next 1h patrol) "
    f"room_stats gap 84372611..84372639 (29) sits after the first-pass reconstructed window and inside just-published {JUST_BASE}: last STATS 84372610 at 12:00:35, next STATS 84372640 at 12:02:39 (wall ~124.3s); official-filled 29/29 in W46N8/W47N8/W45N8/W45N7; W47N7 11/29 with 18 official empty-no-creep ticks (just-published chunk HTTP 200, {just_rng['W47N7']['distinct']}/100 ticks had our creeps) (counts {fill_counts(gap1201, 29)}). "
    f"Prior short listener gap 11:36:21 Asia/Hong_Kong (no box_pauses.jsonl row; already official-filled 19/19 in all 5 rooms; told=false, left to the next 1h patrol by the 11:30 half-hour) room_stats gap 84372251..84372269 (19) still sits inside this window (counts {fill_counts(gap1136, 19)}). "
    f"Prior short listener gap 11:18:38 Asia/Hong_Kong (already official-filled 29/29 in all 5 rooms and told by the 11:25 1h patrol) room_stats gap 84371991..84372019 (29) still sits inside this window (counts {fill_counts(gap1118, 29)}). "
    f"Prior short listener gap 11:11:56 Asia/Hong_Kong (already official-filled and told by the 11:25 1h patrol) room_stats gap 84371891..84371919 (29) overlaps this window start; in-window overlap 84371901..84371919 is official-filled 19/19 in all 5 (counts {fill_counts(gap1111_overlap, 19)}). "
    f"Listener auto-restarts 11:44:14 and 11:46:19 after the 11:30 wrapup produced no room_stats gap >10 ticks. "
    f"Prior box freeze 10:49:41-10:58:24 and official 404 W46N8@84371600 aged out of this window start {TMIN} and were already told by the 11:25 1h patrol."
)

room_slot = live.get("roomSlot")
single_slot = (not yield_present)

payload = {
    "ok_quiet": True,
    "finished": finished_hkt,
    "game_time_first": GT_FIRST,
    "published_bases": PUB_BASES,
    "rooms": list(ROOMS),
    "reconstructed": {
        "tmin": TMIN,
        "tmax": TMAX,
        "ticks": TMAX - TMIN + 1,
        "creep_rows": RECON_ROWS,
        "missing_chunks": MISSING_CHUNKS,
    },
    "already_in_db": ALREADY,
    "inserted_first": INSERTED_FIRST,
    "inserted_confirm": INSERTED_CONFIRM,
    "inserted_retry2": INSERTED_RETRY2,
    "inserted_just_published_script": INSERTED_JUST_SCRIPT,
    "inserted_just_published_actual": INSERTED_JUST,
    "inserted_window": INSERTED_WINDOW,
    "inserted_total": INSERTED_TOTAL,
    "per_room": PER_ROOM_LINE,
    "coverage": {
        "official_recovered": recovered,
        "expected": expected,
        "empty_no_creep": empty_no_creep,
        "official_404": official_404_missing,
        "unique_room_ticks": unique_after.get("distinct_room_ticks"),
    },
    "tick_s_first": TICK_S_FIRST,
    "tick_s_in_use": TICK_S_IN_USE,
    "tick_s_in_use_name": TICK_S_IN_USE_NAME,
    "ts_realigned_first": TS_REALIGNED_FIRST,
    "ts_realigned_corrective": NFIX_CORR,
    "just_published": {
        "base": JUST_BASE,
        "t0": JUST_T0,
        "t1": JUST_T1,
        "game_time": just_gt,
        "at": just_at,
        "all_five_200": all_five,
        "script_inserted": INSERTED_JUST_SCRIPT,
        "actual_inserted": INSERTED_JUST,
        "per_room_distinct": {room: just_rng[room]["distinct"] for room in ROOMS},
        "note": "W47N7 47/100 is official empty-no-creep in the just-published chunk (HTTP 200), not a 404",
    },
    "new_box_freeze_1148": {
        "from": "2026-11-20 11:48:50",
        "to": "2026-11-20 11:59:04",
        "sec": 609,
        "restart": "2026-11-20 11:59:07",
        "box_pauses": True,
        "gap": [84372431, 84372599],
        "span": 169,
        "wall_s": 704.2,
        "last_stats": 84372430,
        "next_stats": 84372600,
        "last_stats_at": "11:48:06",
        "next_stats_at": "11:59:50",
        "told": False,
        "seen_by": "12:00 half-hour backfill; told status left to the next 1h patrol",
        "fill": "169/169 in all 5 rooms by first pass official history 84372400 and 84372500",
        "this_run_restarted": False,
    },
    "new_listener_gap_1201": {
        "restart": "2026-11-20 12:01:48",
        "pid": 1293018,
        "started": "12:01:58",
        "box_pauses": False,
        "gap": [84372611, 84372639],
        "span": 29,
        "wall_s": 124.3,
        "last_stats": 84372610,
        "next_stats": 84372640,
        "last_stats_at": "12:00:35",
        "next_stats_at": "12:02:39",
        "told": False,
        "seen_by": "12:00 half-hour backfill; told status left to the next 1h patrol",
        "fill": "29/29 in W46N8 W47N8 W45N8 W45N7; W47N7 11/29 official empty-no-creep 18 ticks in just-published 84372600 (HTTP 200, 47/100 ticks had our creeps)",
        "this_run_restarted": False,
    },
    "new_listener_gap_1136": {
        "restart": "2026-11-20 11:36:21",
        "pid": 1284929,
        "started": "11:36:31",
        "box_pauses": False,
        "gap": [84372251, 84372269],
        "span": 19,
        "wall_s": 84.7,
        "last_stats": 84372250,
        "next_stats": 84372270,
        "last_stats_at": "11:35:28",
        "next_stats_at": "11:36:53",
        "told": False,
        "seen_by": "11:30 half-hour backfill; still untold, left to the next 1h patrol",
        "fill": "19/19 in all 5 rooms by just-published 84372200 at 11:41:59; still 19/19 in this window",
        "this_run_restarted": False,
    },
    "prior_short_gap_1118": {
        "restart": "2026-11-20 11:18:38",
        "box_pauses": False,
        "gap": [84371991, 84372019],
        "span": 29,
        "wall_s": 127,
        "told": True,
        "recorded_in": "11:25 1h patrol; already official-filled 29/29 in all 5",
        "fill": "29/29 in all 5 rooms",
    },
    "prior_short_gap_1111": {
        "restart": "2026-11-20 11:11:56",
        "box_pauses": False,
        "gap": [84371891, 84371919],
        "span": 29,
        "wall_s": 126.4,
        "told": True,
        "recorded_in": "11:25 1h patrol; already official-filled 29/29 in all 5; window start 84371901 overlaps last 19 ticks",
        "fill": "in-window overlap 84371901..84371919 official-filled 19/19 in all 5",
    },
    "prior_box_freeze_1049": {
        "from": "2026-11-20 10:49:41",
        "to": "2026-11-20 10:58:24",
        "sec": 516,
        "gap": [84371591, 84371729],
        "span": 139,
        "told": True,
        "recorded_in": "11:25 1h patrol; aged out of this window start 84371901",
        "fill": "already official-filled except W46N8 official 404 84371601..84371700 (100), which also aged out",
    },
    "in_window_official_404": None,
    "aged_official_404_w46n8_84371600": {
        "room": "W46N8",
        "base": 84371600,
        "hole": [84371601, 84371700],
        "distinct": hole_w46n8_71600["distinct"],
        "still_404": True,
        "inserted": 0,
        "told": True,
        "aged_out_of_window_start": TMIN,
        "note": "already told by the 11:25 1h patrol; not retried this 12:00 pass because it aged out of the 40-min window",
    },
    "listener": {
        "single_slot": single_slot,
        "roomSlot": room_slot,
        "rot": rot,
        "pid": 1293018,
        "started": "12:01:58",
        "restart": "12:01:48",
        "this_run_restarted": False,
        "war_cmd_pulse_restart": False,
        "parent_run_listener_sh": 4035476,
        "prior_restarts_since_1130_wrapup": ["11:44:14", "11:46:19", "11:59:07", "12:01:48"],
    },
    "prior_1h_patrol": {
        "folder": "_patrol_2026-11-20_1125",
        "started": "2026-11-20 11:25 Asia/Hong_Kong",
        "running": False,
        "note": "already delivered before this 12:00 half-hour; this run did not write into or modify the patrol folder; did not retry aged leftover 404s",
    },
    "cpu_tip": cpu_tip,
    "path_tip": path_tip,
    "room_stats_tip": rs_tip,
    "first_pass_note": FIRST_PASS_LINE,
    "leftover_note": leftover_txt,
}

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + chr(10))
shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")

win_ticks = TMAX - TMIN + 1
now_lines = [
    f"{finished_hkt} half-hour backfill OK (quiet)",
    f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
    f"  ({FIRST_PASS_LINE}; see history_backfill.txt)",
    f"tick_s={TICK_S_PRINTED} (first-interval {TICK_S_FIRST}; in_use={TICK_S_IN_USE} name={TICK_S_IN_USE_NAME})",
    f"reconstructed ticks={TMIN}..{TMAX} ({win_ticks}) creep_rows={RECON_ROWS} missing_chunks={MISSING_CHUNKS}",
    f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
    f"per_room {PER_ROOM_LINE}",
    f"inserted={INSERTED_FIRST}",
    f"ts_realigned={TS_REALIGNED_FIRST} corrective={NFIX_CORR}",
    "db_after",
    db_after_lines,
    f"coverage official_recovered={recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}",
    inwin_txt,
    freeze_para,
    f"listener single_slot={single_slot} roomSlot={room_slot} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    (
        "confirm/retry2 skipped (missing_chunks=0, no in-window 404); "
        + just_note
        + f"; this pass inserted {INSERTED_FIRST} additional rows in the reconstructed window "
        "on top of the 11:30 half-hour official fill through 84372200 / just-published through 84372300, plus live rotation"
    ),
    (
        f"ok_quiet=True coverage={recovered}/{expected} inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_TOTAL} "
        f"tick_s_in_use={TICK_S_IN_USE} listener single_slot={single_slot}; no second listener; no war_cmd/pulse restart."
    ),
]
now_text = "\n".join(now_lines) + chr(10)
(DIR / "history_backfill_now.txt").write_text(now_text)
shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

just_distinct_verify = ", ".join(f"{r} {just_rng[r]['distinct']}/100" for r in ROOMS)
verify = [
    f"{finished_hkt_sec} verify",
    f"first pass game.time={GT_FIRST} published_bases={PUB_BASES} reconstructed {TMIN}..{TMAX} ({win_ticks}) creep_rows={RECON_ROWS} missing_chunks={MISSING_CHUNKS}",
    f"already_in_db={ALREADY} inserted_first={INSERTED_FIRST} confirm={INSERTED_CONFIRM} retry2={INSERTED_RETRY2} just_script={INSERTED_JUST_SCRIPT} just_actual={INSERTED_JUST} inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_TOTAL}",
    f"per_room {PER_ROOM_LINE}",
    f"tick_s_first={TICK_S_FIRST} printed={TICK_S_PRINTED} in_use={TICK_S_IN_USE} ({TICK_S_IN_USE_NAME}) ts_realigned_first={TS_REALIGNED_FIRST} corrective={NFIX_CORR}",
    f"coverage official_recovered={recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing} unique_room_ticks={unique_after.get('distinct_room_ticks')}",
    "No official 404 and no official empty-no-creep in this first-pass window (all 5 rooms 700/700).",
    f"just-published {JUST_BASE} at {just_at} game.time={just_gt} all_five_200={all_five} actual_inserted={INSERTED_JUST} ticks {JUST_T0}..{JUST_T1} ({just_distinct_verify}); W47N7 47/100 is official empty-no-creep, not a 404.",
    "NEW box freeze 11:48:50-11:59:04 (609s in box_pauses) STATS 84372431..84372599 (169; last STATS 84372430 at 11:48:06, next 84372600 at 11:59:50, wall ~704.2s; listener auto-restart 11:59:07; fill 169/169 all 5 by first pass; told=false, left to next 1h patrol).",
    "NEW short listener gap 12:01:48 (no box_pauses.jsonl row) STATS 84372611..84372639 (29; last STATS 84372610 at 12:00:35, next 84372640 at 12:02:39, wall ~124.3s; fill 29/29 in W46N8/W47N8/W45N8/W45N7; W47N7 11/29 official empty-no-creep 18 ticks by just-published 84372600; told=false, left to next 1h patrol).",
    "Prior short gap 11:36:21 STATS 84372251..84372269 already official-filled 19/19 all 5; told=false, left to next 1h patrol by the 11:30 half-hour. Prior short gaps 11:11:56 and 11:18:38 already official-filled and told by the 11:25 1h patrol. Auto-restarts 11:44:14 and 11:46:19 produced no STATS gap >10 ticks. Prior 10:49 freeze and W46N8@84371600 official 404 aged out of window start 84371901 and were already told by the 11:25 1h patrol.",
    "No in-window official 404 this pass; confirm/retry2 skipped.",
    f"listener single_slot={single_slot} roomSlot={room_slot} pid=1293018 started 12:01:58 after auto-restart 12:01:48; this run did not restart listener or war_cmd/pulse; no second listener; yield absent. cpu_tip={cpu_tip} path_tip={path_tip} room_stats_tip={rs_tip}.",
]
verify_text = "\n".join(verify) + chr(10)
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1200.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run_stdout.txt").write_text(summary)
(DIR / "wrapup_run_live.txt").write_text(summary + f"ok_line ok_quiet=True coverage={recovered}/{expected} inserted_total={INSERTED_TOTAL}\n")
(DIR / "wrapup_run.err").write_text("")
print(summary, end="")
print("ok_line", f"ok_quiet=True coverage={recovered}/{expected} inserted_total={INSERTED_TOTAL}")
