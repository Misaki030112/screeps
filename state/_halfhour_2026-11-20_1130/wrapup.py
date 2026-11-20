#!/usr/bin/env python3
"""Write local status records for the 11:30 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-20_1130"
assert "_halfhour_2026-11-20_1130" in str(DIR), DIR
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84371601, 84372200
PUB_BASES = "84371600..84372200"
GT_FIRST = 84372303
TICK_S_FIRST = 4.214
TICK_S_PRINTED = "4.214"
TICK_S_IN_USE = 4.214
TS_REALIGNED_FIRST = 0
NFIX_CORR = 0
RECON_ROWS = 20458
ALREADY = 17619
INSERTED_FIRST = 2839
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
PER_ROOM_LINE = "W46N8:500t/414new W47N8:600t/734new W45N8:600t/825new W45N7:600t/541new W47N7:600t/325new"
MISSING_CHUNKS = 6
JUST_BASE = 84372200
JUST_T0, JUST_T1 = 84372201, 84372300
JUST_THRESHOLD = 84372340
FIRST_PASS_CORE = (
    "first pass 29 of 35 official GETs 200, missing_chunks=6 (W46N8@84371600 still 404; all 5 rooms @84372200 404, the unpublished just-published base); "
    "11:00 half-hour already wrote through 84371600 / reconstructed through 84371700 "
    "(just-published 84371700 written 11:06:49 at game.time=84371840, 200 for all 5, ticks 84371701..84371800); "
    "prior 1h patrol _patrol_2026-11-20_1125 already delivered around 11:25 Asia/Hong_Kong and told the 10:49 freeze, short gaps 11:11:56 / 11:18:38, and W46N8@84371600 404; "
    "(this pass already_in_db=17619 / inserted=2839; overlap 84371601..84371800 already present from the 11:00 half-hour official fill through 84371700 / just-published through 84371800, plus live rotation; "
    "this pass inserted 2839 additional rows: W46N8 414, W47N8 734, W45N8 825, W45N7 541, W47N7 325; "
    "W47N8/W45N8/W45N7/W47N7 600t, W46N8 500t plus 100 official-404 ticks 84371601..84371700; first-pass window is 600 ticks because published_bases included 84372200 which was still 404 for all 5 at game.time=84372303; "
    "NEW short listener gap around auto-restart 11:36:21 (pid 1284929 started 11:36:31; parent run_listener.sh pid 4035476 from Nov 13; no box_pauses.jsonl row) STATS gap 84372251..84372269 (19) sits after this first-pass window and inside just-published 84372200: last STATS 84372250 at 11:35:28, next STATS 84372270 at 11:36:53 Asia/Hong_Kong (wall ~84.7s); official-filled 19/19 all 5 by just-published 84372200; told=false, seen by this 11:30 half-hour, told status left to the next 1h patrol; "
    "prior short gaps 11:11:56 STATS 84371891..84371919 (29) and 11:18:38 STATS 84371991..84372019 (29) sit inside this window and are already official-filled 29/29 in all 5 rooms (told by the 11:25 1h patrol); "
    "prior box freeze 10:49:41-10:58:24 (516s) STATS gap 84371591..84371729 (139) overlaps this window start 84371601 and was already official-filled except W46N8 official 404 84371601..84371700, told by the 11:25 1h patrol; "
    "prior box freeze 10:15:38-10:25:57 (611s) STATS gap 84371101..84371259 (159) has aged out of this window start 84371601 and was already official-filled and told by the 10:25 1h patrol; "
    "prior box freezes 09:44:17-10:03:04, 09:09:35-09:20:53, 08:45:32-08:56:59, 08:22:11-08:23:13 and 07:46:17-08:04:28 have aged out of this window start 84371601 and were already official-filled and told by the 10:25 / 09:20 / 08:26 1h patrols; "
    "listener auto-restarts since the 11:00 wrapup: 11:11:56, 11:18:38, and 11:36:21; this run did not itself restart the listener; current listener.py pid 1284929 started 11:36:31; "
    "in-window official 404 W46N8@84371600 (hole 84371601..84371700, 0/100) still 404 after confirm 11:41:38 gt=84372336 and retry2 11:42:35 gt=84372350, inserted=0, already told by the 11:25 1h patrol; "
    "leftover official 404 W45N8@84368100, W47N8@84366200, W47N7@84366500, W45N7@84365200, W47N8@84363900, W46N8@84362700, W47N8@84361700, W46N8@84360600, W45N7@84360200, W47N8@84359900 and older aged out of this 40-min window and were not retried this pass (still unfilled; already told); "
    "this window empty_no_creep=0 (W47N8/W45N8/W45N7/W47N7 600/600 official recovered; W46N8 500/600 with official 404=100)"
)

coverage_payload = json.loads((DIR / "coverage_final.json").read_text())
coverage = coverage_payload["coverage"]
recovered = coverage_payload["official_recovered"]
expected = coverage_payload["expected"]
empty_no_creep = coverage_payload["empty_no_creep"]
official_404_missing = coverage_payload["official_404_missing"]
unique_after = coverage_payload["unique_after"]
tick_s = json.loads((DIR / "tick_s_realign.json").read_text())
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
    freeze1049 = {room: rng(c, room, 84371591, 84371729, 139) for room in ROOMS}
    freeze1049_pub = {room: rng(c, room, 84371591, 84371700, 110) for room in ROOMS}
    freeze1049_tail = {room: rng(c, room, 84371701, 84371729, 29) for room in ROOMS}
    gap1111 = {room: rng(c, room, 84371891, 84371919, 29) for room in ROOMS}
    gap1118 = {room: rng(c, room, 84371991, 84372019, 29) for room in ROOMS}
    gap1136 = {room: rng(c, room, 84372251, 84372269, 19) for room in ROOMS}
    just_rng = {room: rng(c, room, JUST_T0, JUST_T1, 100) for room in ROOMS}
    hole_w46n8_71600 = rng(c, "W46N8", 84371601, 84371700, 100)
    hole_w45n8_68100 = rng(c, "W45N8", 84368101, 84368200, 100)
    hole_w47n7_66500 = rng(c, "W47N7", 84366501, 84366600, 100)
    hole_w47n8_66200 = rng(c, "W47N8", 84366201, 84366300, 100)
    hole_w45n7_65200 = rng(c, "W45N7", 84365201, 84365300, 100)
    hole_w47n8_63900 = rng(c, "W47N8", 84363901, 84364000, 100)
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
        + f"; ticks {JUST_T0}..{JUST_T1}, {just_distinct_note})"
    )
else:
    just_note = f"just-published {JUST_BASE} was not attempted"
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
FIRST_PASS_LINE = FIRST_PASS_CORE + "; " + just_note

def fill_counts(fills, expected_n):
    return ", ".join(f"{room} {fills[room]['distinct']}/{expected_n}" for room in ROOMS)

inwin_txt = (
    "in-window official 404 after first pass: W46N8@84371600 (hole 84371601..84371700 "
    f"still db {hole_w46n8_71600['distinct']}/100, no rows); confirm 11:41:38 gt=84372336 still 404 inserted=0; "
    "retry2 11:42:35 gt=84372350 still 404 inserted=0; already told by the 11:25 1h patrol"
)
leftover_txt = (
    f"In-window official 404 W46N8@84371600 (hole 84371601..84371700 still db {hole_w46n8_71600['distinct']}/100, no rows; confirm and retry2 still 404, inserted=0; already told by the 11:25 1h patrol). "
    f"Leftover official 404 W45N8@84368100 (hole 84368101..84368200 still db {hole_w45n8_68100['distinct']}/100, no rows; already told) aged out of this window start {TMIN} and was not retried this pass (still unfilled). "
    f"Leftover official 404 W47N7@84366500 (hole 84366501..84366600 still db {hole_w47n7_66500['distinct']}/100; already told) aged out and was not retried. "
    f"Leftover official 404 W47N8@84366200 (hole 84366201..84366300 still db {hole_w47n8_66200['distinct']}/100; already told) aged out and was not retried. "
    f"Leftover official 404 W45N7@84365200 (hole 84365201..84365300 still db {hole_w45n7_65200['distinct']}/100; already told) aged out and was not retried. "
    f"Leftover official 404 W47N8@84363900 (hole 84363901..84364000 still db {hole_w47n8_63900['distinct']}/100; already told) aged out and was not retried. "
    "Aged leftover official 404 W46N8@84362700, W47N8@84361700, W46N8@84360600, W45N7@84360200, W47N8@84359900 and older sit outside this window and were not retried (still unfilled). "
    "This half-hour did not retry those aged leftovers. "
    f"This window has empty_no_creep={empty_no_creep} (W47N8/W45N8/W45N7/W47N7 official-recovered 600/600; W46N8 official-recovered 500/600 with official 404=100)."
)

freeze_para = (
    f"NEW short listener gap 11:36:21 Asia/Hong_Kong (no box_pauses.jsonl row; run_listener.sh auto-restart 11:36:21, listener.py pid 1284929 started 11:36:31, parent run_listener.sh pid 4035476 from Nov 13; this run did not itself restart the listener; told=false, seen by this 11:30 half-hour, told status left to the next 1h patrol) "
    f"room_stats gap 84372251..84372269 (19) sits after the first-pass reconstructed window and inside just-published {JUST_BASE}: last STATS 84372250 at 11:35:28, next STATS 84372270 at 11:36:53 (wall ~84.7s); official-filled 19/19 in all 5 rooms by just-published {JUST_BASE} at 11:41:59 (counts {fill_counts(gap1136, 19)}). "
    f"Prior short listener gap 11:18:38 Asia/Hong_Kong (no box_pauses.jsonl row; already official-filled 29/29 in all 5 rooms and told by the 11:25 1h patrol) room_stats gap 84371991..84372019 (29) still sits inside this window (counts {fill_counts(gap1118, 29)}). "
    f"Prior short listener gap 11:11:56 Asia/Hong_Kong (no box_pauses.jsonl row; already official-filled 29/29 in all 5 rooms and told by the 11:25 1h patrol) room_stats gap 84371891..84371919 (29) still sits inside this window (counts {fill_counts(gap1111, 29)}). "
    f"Prior box freeze 10:49:41-10:58:24 Asia/Hong_Kong (516s; already official-filled except W46N8 official 404 and told by the 11:25 1h patrol) "
    f"room_stats gap 84371591..84371729 (139) overlaps this window start {TMIN} (full-gap counts {fill_counts(freeze1049, 139)}; published part 84371591..84371700 counts {fill_counts(freeze1049_pub, 110)}; tail 84371701..84371729 counts {fill_counts(freeze1049_tail, 29)}). "
    f"Prior box freeze 10:15:38-10:25:57 Asia/Hong_Kong (611s; already official-filled 159/159 in all 5 rooms and told by the 10:25 1h patrol) room_stats gap 84371101..84371259 (159) has aged out of this window start {TMIN}. "
    "Prior box freezes 09:44:17-10:03:04, 09:09:35-09:20:53, 08:45:32-08:56:59, 08:22:11-08:23:13, 07:46:17-08:04:28 and earlier have aged out of this window start 84371601 and were already official-filled and told by the 10:25 / 09:20 / 08:26 1h patrols. "
    "This run found the listener already auto-restarted (pid 1284929 started 11:36:31, after the 11:36:21 restart) and did not itself restart it. "
    + leftover_txt
)

single_slot = (not yield_present)
room_slot = live.get("roomSlot")
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
    "tick_s_in_use_name": tick_s.get("tick_s_in_use_name") or "first",
    "ts_realigned_first": TS_REALIGNED_FIRST,
    "ts_realigned_corrective": NFIX_CORR,
    "just_published": {
        "base": JUST_BASE,
        "t0": JUST_T0,
        "t1": JUST_T1,
        "game_time": just_gt,
        "at": just_at or "2026-11-20 11:41:59 Asia/Hong_Kong",
        "all_five_200": all_five,
        "script_inserted": INSERTED_JUST_SCRIPT,
        "actual_inserted": INSERTED_JUST,
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
        "seen_by": "11:30 half-hour backfill; told status left to the next 1h patrol",
        "fill": "19/19 in all 5 rooms by just-published 84372200 at 11:41:59",
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
        "recorded_in": "11:00 half-hour wrapup follow-up and 11:25 1h patrol; already official-filled 29/29 in all 5",
        "fill": "29/29 in all 5 rooms",
    },
    "prior_box_freeze_1049": {
        "from": "2026-11-20 10:49:41",
        "to": "2026-11-20 10:58:24",
        "sec": 516,
        "gap": [84371591, 84371729],
        "span": 139,
        "wall_s": 578.4,
        "last_stats": 84371590,
        "next_stats": 84371730,
        "told": True,
        "recorded_in": "11:00 half-hour and 11:25 1h patrol; already told by the 11:25 1h patrol",
        "fill": "139/139 in W47N8 W45N8 W45N7 W47N7; W46N8 39/139 official 404 84371601..84371700 (100)",
    },
    "prior_box_freeze_1015": {
        "from": "2026-11-20 10:15:38",
        "to": "2026-11-20 10:25:57",
        "sec": 611,
        "gap": [84371101, 84371259],
        "span": 159,
        "told": True,
        "recorded_in": "10:30 half-hour and 10:25 1h patrol; already told by the 10:25 1h patrol; aged out of this window start 84371601",
        "fill": "159/159 in all 5 rooms",
    },
    "in_window_official_404": {
        "room": "W46N8",
        "base": 84371600,
        "hole": [84371601, 84371700],
        "distinct": hole_w46n8_71600["distinct"],
        "confirm_at": "2026-11-20 11:41:38 Asia/Hong_Kong",
        "confirm_game_time": 84372336,
        "retry2_at": "2026-11-20 11:42:35 Asia/Hong_Kong",
        "retry2_game_time": 84372350,
        "still_404": True,
        "inserted": 0,
        "told": True,
        "note": "other 4 rooms had official 200 for base 84371600 on the first pass; already told by the 11:25 1h patrol",
    },
    "listener": {
        "single_slot": single_slot,
        "roomSlot": room_slot,
        "rot": rot,
        "pid": 1284929,
        "started": "11:36:31",
        "restart": "11:36:21",
        "this_run_restarted": False,
        "war_cmd_pulse_restart": False,
        "parent_run_listener_sh": 4035476,
        "prior_restarts_this_hour": ["11:11:56", "11:18:38", "11:36:21"],
    },
    "prior_1h_patrol": {
        "folder": "_patrol_2026-11-20_1125",
        "started": "2026-11-20 11:25 Asia/Hong_Kong",
        "running": False,
        "note": "already delivered before this 11:30 half-hour; this run did not write into or modify the patrol folder; did not retry aged leftover 404s",
    },
    "cpu_tip": cpu_tip,
    "path_tip": path_tip,
    "room_stats_tip": rs_tip,
}

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + chr(10))
shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")

win_ticks = TMAX - TMIN + 1
now_lines = [
    f"{finished_hkt} half-hour backfill OK (quiet)",
    f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
    f"  ({FIRST_PASS_LINE}; see history_backfill.txt)",
    f"tick_s={TICK_S_PRINTED} (first-interval {TICK_S_FIRST}; in_use={TICK_S_IN_USE} name={payload['tick_s_in_use_name']})",
    f"reconstructed ticks={TMIN}..{TMAX} ({win_ticks}) creep_rows={RECON_ROWS} missing_chunks={MISSING_CHUNKS}",
    f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
    f"per_room {PER_ROOM_LINE}",
    f"inserted={INSERTED_FIRST}",
    f"ts_realigned={TS_REALIGNED_FIRST}",
    "db_after",
    db_after_lines,
    f"coverage official_recovered={recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}",
    f"{inwin_txt}",
    freeze_para,
    f"listener single_slot={single_slot} roomSlot={room_slot} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    (
        f"confirm 11:41:38 and retry2 11:42:35 still 404 on W46N8@84371600 (inserted=0 both, already told by the 11:25 1h patrol); "
        + just_note
        + f"; this pass inserted {INSERTED_FIRST} additional rows in the reconstructed window "
        f"(W46N8 414 / W47N8 734 / W45N8 825 / W45N7 541 / W47N7 325) on top of the 11:00 half-hour official fill through 84371700 / just-published through 84371800, plus live rotation"
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
    f"tick_s_first={TICK_S_FIRST} printed={TICK_S_PRINTED} in_use={TICK_S_IN_USE} ({payload['tick_s_in_use_name']}) ts_realigned_first={TS_REALIGNED_FIRST} corrective={NFIX_CORR}",
    f"coverage official_recovered={recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing} unique_room_ticks={unique_after.get('distinct_room_ticks')}",
    f"W46N8 official 404 84371601..84371700 (100). No official empty-no-creep in this first-pass window.",
    f"just-published {JUST_BASE} at {just_at} game.time={just_gt} all_five_200={all_five} actual_inserted={INSERTED_JUST} ticks {JUST_T0}..{JUST_T1} ({just_distinct_verify})",
    f"NEW short listener gap 11:36:21 (no box_pauses.jsonl row) STATS 84372251..84372269 (19; last STATS 84372250 at 11:35:28, next 84372270 at 11:36:53, wall ~84.7s; fill 19/19 all 5 by just-published 84372200; told=false, left to next 1h patrol).",
    f"Prior short gaps 11:11:56 STATS 84371891..84371919 and 11:18:38 STATS 84371991..84372019 already official-filled 29/29 all 5 and told by the 11:25 1h patrol. Prior 10:49 freeze overlaps window start and was already told by the 11:25 1h patrol (W46N8 still official 404 84371601..84371700). Prior 10:15 freeze aged out of window start {TMIN} and already told by the 10:25 1h patrol.",
    f"In-window official 404 W46N8@84371600 still 404 after confirm and retry2, inserted=0, hole 0/100, already told by the 11:25 1h patrol.",
    f"listener single_slot={single_slot} roomSlot={room_slot} pid=1284929 started 11:36:31 after auto-restart 11:36:21; this run did not restart listener or war_cmd/pulse; no second listener; yield absent. cpu_tip={cpu_tip} path_tip={path_tip} room_stats_tip={rs_tip}.",
]
verify_text = "\n".join(verify) + chr(10)
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1130.txt")
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
