#!/usr/bin/env python3
"""Write local status records for the 23:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-19_2300"
assert "_halfhour_2026-11-19_2300" in str(DIR), DIR
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84360601, 84361300
PUB_BASES = "84360600..84361200"
GT_FIRST = 84361330
TICK_S_FIRST = 4.06582
TICK_S_PRINTED = "4.066"
TICK_S_IN_USE = 4.09411  # all_mean; later_raw/robust 4.09231 slightly worse; no corrective realign
TICK_S_LATER = 4.09231
TS_REALIGNED_FIRST = 0
NFIX_CORR = 0
GT_CORR = None
RECON_ROWS = 24345
ALREADY = 15040
INSERTED_FIRST = 9305
INSERTED_CONFIRM = 0  # confirm 23:07:43 gt=84361365 still 404 W46N8@84360600
INSERTED_RETRY2 = 0  # retry2 23:10:45 gt=84361409 still 404 W46N8@84360600
INSERTED_JUST = 2067  # 84361300 attempted 23:13:04 gt=84361442, 200 for all 5 (ticks 84361301..84361400 just after reconstructed window)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:600t/1759new W47N8:700t/4333new W45N8:700t/931new W45N7:700t/1105new W47N7:700t/1177new"
FIRST_PASS_LINE = (
    "first pass 34 of 35 official GETs 200, missing_chunks=1 (W46N8@84360600); "
    "22:30 half-hour already wrote through 84360800 / reconstructed through 84360900 (just-published 84360900 was attempted then at 22:45:53 gt=84361046 and was 200 for all 5, ticks 84360901..84361000); "
    "(this pass already_in_db=15040 / inserted=9305; overlap 84360601..84361000 already present from the 22:30 half-hour plus live rotation, except the W46N8 official 404 hole 84360601..84360700 live-only 84360601..84360626; "
    "this pass newly wrote 84361000..84361200 for all 5 rooms and 84360600 for W47N8/W45N8/W45N7/W47N7 (W46N8 official 404), filling the official-covered new 22:55:09-23:02:20 freeze STATS gap 84361171..84361289 119/119 in all 5; "
    "prior 22:17:13-22:25:45 freeze STATS gap 84360621..84360759 remains official-filled 139/139 in W47N8/W45N8/W45N7/W47N7 and 65/139 in W46N8 (miss is official 404 hole remainder 84360627..84360700; live-only 84360601..84360626); "
    "prior 21:45:22-22:04:19 freeze STATS gap 84360151..84360449 has now aged out of this window start 84360601, except that it does not overlap this window at all); "
    "leftover official 404 W45N7@84360200 aged out of this 40-min window and was not retried (hole 84360201..84360300 still db 0/100; already told by the 22:30 patrol); "
    "leftover official 404 W47N8@84359900, W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out and were not retried; "
    "in-window official 404 W46N8@84360600 still 404 after confirm 23:07:44 game.time=84361365 and retry2 23:10:46 game.time=84361409 (neighbors @84360500 and @84360700 200 at 23:07:53-55, hole 84360601..84360700 db 26/100 live-only 84360601..84360626; already told by the 22:30 patrol, no newer official 404); "
    "just-published 84361300 attempted at 23:13:04 game.time=84361442 and was 200 for all 5 rooms (inserted=2067; ticks 84361301..84361400 sit just after this reconstructed window)"
)
MISSING_CHUNKS = 1

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
    freeze2217 = {room: rng(c, room, 84360621, 84360759, 139) for room in ROOMS}
    freeze2255 = {room: rng(c, room, 84361171, 84361289, 119) for room in ROOMS}
    aged_w47n8_59900 = rng(c, "W47N8", 84359901, 84360000, 100)
    aged_w45n7_60200 = rng(c, "W45N7", 84360201, 84360300, 100)
    hole_w46n8_60600 = rng(c, "W46N8", 84360601, 84360700, 100)
    just_pub = {room: rng(c, room, 84361301, 84361400, 100) for room in ROOMS}
db_after_lines = "\n".join(db_lines)

def empty_ranges(room):
    return (coverage.get(room) or {}).get("official_empty_no_creep_ranges") or []

inwin_txt = (
    "in-window official 404 after first pass: 34 of 35 official GETs 200, missing_chunks=1; "
    "W46N8@84360600 still official 404 after confirm 23:07:44 game.time=84361365 and retry2 23:10:46 game.time=84361409 "
    "(neighbors @84360500 and @84360700 200 at 23:07:53-55, hole 84360601..84360700 db 26/100 live-only 84360601..84360626; "
    "already told by the 22:30 patrol, no newer official 404 this pass); "
    "final official_404_in_window=1 (W46N8@84360600)"
)
leftover_txt = (
    "in-window official 404 remaining: W46N8@84360600 (hole 84360601..84360700 db 26/100 live-only 84360601..84360626). "
    "It was already told by the 22:30 Asia/Hong_Kong patrol (together with W45N7@84360200 and W47N8@84359900); next 1h patrol should fold only newer official 404s than those. "
    "Aged leftover official 404 W45N7@84360200 (hole 84360201..84360300 still db 0/100; already told) aged out of this window start 84360601 and was not retried this pass (still unfilled). "
    "Aged leftover official 404 W47N8@84359900 (hole 84359901..84360000 still db 6/100 live-only 84359901..84359906; already told) also sits outside this window and was not retried (still unfilled). "
    "Aged leftover official 404 W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) were not retried this pass "
    "(already outside this 40-min window). "
    "This window has empty_no_creep=0."
)
confirm_summary = (
    "confirm 23:07:43 game.time=84361365 still_404 W46N8@84360600 (inserted=0); "
    "neighbors @84360500 and @84360700 200 at 23:07:53-55; "
    "retry2 23:10:45 game.time=84361409 still official 404 (inserted=0); "
    "just-published 84361300 attempted at 23:13:04 game.time=84361442 (typically publishable around game.time>=84361440) and was 200 for all 5 rooms (inserted=2067; ticks 84361301..84361400 sit just after this reconstructed window); "
    "this pass newly wrote 84361000..84361200 for all 5 and 84360600 for four rooms (W46N8 still official 404)"
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
    f"later-mean-robust {TICK_S_LATER:.5f} (raw later-mean also 4.09231) is slightly worse than live-anchor-best all_mean {TICK_S_IN_USE:.5f} "
    f"(delta first-robust {TICK_S_FIRST-TICK_S_LATER:.5f} s/tick, ~{(GT_FIRST-TMIN)*abs(TICK_S_FIRST-TICK_S_LATER):.1f}s at tmin; "
    f"over45 later={vs_later_before} vs first={vs_first_over45} vs all_mean={all_vs.get('over45')} vs prev_later={prev_vs.get('over45')}, "
    f"over15 later={vs_later_over15_before} vs first={vs_first_over15} vs all_mean={all_vs.get('over15')} vs prev_later={prev_vs.get('over15')}; "
    f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')}; "
    f"lowest_over45 among sane was {tick_s.get('lowest_over45_sane')} {TICK_S_IN_USE:.5f} "
    f"(mean_off {all_vs.get('mean_off')} closer to the live anchor than later {later_vs.get('mean_off')}, first {first_vs.get('mean_off')} or prev_later {prev_vs.get('mean_off')}); "
    f"first-pass realign moved {TS_REALIGNED_FIRST} rows; "
    f"tick_s_check did not apply a corrective realign (all sane candidates already inside the 45s gate; later-mean-robust was refused as slightly worse than all_mean); "
    f"still_over_45s_vs_later={tick_s.get('still_over_45s_vs_later')}; skipped_cross_chunk={tick_s.get('skipped_cross_chunk')}; "
    f"in-use all_mean {TICK_S_IN_USE:.5f}; "
    f"confirm and retry2 still official 404 W46N8@84360600; just-published 84361300 written for all 5 this pass"
)

stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
freeze_para = (
    f"NEW box freeze 22:55:09-23:02:20 Asia/Hong_Kong (431s) caused run_listener.sh auto-restart 23:02:24 (listener.py pid 998881 started 23:02:33; this run waited for reconnect and did not itself restart the listener). "
    f"room_stats gap 84361171..84361289 (119): official-filled 119/119 in all 5 rooms (both 84361100 and 84361200 chunks were official 200 this first pass; no unpublished tail remains in this gap, which ends at 84361289 inside published 84361200). "
    f"Prior box freeze 22:17:13-22:25:45 Asia/Hong_Kong (511s; run_listener.sh auto-restart 22:25:48, listener.py pid 983114 started 22:25:57 then; not this run) "
    f"room_stats gap 84360621..84360759 (139) remains official-filled 139/139 in W47N8/W45N8/W45N7/W47N7 and 65/139 in W46N8 "
    f"(W46N8 miss is the official 404 hole remainder 84360627..84360700 inside W46N8@84360600; live-only 84360601..84360626). "
    f"Prior box freeze 21:45:22-22:04:19 Asia/Hong_Kong (1127s; restart 22:04:22) room_stats gap 84360151..84360449 (299) has aged out of this window start 84360601 "
    f"(already official-filled 299/299 in W46N8/W47N8/W45N8/W47N7 and 199/299 in W45N7; W45N7 miss is official 404 W45N7@84360200). "
    f"Prior 21:12:19-21:17:18 and 20:42:14-21:03:05 freeze STATS gaps have also aged out of this window. "
    f"Aged official 404 W45N7@84360200, W47N8@84359900, W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300 (and older) remain outside this window. "
    f"This window empty_no_creep=0. "
    f"live.json / stats.t were fresh at pre-check 23:05:00 (age ~2.0s, tip stats.t=84361320, roomSlot W46N8 objects_n=263, live.json gameTime=84361325) after the 23:02:24 auto-reconnect; "
    f"CPU/path buffers were already flowing (creep_cpu through 84361310 / path_arrivals through 84361308); "
    f"this pass wrote 84361000..84361200 for all 5 and just-published 84361300 was attempted and 200 for all 5 at gt=84361442; "
    f"single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84361310 / path_arrivals through 84361308 at pre-check; through {cpu_tip} / {path_tip} at wrapup); this run did not restart the listener."
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
        "base": 84361300,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "2026-11-19 23:13:04 Asia/Hong_Kong",
        "recovered_game_time": 84361442,
        "inserted": INSERTED_JUST,
        "note": "attempted at 23:13:04 game.time=84361442 (typically publishable around game.time>=84361440); 200 for all 5 rooms; inserted=2067; ticks 84361301..84361400 sit just after this reconstructed window 84360601..84361300 and will be overlap for the next half-hour",
        "first_try_all_404": False,
        "first_try_at": "2026-11-19 23:13:04 Asia/Hong_Kong",
        "first_try_game_time": 84361442,
        "first_try_recovered": ["W46N8@84361300", "W47N8@84361300", "W45N8@84361300", "W45N7@84361300", "W47N7@84361300"],
        "first_try_still_404": [],
        "retry_at": None,
        "retry_game_time": None,
        "retry_inserted": 0,
        "ticks": [84361301, 84361400],
        "all_five_official_200": True,
        "still_404": [],
        "in_window_still_404": ["W46N8@84360600"],
        "w45n7_empty_no_creep": empty_ranges("W45N7"),
        "w47n7_empty_no_creep": empty_ranges("W47N7"),
        "distinct": just_pub,
        "skipped": False,
    },
    "confirm": {
        "at": "2026-11-19 23:07:43 Asia/Hong_Kong",
        "game_time": 84361365,
        "inserted": INSERTED_CONFIRM,
        "script_reported_inserted": INSERTED_CONFIRM,
        "ssl_abort_first": None,
        "targets": 1,
        "recovered": [],
        "still_404": ["W46N8@84360600"],
        "skipped": False,
        "neighbors_at": "2026-11-19 23:07:53 Asia/Hong_Kong",
        "neighbors_game_time": None,
        "neighbors": {
            "W46N8@84360500": 200,
            "W46N8@84360600": 404,
            "W46N8@84360700": 200,
        },
        "note": "confirm still official 404 W46N8@84360600 (inserted=0); neighbors @84360500 and @84360700 200 at 23:07:53-55",
    },
    "retry2": {
        "at": "2026-11-19 23:10:45 Asia/Hong_Kong",
        "game_time": 84361409,
        "inserted": INSERTED_RETRY2,
        "script_reported_inserted": INSERTED_RETRY2,
        "skipped": False,
        "recovered": [],
        "still_404": ["W46N8@84360600"],
        "note": "retry2 still official 404 W46N8@84360600; hole 84360601..84360700 db 26/100 live-only 84360601..84360626; already told by the 22:30 patrol",
    },
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 998881,
        "pid_at_precheck": 998881,
        "loop_pid": 4035476,
        "restart_at": "23:02:24",
        "listener_started": "23:02:33",
        "earlier_restart_this_hour": "22:25:48",
        "wrapup_ws_timeout": None,
        "wrapup_autorestart": None,
        "wrapup_listener_started": None,
        "this_run_restarted": False,
        "waited_for_reconnect": True,
        "live_objects_empty_after_reconnect": False,
        "live_gameTime_none_after_reconnect": False,
        "pre_cpu_path_after_wait": (
            f"creep_cpu through 84361310 / path_arrivals through 84361308 at pre-check 23:05:00; "
            f"live.json gameTime=84361325 and objects_n=263 at pre-check (roomSlot W46N8) after the 23:02:24 auto-reconnect; "
            f"by wrapup roomSlot {live.get('roomSlot')} objects_n={len(live.get('objects') or {})}, live.json gameTime={live.get('gameTime')} stats.t={stats.get('t')}, "
            f"creep_cpu through {cpu_tip} / path_arrivals through {path_tip}"
        ),
    },
    "box_freeze": {
        "from": "2026-11-19 22:55:09",
        "to": "2026-11-19 23:02:20",
        "sec": 431,
        "restart_at": "23:02:24",
        "room_stats_gap": "84361171..84361289",
        "official_filled": "official-filled 119/119 in all 5 rooms (84361100 and 84361200 both official 200 this pass); no unpublished tail",
        "counts": freeze2255,
        "earlier_restart_gap": "22:25:48 after 22:17:13-22:25:45; 22:04:22 after 21:45:22-22:04:19; 21:17:21 after 21:12:19-21:17:18",
        "earlier_freeze": {
            "from": "2026-11-19 22:17:13",
            "to": "2026-11-19 22:25:45",
            "sec": 511,
            "restart_at": "22:25:48",
            "room_stats_gap": "84360621..84360759",
            "official_filled": (
                "still official-filled 139/139 in W47N8/W45N8/W45N7/W47N7 and 65/139 in W46N8 "
                "(W46N8 miss is official 404 W46N8@84360600 hole remainder 84360627..84360700; live-only 84360601..84360626)"
            ),
            "counts": freeze2217,
        },
        "earlier_freeze_2145": {
            "from": "2026-11-19 21:45:22",
            "to": "2026-11-19 22:04:19",
            "sec": 1127,
            "restart_at": "22:04:22",
            "room_stats_gap": "84360151..84360449",
            "official_filled": "aged out of this window start 84360601 (already official-filled 299/299 in W46N8/W47N8/W45N8/W47N7 and 199/299 in W45N7; W45N7 miss is official 404 W45N7@84360200)",
        },
        "new_freeze_this_run": True,
        "already_recorded_by_patrol": False,
        "missed_halfhours": None,
    },
    "new_official_404_not_yet_told": [],
    "already_told_still_unfilled": [
        {"room": "W46N8", "base": 84360600, "hole": [84360601, 84360700], "db_distinct": hole_w46n8_60600["distinct"], "db_note": "live-only 84360601..84360626; still in-window; already told by the 22:30 patrol", "in_window": True},
        {"room": "W45N7", "base": 84360200, "hole": [84360201, 84360300], "db_distinct": aged_w45n7_60200["distinct"], "db_note": "db 0/100; aged out of this window start 84360601, not retried, still unfilled; already told by the 22:30 patrol", "in_window": False},
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
    f"{finished_hkt_sec} verify 23:00 half-hour official-history backfill",
    f"window ticks {TMIN}..{TMAX} published_bases {PUB_BASES} game.time_first={GT_FIRST}",
    f"inserted_first={INSERTED_FIRST} confirm={INSERTED_CONFIRM} retry2={INSERTED_RETRY2} just_published={INSERTED_JUST} total={INSERTED_TOTAL}",
    f"coverage {recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}",
    f"tick_s_first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} in_use={TICK_S_IN_USE:.5f} later_mean_robust={TICK_S_LATER:.5f} corrective={tick_s.get('corrective_applied')} nfix={NFIX_CORR} later_mean_applied_then_reverted=False",
    f"{inwin_txt}",
    f"{leftover_txt}",
    freeze_para,
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 23:02:24 (listener.py pid 998881 started 23:02:33) after the new box freeze 22:55:09-23:02:20 (431s, room_stats gap 84361171..84361289). Earlier: 22:25:48 after 22:17:13-22:25:45; 22:04:22 after 21:45:22-22:04:19. This run waited for the 23:02:24 reconnect; by pre-check 23:05:00 live.json was fresh (gameTime=84361325, stats.t=84361320, roomSlot W46N8, objects_n=263) and CPU/path buffers were flowing (creep_cpu through 84361310 / path_arrivals through 84361308); single_slot held.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_note = DIR / "backfill_retry2.txt"
shutil.copyfile(retry2_note, ROOT / "state" / "_halfhour_backfill_retry2_2300.txt")
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
