#!/usr/bin/env python3
"""Write local status records for the 23:30 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-19_2330"
assert "_halfhour_2026-11-19_2330" in str(DIR), DIR
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84361001, 84361700
PUB_BASES = "84361000..84361600"
GT_FIRST = 84361728
TICK_S_FIRST = 4.11021
TICK_S_PRINTED = "4.110"
TICK_S_IN_USE = 4.09411  # prev_later (23:00 all_mean); later_raw/robust 4.11281 worse (over45=12); first over45=3; no corrective realign
TICK_S_LATER = 4.11281
TS_REALIGNED_FIRST = 7700
NFIX_CORR = 0
GT_CORR = None
RECON_ROWS = 25579
ALREADY = 22410
INSERTED_FIRST = 3169
INSERTED_CONFIRM = 0  # confirm skipped; no in-window official 404
INSERTED_RETRY2 = 0  # retry2 skipped; no in-window official 404
INSERTED_JUST = 1898  # 84361700 attempted 23:40:19 gt=84361843, 200 for W46N8/W45N8/W45N7/W47N7; W47N8 still 404 after retry 23:41:43 gt=84361864 (ticks 84361701..84361800 just after reconstructed window)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/147new W47N8:700t/1741new W45N8:700t/443new W45N7:700t/427new W47N7:700t/411new"
FIRST_PASS_LINE = (
    "first pass 35 of 35 official GETs 200, missing_chunks=0; "
    "23:00 half-hour already wrote through 84361200 / reconstructed through 84361300 (just-published 84361300 was attempted then at 23:13:04 gt=84361442 and was 200 for all 5, ticks 84361301..84361400); "
    "the 23:24 1h patrol already wrote published_bases 84360900..84361500 / reconstructed 84360901..84361600 at 23:26 gt=84361633 (missing_chunks=0, inserted=6603, tick_s=3.978, ts_realigned=11192); "
    "(this pass already_in_db=22410 / inserted=3169; overlap 84361001..84361600 already present from the 23:00 half-hour plus the 23:24 patrol plus live rotation; "
    "this pass newly wrote 84361600 for all 5 rooms, filling the official-covered new 23:20:04-23:24:46 freeze STATS gap 84361541..84361619 79/79 in all 5, including the previously unpublished tail 84361601..84361619; "
    "prior 22:55:09-23:02:20 freeze STATS gap 84361171..84361289 remains official-filled 119/119 in all 5; "
    "prior 22:17:13-22:25:45 freeze STATS gap 84360621..84360759 has now aged out of this window start 84361001); "
    "leftover official 404 W46N8@84360600 aged out of this 40-min window and was not retried (hole 84360601..84360700 still db 26/100 live-only 84360601..84360626; already told by the 22:30 patrol); "
    "leftover official 404 W45N7@84360200, W47N8@84359900, W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out and were not retried; "
    "in-window official 404: none (confirm and retry2 skipped); "
    "just-published 84361700 attempted at 23:40:19 game.time=84361843 and was 200 for W46N8/W45N8/W45N7/W47N7 (inserted=1898); W47N8@84361700 still official 404 after retry 23:41:43 game.time=84361864 (hole 84361701..84361800 db 45/100 live-only 84361756..84361800; ticks sit just after this reconstructed window; NEW official 404 not yet told, next 1h patrol should fold it)"
)
MISSING_CHUNKS = 0

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
    freeze2320 = {room: rng(c, room, 84361541, 84361619, 79) for room in ROOMS}
    freeze2255 = {room: rng(c, room, 84361171, 84361289, 119) for room in ROOMS}
    aged_w47n8_59900 = rng(c, "W47N8", 84359901, 84360000, 100)
    aged_w45n7_60200 = rng(c, "W45N7", 84360201, 84360300, 100)
    hole_w46n8_60600 = rng(c, "W46N8", 84360601, 84360700, 100)
    just_pub = {room: rng(c, room, 84361701, 84361800, 100) for room in ROOMS}
db_after_lines = "\n".join(db_lines)

def empty_ranges(room):
    return (coverage.get(room) or {}).get("official_empty_no_creep_ranges") or []

inwin_txt = (
    "in-window official 404 after first pass: 35 of 35 official GETs 200, missing_chunks=0; "
    "confirm and retry2 skipped; "
    "final official_404_in_window=0"
)
leftover_txt = (
    "in-window official 404 remaining: none. "
    "Aged leftover official 404 W46N8@84360600 (hole 84360601..84360700 still db 26/100 live-only 84360601..84360626; already told by the 22:30 patrol) aged out of this window start 84361001 and was not retried this pass (still unfilled). "
    "Aged leftover official 404 W45N7@84360200 (hole 84360201..84360300 still db 0/100; already told) and W47N8@84359900 (hole 84359901..84360000 still db 6/100 live-only 84359901..84359906; already told) also sit outside this window and were not retried (still unfilled). "
    "Aged leftover official 404 W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) were not retried this pass "
    "(already outside this 40-min window). "
    "NEW official 404 just after this window: W47N8@84361700 (hole 84361701..84361800 db 45/100 live-only 84361756..84361800) still 404 after just-published first try 23:40:24 game.time=84361843 and retry 23:41:43 game.time=84361864; next 1h patrol should fold this (already-told through the 22:30 patrol remain W47N8@84359900, W45N7@84360200, W46N8@84360600 and older leftovers). "
    "This window has empty_no_creep=0."
)
confirm_summary = (
    "confirm and retry2 skipped (no in-window official 404 after first pass 35/35 200); "
    "just-published 84361700 attempted at 23:40:19 game.time=84361843 (typically publishable around game.time>=84361840) and was 200 for W46N8/W45N8/W45N7/W47N7 (inserted=1898); "
    "W47N8@84361700 still official 404 after retry 23:41:43 game.time=84361864 (hole 84361701..84361800 db 45/100 live-only 84361756..84361800; ticks 84361701..84361800 sit just after this reconstructed window); "
    "this pass newly wrote 84361600 for all 5, filling the 23:20:04-23:24:46 freeze unpublished tail"
)
vs_later_before = tick_s.get("still_over_45s_vs_later_before")
vs_first_over45 = vs_first.get("over45")
vs_later_over15_before = tick_s.get("still_over_15s_vs_later_before")
vs_first_over15 = vs_first.get("over15")
span_vs = (vs_cand.get("span_mean") or {})
prev_vs = (vs_cand.get("prev_later") or {})
later_vs = (vs_cand.get("later_robust") or vs_cand.get("later_raw") or {})
first_vs = (vs_cand.get("first") or vs_first or {})
all_vs = (vs_cand.get("all_mean") or {})
tick_s_corr_txt = (
    f"script {TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} (raw later-mean also 4.11281) is worse than live-anchor-best prev_later {TICK_S_IN_USE:.5f} "
    f"(delta first-robust {TICK_S_FIRST-TICK_S_LATER:.5f} s/tick, ~{(GT_FIRST-TMIN)*abs(TICK_S_FIRST-TICK_S_LATER):.1f}s at tmin; "
    f"over45 later={vs_later_before} vs first={vs_first_over45} vs all_mean={all_vs.get('over45')} vs prev_later={prev_vs.get('over45')}, "
    f"over15 later={vs_later_over15_before} vs first={vs_first_over15} vs all_mean={all_vs.get('over15')} vs prev_later={prev_vs.get('over15')}; "
    f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')}; "
    f"lowest_over45 among sane was {tick_s.get('lowest_over45_sane')} {TICK_S_IN_USE:.5f} "
    f"(mean_off {prev_vs.get('mean_off')} closer to the live anchor than later {later_vs.get('mean_off')}, first {first_vs.get('mean_off')} or all_mean {all_vs.get('mean_off')}); "
    f"first-pass realign moved {TS_REALIGNED_FIRST} rows (likely correcting the 23:24 patrol's tick_s=3.978 realign of 11192 rows); "
    f"tick_s_check did not apply a corrective realign (live-anchor-best prev_later already inside the 45s gate with over45=0; later-mean-robust was refused as worse than prev_later); "
    f"still_over_45s_vs_later={tick_s.get('still_over_45s_vs_later')}; skipped_cross_chunk={tick_s.get('skipped_cross_chunk')}; "
    f"in-use prev_later {TICK_S_IN_USE:.5f}; "
    f"confirm and retry2 skipped (no in-window 404); just-published 84361700 written for four rooms this pass, W47N8 still official 404 after retry"
)

stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
freeze_para = (
    f"NEW box freeze 23:20:04-23:24:46 Asia/Hong_Kong (276s) caused run_listener.sh auto-restart 23:24:49 (listener.py pid 1008796 started 23:24:58; this run found the listener already fresh and did not itself restart it). "
    f"room_stats gap 84361541..84361619 (79): official-filled 79/79 in all 5 rooms (84361500 was already official-filled by the 23:24 patrol through 84361600; this pass wrote just-published-at-the-time 84361600, filling the unpublished tail 84361601..84361619 in all 5). "
    f"Prior box freeze 22:55:09-23:02:20 Asia/Hong_Kong (431s; run_listener.sh auto-restart 23:02:24, listener.py pid 998881 started 23:02:33 then; not this run) "
    f"room_stats gap 84361171..84361289 (119) remains official-filled 119/119 in all 5. "
    f"Prior box freeze 22:17:13-22:25:45 Asia/Hong_Kong (511s; restart 22:25:48) room_stats gap 84360621..84360759 (139) has aged out of this window start 84361001 "
    f"(already official-filled 139/139 in W47N8/W45N8/W45N7/W47N7 and 65/139 in W46N8; W46N8 miss is official 404 W46N8@84360600). "
    f"Prior 21:45:22-22:04:19, 21:12:19-21:17:18 and 20:42:14-21:03:05 freeze STATS gaps have also aged out of this window. "
    f"Aged official 404 W46N8@84360600, W45N7@84360200, W47N8@84359900, W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300 (and older) remain outside this window. "
    f"This window empty_no_creep=0. "
    f"live.json / stats.t were fresh at pre-check 23:32:13 (age ~0.8s, tip stats.t=84361720, roomSlot W46N8 objects_n=260, live.json gameTime=84361723) after the 23:24:49 auto-reconnect; "
    f"CPU/path buffers were already flowing (creep_cpu through 84361720 / path_arrivals through 84361720); "
    f"this pass wrote 84361600 for all 5 and just-published 84361700 was attempted at gt=84361843 (200 for four rooms, W47N8 still official 404 after retry at gt=84361864); "
    f"single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84361720 / path_arrivals through 84361720 at pre-check; through {cpu_tip} / {path_tip} at wrapup); this run did not restart the listener."
)

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
        "base": 84361700,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "2026-11-19 23:40:19 Asia/Hong_Kong",
        "recovered_game_time": 84361843,
        "inserted": INSERTED_JUST,
        "note": "attempted at 23:40:19 game.time=84361843 (typically publishable around game.time>=84361840); 200 for W46N8/W45N8/W45N7/W47N7 inserted=1898; W47N8@84361700 still official 404 after retry 23:41:43 game.time=84361864 (hole 84361701..84361800 db 45/100 live-only 84361756..84361800); ticks 84361701..84361800 sit just after this reconstructed window 84361001..84361700 and will be overlap for the next half-hour",
        "first_try_all_404": False,
        "first_try_at": "2026-11-19 23:40:19 Asia/Hong_Kong",
        "first_try_game_time": 84361843,
        "first_try_recovered": ["W46N8@84361700", "W45N8@84361700", "W45N7@84361700", "W47N7@84361700"],
        "first_try_still_404": ["W47N8@84361700"],
        "retry_at": "2026-11-19 23:41:43 Asia/Hong_Kong",
        "retry_game_time": 84361864,
        "retry_inserted": 0,
        "ticks": [84361701, 84361800],
        "all_five_official_200": False,
        "still_404": ["W47N8@84361700"],
        "in_window_still_404": [],
        "w45n7_empty_no_creep": empty_ranges("W45N7"),
        "w47n7_empty_no_creep": empty_ranges("W47N7"),
        "distinct": just_pub,
        "skipped": False,
    },
    "confirm": {
        "at": None,
        "game_time": None,
        "inserted": INSERTED_CONFIRM,
        "script_reported_inserted": INSERTED_CONFIRM,
        "ssl_abort_first": None,
        "targets": 0,
        "recovered": [],
        "still_404": [],
        "skipped": True,
        "neighbors_at": None,
        "neighbors_game_time": None,
        "neighbors": {},
        "note": "confirm skipped; no in-window official 404 after first pass 35/35 200",
    },
    "retry2": {
        "at": None,
        "game_time": None,
        "inserted": INSERTED_RETRY2,
        "script_reported_inserted": INSERTED_RETRY2,
        "skipped": True,
        "recovered": [],
        "still_404": [],
        "note": "retry2 skipped; no in-window official 404. just-published W47N8@84361700 (outside this reconstructed window) still official 404 after retry 23:41:43 gt=84361864",
    },
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 1008796,
        "pid_at_precheck": 1008796,
        "loop_pid": 4035476,
        "restart_at": "23:24:49",
        "listener_started": "23:24:58",
        "earlier_restart_this_hour": "23:02:24",
        "wrapup_ws_timeout": None,
        "wrapup_autorestart": None,
        "wrapup_listener_started": None,
        "this_run_restarted": False,
        "waited_for_reconnect": False,
        "live_objects_empty_after_reconnect": False,
        "live_gameTime_none_after_reconnect": False,
        "pre_cpu_path_after_wait": (
            f"creep_cpu through 84361720 / path_arrivals through 84361720 at pre-check 23:32:13; "
            f"live.json gameTime=84361723 and objects_n=260 at pre-check (roomSlot W46N8) after the 23:24:49 auto-reconnect (already fresh, no wait); "
            f"by wrapup roomSlot {live.get('roomSlot')} objects_n={len(live.get('objects') or {})}, live.json gameTime={live.get('gameTime')} stats.t={stats.get('t')}, "
            f"creep_cpu through {cpu_tip} / path_arrivals through {path_tip}"
        ),
    },
    "box_freeze": {
        "from": "2026-11-19 23:20:04",
        "to": "2026-11-19 23:24:46",
        "sec": 276,
        "restart_at": "23:24:49",
        "room_stats_gap": "84361541..84361619",
        "official_filled": "official-filled 79/79 in all 5 rooms (84361500 already filled by the 23:24 patrol through 84361600; this pass wrote 84361600 filling unpublished tail 84361601..84361619)",
        "counts": freeze2320,
        "earlier_restart_gap": "23:02:24 after 22:55:09-23:02:20; 22:25:48 after 22:17:13-22:25:45; 22:04:22 after 21:45:22-22:04:19",
        "earlier_freeze": {
            "from": "2026-11-19 22:55:09",
            "to": "2026-11-19 23:02:20",
            "sec": 431,
            "restart_at": "23:02:24",
            "room_stats_gap": "84361171..84361289",
            "official_filled": "still official-filled 119/119 in all 5 rooms",
            "counts": freeze2255,
        },
        "earlier_freeze_2217": {
            "from": "2026-11-19 22:17:13",
            "to": "2026-11-19 22:25:45",
            "sec": 511,
            "restart_at": "22:25:48",
            "room_stats_gap": "84360621..84360759",
            "official_filled": "aged out of this window start 84361001 (already official-filled 139/139 in W47N8/W45N8/W45N7/W47N7 and 65/139 in W46N8; W46N8 miss is official 404 W46N8@84360600)",
        },
        "new_freeze_this_run": True,
        "already_recorded_by_patrol": True,
        "missed_halfhours": None,
    },
    "new_official_404_not_yet_told": [
        {"room": "W47N8", "base": 84361700, "hole": [84361701, 84361800], "db_distinct": just_pub["W47N8"]["distinct"], "db_note": "live-only 84361756..84361800; just after this reconstructed window; still 404 after first try 23:40:24 gt=84361843 and retry 23:41:43 gt=84361864; next 1h patrol should fold this", "in_window": False},
    ],
    "already_told_still_unfilled": [
        {"room": "W46N8", "base": 84360600, "hole": [84360601, 84360700], "db_distinct": hole_w46n8_60600["distinct"], "db_note": "live-only 84360601..84360626; aged out of this window start 84361001, not retried, still unfilled; already told by the 22:30 patrol", "in_window": False},
        {"room": "W45N7", "base": 84360200, "hole": [84360201, 84360300], "db_distinct": aged_w45n7_60200["distinct"], "db_note": "db 0/100; aged out, not retried, still unfilled; already told by the 22:30 patrol", "in_window": False},
        {"room": "W47N8", "base": 84359900, "hole": [84359901, 84360000], "db_distinct": aged_w47n8_59900["distinct"], "db_note": "live-only 84359901..84359906; aged out, not retried, still unfilled; already told by the 22:30 patrol", "in_window": False},
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
    f"{finished_hkt_sec} verify 23:30 half-hour official-history backfill",
    f"window ticks {TMIN}..{TMAX} published_bases {PUB_BASES} game.time_first={GT_FIRST}",
    f"inserted_first={INSERTED_FIRST} confirm={INSERTED_CONFIRM} retry2={INSERTED_RETRY2} just_published={INSERTED_JUST} total={INSERTED_TOTAL}",
    f"coverage {recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}",
    f"tick_s_first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} in_use={TICK_S_IN_USE:.5f} later_mean_robust={TICK_S_LATER:.5f} corrective={tick_s.get('corrective_applied')} nfix={NFIX_CORR} later_mean_applied_then_reverted=False",
    f"{inwin_txt}",
    f"{leftover_txt}",
    freeze_para,
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 23:24:49 (listener.py pid 1008796 started 23:24:58) after the new box freeze 23:20:04-23:24:46 (276s, room_stats gap 84361541..84361619). Earlier: 23:02:24 after 22:55:09-23:02:20; 22:25:48 after 22:17:13-22:25:45. This run found the listener already fresh; by pre-check 23:32:13 live.json was fresh (gameTime=84361723, stats.t=84361720, roomSlot W46N8, objects_n=260) and CPU/path buffers were flowing (creep_cpu through 84361720 / path_arrivals through 84361720); single_slot held.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_note = DIR / "backfill_retry2.txt"
shutil.copyfile(retry2_note, ROOT / "state" / "_halfhour_backfill_retry2_2330.txt")
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
