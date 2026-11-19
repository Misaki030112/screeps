#!/usr/bin/env python3
"""Write local status records for the 07:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-20_0700"
assert "_halfhour_2026-11-20_0700" in str(DIR), DIR
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84367601, 84368300
PUB_BASES = "84367600..84368200"
GT_FIRST = 84368381
TICK_S_FIRST = 4.02929
TICK_S_PRINTED = "4.029"
TICK_S_IN_USE = 4.02929
TS_REALIGNED_FIRST = 8508
NFIX_CORR = 150
GT_CORR = 84368407
RECON_ROWS = 25335
ALREADY = 8678
INSERTED_FIRST = 16657
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
INSERTED_JUST_SCRIPT = 3269
# actual db inserts in 84368301..84368400 minus pre-insert counts:
# W46N8 982-96=886 (script 889, live slot race), W47N8 1306, W45N8 428-128=300,
# W45N7 236-75=161 (script 244), W47N7 530.
INSERTED_JUST = 3183
PER_ROOM_LINE = "W46N8:700t/6045new W47N8:700t/5175new W45N8:600t/1851new W45N7:700t/991new W47N7:700t/2595new"
MISSING_CHUNKS = 1
FIRST_PASS_CORE = (
    "first pass 34 of 35 official GETs 200, missing_chunks=1 W45N8@84368100; "
    "06:30 half-hour already wrote through 84367700 / reconstructed through 84367800 "
    "(just-published 84367800 was not attempted then, game.time_first=84367837 still short of 84367940); "
    "the 06:19 1h patrol (delivered ~06:29) had already official-filled through 84367700; "
    "(this pass already_in_db=8678 / inserted=16657; overlap 84367601..84368300 already partly present from the 06:30 half-hour official fill through 84367800, the 06:19 patrol fill through 84367700, and live rotation before the 06:37 freeze; "
    "this pass inserted 16657 additional rows: W46N8 6045, W47N8 5175, W45N8 1851, W45N7 991, W47N7 2595; W45N8 600t because of the 404 hole 84368101..84368200; "
    "box freeze 06:14:32-06:19:42 STATS gap 84367611..84367699 (89) still overlaps the start of this window and stays official-filled 89/89 in W46N8/W47N8/W45N8/W47N7, W45N7 54/89 missing 84367665..84367699 because official empty_no_creep (already told by the 06:29 1h patrol); "
    "box freeze 05:53:08-05:56:59 STATS gap 84367301..84367369 and 05:59:54-06:01:32 STATS gap 84367401..84367429 have aged out of this window start 84367601 (already told by the 06:29 1h patrol); "
    "new box freeze 06:37:56-07:03:44 (1542s) STATS gap 84367951..84368339 (389) is fully inside this reconstructed window plus just-published 84368300: official-filled 389/389 in W46N8/W47N8/W47N7; W45N8 289/389 missing 84368101..84368200 because in-window official 404 W45N8@84368100; W45N7 300/389 missing 89 because official empty_no_creep 84368044..84368071 and 84368205..84368265; not yet told, for the next 1h patrol; "
    "listener auto-restart 07:03:47 (pid 1177605 started 07:03:57, after the 06:37 freeze); this run did not itself restart the listener; "
    "leftover official 404 W47N7@84366500, W47N8@84366200, W45N7@84365200, W47N8@84363900, W46N8@84362700, W47N8@84361700, W46N8@84360600, W45N7@84360200, W47N8@84359900 and older aged out of this 40-min window and were not retried this pass (still unfilled; last 06:19/06:29 patrol retry still 404); "
    "in-window official 404: W45N8@84368100 (hole 84368101..84368200 still db 0/100; confirm 07:09:13 gt=84368410 and retry2 07:11:04 gt=84368437 both stayed official 404; NEW, not yet told, for the next 1h patrol); "
    "this window empty_no_creep=260 (W45N7 84367665..84367835, 84368044..84368071, 84368205..84368265)"
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
just_pub_path = DIR / "just_published_84368300.json"
just_pub_payload = json.loads(just_pub_path.read_text()) if just_pub_path.exists() else {}
confirm_payload = {}
try:
    confirm_payload = json.loads((DIR / "backfill_confirm_gets.json").read_text())
except Exception:
    confirm_payload = {}

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
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
just_note = (
    f"just-published 84368300 attempted at {just_at} game.time={just_gt} "
    f"(typically publishable around game.time>=84368440) and was "
    + ("200 for all 5 rooms" if all_five else f"not fully published (recovered={just_recovered or []} still_404={just_still_404 or []})")
    + f" (script inserted={INSERTED_JUST_SCRIPT}, actual db inserted={INSERTED_JUST}; ticks 84368301..84368400, 100/100 distinct in all 5)"
)
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
FIRST_PASS_LINE = FIRST_PASS_CORE + "; " + just_note

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
    freeze0614 = {room: rng(c, room, 84367611, 84367699, 89) for room in ROOMS}
    freeze0637 = {room: rng(c, room, 84367951, 84368339, 389) for room in ROOMS}
    just_rng = {room: rng(c, room, 84368301, 84368400, 100) for room in ROOMS}
    empty_w45n7_a = rng(c, "W45N7", 84367665, 84367835, 171)
    empty_w45n7_b = rng(c, "W45N7", 84368044, 84368071, 28)
    empty_w45n7_c = rng(c, "W45N7", 84368205, 84368265, 61)
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

def fill_line(fills, expected_n):
    parts = []
    for room in ROOMS:
        f = fills[room]
        parts.append(f"{room} {f['distinct']}/{expected_n}")
    return ", ".join(parts)

inwin_txt = (
    "in-window official 404 after first pass: W45N8@84368100 (34 of 35 official GETs 200, missing_chunks=1); "
    f"confirm 07:09:13 gt=84368410 and retry2 07:11:04 gt=84368437 both stayed official 404; "
    f"final official_404_in_window=1 hole 84368101..84368200 still db {hole_w45n8_68100['distinct']}/100, no rows; NEW, not yet told, for the next 1h patrol"
)
leftover_txt = (
    f"Leftover official 404 W47N7@84366500 (hole 84366501..84366600 still db {hole_w47n7_66500['distinct']}/100, no rows; already told by the 05:23 1h patrol) aged out of this window start 84367601 and was not retried this pass (still unfilled). "
    f"Leftover official 404 W47N8@84366200 (hole 84366201..84366300 still db {hole_w47n8_66200['distinct']}/100, no rows; already told by the 05:23 1h patrol) aged out of this window start 84367601 and was not retried this pass (still unfilled). "
    f"Leftover official 404 W45N7@84365200 (hole 84365201..84365300 still db {hole_w45n7_65200['distinct']}/100, no rows; already told by the 04:21 1h patrol) aged out of this window start 84367601 and was not retried this pass (still unfilled). "
    f"Leftover official 404 W47N8@84363900 (hole 84363901..84364000 still db {hole_w47n8_63900['distinct']}/100 live-only {hole_w47n8_63900['min']}..{hole_w47n8_63900['max']}, missing 84363901..84363950; already told by the 02:34 1h patrol) aged out of this window start 84367601 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W46N8@84362700 (hole 84362701..84362800 still db {hole_w46n8_62700['distinct']}/100, no live rows; already told by the 01:26 1h patrol) aged out of this window start 84367601 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W47N8@84361700 (hole 84361701..84361800 still db {hole_w47n8_61700['distinct']}/100 live-only; already told) aged out of this window start 84367601 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W46N8@84360600 (hole 84360601..84360700 still db {hole_w46n8_60600['distinct']}/100 live-only; already told) aged out and was not retried (still unfilled). "
    f"Aged leftover official 404 W45N7@84360200 (hole 84360201..84360300 still db {aged_w45n7_60200['distinct']}/100; already told) and W47N8@84359900 (hole 84359901..84360000 still db {aged_w47n8_59900['distinct']}/100; already told) also sit outside this window and were not retried (still unfilled). "
    "Aged leftover official 404 W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) were not retried this pass (already outside this 40-min window). "
    f"This window has empty_no_creep=260 (W45N7 84367665..84367835 / {empty_w45n7_a['distinct']} db rows, 84368044..84368071 / {empty_w45n7_b['distinct']} db rows, 84368205..84368265 / {empty_w45n7_c['distinct']} db rows; official history 200 for the corresponding W45N7 chunks; no owned creeps in those ranges). "
    f"New in-window official 404 W45N8@84368100 (hole 84368101..84368200 still db {hole_w45n8_68100['distinct']}/100, no rows; confirm and retry2 stayed 404; NEW, not yet told, for the next 1h patrol)."
)
freeze_para = (
    f"New box freeze 06:37:56-07:03:44 Asia/Hong_Kong (1542s; run_listener.sh auto-restart 07:03:47, listener.py pid 1177605 started 07:03:57; not yet told, for the next 1h patrol) "
    f"room_stats gap 84367951..84368339 (389) is fully inside this reconstructed window plus just-published 84368300: "
    f"official-filled 389/389 in W46N8/W47N8/W47N7; W45N8 289/389 missing 84368101..84368200 because in-window official 404 W45N8@84368100; "
    f"W45N7 300/389 missing 89 because official empty_no_creep 84368044..84368071 and 84368205..84368265 "
    f"(counts {fill_line(freeze0637, 389)}). "
    f"Box freeze 06:14:32-06:19:42 Asia/Hong_Kong (304s; already told by the 06:29 1h patrol) room_stats gap 84367611..84367699 (89) still overlaps this window start 84367601: official-filled 89/89 in W46N8/W47N8/W45N8/W47N7; W45N7 54/89 missing 84367665..84367699 because official empty_no_creep "
    f"(counts {fill_line(freeze0614, 89)}). "
    "Box freezes 05:53:08-05:56:59, 05:59:54-06:01:32, 05:18:07-05:19:42, 04:42:44-05:00:03 and earlier have aged out of this window start 84367601 or were already told by the 06:29 / 05:23 1h patrols. "
    "This run found the listener already auto-restarted (pid 1177605) after the 06:37 freeze and did not itself restart it. "
    + leftover_txt
    + f" live.json was fresh at pre-check 07:06:50 (age ~0s, tip stats.t=84368370, roomSlot W45N7, gameTime was still None on the W45N8/W45N7 1-weight slots while room ingest, CPU and path buffers were already flowing: creep_ticks W45N8 84368336..84368363 and W45N7 from 84368365, creep_cpu through 84368360 / path_arrivals through 84368359); "
    f"by wrapup live gameTime and objects were back on the W46N8 5-weight slot; "
    f"this pass inserted {INSERTED_FIRST} additional rows in 84367601..84368300 plus just-published actual {INSERTED_JUST} in 84368301..84368400; "
    f"single_slot held, creep_cpu through {cpu_tip} / path_arrivals through {path_tip} / room_stats through {rs_tip} at wrapup; this run did not restart the listener."
)

slot = live.get("roomSlot")
listener = {
    "single_slot": True,
    "roomSlot": slot,
    "rot": rot,
    "yield": yield_present,
    "listener_pid": 1177605,
    "run_listener_pid": 4035476,
    "auto_restart": "2026-11-20 07:03:47",
    "second_listener": False,
    "war_cmd_or_pulse_restart": False,
}
listener_line = (
    f"listener single_slot=True roomSlot={slot} rot={rot} yield={'present' if yield_present else 'absent'}; "
    "no second listener started; no war_cmd/pulse restart."
)
confirm_summary = (
    "confirm 2026-11-20 07:09:13 Asia/Hong_Kong game.time=84368410 and retry2 07:11:04 Asia/Hong_Kong game.time=84368437 "
    "both stayed official 404 for W45N8@84368100 (inserted +0 / +0); "
    + just_note
    + f"; this pass inserted {INSERTED_FIRST} additional rows in the reconstructed window "
    "(W46N8 6045 / W47N8 5175 / W45N8 1851 / W45N7 991 / W47N7 2595) on top of the 06:30 half-hour official fill through 84367800 and the 06:19 1h patrol fill through 84367700"
)

tick_s_corr_txt = (
    f"script {TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band and is live-anchor-best "
    f"(after corrective, vs_first over45={vs_first.get('over45')} mean_off={vs_first.get('mean_off')}, over15={vs_first.get('over15')}); "
    f"later-mean-robust {tick_s.get('later_mean_w46') or tick_s.get('later_mean_robust')} is worse "
    f"(before, over45={tick_s.get('still_over_45s_vs_later_before')} mean_off={(vs_cand.get('later_mean_robust') or vs_cand.get('later') or {}).get('mean_off')}) and was refused; "
    f"all_mean {tick_s.get('all_mean_w46')}; prev_later {tick_s.get('prev_later_mean')}. "
    f"First-pass realign moved {TS_REALIGNED_FIRST} rows onto {TICK_S_FIRST:.5f}; "
    f"corrective first realign moved {NFIX_CORR} rows at game.time={GT_CORR} (still_over_45s_vs_target=0); "
    f"in-use first {TICK_S_IN_USE:.5f}; in-window official 404 W45N8@84368100 stayed 404 after confirm/retry2; "
    + just_note
)

new_box_freezes_not_yet_told = [
    {
        "from": "2026-11-20 06:37:56",
        "to": "2026-11-20 07:03:44",
        "sec": 1542,
        "stats_gap": "84367951..84368339",
        "span": 389,
        "listener_restart": "2026-11-20 07:03:47",
        "listener_pid": 1177605,
        "fill": freeze0637,
        "note": "W45N8 missing 84368101..84368200 official 404; W45N7 missing 89 official empty_no_creep",
    }
]

payload = {
    "at": finished_hkt_sec,
    "ok": True,
    "quiet": True,
    "window": {"tmin": TMIN, "tmax": TMAX, "published_bases": PUB_BASES, "rooms": list(ROOMS)},
    "game_time_first": GT_FIRST,
    "tick_s_first": TICK_S_FIRST,
    "tick_s_printed": TICK_S_PRINTED,
    "tick_s_in_use": TICK_S_IN_USE,
    "ts_realigned_first": TS_REALIGNED_FIRST,
    "ts_realigned_corrective": NFIX_CORR,
    "gt_corrective": GT_CORR,
    "later_mean_applied_then_reverted": False,
    "override_poisoned_first": False,
    "reconstructed_rows": RECON_ROWS,
    "already_in_db": ALREADY,
    "inserted_first": INSERTED_FIRST,
    "inserted_confirm": INSERTED_CONFIRM,
    "inserted_retry2": INSERTED_RETRY2,
    "inserted_just_published": INSERTED_JUST,
    "inserted_just_published_script": INSERTED_JUST_SCRIPT,
    "inserted_window": INSERTED_WINDOW,
    "inserted_total": INSERTED_TOTAL,
    "missing_chunks": MISSING_CHUNKS,
    "first_pass": FIRST_PASS_LINE,
    "per_room": PER_ROOM_LINE,
    "coverage": coverage_payload,
    "tick_s_realign": tick_s,
    "just_published": {
        "attempted": True,
        "base": 84368300,
        "threshold": 84368440,
        "game_time": just_gt,
        "at": just_at,
        "recovered": just_recovered,
        "still_404": just_still_404,
        "inserted_script": INSERTED_JUST_SCRIPT,
        "inserted_actual": INSERTED_JUST,
        "per_room_after": just_rng,
    },
    "confirm": confirm_payload,
    "listener": listener,
    "box_freeze": {
        "new": new_box_freezes_not_yet_told,
        "already_told_in_window": {"06:14:32-06:19:42": freeze0614},
    },
    "new_official_404_not_yet_told": ["W45N8@84368100"],
    "new_box_freezes_not_yet_told": new_box_freezes_not_yet_told,
    "already_told_still_unfilled": [
        "W47N7@84366500", "W47N8@84366200", "W45N7@84365200", "W47N8@84363900",
        "W46N8@84362700", "W47N8@84361700", "W46N8@84360600", "W45N7@84360200", "W47N8@84359900",
    ],
    "inwin_txt": inwin_txt,
    "leftover_txt": leftover_txt,
    "freeze_para": freeze_para,
    "confirm_summary": confirm_summary,
    "db_after": db_after_lines,
    "cpu_tip": cpu_tip,
    "path_tip": path_tip,
    "rs_tip": rs_tip,
}

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")

ok_line = (
    f"ok_quiet=True coverage={recovered}/{expected} inserted_window={INSERTED_WINDOW} "
    f"inserted_total={INSERTED_TOTAL} tick_s_in_use={TICK_S_IN_USE:.5f} listener single_slot=True; "
    "no second listener; no war_cmd/pulse restart."
)
now_text = "\n".join([
    f"{finished_hkt} half-hour backfill OK (quiet)",
    f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
    f"  ({FIRST_PASS_LINE}; see history_backfill.txt)",
    f"tick_s={TICK_S_PRINTED} ({tick_s_corr_txt})",
    f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks={MISSING_CHUNKS}",
    f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
    f"per_room {PER_ROOM_LINE}",
    f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 +{INSERTED_RETRY2}, just_published +{INSERTED_JUST} actual / script {INSERTED_JUST_SCRIPT}, window {INSERTED_WINDOW}, run total {INSERTED_TOTAL})",
    f"ts_realigned_first={TS_REALIGNED_FIRST} ts_realigned_corrective={NFIX_CORR} tick_s_in_use={TICK_S_IN_USE:.5f}",
    "db_after",
    db_after_lines,
    f"coverage official_recovered={recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing} unique_room_ticks={unique_after.get('distinct_room_ticks')}",
    inwin_txt,
    leftover_txt,
    freeze_para,
    listener_line,
    confirm_summary,
    ok_line,
]) + "\n"
(DIR / "history_backfill_now.txt").write_text(now_text)
shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")
shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

verify = [
    f"{finished_hkt_sec} verify 07:00 half-hour official-history backfill",
    f"window ticks {TMIN}..{TMAX} published_bases {PUB_BASES} game.time_first={GT_FIRST}",
    f"inserted_first={INSERTED_FIRST} confirm={INSERTED_CONFIRM} retry2={INSERTED_RETRY2} just_published={INSERTED_JUST} (script {INSERTED_JUST_SCRIPT}) total={INSERTED_TOTAL}",
    f"coverage {recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}",
    f"tick_s_in_use={TICK_S_IN_USE:.5f} ts_realigned_first={TS_REALIGNED_FIRST} ts_realigned_corrective={NFIX_CORR}",
    f"{inwin_txt}",
    f"{leftover_txt}",
    freeze_para,
    listener_line,
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 07:03:47 (listener.py pid 1177605 started 07:03:57), after the new box freeze 06:37:56-07:03:44 (1542s, room_stats gap 84367951..84368339; official-filled 389/389 in W46N8/W47N8/W47N7, W45N8 289/389 missing official 404 W45N8@84368100, W45N7 300/389 official empty_no_creep; not yet told, for the next 1h patrol). Earlier already-told: 06:19:45 after 06:14:32-06:19:42; 06:01:35 after 05:59:54-06:01:32; 05:57:02 after 05:53:08-05:56:59 (all told by the 06:29 1h patrol). By wrapup live.json gameTime and objects were flowing on roomSlot W46N8 and CPU/path buffers were flowing; single_slot held.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0700.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
print(summary, end="")
print("ok_line", ok_line)
