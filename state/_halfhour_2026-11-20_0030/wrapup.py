#!/usr/bin/env python3
"""Write local status records for the 00:30 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-20_0030"
assert "_halfhour_2026-11-20_0030" in str(DIR), DIR
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84361901, 84362600
PUB_BASES = "84361900..84362500"
GT_FIRST = 84362699
TICK_S_FIRST = 4.02142
TICK_S_PRINTED = "4.021"
TICK_S_IN_USE = 4.02142  # first; later_raw/robust 4.08458 worse (over45=8812); all_mean 4.07539 also worse (over45=7170)
TICK_S_LATER = 4.08458
TS_REALIGNED_FIRST = 0
NFIX_CORR = 0
GT_CORR = 84362727
RECON_ROWS = 27704
ALREADY = 21223
INSERTED_FIRST = 6481
INSERTED_CONFIRM = 0  # confirm skipped; no in-window official 404
INSERTED_RETRY2 = 0  # retry2 skipped; no in-window official 404
INSERTED_JUST = 3091  # 84362600 attempted 00:41:15 gt=84362740, 200 for all 5 (ticks 84362601..84362700 just after reconstructed window)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/1059new W47N8:700t/2693new W45N8:700t/710new W45N7:700t/667new W47N7:700t/1352new"
FIRST_PASS_LINE = (
    "first pass 35 of 35 official GETs 200, missing_chunks=0; "
    "00:00 half-hour already wrote through 84362000 / reconstructed through 84362100 (just-published 84362100 was attempted then at 00:07:20 gt=84362243 and was 200 for all 5, ticks 84362101..84362200); "
    "the 00:18 1h patrol already wrote published_bases 84361700..84362300 / reconstructed 84361701..84362400 at gt=84362418 (missing_chunks=1 W47N8@84361700, inserted=6149, tick_s=3.932, ts_realigned=16970); "
    "(this pass already_in_db=21223 / inserted=6481; overlap 84361901..84362400 already present from the 00:00 half-hour plus the 00:18 patrol plus live rotation, except W47N7 official empty-no-creep 84361901..84361987 (tail of 84361854..84361987); "
    "this pass newly wrote 84362400..84362500 for all 5 rooms, filling the previously unpublished tail of the 00:13:42-00:18:42 freeze STATS gap 84362331..84362419 (89/89 in all 5; official 84362331..84362400 was already filled at patrol time, this pass wrote 84362401..84362419) and the official-covered head of the NEW 00:31:21-00:32:40 freeze STATS gap 84362591..84362619 (84362591..84362600 in-window, tail 84362601..84362619 via just-published 84362600); "
    "prior 23:47:48-23:55:08 freeze STATS gap 84361951..84362069 remains official-filled 119/119 in W46N8/W47N8/W45N8/W45N7 and 82/119 in W47N7 (W47N7 miss 84361951..84361987 is official empty-no-creep); "
    "prior 23:20:04-23:24:46 freeze STATS gap 84361541..84361619 has now aged out of this window start 84361901); "
    "leftover official 404 W47N8@84361700 aged out of this 40-min window and was not retried (hole 84361701..84361800 still db 45/100 live-only 84361756..84361800; already told by the 00:28 1h patrol); "
    "leftover official 404 W46N8@84360600, W45N7@84360200, W47N8@84359900, W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out and were not retried; "
    "in-window official 404: none (confirm and retry2 skipped); "
    "just-published 84362600 attempted at 00:41:15 game.time=84362740 and was 200 for all 5 rooms (inserted=3091; ticks 84362601..84362700 sit just after this reconstructed window)"
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
just_pub_payload = json.loads((DIR / "just_published_84362600.json").read_text())
confirm_payload = json.loads((DIR / "backfill_confirm_gets.json").read_text())

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
    freeze2347 = {room: rng(c, room, 84361951, 84362069, 119) for room in ROOMS}
    freeze0013 = {room: rng(c, room, 84362331, 84362419, 89) for room in ROOMS}
    freeze0031 = {room: rng(c, room, 84362591, 84362619, 29) for room in ROOMS}
    freeze2320 = {room: rng(c, room, 84361541, 84361619, 79) for room in ROOMS}
    aged_w47n8_59900 = rng(c, "W47N8", 84359901, 84360000, 100)
    aged_w45n7_60200 = rng(c, "W45N7", 84360201, 84360300, 100)
    hole_w46n8_60600 = rng(c, "W46N8", 84360601, 84360700, 100)
    hole_w47n8_61700 = rng(c, "W47N8", 84361701, 84361800, 100)
    just_pub = {room: rng(c, room, 84362601, 84362700, 100) for room in ROOMS}
db_after_lines = "\n".join(db_lines)

inwin_txt = (
    "in-window official 404 after first pass: 35 of 35 official GETs 200, missing_chunks=0; "
    "confirm and retry2 skipped; "
    "final official_404_in_window=0"
)
leftover_txt = (
    "in-window official 404 remaining: none. "
    f"Aged leftover official 404 W47N8@84361700 (hole 84361701..84361800 still db {hole_w47n8_61700['distinct']}/100 live-only 84361756..84361800; already told by the 00:28 1h patrol) aged out of this window start 84361901 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W46N8@84360600 (hole 84360601..84360700 still db {hole_w46n8_60600['distinct']}/100 live-only 84360601..84360626; already told by the 22:30 patrol) aged out of this window start 84361901 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W45N7@84360200 (hole 84360201..84360300 still db {aged_w45n7_60200['distinct']}/100; already told) and W47N8@84359900 (hole 84359901..84360000 still db {aged_w47n8_59900['distinct']}/100 live-only 84359901..84359906; already told) also sit outside this window and were not retried (still unfilled). "
    "Aged leftover official 404 W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) were not retried this pass "
    "(already outside this 40-min window). "
    "This window has empty_no_creep=87 (W47N7 official 200 with no owned creeps 84361901..84361987, tail of 84361854..84361987)."
)
confirm_summary = (
    "confirm and retry2 skipped (no in-window official 404 after first pass 35/35 200); "
    "just-published 84362600 attempted at 00:41:15 game.time=84362740 (typically publishable around game.time>=84362740) and was 200 for all 5 rooms (inserted=3091); "
    "ticks 84362601..84362700 sit just after this reconstructed window; "
    "this pass newly wrote 84362400..84362500 for all 5, filling the 00:13:42-00:18:42 freeze unpublished tail and the official-covered head of the 00:31:21-00:32:40 freeze (just-published filled the tail)"
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
    f"later-mean-robust {TICK_S_LATER:.5f} (raw later-mean also 4.08458) is worse than live-anchor-best first {TICK_S_IN_USE:.5f} "
    f"(delta first-robust {TICK_S_FIRST-TICK_S_LATER:.5f} s/tick, ~{(GT_FIRST-TMIN)*abs(TICK_S_FIRST-TICK_S_LATER):.1f}s at tmin; "
    f"over45 later={vs_later_before} vs first={vs_first_over45} vs all_mean={all_vs.get('over45')} vs prev_later={prev_vs.get('over45')}, "
    f"over15 later={vs_later_over15_before} vs first={vs_first_over15} vs all_mean={all_vs.get('over15')} vs prev_later={prev_vs.get('over15')}; "
    f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')}; "
    f"lowest_over45 among sane was {tick_s.get('lowest_over45_sane')} {TICK_S_IN_USE:.5f} "
    f"(mean_off {first_vs.get('mean_off')} closer to the live anchor than later {later_vs.get('mean_off')}, all_mean {all_vs.get('mean_off')} or prev_later {prev_vs.get('mean_off')}); "
    f"first-pass realign moved {TS_REALIGNED_FIRST} rows; "
    f"tick_s_check applied a no-op corrective first realign (nfix=0) at game.time={GT_CORR} (live-anchor-best first already preferred; later-mean-robust was refused as worse than first; still_over_45s_vs_target=0); "
    f"still_over_45s_vs_later={tick_s.get('still_over_45s_vs_later')}; skipped_cross_chunk={tick_s.get('skipped_cross_chunk')}; "
    f"in-use first {TICK_S_IN_USE:.5f}; "
    f"confirm and retry2 skipped; just-published 84362600 written for all 5 rooms this pass"
)

stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
f2347 = ", ".join(f"{r} {freeze2347[r]['distinct']}/119" for r in ROOMS)
f0013 = ", ".join(f"{r} {freeze0013[r]['distinct']}/89" for r in ROOMS)
f0031 = ", ".join(f"{r} {freeze0031[r]['distinct']}/29" for r in ROOMS)
objs = live.get("objects") or {}
objects_n = len(objs) if isinstance(objs, (list, dict)) else 0
freeze_para = (
    f"NEW box freeze 00:31:21-00:32:40 Asia/Hong_Kong (76s) caused run_listener.sh auto-restart 00:32:43 (listener.py pid 1039908 started 00:32:52; this run found the listener already fresh and did not itself restart it). "
    f"room_stats gap 84362591..84362619 (29): official-filled 29/29 in all 5 "
    f"(head 84362591..84362600 written in this first pass; tail 84362601..84362619 written by just-published 84362600; counts {f0031}). "
    f"Prior box freeze 00:13:42-00:18:42 Asia/Hong_Kong (298s; run_listener.sh auto-restart 00:18:45; already told by the 00:28 1h patrol) "
    f"room_stats gap 84362331..84362419 (89) is now official-filled 89/89 in all 5 "
    f"(patrol had official 84362331..84362400 filled and tail 84362401..84362419 unpublished; this pass wrote 84362400 filling that tail; counts {f0013}). "
    f"Prior box freeze 23:47:48-23:55:08 Asia/Hong_Kong (439s; restart 23:55:11) room_stats gap 84361951..84362069 (119) remains official-filled 119/119 in W46N8/W47N8/W45N8/W45N7 and 82/119 in W47N7 "
    f"(W47N7 miss 37 ticks 84361951..84361987 is official empty-no-creep, part of 84361854..84361987; counts {f2347}). "
    f"Prior box freeze 23:20:04-23:24:46 Asia/Hong_Kong (276s; restart 23:24:49) room_stats gap 84361541..84361619 (79) has aged out of this window start 84361901 (already official-filled 79/79 in all 5). "
    f"Prior 22:55:09-23:02:20 and earlier freeze STATS gaps have also aged out of this window. "
    f"Aged official 404 W47N8@84361700, W46N8@84360600, W45N7@84360200, W47N8@84359900, W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300 (and older) remain outside this window. "
    f"This window empty_no_creep=87 (W47N7 84361901..84361987). "
    f"live.json / stats.t were fresh at pre-check 00:37:55 (age ~1.1s, tip stats.t=84362690, roomSlot W47N8 objects_n=0, live.json gameTime=84362673) after the 00:32:43 auto-reconnect; "
    f"CPU/path buffers were already flowing (creep_cpu through 84362690 / path_arrivals through 84362686); "
    f"this pass wrote 84362400..84362500 for all 5 and just-published 84362600 was attempted at gt=84362740 (200 for all 5); "
    f"single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84362690 / path_arrivals through 84362686 at pre-check; through {cpu_tip} / {path_tip} at wrapup); this run did not restart the listener."
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
        "corrective_applied": True,
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
        "corrective_nfix": NFIX_CORR,
        "corrective_note": "no-op corrective first realign at gt=84362727; later refused as worse than first",
    },
    "just_published": {
        "base": 84362600,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "2026-11-20 00:41:15 Asia/Hong_Kong",
        "recovered_game_time": 84362740,
        "inserted": INSERTED_JUST,
        "note": "attempted at 00:41:15 game.time=84362740 (typically publishable around game.time>=84362740); 200 for all 5 rooms; inserted=3091; ticks 84362601..84362700 sit just after this reconstructed window 84361901..84362600 and will be overlap for the next half-hour; also filled the 00:31:21-00:32:40 freeze tail 84362601..84362619",
        "first_try_all_404": False,
        "first_try_at": "2026-11-20 00:41:15 Asia/Hong_Kong",
        "first_try_game_time": 84362740,
        "first_try_recovered": ["W46N8@84362600", "W47N8@84362600", "W45N8@84362600", "W45N7@84362600", "W47N7@84362600"],
        "first_try_still_404": [],
        "retry_at": None,
        "retry_game_time": None,
        "retry_inserted": 0,
        "ticks": [84362601, 84362700],
        "all_five_official_200": True,
        "still_404": [],
        "in_window_still_404": [],
        "w45n7_empty_no_creep": [],
        "w47n7_empty_no_creep": [[84361901, 84361987]],
        "distinct": just_pub,
        "skipped": False,
        "raw": just_pub_payload,
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
        "raw": confirm_payload,
    },
    "retry2": {
        "at": None,
        "game_time": None,
        "inserted": 0,
        "script_reported_inserted": 0,
        "skipped": True,
        "recovered": [],
        "still_404": [],
        "note": "retry2 skipped; no in-window official 404 after first pass 35/35 200",
    },
    "listener": {
        "single_slot": True,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 1039908,
        "pid_at_precheck": 1039908,
        "loop_pid": 4035476,
        "restart_at": "00:32:43",
        "listener_started": "00:32:52",
        "earlier_restart_this_hour": "00:18:45",
        "wrapup_ws_timeout": None,
        "wrapup_autorestart": None,
        "wrapup_listener_started": None,
        "this_run_restarted": False,
        "waited_for_reconnect": False,
        "live_objects_empty_after_reconnect": objects_n == 0 and live.get("roomSlot") == "W47N8",
        "live_gameTime_none_after_reconnect": False,
        "pre_cpu_path_after_wait": (
            f"creep_cpu through 84362690 / path_arrivals through 84362686 at pre-check 00:37:55; "
            f"live.json gameTime=84362673 and objects_n=0 at pre-check (roomSlot W47N8) after the 00:32:43 auto-reconnect; "
            f"stats.t and listener_rot were advancing (stats.t=84362690); "
            f"by wrapup roomSlot {live.get('roomSlot')} objects_n={objects_n}, "
            f"live.json gameTime={live.get('gameTime')} stats.t={stats.get('t')}, "
            f"creep_cpu through {cpu_tip} / path_arrivals through {path_tip}"
        ),
    },
    "box_freeze": {
        "from": "2026-11-20 00:31:21",
        "to": "2026-11-20 00:32:40",
        "sec": 76,
        "restart_at": "00:32:43",
        "room_stats_gap": "84362591..84362619",
        "official_filled": "official-filled 29/29 in all 5 rooms (this pass wrote 84362500 covering 84362591..84362600; just-published 84362600 filled tail 84362601..84362619)",
        "counts": freeze0031,
        "earlier_restart_gap": "00:18:45 after 00:13:42-00:18:42; 23:55:11 after 23:47:48-23:55:08; 23:24:49 after 23:20:04-23:24:46",
        "earlier_freeze": {
            "from": "2026-11-20 00:13:42",
            "to": "2026-11-20 00:18:42",
            "sec": 298,
            "restart_at": "00:18:45",
            "room_stats_gap": "84362331..84362419",
            "official_filled": "now official-filled 89/89 in all 5 rooms (patrol filled 84362331..84362400; this pass wrote 84362400 filling unpublished tail 84362401..84362419)",
            "counts": freeze0013,
        },
        "earlier_freeze_2347": {
            "from": "2026-11-19 23:47:48",
            "to": "2026-11-19 23:55:08",
            "sec": 439,
            "restart_at": "23:55:11",
            "room_stats_gap": "84361951..84362069",
            "official_filled": "still official-filled 119/119 in W46N8/W47N8/W45N8/W45N7 and 82/119 in W47N7 (W47N7 miss is official empty-no-creep)",
            "counts": freeze2347,
        },
        "new_freeze_this_run": True,
        "already_recorded_by_patrol": False,
        "missed_halfhours": None,
    },
    "new_official_404_not_yet_told": [],
    "already_told_still_unfilled": [
        {"room": "W47N8", "base": 84361700, "hole": [84361701, 84361800], "db_distinct": hole_w47n8_61700["distinct"], "db_note": "live-only 84361756..84361800; aged out of this window start 84361901, not retried, still unfilled; already told by the 00:28 1h patrol", "in_window": False},
        {"room": "W46N8", "base": 84360600, "hole": [84360601, 84360700], "db_distinct": hole_w46n8_60600["distinct"], "db_note": "live-only 84360601..84360626; aged out of this window start 84361901, not retried, still unfilled; already told by the 22:30 patrol", "in_window": False},
        {"room": "W45N7", "base": 84360200, "hole": [84360201, 84360300], "db_distinct": aged_w45n7_60200["distinct"], "db_note": "db 0/100; aged out, not retried, still unfilled; already told", "in_window": False},
        {"room": "W47N8", "base": 84359900, "hole": [84359901, 84360000], "db_distinct": aged_w47n8_59900["distinct"], "db_note": "live-only 84359901..84359906; aged out, not retried, still unfilled; already told", "in_window": False},
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
    f"{finished_hkt_sec} verify 00:30 half-hour official-history backfill",
    f"window ticks {TMIN}..{TMAX} published_bases {PUB_BASES} game.time_first={GT_FIRST}",
    f"inserted_first={INSERTED_FIRST} confirm={INSERTED_CONFIRM} retry2={INSERTED_RETRY2} just_published={INSERTED_JUST} total={INSERTED_TOTAL}",
    f"coverage {recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}",
    f"tick_s_first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} in_use={TICK_S_IN_USE:.5f} later_mean_robust={TICK_S_LATER:.5f} corrective={tick_s.get('corrective_applied')} nfix={NFIX_CORR} later_mean_applied_then_reverted=False",
    f"{inwin_txt}",
    f"{leftover_txt}",
    freeze_para,
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 00:32:43 (listener.py pid 1039908 started 00:32:52) after the new box freeze 00:31:21-00:32:40 (76s, room_stats gap 84362591..84362619). Earlier: 00:18:45 after 00:13:42-00:18:42; 23:55:11 after 23:47:48-23:55:08. This run found the listener already fresh; by pre-check 00:37:55 live.json was fresh (gameTime=84362673, stats.t=84362690, roomSlot W47N8, objects_n=0) and CPU/path buffers were flowing (creep_cpu through 84362690 / path_arrivals through 84362686); single_slot held.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_note = DIR / "backfill_retry2.txt"
shutil.copyfile(retry2_note, ROOT / "state" / "_halfhour_backfill_retry2_0030.txt")
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
