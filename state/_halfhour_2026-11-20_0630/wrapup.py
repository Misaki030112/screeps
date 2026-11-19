#!/usr/bin/env python3
"""Write local status records for the 06:30 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-20_0630"
assert "_halfhour_2026-11-20_0630" in str(DIR), DIR
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84367101, 84367800
PUB_BASES = "84367100..84367700"
GT_FIRST = 84367837
TICK_S_FIRST = 4.02609
TICK_S_PRINTED = "4.026"
TICK_S_IN_USE = 4.02609
TS_REALIGNED_FIRST = 12384
NFIX_CORR = 0
GT_CORR = None
RECON_ROWS = 27212
ALREADY = 24753
INSERTED_FIRST = 2459
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
INSERTED_JUST_SCRIPT = 0
INSERTED_JUST = 0
PER_ROOM_LINE = "W46N8:700t/102new W47N8:700t/1436new W45N8:700t/257new W45N7:700t/0new W47N7:700t/664new"
MISSING_CHUNKS = 0
FIRST_PASS_CORE = (
    "first pass 35 of 35 official GETs 200, missing_chunks=0; "
    "06:00 half-hour already wrote through 84367300 / reconstructed through 84367400 (just-published 84367400 was attempted then at 06:09:31 gt=84367541 and recovered all 5 rooms, ticks 84367401..84367500); "
    "concurrent 1h patrol started 06:19 (still running at this wrapup) already official-filled 84366901..84367600 (inserted 3521, missing_chunks=0) and just-published 84367500+84367600 ticks 84367501..84367700 (inserted 3504); leftover official 404 retries by that patrol stayed 404 (now200=[]); "
    "(this pass already_in_db=24753 / inserted=2459; overlap 84367101..84367800 already partly present from the 06:00 half-hour official fill, just-published 84367400, the 06:19 patrol fill through 84367700, and live rotation; "
    "this pass inserted 2459 additional rows: W46N8 102, W47N8 1436, W45N8 257, W45N7 0, W47N7 664; "
    "box freeze 05:18:07-05:19:42 STATS gap 84366781..84366819 (39) has aged out of this window start 84367101 (already told by the 05:23 1h patrol); "
    "box freeze 04:42:44-05:00:03 STATS gap 84366271..84366539 (269) has aged out of this window start 84367101 (already told; still unfilled 30 ticks in W47N8@84366200 and 39 ticks in W47N7@84366500); "
    "box freeze 05:53:08-05:56:59 (223s) STATS gap 84367301..84367369 (69) is fully inside this reconstructed window and official-filled 69/69 in all 5 (recorded not-yet-told by the 06:00 half-hour for the 06:19 1h patrol, which is still running); "
    "box freeze 05:59:54-06:01:32 (90s) STATS gap 84367401..84367429 (29) is fully inside this reconstructed window and official-filled 29/29 in all 5 (same not-yet-told status); "
    "new box freeze 06:14:32-06:19:42 (304s) STATS gap 84367611..84367699 (89) is fully inside this reconstructed window: official-filled 89/89 in W46N8/W47N8/W45N8/W47N7; W45N7 54/89 missing 84367665..84367699 because official empty_no_creep W45N7 84367665..84367800 (136 ticks, no owned creeps; 200 official history for W45N7@84367600 and W45N7@84367700); not yet told, for the 06:19/next 1h patrol; "
    "listener auto-restart 06:19:45 (pid 1166330 started 06:19:54, after the 06:14 freeze); this run did not itself restart the listener; "
    "leftover official 404 W47N7@84366500, W47N8@84366200, W45N7@84365200, W47N8@84363900, W46N8@84362700, W47N8@84361700, W46N8@84360600, W45N7@84360200, W47N8@84359900 and older aged out of this 40-min window and were not retried this pass (the 06:19 patrol retried them, still 404); "
    "no in-window official 404; "
    "this window empty_no_creep=136 (W45N7 84367665..84367800)"
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

just_note = (
    "just-published 84367800 was not attempted this pass "
    f"(game.time_first={GT_FIRST}, later tick_s-check game.time={tick_s.get('gt_check')}; "
    "typically publishable around game.time>=84367940, still short); "
    "ticks 84367801..84367900 remain the in-progress unpublished official chunk"
)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
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
    freeze0442 = {room: rng(c, room, 84366271, 84366539, 269) for room in ROOMS}
    freeze0518 = {room: rng(c, room, 84366781, 84366819, 39) for room in ROOMS}
    freeze0553 = {room: rng(c, room, 84367301, 84367369, 69) for room in ROOMS}
    freeze0559 = {room: rng(c, room, 84367401, 84367429, 29) for room in ROOMS}
    freeze0614 = {room: rng(c, room, 84367611, 84367699, 89) for room in ROOMS}
    empty_w45n7 = rng(c, "W45N7", 84367665, 84367800, 136)
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
    "in-window official 404 after first pass: none (35 of 35 official GETs 200, missing_chunks=0); "
    "confirm/retry2 skipped; final official_404_in_window=0"
)
leftover_txt = (
    f"Leftover official 404 W47N7@84366500 (hole 84366501..84366600 still db {hole_w47n7_66500['distinct']}/100, no rows; already told by the 05:23 1h patrol) aged out of this window start 84367101 and was not retried this pass (still unfilled; 06:19 patrol retry still 404). "
    f"Leftover official 404 W47N8@84366200 (hole 84366201..84366300 still db {hole_w47n8_66200['distinct']}/100, no rows; already told by the 05:23 1h patrol) aged out of this window start 84367101 and was not retried this pass (still unfilled; 06:19 patrol retry still 404). "
    f"Leftover official 404 W45N7@84365200 (hole 84365201..84365300 still db {hole_w45n7_65200['distinct']}/100, no rows; already told by the 04:21 1h patrol) aged out of this window start 84367101 and was not retried this pass (still unfilled; 06:19 patrol retry still 404). "
    f"Leftover official 404 W47N8@84363900 (hole 84363901..84364000 still db {hole_w47n8_63900['distinct']}/100 live-only 84363951..84364000, missing 84363901..84363950; already told by the 02:34 1h patrol) aged out of this window start 84367101 and was not retried this pass (still unfilled; 06:19 patrol retry still 404). "
    f"Aged leftover official 404 W46N8@84362700 (hole 84362701..84362800 still db {hole_w46n8_62700['distinct']}/100, no live rows; already told by the 01:26 1h patrol) aged out of this window start 84367101 and was not retried this pass (still unfilled; 06:19 patrol retry still 404). "
    f"Aged leftover official 404 W47N8@84361700 (hole 84361701..84361800 still db {hole_w47n8_61700['distinct']}/100 live-only; already told) aged out of this window start 84367101 and was not retried this pass (still unfilled; 06:19 patrol retry still 404). "
    f"Aged leftover official 404 W46N8@84360600 (hole 84360601..84360700 still db {hole_w46n8_60600['distinct']}/100 live-only; already told) aged out and was not retried (still unfilled; 06:19 patrol retry still 404). "
    f"Aged leftover official 404 W45N7@84360200 (hole 84360201..84360300 still db {aged_w45n7_60200['distinct']}/100; already told) and W47N8@84359900 (hole 84359901..84360000 still db {aged_w47n8_59900['distinct']}/100; already told) also sit outside this window and were not retried (still unfilled; 06:19 patrol retry still 404). "
    "Aged leftover official 404 W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) were not retried this pass "
    "(already outside this 40-min window; 06:19 patrol also retried the still-listed leftovers, all still 404). "
    "This window has empty_no_creep=136 (W45N7 84367665..84367800 official empty, no owned creeps; official history 200 for W45N7@84367600 and W45N7@84367700)."
)
confirm_summary = (
    "confirm/retry2 skipped 2026-11-20 06:31 Asia/Hong_Kong "
    "(first pass 35/35 official GETs 200, missing_chunks=0; no in-window official 404 to confirm or retry); "
    + just_note
    + "; this pass inserted 2459 additional rows in the reconstructed window (W46N8 102 / W47N8 1436 / W45N8 257 / W45N7 0 / W47N7 664) on top of the 06:00 half-hour official fill, just-published 84367400, and the 06:19 1h patrol fill through 84367700"
)

first_vs = (vs_cand.get("first") or vs_first or {})
later_vs = (vs_cand.get("later_raw") or vs_cand.get("later_robust") or {})
all_vs = (vs_cand.get("all_mean") or {})
prev_vs = (vs_cand.get("prev_later") or {})
tick_s_corr_txt = (
    f"script {TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band and is live-anchor-best "
    f"(over45={first_vs.get('over45')} mean_off={float(first_vs.get('mean_off') or 0):.1f}, over15={first_vs.get('over15')}); "
    f"later-mean-robust {tick_s.get('later_mean_w46_robust'):.5f} is worse (over45={later_vs.get('over45')} mean_off={float(later_vs.get('mean_off') or 0):.1f}) and was refused "
    f"(later mean is pulled up by the 84367500..84367600 interval 4.27382); "
    f"all_mean {tick_s.get('all_mean_w46'):.5f}; prev_later {tick_s.get('prev_later_mean'):.5f} "
    f"(over45={prev_vs.get('over45')} mean_off={float(prev_vs.get('mean_off') or 0):.1f}). "
    f"First-pass realign moved {TS_REALIGNED_FIRST} rows onto {TICK_S_FIRST:.5f}; no corrective realign (already inside the 45s gate); "
    f"in-use first {TICK_S_IN_USE:.5f}; no in-window official 404; {just_note}"
)

def counts_txt(fills, n):
    return "counts " + ", ".join(f"{room} {fills[room]['distinct']}/{n}" for room in ROOMS)

freeze_para = (
    f"New box freeze 06:14:32-06:19:42 Asia/Hong_Kong (304s; run_listener.sh auto-restart 06:19:45, listener.py pid 1166330 started 06:19:54; not yet told, for the 06:19/next 1h patrol) "
    f"room_stats gap 84367611..84367699 (89) is fully inside this reconstructed window: official-filled 89/89 in W46N8/W47N8/W45N8/W47N7; "
    f"W45N7 54/89 missing 84367665..84367699 because official empty_no_creep W45N7 84367665..84367800 ({empty_w45n7['distinct']}/136 db rows in that empty range; official history 200). "
    f"({counts_txt(freeze0614, 89)}). "
    f"Box freeze 05:53:08-05:56:59 Asia/Hong_Kong (223s; run_listener.sh auto-restart 05:57:02; recorded not-yet-told by the 06:00 half-hour for the 06:19 1h patrol, which is still running) "
    f"room_stats gap 84367301..84367369 (69) is fully inside this reconstructed window and official-filled 69/69 in all 5 ({counts_txt(freeze0553, 69)}). "
    f"Box freeze 05:59:54-06:01:32 Asia/Hong_Kong (90s; run_listener.sh auto-restart 06:01:35, listener.py pid 1159748 started 06:01:45; same not-yet-told status) "
    f"room_stats gap 84367401..84367429 (29) is fully inside this reconstructed window and official-filled 29/29 in all 5 ({counts_txt(freeze0559, 29)}). "
    f"Box freeze 05:18:07-05:19:42 Asia/Hong_Kong (89s; already told by the 05:23 1h patrol) room_stats gap 84366781..84366819 (39) has aged out of this window start 84367101 "
    f"(still official-filled 39/39 in all 5; {counts_txt(freeze0518, 39)}). "
    f"Box freeze 04:42:44-05:00:03 Asia/Hong_Kong (1033s; already told by the 05:23 1h patrol) room_stats gap 84366271..84366539 (269) has aged out of this window start 84367101: "
    f"official-filled 269/269 in W46N8/W45N8/W45N7; W47N8 239/269 missing 84366271..84366300 because leftover official 404 W47N8@84366200; "
    f"W47N7 230/269 missing 84366501..84366539 because leftover official 404 W47N7@84366500 ({counts_txt(freeze0442, 269)}). "
    "Listener auto-restart 06:01:35 is the previous freeze restart (already recorded). Earlier already-told: 05:19:45 after 05:18:07-05:19:42; 05:00:06 after 04:42:44-05:00:03 (both told by the 05:23 1h patrol). "
    "This run found the listener already auto-restarted (pid 1166330) and did not itself restart it. "
    "Prior box freeze 03:46:06-04:06:15 and earlier freezes have aged out of this window start 84367101 (already told). "
    + leftover_txt + " "
    + f"live.json / stats.t were fresh at pre-check 06:29:31 (age ~0.4s, tip stats.t=84367830, roomSlot W47N8, gameTime=84367810, CPU/path were flowing); "
    f"this pass inserted 2459 additional rows in 84367101..84367800; {just_note}; "
    f"single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through {cpu_tip} / path_arrivals through {path_tip} at wrapup); this run did not restart the listener."
)

listener = {
    "single_slot": (live.get("roomSlot") is not None) and not yield_present,
    "roomSlot": live.get("roomSlot"),
    "rot": rot,
    "yield": yield_present,
    "pid": 1166330,
    "started": "2026-11-20 06:19:54",
    "auto_restart_at": "2026-11-20 06:19:45",
    "prior_auto_restart_at": "2026-11-20 06:01:35",
}
listener_line = (
    f"listener single_slot={listener['single_slot']} roomSlot={listener['roomSlot']} rot={rot} "
    f"yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart."
)

box_freeze = {
    "from": "2026-11-20 06:14:32",
    "to": "2026-11-20 06:19:42",
    "sec": 304,
    "restart_at": ["2026-11-20 06:19:45"],
    "listener_pid": 1166330,
    "listener_started": "2026-11-20 06:19:54",
    "room_stats_gap": [84367611, 84367699, 89],
    "official_fill": freeze0614,
    "told_by": None,
    "not_yet_told": True,
    "empty_no_creep_w45n7": [84367665, 84367800, 136],
    "prior_0559": {
        "from": "2026-11-20 05:59:54",
        "to": "2026-11-20 06:01:32",
        "sec": 90,
        "restart_at": "2026-11-20 06:01:35",
        "gap": [84367401, 84367429, 29],
        "fill": freeze0559,
        "told_by": None,
        "not_yet_told": True,
        "note": "already recorded by the 06:00 half-hour for the 06:19 1h patrol (still running at wrapup)",
    },
    "prior_0553": {
        "from": "2026-11-20 05:53:08",
        "to": "2026-11-20 05:56:59",
        "sec": 223,
        "restart_at": "2026-11-20 05:57:02",
        "gap": [84367301, 84367369, 69],
        "fill": freeze0553,
        "told_by": None,
        "not_yet_told": True,
        "note": "already recorded by the 06:00 half-hour for the 06:19 1h patrol (still running at wrapup)",
    },
    "prior_0518": {
        "gap": [84366781, 84366819, 39],
        "fill": freeze0518,
        "told_by": "05:23 1h patrol",
        "aged_out": True,
    },
}

new_box_freezes_not_yet_told = [
    {
        "from": "2026-11-20 05:53:08",
        "to": "2026-11-20 05:56:59",
        "sec": 223,
        "gap": [84367301, 84367369, 69],
        "fill": "69/69 all 5",
        "restart_at": "2026-11-20 05:57:02",
        "note": "already recorded by the 06:00 half-hour; 06:19 1h patrol still running at wrapup, not confirmed told",
    },
    {
        "from": "2026-11-20 05:59:54",
        "to": "2026-11-20 06:01:32",
        "sec": 90,
        "gap": [84367401, 84367429, 29],
        "fill": "29/29 all 5",
        "restart_at": "2026-11-20 06:01:35",
        "note": "already recorded by the 06:00 half-hour; 06:19 1h patrol still running at wrapup, not confirmed told",
    },
    {
        "from": "2026-11-20 06:14:32",
        "to": "2026-11-20 06:19:42",
        "sec": 304,
        "gap": [84367611, 84367699, 89],
        "fill": "89/89 in W46N8/W47N8/W45N8/W47N7; W45N7 54/89 official empty_no_creep 84367665..84367699",
        "restart_at": "2026-11-20 06:19:45",
        "note": "new this half-hour; for the 06:19/next 1h patrol",
    },
]

payload = {
    "ok_quiet": True,
    "finished_hkt": finished_hkt,
    "game_time_first": GT_FIRST,
    "published_bases": PUB_BASES,
    "rooms": list(ROOMS),
    "tmin": TMIN,
    "tmax": TMAX,
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
        "attempted": False,
        "base": 84367800,
        "threshold": 84367940,
        "game_time_first": GT_FIRST,
        "gt_check": tick_s.get("gt_check"),
        "reason": "game.time still short of 84367940; in-progress unpublished chunk",
    },
    "confirm": {},
    "retry2": {},
    "listener": listener,
    "box_freeze": box_freeze,
    "new_official_404_not_yet_told": [],
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
    "concurrent_1h_patrol": "started 06:19, still running at wrapup; already official-filled through 84367700",
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
    f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks=0",
    f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
    f"per_room {PER_ROOM_LINE}",
    f"inserted={INSERTED_FIRST} (confirm +0, retry2 +0, just_published +{INSERTED_JUST} actual / script {INSERTED_JUST_SCRIPT}, window {INSERTED_WINDOW}, run total {INSERTED_TOTAL})",
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
    f"{finished_hkt_sec} verify 06:30 half-hour official-history backfill",
    f"window ticks {TMIN}..{TMAX} published_bases {PUB_BASES} game.time_first={GT_FIRST}",
    f"inserted_first={INSERTED_FIRST} confirm={INSERTED_CONFIRM} retry2={INSERTED_RETRY2} just_published={INSERTED_JUST} (script {INSERTED_JUST_SCRIPT}) total={INSERTED_TOTAL}",
    f"coverage {recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}",
    f"tick_s_in_use={TICK_S_IN_USE:.5f} ts_realigned_first={TS_REALIGNED_FIRST} ts_realigned_corrective={NFIX_CORR}",
    f"{inwin_txt}",
    f"{leftover_txt}",
    freeze_para,
    listener_line,
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 06:19:45 (listener.py pid 1166330 started 06:19:54), after the new box freeze 06:14:32-06:19:42 (304s, room_stats gap 84367611..84367699; official-filled 89/89 in W46N8/W47N8/W45N8/W47N7, W45N7 54/89 official empty_no_creep 84367665..84367699; not yet told, for the 06:19/next 1h patrol). Earlier: 06:01:35 after 05:59:54-06:01:32 and 05:57:02 after 05:53:08-05:56:59 (both recorded not-yet-told by the 06:00 half-hour for the 06:19 1h patrol, which is still running at wrapup). The 05:34:07 restart is not a box freeze (not in box_pauses.jsonl). Earlier already-told: 05:19:45 after 05:18:07-05:19:42; 05:00:06 after 04:42:44-05:00:03 (both told by the 05:23 1h patrol). By pre-check 06:29:31 live.json was fresh (stats.t=84367830, roomSlot W47N8, gameTime=84367810) and CPU/path buffers were flowing; single_slot held.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0630.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
print(summary, end="")
print("ok_line", ok_line)
