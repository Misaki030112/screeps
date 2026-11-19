#!/usr/bin/env python3
"""Write local status records for the 22:30 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-19_2230"
assert "_halfhour_2026-11-19_2230" in str(DIR), DIR
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84360201, 84360900
PUB_BASES = "84360200..84360800"
GT_FIRST = 84360906
TICK_S_FIRST = 4.12119
TICK_S_PRINTED = "4.121"
TICK_S_IN_USE = 4.11847  # later_raw == later_robust; all candidates over45=0; no corrective realign
TICK_S_LATER = 4.11847
TS_REALIGNED_FIRST = 0
NFIX_CORR = 0
GT_CORR = None
RECON_ROWS = 22233
ALREADY = 18247
INSERTED_FIRST = 3986
INSERTED_CONFIRM = 1956  # confirm 22:40:27-38 gt=84360965 recovered W47N8/W45N8/W47N7@84360800
INSERTED_RETRY2 = 221  # retry2 22:43:39 gt=84361014 still 404 W45N7@84360200 and W46N8@84360600; +221 more on already-200 84360800 rooms
INSERTED_JUST = 2192  # 84360900 attempted 22:45:53 gt=84361046, 200 for all 5 (ticks 84360901..84361000 just after reconstructed window)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:600t/1103new W47N8:600t/1484new W45N8:600t/495new W45N7:600t/589new W47N7:600t/315new"
FIRST_PASS_LINE = (
    "first pass 30 of 35 official GETs 200, missing_chunks=5 (W45N7@84360200, W46N8@84360600, W47N8@84360800, W45N8@84360800, W47N7@84360800); "
    "22:00 half-hour already wrote through 84360300 / reconstructed through 84360400 (just-published 84360400 was not attempted then at gt=84360495, typically publishable around game.time>=84360540); "
    "(this pass already_in_db=18247 / inserted=3986; overlap 84360201..84360400 already present from the 22:00 half-hour plus live rotation, except W45N7 official 404 hole 84360201..84360300; "
    "this pass newly wrote previously unpublished 84360400 for all 5 rooms (filling the unpublished tail 84360401..84360449 of the 21:45:22-22:04:19 freeze STATS gap 49/49 in all 5), 84360500 for all 5, 84360600 for W47N8/W45N8/W45N7/W47N7 (W46N8 official 404), 84360700 for all 5, and 84360800 for W46N8/W45N7 (W47N8/W45N8/W47N7 recovered at confirm 22:40:27-38 gt=84360965 after first-pass gt=84360906 was still short of the typical publish threshold ~84360940), filling the official-covered new 22:17:13-22:25:45 freeze STATS gap 84360621..84360759 139/139 in W47N8/W45N8/W45N7/W47N7 and 65/139 in W46N8 (the 74-tick miss is the official 404 hole remainder 84360627..84360700; live-only 84360601..84360626); "
    "prior 21:45:22-22:04:19 freeze STATS gap 84360151..84360449 is now official-filled 299/299 in W46N8/W47N8/W45N8/W47N7 and 199/299 in W45N7 (miss is official 404 hole 84360201..84360300), including the previously unpublished tail; the 50 ticks 84360151..84360200 sit just before this window start 84360201 and are complete in all 5; "
    "prior 21:12:19-21:17:18 and 20:42:14-21:03:05 freeze STATS gaps have now aged out of this window start 84360201); "
    "leftover official 404 W47N8@84359900 aged out of this 40-min window and was not retried (hole 84359901..84360000 still db 6/100 live-only 84359901..84359906; NEW, not yet told); leftover official 404 W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out and were not retried; "
    "in-window official 404 W45N7@84360200 still 404 after confirm 22:40:24 game.time=84360965 and retry2 22:43:40 game.time=84361014 (neighbors @84360100 and @84360300 200 at 22:40:51-52, hole 84360201..84360300 db 0/100; NEW, not yet told); "
    "in-window official 404 W46N8@84360600 still 404 after confirm 22:40:25 game.time=84360965 and retry2 22:43:42 game.time=84361014 (neighbors @84360500 and @84360700 200 at 22:40:53-54, hole 84360601..84360700 db 26/100 live-only 84360601..84360626; NEW, not yet told); "
    "just-published 84360900 attempted at 22:45:53 game.time=84361046 and was 200 for all 5 rooms (inserted=2192; ticks 84360901..84361000 sit just after this reconstructed window)"
)
MISSING_CHUNKS = 5

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

def rng(c, room, t0, t1, expected):
    d, n, mn, mx = c.execute(
        "SELECT count(DISTINCT tick), count(*), min(tick), max(tick) "
        "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, t0, t1),
    ).fetchone()
    return {"distinct": d or 0, "rows": n or 0, "min": mn, "max": mx, "missing": expected - (d or 0)}

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
    freeze2145 = {room: rng(c, room, 84360151, 84360449, 299) for room in ROOMS}
    freeze2145_official = {room: rng(c, room, 84360151, 84360400, 250) for room in ROOMS}
    freeze2145_tail = {room: rng(c, room, 84360401, 84360449, 49) for room in ROOMS}
    freeze2217 = {room: rng(c, room, 84360621, 84360759, 139) for room in ROOMS}
    freeze2217_606 = {room: rng(c, room, 84360621, 84360700, 80) for room in ROOMS}
    freeze2217_607 = {room: rng(c, room, 84360701, 84360759, 59) for room in ROOMS}
    aged_w47n8_59900 = rng(c, "W47N8", 84359901, 84360000, 100)
    just_pub = {room: rng(c, room, 84360901, 84361000, 100) for room in ROOMS}
db_after_lines = "\n".join(db_lines)

def empty_ranges(room):
    return (coverage.get(room) or {}).get("official_empty_no_creep_ranges") or []

inwin_txt = (
    "in-window official 404 after first pass: 30 of 35 official GETs 200, missing_chunks=5; "
    "W47N8@84360800, W45N8@84360800 and W47N7@84360800 recovered 200 at confirm 22:40:27-38 game.time=84360965 "
    "(first-pass gt=84360906 was still short of the typical publish threshold ~84360940; retry2 22:43:44-51 still 200, inserted +221 more); "
    "W45N7@84360200 still official 404 after confirm 22:40:24 game.time=84360965 and retry2 22:43:40 game.time=84361014 "
    "(neighbors @84360100 and @84360300 200 at 22:40:51-52, hole 84360201..84360300 db 0/100; NEW, not yet told); "
    "W46N8@84360600 still official 404 after confirm 22:40:25 game.time=84360965 and retry2 22:43:42 game.time=84361014 "
    "(neighbors @84360500 and @84360700 200 at 22:40:53-54, hole 84360601..84360700 db 26/100 live-only 84360601..84360626; NEW, not yet told); "
    "final official_404_in_window=2 (W45N7@84360200, W46N8@84360600)"
)
leftover_txt = (
    "in-window official 404 remaining: W45N7@84360200 (hole 84360201..84360300 db 0/100) and "
    "W46N8@84360600 (hole 84360601..84360700 db 26/100 live-only 84360601..84360626). Both are NEW (not yet told to the user; next 1h patrol should fold them). "
    "Aged leftover official 404 W47N8@84359900 (hole 84359901..84360000 still db 6/100 live-only 84359901..84359906; NEW, not yet told) aged out of this window start 84360201 and was not retried this pass (still unfilled). "
    "Aged leftover official 404 W47N8@84359500 (hole 84359501..84359600), W45N7@84358500 (hole 84358501..84358600) and W47N8@84358700 (hole 84358701..84358800) were not retried this pass "
    "(already outside this 40-min window, along with W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800, and older). "
    "W45N7 official empty-no-creep 84359756..84359931 (176) after remote workers fled the W45N7 Invader Core threat (since 84359712; last our-creep tick 84359755 before a defender arrived 84359932) "
    "and 84360134..84360144 (11) have aged out of this window start 84360201; this window has empty_no_creep=0."
)
confirm_summary = (
    "confirm 22:40:23 game.time=84360965 recovered W47N8/W45N8/W47N7@84360800 (inserted=1956) and still_404 W45N7@84360200 and W46N8@84360600; "
    "neighbors of both remaining holes 200 at 22:40:51-54; "
    "retry2 22:43:39 game.time=84361014 both remaining still official 404 (inserted=221 more on already-200 84360800 rooms); "
    "just-published 84360900 attempted at 22:45:53 game.time=84361046 (typically publishable around game.time>=84361040) and was 200 for all 5 rooms (inserted=2192; ticks 84360901..84361000 sit just after this reconstructed window); "
    "previously unpublished 84360400 (in-progress at the 22:00 half-hour / not attempted then at gt=84360495) was written for all 5 rooms this pass, and 84360500..84360800 as described above"
)
vs_later_before = tick_s.get("still_over_45s_vs_later_before")
vs_first_over45 = vs_first.get("over45")
vs_later_over15_before = tick_s.get("still_over_15s_vs_later_before")
vs_first_over15 = vs_first.get("over15")
span_vs = (vs_cand.get("span_mean") or {})
prev_vs = (vs_cand.get("prev_later") or {})
later_vs = (vs_cand.get("later_robust") or vs_cand.get("later_raw") or {})
first_vs = (vs_cand.get("first") or vs_first or {})
tick_s_corr_txt = (
    f"script {TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} (raw later-mean also 4.11847) is the live-anchor-best estimate and is slightly better than first {TICK_S_FIRST:.5f} and prev_later 4.13709 "
    f"(delta first-robust 0.00272 s/tick, ~1.9s at tmin; "
    f"over45 later={vs_later_before} vs first={vs_first_over45} vs prev_later={prev_vs.get('over45')}, "
    f"over15 later={vs_later_over15_before} vs first={vs_first_over15} vs prev_later={prev_vs.get('over15')}; "
    f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')}; "
    f"lowest_over45 among sane was {tick_s.get('lowest_over45_sane')} {TICK_S_IN_USE:.5f} "
    f"(same value as later_robust; mean_off {later_vs.get('mean_off')} closer to the live anchor than first {first_vs.get('mean_off')} or prev_later {prev_vs.get('mean_off')}); "
    f"first-pass realign moved {TS_REALIGNED_FIRST} rows; "
    f"tick_s_check did not apply a corrective realign (all sane candidates already inside the 45s gate; later was not blindly applied as a worse estimate — this window later-mean is genuinely the best and already matched current rows); "
    f"still_over_45s_vs_later={tick_s.get('still_over_45s_vs_later')}; skipped_cross_chunk={tick_s.get('skipped_cross_chunk')}; "
    f"in-use later_raw/later_robust {TICK_S_IN_USE:.5f}; "
    f"confirm recovered W47N8/W45N8/W47N7@84360800; confirm and retry2 still official 404 W45N7@84360200 and W46N8@84360600; just-published 84360900 written for all 5 this pass"
)

freeze_para = (
    f"NEW box freeze 22:17:13-22:25:45 Asia/Hong_Kong (511s) caused run_listener.sh auto-restart 22:25:48 (listener.py pid 983114 started 22:25:57; not this run). "
    f"room_stats gap 84360621..84360759 (139): official-filled 139/139 in W47N8/W45N8/W45N7/W47N7 and 65/139 in W46N8 "
    f"(W46N8 miss is the official 404 hole remainder 84360627..84360700 inside W46N8@84360600; live-only 84360601..84360626, of which 84360621..84360626 sit in this gap; 84360701..84360759 is 59/59 in all 5). "
    f"No unpublished tail remains in this freeze gap (both 84360600 and 84360700 chunks are published except the W46N8 404). "
    f"Prior box freeze 21:45:22-22:04:19 Asia/Hong_Kong (1127s; run_listener.sh auto-restart 22:04:22, listener.py pid 976439 started 22:04:32 then; not this run) "
    f"room_stats gap 84360151..84360449 (299) is now official-filled 299/299 in W46N8/W47N8/W45N8/W47N7 and 199/299 in W45N7 "
    f"(W45N7 miss is the official 404 hole 84360201..84360300); the previously unpublished tail 84360401..84360449 was written this pass 49/49 in all 5 once 84360400 published. "
    f"The 50 ticks 84360151..84360200 sit just before this window start 84360201 and are complete in all 5. "
    f"Prior 21:12:19-21:17:18 freeze STATS gap 84359661..84359749 and 20:42:14-21:03:05 freeze STATS gap 84359231..84359549 have aged out of this window start 84360201, "
    f"including the still-open official 404 hole W47N8@84359500 (hole 84359501..84359600) which remains outside this window. "
    f"Aged official 404 W47N8@84359900 (hole 84359901..84360000 still db 6/100 live-only 84359901..84359906; NEW, not yet told) also sits outside this window and was not retried. "
    f"Aged official 404 W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) remain outside this window. "
    f"W45N7 official empty-no-creep 84359756..84359931 (176) and 84360134..84360144 (11) have aged out of this window; this window empty_no_creep=0. "
    f"live.json / stats.t were fresh at pre-check (age ~1.9s, tip stats.t=84360890, roomSlot W47N8 objects_n=0, live.json gameTime=84360871) after the 22:25:48 auto-reconnect; "
    f"CPU/path buffers were already flowing (creep_cpu through 84360880 / path_arrivals through 84360865); "
    f"previously unpublished 84360400 (all 5) and 84360500..84360800 were written this pass as described; just-published 84360900 was attempted and 200 for all 5 at gt=84361046; "
    f"single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84360880 / path_arrivals through 84360865 at pre-check; through {cpu_tip} / {path_tip} at wrapup); this run did not restart the listener. "
    f"At wrapup live.json gameTime was still stuck at 84360871 while stats.t continued advancing (normal tip-slot quirk, same family as prior gameTime=None); ingest and 5:5:1:1 rotation continued."
)

stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
single = True
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
    "later_mean_applied_nfix": 0,
    "later_mean_reverted_nfix": 0,
    "reconstructed_rows": RECON_ROWS,
    "already_in_db": ALREADY,
    "inserted_first": INSERTED_FIRST,
    "inserted_confirm": INSERTED_CONFIRM,
    "inserted_retry2": INSERTED_RETRY2,
    "inserted_just_published": INSERTED_JUST,
    "inserted_window": INSERTED_WINDOW,
    "inserted_total": INSERTED_TOTAL,
    "missing_chunks": MISSING_CHUNKS,
    "first_pass": FIRST_PASS_LINE,
    "per_room": PER_ROOM_LINE,
    "coverage": coverage_payload,
    "tick_s_realign": {
        "corrective_applied": False,
        "later_mean_w46": tick_s.get("later_mean_w46"),
        "later_mean_applied_then_reverted": False,
        "tick_s_in_use": TICK_S_IN_USE,
        "tick_s_in_use_name": tick_s.get("tick_s_in_use_name"),
        "still_over_45s_vs_later": tick_s.get("still_over_45s_vs_later"),
        "reason": tick_s.get("reason"),
        "prev_later_over45_before_corrective": (prev_vs or {}).get("over45"),
        "prev_later_mean": tick_s.get("prev_later_mean"),
        "lowest_over45_sane": tick_s.get("lowest_over45_sane"),
        "note": tick_s_corr_txt,
    },
    "just_published": {
        "base": 84360900,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "2026-11-19 22:45:53 Asia/Hong_Kong",
        "recovered_game_time": 84361046,
        "inserted": INSERTED_JUST,
        "note": "attempted at 22:45:53 game.time=84361046 (typically publishable around game.time>=84361040); 200 for all 5 rooms; inserted=2192; ticks 84360901..84361000 sit just after this reconstructed window 84360201..84360900 and will be overlap for the next half-hour",
        "first_try_all_404": False,
        "first_try_at": "2026-11-19 22:45:53 Asia/Hong_Kong",
        "first_try_game_time": 84361046,
        "first_try_recovered": ["W46N8@84360900", "W47N8@84360900", "W45N8@84360900", "W45N7@84360900", "W47N7@84360900"],
        "first_try_still_404": [],
        "retry_at": None,
        "retry_game_time": None,
        "retry_inserted": 0,
        "ticks": [84360901, 84361000],
        "all_five_official_200": True,
        "still_404": [],
        "in_window_still_404": ["W45N7@84360200", "W46N8@84360600"],
        "w45n7_empty_no_creep": empty_ranges("W45N7"),
        "w47n7_empty_no_creep": empty_ranges("W47N7"),
        "distinct": just_pub,
        "skipped": False,
    },
    "confirm": {
        "at": "2026-11-19 22:40:23 Asia/Hong_Kong",
        "game_time": 84360965,
        "inserted": INSERTED_CONFIRM,
        "script_reported_inserted": INSERTED_CONFIRM,
        "ssl_abort_first": None,
        "targets": 5,
        "recovered": ["W47N8@84360800", "W45N8@84360800", "W47N7@84360800"],
        "still_404": ["W45N7@84360200", "W46N8@84360600"],
        "skipped": False,
        "neighbors_at": "2026-11-19 22:40:51 Asia/Hong_Kong",
        "neighbors_game_time": None,
        "neighbors": {
            "W45N7@84360100": 200,
            "W45N7@84360200": 404,
            "W45N7@84360300": 200,
            "W46N8@84360500": 200,
            "W46N8@84360600": 404,
            "W46N8@84360700": 200,
        },
        "note": "confirm recovered W47N8/W45N8/W47N7@84360800 (late publish, inserted=1956); still official 404 W45N7@84360200 and W46N8@84360600; neighbors of both remaining holes 200 at 22:40:51-54",
    },
    "retry2": {
        "at": "2026-11-19 22:43:39 Asia/Hong_Kong",
        "game_time": 84361014,
        "inserted": INSERTED_RETRY2,
        "script_reported_inserted": INSERTED_RETRY2,
        "skipped": False,
        "recovered": ["W45N8@84360800", "W47N7@84360800"],
        "still_404": ["W45N7@84360200", "W46N8@84360600"],
        "note": "retry2 remaining two still official 404; W45N7@84360200 hole 84360201..84360300 db 0/100; W46N8@84360600 hole 84360601..84360700 db 26/100 live-only 84360601..84360626; already-200 84360800 rooms inserted +221 more",
    },
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 983114,
        "pid_at_precheck": 983114,
        "loop_pid": 4035476,
        "restart_at": "22:25:48",
        "listener_started": "22:25:57",
        "earlier_restart_this_hour": "22:04:22",
        "wrapup_ws_timeout": None,
        "wrapup_autorestart": None,
        "wrapup_listener_started": None,
        "this_run_restarted": False,
        "waited_for_reconnect": False,
        "live_objects_empty_after_reconnect": True,
        "live_gameTime_none_after_reconnect": False,
        "pre_cpu_path_after_wait": (
            f"creep_cpu through 84360880 / path_arrivals through 84360865 at pre-check 22:35:42; "
            f"live.json gameTime=84360871 and objects_n=0 at pre-check (roomSlot W47N8) but stats.t=84360890 was advancing and buffers were flowing after the 22:25:48 auto-reconnect; "
            f"by wrapup roomSlot {live.get('roomSlot')} objects_n={len(live.get('objects') or {})}, live.json gameTime still stuck at {live.get('gameTime')} while stats.t={stats.get('t')}, "
            f"creep_cpu through {cpu_tip} / path_arrivals through {path_tip}"
        ),
    },
    "box_freeze": {
        "from": "2026-11-19 22:17:13",
        "to": "2026-11-19 22:25:45",
        "sec": 511,
        "restart_at": "22:25:48",
        "room_stats_gap": "84360621..84360759",
        "official_filled": (
            "official-filled 139/139 in W47N8/W45N8/W45N7/W47N7 and 65/139 in W46N8 "
            "(W46N8 miss is official 404 W46N8@84360600 hole remainder 84360627..84360700; live-only 84360601..84360626); "
            "no unpublished tail (84360701..84360759 is 59/59 in all 5)"
        ),
        "counts": freeze2217,
        "earlier_restart_gap": "22:04:22 after 21:45:22-22:04:19; 21:17:21 after 21:12:19-21:17:18",
        "earlier_freeze": {
            "from": "2026-11-19 21:45:22",
            "to": "2026-11-19 22:04:19",
            "sec": 1127,
            "restart_at": "22:04:22",
            "room_stats_gap": "84360151..84360449",
            "official_filled": (
                "now official-filled 299/299 in W46N8/W47N8/W45N8/W47N7 and 199/299 in W45N7 "
                "(W45N7 miss is official 404 W45N7@84360200 hole 84360201..84360300); "
                "previously unpublished tail 84360401..84360449 written this pass 49/49 in all 5"
            ),
        },
        "earlier_freeze_2112": {
            "from": "2026-11-19 21:12:19",
            "to": "2026-11-19 21:17:18",
            "sec": 298,
            "restart_at": "21:17:21",
            "room_stats_gap": "84359661..84359749",
            "official_filled": "aged out of this window start 84360201 (already official-filled 89/89 in all 5)",
        },
        "new_freeze_this_run": True,
        "already_recorded_by_patrol": False,
        "missed_halfhours": None,
    },
    "new_official_404_not_yet_told": [
        {"room": "W47N8", "base": 84359900, "hole": [84359901, 84360000], "db_distinct": aged_w47n8_59900["distinct"], "db_note": "live-only 84359901..84359906; aged out of this window start 84360201, not retried, still unfilled; NEW, not yet told"},
        {"room": "W45N7", "base": 84360200, "hole": [84360201, 84360300], "db_distinct": 0, "db_note": "db 0/100; still in-window; NEW, not yet told (already recorded by the 22:00 wrapup as NEW)"},
        {"room": "W46N8", "base": 84360600, "hole": [84360601, 84360700], "db_distinct": 26, "db_note": "live-only 84360601..84360626; NEW this pass, not yet told"},
    ],
}

ok_line = (
    f"ok_quiet=True coverage={recovered}/{expected} inserted_window={INSERTED_WINDOW} "
    f"inserted_total={INSERTED_TOTAL} tick_s_in_use={TICK_S_IN_USE:.5f} "
    f"listener single_slot=True; no second listener; no war_cmd/pulse restart."
)
payload["ok_line"] = ok_line

now_text = "\n".join([
    f"{finished_hkt} half-hour backfill OK (quiet)",
    f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
    f"  ({FIRST_PASS_LINE}; see history_backfill.txt)",
    f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST:.5f}; {tick_s_corr_txt})",
    f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks={MISSING_CHUNKS}",
    f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
    f"per_room {PER_ROOM_LINE}",
    f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 +{INSERTED_RETRY2}, just_published +{INSERTED_JUST}, window {INSERTED_WINDOW}, run total {INSERTED_TOTAL})",
    f"ts_realigned_first={TS_REALIGNED_FIRST} ts_realigned_corrective={NFIX_CORR} tick_s_in_use={TICK_S_IN_USE:.5f}",
    "db_after",
    db_after_lines,
    f"coverage official_recovered={recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing} unique_room_ticks={unique_after.get('distinct_room_ticks')}",
    f"{inwin_txt}",
    f"{leftover_txt}",
    freeze_para,
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}",
    confirm_summary,
    ok_line,
]) + "\n"

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
(DIR / "history_backfill_now.txt").write_text(now_text)
shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")
shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

verify = [
    f"{finished_hkt_sec} verify 22:30 half-hour official-history backfill",
    f"window ticks {TMIN}..{TMAX} published_bases {PUB_BASES} game.time_first={GT_FIRST}",
    f"inserted_first={INSERTED_FIRST} confirm={INSERTED_CONFIRM} retry2={INSERTED_RETRY2} just_published={INSERTED_JUST} total={INSERTED_TOTAL}",
    f"coverage {recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}",
    f"tick_s_first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} in_use={TICK_S_IN_USE:.5f} later_mean_robust={TICK_S_LATER:.5f} corrective={tick_s.get('corrective_applied')} nfix={NFIX_CORR} later_mean_applied_then_reverted=False",
    f"{inwin_txt}",
    f"{leftover_txt}",
    freeze_para,
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 22:25:48 (listener.py pid 983114 started 22:25:57) after the new box freeze 22:17:13-22:25:45 (511s, room_stats gap 84360621..84360759). Earlier: 22:04:22 after 21:45:22-22:04:19; 21:17:21 after 21:12:19-21:17:18. The 22:25:48 reconnect had already recovered stats/CPU/path by pre-check 22:35:42 (live.json fresh, stats.t=84360890 advancing, roomSlot W47N8, gameTime=84360871; single_slot held).",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_note = DIR / "backfill_retry2.txt"
shutil.copyfile(retry2_note, ROOT / "state" / "_halfhour_backfill_retry2_2230.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run_tee.txt").write_text(summary + now_text)
(DIR / "wrapup_run_stdout.txt").write_text(summary + f"now_text_bytes {len(now_text)}\n")
print(summary, end="")
print("wrote", DIR / "history_backfill.json")
