#!/usr/bin/env python3
"""Write local status records for the 11:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-20_1100"
assert "_halfhour_2026-11-20_1100" in str(DIR), DIR
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84371001, 84371700
PUB_BASES = "84371000..84371600"
GT_FIRST = 84371748
TICK_S_FIRST = 4.07432
TICK_S_PRINTED = "4.074"
TICK_S_IN_USE = 4.07432
TS_REALIGNED_FIRST = 706
NFIX_CORR = 0
RECON_ROWS = 23313
ALREADY = 17896
INSERTED_FIRST = 5417
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
PER_ROOM_LINE = "W46N8:600t/319new W47N8:700t/2500new W45N8:700t/1107new W45N7:700t/705new W47N7:700t/786new"
MISSING_CHUNKS = 1
JUST_BASE = 84371700
JUST_T0, JUST_T1 = 84371701, 84371800
JUST_THRESHOLD = 84371840
FIRST_PASS_CORE = (
    "first pass 34 of 35 official GETs 200, missing_chunks=1 (W46N8@84371600 404; other 4 rooms 200 for that base); "
    "10:30 half-hour already wrote through 84371300 / reconstructed through 84371400 "
    "(just-published 84371400 written 10:46:08 at game.time=84371541, 200 for all 5, ticks 84371401..84371500); "
    "prior 1h patrol _patrol_2026-11-20_1025 started 10:25:43 already official-filled 84370501..84371200 "
    "and just-published 84371200 at 10:35:10 Asia/Hong_Kong game.time=84371383, and had already delivered by ~10:37; "
    "(this pass already_in_db=17896 / inserted=5417; overlap 84371001..84371500 already present from the 10:30 half-hour official fill through 84371500, the prior patrol official fill through 84371300, plus live rotation; "
    "this pass inserted 5417 additional rows: W46N8 319, W47N8 2500, W45N8 1107, W45N7 705, W47N7 786; "
    "W47N8/W45N8/W47N7 700t, W45N7 447t plus 253 official empty-no-creep ticks 84371270, 84371272..84371477 and 84371501..84371546, W46N8 600t plus 100 official-404 ticks 84371601..84371700; "
    "NEW box freeze 10:49:41-10:58:24 (516s) STATS gap 84371591..84371729 (139) sits inside/beyond this reconstructed window: last STATS 84371590 at 10:49:29, next STATS 84371730 at 10:59:08 Asia/Hong_Kong (wall ~578.4s); listener auto-restart 10:58:27 (listener.py pid 1264845 started 10:58:37; parent run_listener.sh pid 4035476 from Nov 13); official-filled 139/139 in W47N8/W45N8/W45N7/W47N7; W46N8 39/139 missing official 404 84371601..84371700 (100); published part 84371591..84371700 is 110/110 in the other 4 rooms and 10/110 in W46N8 (84371591..84371600 only); tail 84371701..84371729 filled 29/29 all 5 by just-published 84371700; told=false, seen by this 11:00 half-hour, told status left to the next 1h patrol; "
    "prior box freeze 10:15:38-10:25:57 (611s) STATS gap 84371101..84371259 (159) still sits inside this window and was already official-filled 159/159 in all 5 rooms (told by the 10:25 1h patrol); "
    "prior box freeze 09:44:17-10:03:04 (1127s) STATS gap 84370641..84370929 (289) has aged out of this window start 84371001 and was already official-filled and told by the 10:25 1h patrol; "
    "prior box freezes 09:09:35-09:20:53, 08:45:32-08:56:59, 08:22:11-08:23:13 and 07:46:17-08:04:28 have aged out of this window start 84371001 and were already official-filled and told by the 08:26 / 09:20 1h patrols; "
    "listener auto-restart 10:58:27 (pid 1264845 started 10:58:37) after the 10:49 freeze; this run did not itself restart the listener; "
    "NEW in-window official 404 W46N8@84371600 (hole 84371601..84371700, 0/100) still 404 after confirm 11:01:39 gt=84371767 and retry2 11:07:19 gt=84371847, inserted=0, not yet told, left to the next 1h patrol; "
    "leftover official 404 W45N8@84368100, W47N8@84366200, W47N7@84366500, W45N7@84365200, W47N8@84363900, W46N8@84362700, W47N8@84361700, W46N8@84360600, W45N7@84360200, W47N8@84359900 and older aged out of this 40-min window and were not retried this pass (still unfilled; W45N8@84368100 already told by the 07:29 1h patrol); "
    "this window empty_no_creep=253 (W45N7 official empty 84371270, 84371272..84371477 and 84371501..84371546; W47N8/W45N8/W47N7 700/700 official recovered; W46N8 600/700 with official 404=100)"
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
    freeze0944 = {room: rng(c, room, 84370641, 84370929, 289) for room in ROOMS}
    freeze1015 = {room: rng(c, room, 84371101, 84371259, 159) for room in ROOMS}
    freeze1049 = {room: rng(c, room, 84371591, 84371729, 139) for room in ROOMS}
    freeze1049_pub = {room: rng(c, room, 84371591, 84371700, 110) for room in ROOMS}
    freeze1049_tail = {room: rng(c, room, 84371701, 84371729, 29) for room in ROOMS}
    just_rng = {room: rng(c, room, JUST_T0, JUST_T1, 100) for room in ROOMS}
    hole_w46n8_71600 = rng(c, "W46N8", 84371601, 84371700, 100)
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
    (DIR / "just_published_post_counts.json").write_text(json.dumps(just_rng, indent=2, default=str) + "\n")

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
    f"still db {hole_w46n8_71600['distinct']}/100, no rows); confirm 11:01:39 gt=84371767 still 404 inserted=0; "
    "retry2 11:07:19 gt=84371847 still 404 inserted=0; not yet told, left to the next 1h patrol"
)
leftover_txt = (
    f"NEW in-window official 404 W46N8@84371600 (hole 84371601..84371700 still db {hole_w46n8_71600['distinct']}/100, no rows; confirm and retry2 still 404, inserted=0; not yet told, left to the next 1h patrol). "
    f"Leftover official 404 W45N8@84368100 (hole 84368101..84368200 still db {hole_w45n8_68100['distinct']}/100, no rows; already told by the 07:29 1h patrol) aged out of this window start {TMIN} and was not retried this pass (still unfilled). "
    f"Leftover official 404 W47N7@84366500 (hole 84366501..84366600 still db {hole_w47n7_66500['distinct']}/100; already told) aged out and was not retried. "
    f"Leftover official 404 W47N8@84366200 (hole 84366201..84366300 still db {hole_w47n8_66200['distinct']}/100; already told) aged out and was not retried. "
    f"Leftover official 404 W45N7@84365200 (hole 84365201..84365300 still db {hole_w45n7_65200['distinct']}/100; already told) aged out and was not retried. "
    f"Leftover official 404 W47N8@84363900 (hole 84363901..84364000 still db {hole_w47n8_63900['distinct']}/100; already told) aged out and was not retried. "
    f"Aged leftover official 404 W46N8@84362700, W47N8@84361700, W46N8@84360600, W45N7@84360200, W47N8@84359900 and older sit outside this window and were not retried (still unfilled). "
    "This half-hour did not retry those aged leftovers. "
    f"This window has empty_no_creep={empty_no_creep} (W45N7 official empty-no-creep 84371270, 84371272..84371477 and 84371501..84371546; W47N8/W45N8/W47N7 official-recovered 700/700; W46N8 official-recovered 600/700 with official 404=100)."
)

freeze_para = (
    f"NEW box freeze 10:49:41-10:58:24 Asia/Hong_Kong (516s; run_listener.sh auto-restart 10:58:27, listener.py pid 1264845 started 10:58:37, parent run_listener.sh pid 4035476 from Nov 13; this run did not itself restart the listener; told=false, seen by this 11:00 half-hour, told status left to the next 1h patrol) "
    f"room_stats gap 84371591..84371729 (139) sits inside/beyond this reconstructed window: last STATS 84371590 at 10:49:29, next STATS 84371730 at 10:59:08 (wall ~578.4s); official-filled 139/139 in W47N8/W45N8/W45N7/W47N7; W46N8 39/139 missing official 404 84371601..84371700 (100) (full-gap counts {fill_counts(freeze1049, 139)}; published part 84371591..84371700 counts {fill_counts(freeze1049_pub, 110)}; tail 84371701..84371729 filled 29/29 all 5 by just-published 84371700 at 11:06:49, counts {fill_counts(freeze1049_tail, 29)}). "
    f"Prior box freeze 10:15:38-10:25:57 Asia/Hong_Kong (611s; already official-filled 159/159 in all 5 rooms and told by the 10:25 1h patrol) "
    f"room_stats gap 84371101..84371259 (159) still sits inside this window (counts {fill_counts(freeze1015, 159)}). "
    f"Prior box freeze 09:44:17-10:03:04 Asia/Hong_Kong (1127s; already official-filled and told by the 10:25 1h patrol) "
    f"room_stats gap 84370641..84370929 (289) has aged out of this window start 84371001 (counts {fill_counts(freeze0944, 289)}; W45N7 269/289 official empty-no-creep 84370666..84370685). "
    "Prior box freezes 09:09:35-09:20:53, 08:45:32-08:56:59, 08:22:11-08:23:13, 07:46:17-08:04:28 and earlier have aged out of this window start 84371001 and were already official-filled and told by the 08:26 / 09:20 / 07:29 / 06:29 1h patrols. "
    "This run found the listener already auto-restarted (pid 1264845 started 10:58:37, after the 10:58:27 restart at the end of the 10:49 freeze) and did not itself restart it. "
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
        "at": just_at or "2026-11-20 11:06:49 Asia/Hong_Kong",
        "all_five_200": all_five,
        "script_inserted": INSERTED_JUST_SCRIPT,
        "actual_inserted": INSERTED_JUST,
    },
    "new_box_freeze": {
        "from": "2026-11-20 10:49:41",
        "to": "2026-11-20 10:58:24",
        "sec": 516,
        "gap": [84371591, 84371729],
        "span": 139,
        "wall_s": 578.4,
        "last_stats": 84371590,
        "next_stats": 84371730,
        "told": False,
        "seen_by": "11:00 half-hour backfill; told status left to the next 1h patrol",
        "fill": "139/139 in W47N8 W45N8 W45N7 W47N7; W46N8 39/139 official 404 84371601..84371700 (100); published part 84371591..84371700 110/110 in 4 rooms, W46N8 10/110; tail 84371701..84371729 29/29 all 5 by just-published 84371700 at 11:06:49",
    },
    "prior_box_freeze_1015": {
        "from": "2026-11-20 10:15:38",
        "to": "2026-11-20 10:25:57",
        "sec": 611,
        "gap": [84371101, 84371259],
        "span": 159,
        "wall_s": 669.3,
        "last_stats": 84371100,
        "next_stats": 84371260,
        "told": True,
        "recorded_in": "10:30 half-hour and 10:25 1h patrol; already told by the 10:25 1h patrol",
        "fill": "159/159 in all 5 rooms",
    },
    "prior_box_freeze_0944": {
        "from": "2026-11-20 09:44:17",
        "to": "2026-11-20 10:03:04",
        "sec": 1127,
        "gap": [84370641, 84370929],
        "span": 289,
        "wall_s": 1199,
        "last_stats": 84370640,
        "next_stats": 84370930,
        "told": True,
        "recorded_in": "10:00/10:30 half-hour and 10:25 1h patrol; already told by the 10:25 1h patrol; aged out of this window start 84371001",
        "fill": "289/289 in W46N8 W47N8 W45N8 W47N7; W45N7 269/289 official empty-no-creep 84370666..84370685",
    },
    "new_official_404": {
        "room": "W46N8",
        "base": 84371600,
        "hole": [84371601, 84371700],
        "distinct": hole_w46n8_71600["distinct"],
        "confirm_at": "2026-11-20 11:01:39 Asia/Hong_Kong",
        "confirm_game_time": 84371767,
        "retry2_at": "2026-11-20 11:07:19 Asia/Hong_Kong",
        "retry2_game_time": 84371847,
        "still_404": True,
        "inserted": 0,
        "told": False,
        "note": "other 4 rooms had official 200 for base 84371600 on the first pass; left to the next 1h patrol to tell",
    },
    "listener": {
        "single_slot": single_slot,
        "roomSlot": room_slot,
        "rot": rot,
        "pid": 1264845,
        "started": "10:58:37",
        "restart": "10:58:27",
        "this_run_restarted": False,
        "war_cmd_pulse_restart": False,
        "parent_run_listener_sh": 4035476,
    },
    "prior_1h_patrol": {
        "folder": "_patrol_2026-11-20_1025",
        "started": "2026-11-20 10:25:43 Asia/Hong_Kong",
        "running": False,
        "note": "already delivered before this 11:00 half-hour; this run did not write into or modify the patrol folder; did not retry aged leftover 404s",
    },
    "cpu_tip": cpu_tip,
    "path_tip": path_tip,
    "room_stats_tip": rs_tip,
}

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")

now_lines = [
    f"{finished_hkt} half-hour backfill OK (quiet)",
    f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
    f"  ({FIRST_PASS_LINE}; see history_backfill.txt)",
    f"tick_s={TICK_S_PRINTED} (first-interval {TICK_S_FIRST}; in_use={TICK_S_IN_USE} name={payload['tick_s_in_use_name']})",
    f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks={MISSING_CHUNKS}",
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
        f"confirm 11:01:39 and retry2 11:07:19 still 404 on W46N8@84371600 (inserted=0 both); "
        + just_note
        + f"; this pass inserted {INSERTED_FIRST} additional rows in the reconstructed window "
        f"(W46N8 319 / W47N8 2500 / W45N8 1107 / W45N7 705 / W47N7 786) on top of the 10:30 half-hour official fill through 84371500, the prior 1h patrol official fill through 84371300, plus live rotation"
    ),
    (
        f"ok_quiet=True coverage={recovered}/{expected} inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_TOTAL} "
        f"tick_s_in_use={TICK_S_IN_USE} listener single_slot={single_slot}; no second listener; no war_cmd/pulse restart."
    ),
]
now_text = "\n".join(now_lines) + "\n"
(DIR / "history_backfill_now.txt").write_text(now_text)
shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

just_distinct_verify = ", ".join(f"{r} {just_rng[r]['distinct']}/100" for r in ROOMS)
verify = [
    f"{finished_hkt_sec} verify",
    f"first pass game.time={GT_FIRST} published_bases={PUB_BASES} reconstructed {TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks={MISSING_CHUNKS}",
    f"already_in_db={ALREADY} inserted_first={INSERTED_FIRST} confirm={INSERTED_CONFIRM} retry2={INSERTED_RETRY2} just_script={INSERTED_JUST_SCRIPT} just_actual={INSERTED_JUST} inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_TOTAL}",
    f"per_room {PER_ROOM_LINE}",
    f"tick_s_first={TICK_S_FIRST} printed={TICK_S_PRINTED} in_use={TICK_S_IN_USE} ({payload['tick_s_in_use_name']}) ts_realigned_first={TS_REALIGNED_FIRST} corrective={NFIX_CORR}",
    f"coverage official_recovered={recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing} unique_room_ticks={unique_after.get('distinct_room_ticks')}",
    f"W45N7 official empty-no-creep ranges: 84371270; 84371272..84371477; 84371501..84371546 (253). W46N8 official 404 84371601..84371700 (100).",
    f"just-published {JUST_BASE} at {just_at} game.time={just_gt} all_five_200={all_five} actual_inserted={INSERTED_JUST} ticks {JUST_T0}..{JUST_T1} ({just_distinct_verify})",
    f"NEW freeze 10:49:41-10:58:24 (516s) STATS 84371591..84371729 (139; last STATS 84371590 at 10:49:29, next 84371730 at 10:59:08, wall ~578.4s; fill 139/139 in 4 rooms, W46N8 39/139 official 404 84371601..84371700; tail 29/29 all 5 by just-published; told=false, left to next 1h patrol).",
    f"Prior 10:15:38-10:25:57 freeze STATS 84371101..84371259 already official-filled 159/159 all 5 and told by the 10:25 1h patrol. Prior 09:44 freeze aged out of window start {TMIN} and already told by the 10:25 1h patrol.",
    f"NEW official 404 W46N8@84371600 still 404 after confirm and retry2, inserted=0, hole 0/100, not yet told.",
    f"listener single_slot={single_slot} roomSlot={room_slot} pid=1264845 started 10:58:37 after auto-restart 10:58:27; this run did not restart listener or war_cmd/pulse; no second listener; yield absent. cpu_tip={cpu_tip} path_tip={path_tip} room_stats_tip={rs_tip}.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1100.txt")
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
