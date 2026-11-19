#!/usr/bin/env python3
"""Write local status records for the 22:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-19_2200"
assert "_halfhour_2026-11-19_2200" in str(DIR), DIR
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84359701, 84360400
PUB_BASES = "84359700..84360300"
GT_FIRST = 84360495
TICK_S_FIRST = 4.15554
TICK_S_PRINTED = "4.156"
TICK_S_IN_USE = 4.13709  # prev_later; later-mean-robust 4.04754 was applied then reverted
TICK_S_LATER = 4.04754
TS_REALIGNED_FIRST = 8178
NFIX_CORR = 0  # later-mean-robust briefly applied (11497 rows at gt=84360520) then reverted onto prev_later (9643 rows at 22:10:36 gt=84360529)
GT_CORR = None
RECON_ROWS = 26177
ALREADY = 10706
INSERTED_FIRST = 15471
INSERTED_CONFIRM = 0  # confirm 22:10:50-52 gt=84360532 still official 404 W47N8@84359900 and W45N7@84360200
INSERTED_RETRY2 = 0  # retry2 22:13:33-34 gt=84360572 still official 404 both
INSERTED_JUST = 0  # 84360400 not attempted (first-pass game.time=84360495 still in-progress)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/3295new W47N8:600t/6550new W45N8:700t/2396new W45N7:600t/848new W47N7:700t/2382new"
FIRST_PASS_LINE = (
    "first pass 33 of 35 official GETs 200, missing_chunks=2 (W47N8@84359900, W45N7@84360200); "
    "21:30 half-hour already wrote through 84359800 / reconstructed through 84359900 (just-published 84359900 was not attempted then at gt=84359916, typically publishable around game.time>=84360040); "
    "(this pass already_in_db=10706 / inserted=15471; overlap 84359701..84359900 already present from the 21:30 half-hour plus live rotation; "
    "this pass newly wrote previously unpublished 84359900 for W46N8/W45N8/W45N7/W47N7 (W47N8 official 404) and 84360000..84360300 for all 5 rooms except W45N7@84360200 official 404, filling the official-covered portion of the new 21:45:22-22:04:19 freeze STATS gap 84360151..84360400 250/250 in W46N8/W47N8/W45N8/W47N7 and 150/250 in W45N7 (the 100-tick miss is the official 404 hole 84360201..84360300); "
    "unpublished tail 84360401..84360449 of that 299-tick gap still sits in the in-progress 84360400 chunk; "
    "prior 21:12:19-21:17:18 freeze STATS gap and 20:42:14-21:03:05 freeze STATS gap have now aged out of this window start 84359701, except the last 49 official-filled ticks 84359701..84359749 of the 21:12 gap which remain complete in all 5 rooms); "
    "leftover official 404 W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out of this 40-min window and were not retried; "
    "in-window official 404 W47N8@84359900 still 404 after confirm 22:10:50 game.time=84360532 and retry2 22:13:33 game.time=84360572 (neighbors @84359800 and @84360000 200 at 22:11:01-02, hole 84359901..84360000 db 6/100 live-only 84359901..84359906; NEW, not yet told); "
    "in-window official 404 W45N7@84360200 still 404 after confirm 22:10:52 game.time=84360532 and retry2 22:13:34 game.time=84360572 (neighbors @84360100 and @84360300 200 at 22:11:03-04, hole 84360201..84360300 db 0/100; NEW, not yet told); "
    "just-published 84360400 not attempted (first-pass game.time=84360495 still inside the in-progress chunk)"
)
MISSING_CHUNKS = 2

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
    tail = {}
    for room in ROOMS:
        d, n, mn, mx = c.execute(
            "SELECT count(DISTINCT tick), count(*), min(tick), max(tick) "
            "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, 84360401, 84360449),
        ).fetchone()
        tail[room] = {"distinct": d or 0, "rows": n or 0, "min": mn, "max": mx, "missing": 49 - (d or 0)}
    freeze2145 = {}
    for room in ROOMS:
        d, n, mn, mx = c.execute(
            "SELECT count(DISTINCT tick), count(*), min(tick), max(tick) "
            "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, 84360151, 84360449),
        ).fetchone()
        freeze2145[room] = {"distinct": d or 0, "rows": n or 0, "min": mn, "max": mx, "missing": 299 - (d or 0)}
    freeze2145_official = {}
    for room in ROOMS:
        d, n, mn, mx = c.execute(
            "SELECT count(DISTINCT tick), count(*), min(tick), max(tick) "
            "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, 84360151, 84360400),
        ).fetchone()
        freeze2145_official[room] = {"distinct": d or 0, "rows": n or 0, "min": mn, "max": mx, "missing": 250 - (d or 0)}
    aged2112 = {}
    for room in ROOMS:
        d, n, mn, mx = c.execute(
            "SELECT count(DISTINCT tick), count(*), min(tick), max(tick) "
            "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, 84359701, 84359749),
        ).fetchone()
        aged2112[room] = {"distinct": d or 0, "rows": n or 0, "min": mn, "max": mx, "missing": 49 - (d or 0)}
db_after_lines = "\n".join(db_lines)

def empty_ranges(room):
    return (coverage.get(room) or {}).get("official_empty_no_creep_ranges") or []

inwin_txt = (
    "in-window official 404 after first pass: 33 of 35 official GETs 200, missing_chunks=2; "
    "W47N8@84359900 still official 404 after confirm 22:10:50 game.time=84360532 and retry2 22:13:33 game.time=84360572 "
    "(neighbors @84359800 and @84360000 200 at 22:11:01-02, hole 84359901..84360000 db 6/100 live-only 84359901..84359906; NEW, not yet told); "
    "W45N7@84360200 still official 404 after confirm 22:10:52 game.time=84360532 and retry2 22:13:34 game.time=84360572 "
    "(neighbors @84360100 and @84360300 200 at 22:11:03-04, hole 84360201..84360300 db 0/100; NEW, not yet told); "
    "final official_404_in_window=2 (W47N8@84359900, W45N7@84360200)"
)
leftover_txt = (
    "in-window official 404 remaining: W47N8@84359900 (hole 84359901..84360000 db 6/100 live-only 84359901..84359906) and "
    "W45N7@84360200 (hole 84360201..84360300 db 0/100). Both are NEW (not yet told to the user; next 1h patrol should fold them). "
    "Aged leftover official 404 W47N8@84359500 (hole 84359501..84359600), W45N7@84358500 (hole 84358501..84358600) and W47N8@84358700 (hole 84358701..84358800) were not retried this pass "
    "(already outside this 40-min window, along with W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800, and older). "
    "W45N7 official empty-no-creep 84359756..84359931 (176) after remote workers fled the W45N7 Invader Core threat (since 84359712; last our-creep tick 84359755 before a defender arrived 84359932) "
    "and 84360134..84360144 (11)."
)
confirm_summary = (
    "confirm 22:10:49 game.time=84360532 still_404 W47N8@84359900 and W45N7@84360200 (inserted=0); "
    "neighbors of both holes 200 at 22:11:01-04; "
    "retry2 22:13:32 game.time=84360572 both still official 404 (inserted=0); "
    "just-published 84360400 not attempted (first-pass game.time=84360495 still inside the in-progress chunk; typically publishable around game.time>=84360540; retry2 gt=84360572 was past that threshold but this pass did not attempt it; next half-hour overlap will catch it); "
    "previously unpublished 84359900 (in-progress at the 21:30 half-hour / not attempted then at gt=84359916) was written for four rooms this pass (W47N8 official 404), and 84360000..84360300 for all 5 except W45N7@84360200 official 404"
)
vs_later_before = tick_s.get("still_over_45s_vs_later_before")
vs_first_over45 = vs_first.get("over45")
vs_later_over15_before = tick_s.get("still_over_15s_vs_later_before")
vs_first_over15 = vs_first.get("over15")
span_vs = (vs_cand.get("span_mean") or {})
prev_vs = (vs_cand.get("prev_later") or {})
later_vs = (vs_cand.get("later_robust") or vs_cand.get("later_raw") or {})
tick_s_corr_txt = (
    f"script {TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} was worse than first/prev_later versus the live anchor "
    f"(delta first-robust 0.10800 s/tick, ~85.8s at tmin; "
    f"over45 later={vs_later_before} vs first={vs_first_over45}, over15 later={vs_later_over15_before} vs first={vs_first_over15}; "
    f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')}; "
    f"lowest_over45 among sane was {tick_s.get('lowest_over45_sane')} (prev_later mean_off closer to the live anchor than first or later, over45 0 vs first {vs_first_over45} vs later {vs_later_before}); "
    f"first-pass realign moved {TS_REALIGNED_FIRST} rows; "
    f"tick_s_check then applied later-mean-robust realign of 11497 rows at game.time=84360520 because later over45 was >0, "
    f"but later was the worse live-anchor fit (after-apply vs_later over45=0 / vs_first over45=11711); "
    f"the script did not auto-revert because after-vs-later over45 became 0; "
    f"this run immediately reverted onto prev_later 4.13709 (nfix=9643 at 22:10:36 game.time=84360529; after revert vs_prev_later over45=91 mean_off~+4.5s, just over the 45s gate); "
    f"still_over_45s_vs_later={tick_s.get('still_over_45s_vs_later')}; skipped_cross_chunk={tick_s.get('skipped_cross_chunk')}; "
    f"in-use prev_later {TICK_S_IN_USE:.5f}; "
    f"confirm and retry2 still official 404 W47N8@84359900 and W45N7@84360200; just-published 84360400 not attempted; previously unpublished 84359900 (four rooms) and 84360000..84360300 were written this pass"
)

f2145 = freeze2145_official
w47_tail = tail["W47N8"]
freeze_para = (
    f"Box freeze 21:45:22-22:04:19 Asia/Hong_Kong (1127s) caused run_listener.sh auto-restart 22:04:22 (listener.py pid 976439 started 22:04:32; not this run). "
    f"room_stats gap 84360151..84360449 (299): official-covered 84360151..84360400 is now official-filled 250/250 in W46N8/W47N8/W45N8/W47N7 and 150/250 in W45N7 "
    f"(W45N7 miss is the official 404 hole 84360201..84360300); unpublished tail 84360401..84360449 still sits in the in-progress 84360400 chunk "
    f"(W47N8 live already has {w47_tail['distinct']} ticks {w47_tail['min']}..{w47_tail['max'] if w47_tail['max'] else ''} after reconnect while still on that slot; other rooms 0/49). "
    f"Prior 21:12:19-21:17:18 freeze STATS gap 84359661..84359749 has aged mostly out of this window start 84359701; the remaining official-covered tail 84359701..84359749 stays official-filled 49/49 in all 5 rooms. "
    f"Prior 20:42:14-21:03:05 freeze STATS gap 84359231..84359549 has aged out of this window, including the still-open official 404 hole W47N8@84359500 (hole 84359501..84359600) which remains outside this window. "
    f"Aged official 404 W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) remain outside this window. "
    f"W45N7 official empty-no-creep 84359756..84359931 (176) after they fled the Invader Core (threat since 84359712; last our-creep tick 84359755 before a defender arrived 84359932) and 84360134..84360144 (11). "
    f"live.json / stats.t were fresh at pre-check (age ~1s, tip stats.t=84360480, roomSlot W47N8 objects_n=0, live.json gameTime still None) after the 22:04:22 auto-reconnect; CPU/path buffers were already flowing (creep_cpu through 84360480 / path_arrivals through 84360459) and W47N8 live ticks had resumed 84360460..84360491; "
    f"previously unpublished 84359900 (four rooms) and 84360000..84360300 were written this pass; just-published 84360400 was not yet attempted (game.time=84360495 at first pass); "
    f"unpublished live tail of the in-progress 84360400 chunk starts at 84360401; "
    f"single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84360480 / path_arrivals through 84360459 at pre-check; through {cpu_tip} / {path_tip} at wrapup); this run did not restart the listener."
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
    "later_mean_applied_then_reverted": True,
    "later_mean_applied_nfix": 11497,
    "later_mean_reverted_nfix": 9643,
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
        "later_mean_applied_then_reverted": True,
        "tick_s_in_use": TICK_S_IN_USE,
        "still_over_45s_vs_later": tick_s.get("still_over_45s_vs_later"),
        "reason": tick_s.get("reason"),
        "prev_later_over45_before_corrective": (prev_vs or {}).get("over45"),
        "prev_later_mean": tick_s.get("prev_later_mean"),
        "note": tick_s_corr_txt,
    },
    "just_published": {
        "base": 84360400,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": None,
        "recovered_game_time": None,
        "inserted": 0,
        "note": "not attempted; first-pass game.time=84360495 was still inside the in-progress chunk (typically publishable around game.time>=84360540; retry2 game.time=84360572 was past that threshold but this pass did not attempt it; next half-hour overlap will catch it)",
        "first_try_all_404": None,
        "first_try_at": None,
        "first_try_game_time": None,
        "first_try_recovered": [],
        "first_try_still_404": [],
        "retry_at": None,
        "retry_game_time": None,
        "retry_inserted": 0,
        "ticks": None,
        "all_five_official_200": None,
        "still_404": [],
        "in_window_still_404": ["W47N8@84359900", "W45N7@84360200"],
        "w45n7_empty_no_creep": empty_ranges("W45N7"),
        "w47n7_empty_no_creep": empty_ranges("W47N7"),
        "distinct": None,
        "skipped": True,
    },
    "confirm": {
        "at": "2026-11-19 22:10:49 Asia/Hong_Kong",
        "game_time": 84360532,
        "inserted": 0,
        "script_reported_inserted": 0,
        "ssl_abort_first": None,
        "targets": 2,
        "recovered": [],
        "still_404": ["W47N8@84359900", "W45N7@84360200"],
        "skipped": False,
        "neighbors_at": "2026-11-19 22:11:01 Asia/Hong_Kong",
        "neighbors_game_time": None,
        "neighbors": {
            "W47N8@84359800": 200,
            "W47N8@84359900": 404,
            "W47N8@84360000": 200,
            "W45N7@84360100": 200,
            "W45N7@84360200": 404,
            "W45N7@84360300": 200,
        },
        "note": "confirm still official 404 W47N8@84359900 and W45N7@84360200; neighbors of both holes 200 at 22:11:01-04",
    },
    "retry2": {
        "at": "2026-11-19 22:13:32 Asia/Hong_Kong",
        "game_time": 84360572,
        "inserted": 0,
        "script_reported_inserted": 0,
        "skipped": False,
        "recovered": [],
        "still_404": ["W47N8@84359900", "W45N7@84360200"],
        "note": "retry2 both still official 404; W47N8@84359900 hole 84359901..84360000 db 6/100 live-only 84359901..84359906; W45N7@84360200 hole 84360201..84360300 db 0/100",
    },
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 976439,
        "pid_at_precheck": 976439,
        "loop_pid": 4035476,
        "restart_at": "22:04:22",
        "listener_started": "22:04:32",
        "earlier_restart_this_hour": "21:17:21",
        "wrapup_ws_timeout": None,
        "wrapup_autorestart": None,
        "wrapup_listener_started": None,
        "this_run_restarted": False,
        "waited_for_reconnect": True,
        "live_objects_empty_after_reconnect": True,
        "live_gameTime_none_after_reconnect": True,
        "pre_cpu_path_after_wait": (
            f"creep_cpu through 84360480 / path_arrivals through 84360459 at pre-check 22:07:50; "
            f"live.json gameTime None and objects_n=0 at pre-check (roomSlot W47N8) but W47N8 live ticks had already resumed 84360460..84360491 and stats.t=84360480 was advancing; "
            f"by wrapup roomSlot {live.get('roomSlot')} objects_n={len(live.get('objects') or {})}, live.json gameTime still {live.get('gameTime')}, stats.t={stats.get('t')}, "
            f"creep_cpu through {cpu_tip} / path_arrivals through {path_tip}"
        ),
    },
    "box_freeze": {
        "from": "2026-11-19 21:45:22",
        "to": "2026-11-19 22:04:19",
        "sec": 1127,
        "restart_at": "22:04:22",
        "room_stats_gap": "84360151..84360449",
        "official_filled": (
            "official-covered 84360151..84360400 250/250 in W46N8/W47N8/W45N8/W47N7 and 150/250 in W45N7 "
            "(W45N7 miss is official 404 W45N7@84360200 hole 84360201..84360300); "
            f"unpublished tail 84360401..84360449 still in-progress (W47N8 live {w47_tail['distinct']}/49, others 0/49)"
        ),
        "earlier_restart_gap": "21:17:21 after 21:12:19-21:17:18",
        "earlier_freeze": {
            "from": "2026-11-19 21:12:19",
            "to": "2026-11-19 21:17:18",
            "sec": 298,
            "restart_at": "21:17:21",
            "room_stats_gap": "84359661..84359749",
            "official_filled": "aged mostly out of this window start 84359701; remaining tail 84359701..84359749 official-filled 49/49 in all 5 rooms",
        },
        "new_freeze_this_run": True,
        "already_recorded_by_patrol": False,
        "missed_halfhours": None,
    },
    "new_official_404_not_yet_told": [
        {"room": "W47N8", "base": 84359900, "hole": [84359901, 84360000], "db_distinct": 6, "db_note": "live-only 84359901..84359906"},
        {"room": "W45N7", "base": 84360200, "hole": [84360201, 84360300], "db_distinct": 0, "db_note": "db 0/100"},
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
    f"{finished_hkt_sec} verify 22:00 half-hour official-history backfill",
    f"window ticks {TMIN}..{TMAX} published_bases {PUB_BASES} game.time_first={GT_FIRST}",
    f"inserted_first={INSERTED_FIRST} confirm={INSERTED_CONFIRM} retry2={INSERTED_RETRY2} just_published={INSERTED_JUST} total={INSERTED_TOTAL}",
    f"coverage {recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}",
    f"tick_s_first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} in_use={TICK_S_IN_USE:.5f} later_mean_robust={TICK_S_LATER:.5f} corrective={tick_s.get('corrective_applied')} nfix={NFIX_CORR} later_mean_applied_then_reverted=True",
    f"{inwin_txt}",
    f"{leftover_txt}",
    freeze_para,
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 22:04:22 (listener.py pid 976439 started 22:04:32) after the new box freeze 21:45:22-22:04:19 (1127s, room_stats gap 84360151..84360449). Earlier: 21:17:21 after 21:12:19-21:17:18. The 22:04:22 reconnect had already recovered stats/CPU/path by pre-check 22:07:50 (live.json fresh, stats.t=84360480 advancing, roomSlot W47N8; W47N8 live ticks resumed; single_slot held). live.json gameTime stayed None and objects_n=0 after reconnect, but ingest and 5:5:1:1 rotation continued.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_note = DIR / "backfill_retry2.txt"
shutil.copyfile(retry2_note, ROOT / "state" / "_halfhour_backfill_retry2_2200.txt")
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
