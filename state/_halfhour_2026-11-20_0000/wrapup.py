#!/usr/bin/env python3
"""Write local status records for the 00:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-20_0000"
assert "_halfhour_2026-11-20_0000" in str(DIR), DIR
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84361401, 84362100
PUB_BASES = "84361400..84362000"
GT_FIRST = 84362142
TICK_S_FIRST = 4.07163
TICK_S_PRINTED = "4.072"
TICK_S_IN_USE = 4.058805  # all_mean; later_raw/robust 4.06418 slightly worse (same over45=0, higher mean_off); no corrective realign
TICK_S_LATER = 4.06418
TS_REALIGNED_FIRST = 0
NFIX_CORR = 0
GT_CORR = None
RECON_ROWS = 27054
ALREADY = 16650
INSERTED_FIRST = 10404
INSERTED_CONFIRM = 0  # confirm 00:02:28 gt=84362172 still 404 W47N8@84361700
INSERTED_RETRY2 = 0  # retry2 00:05:55 gt=84362222 still 404 W47N8@84361700
INSERTED_JUST = 3073  # 84362100 attempted 00:07:20 gt=84362243, 200 for all 5 (ticks 84362101..84362200 just after reconstructed window)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/2682new W47N8:600t/4835new W45N8:700t/1461new W45N7:700t/925new W47N7:700t/501new"
FIRST_PASS_LINE = (
    "first pass 34 of 35 official GETs 200, missing_chunks=1 (W47N8@84361700); "
    "23:30 half-hour already wrote through 84361600 / reconstructed through 84361700 (just-published 84361700 was attempted then at 23:40:19 gt=84361843 and was 200 for W46N8/W45N8/W45N7/W47N7, ticks 84361701..84361800; W47N8@84361700 still official 404 after retry 23:41:43 gt=84361864); "
    "(this pass already_in_db=16650 / inserted=10404; overlap 84361401..84361700 already present from the 23:30 half-hour plus live rotation, except the W47N8 official 404 hole 84361701..84361755 live-only 84361756..84361800; "
    "this pass newly wrote 84361800..84362000 for all 5 rooms and 84361700 for W46N8/W45N8/W45N7/W47N7 (W47N8 official 404), filling the official-covered new 23:47:48-23:55:08 freeze STATS gap 84361951..84362069 119/119 in W46N8/W47N8/W45N8/W45N7 and 82/119 in W47N7 (W47N7 miss 84361951..84361987 is official empty-no-creep, part of 84361854..84361987); "
    "prior 23:20:04-23:24:46 freeze STATS gap 84361541..84361619 remains official-filled 79/79 in all 5; "
    "prior 22:55:09-23:02:20 freeze STATS gap 84361171..84361289 has now aged out of this window start 84361401); "
    "leftover official 404 W46N8@84360600 aged out of this 40-min window and was not retried (hole 84360601..84360700 still db 26/100 live-only 84360601..84360626; already told by the 22:30 patrol); "
    "leftover official 404 W45N7@84360200, W47N8@84359900, W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out and were not retried; "
    "in-window official 404 W47N8@84361700 still 404 after confirm 00:02:29 game.time=84362172 and retry2 00:05:56 game.time=84362222 (neighbors @84361600 and @84361800 200 on first pass, hole 84361701..84361800 db 45/100 live-only 84361756..84361800; first seen as just-published 404 at 23:40:24/23:41:43 last half-hour, not yet told by a 1h patrol); "
    "just-published 84362100 attempted at 00:07:20 game.time=84362243 and was 200 for all 5 rooms (inserted=3073; ticks 84362101..84362200 sit just after this reconstructed window)"
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
just_pub_payload = json.loads((DIR / "just_published_84362100.json").read_text())
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
    freeze2320 = {room: rng(c, room, 84361541, 84361619, 79) for room in ROOMS}
    freeze2255 = {room: rng(c, room, 84361171, 84361289, 119) for room in ROOMS}
    aged_w47n8_59900 = rng(c, "W47N8", 84359901, 84360000, 100)
    aged_w45n7_60200 = rng(c, "W45N7", 84360201, 84360300, 100)
    hole_w46n8_60600 = rng(c, "W46N8", 84360601, 84360700, 100)
    hole_w47n8_61700 = rng(c, "W47N8", 84361701, 84361800, 100)
    just_pub = {room: rng(c, room, 84362101, 84362200, 100) for room in ROOMS}
db_after_lines = "\n".join(db_lines)

inwin_txt = (
    "in-window official 404 after first pass: 34 of 35 official GETs 200, missing_chunks=1 (W47N8@84361700); "
    "confirm 00:02:29 game.time=84362172 still 404; retry2 00:05:56 game.time=84362222 still 404; "
    "final official_404_in_window=1 (W47N8@84361700, hole 84361701..84361800 db 45/100 live-only 84361756..84361800)"
)
leftover_txt = (
    "in-window official 404 remaining: W47N8@84361700 still official 404 after confirm 00:02:29 game.time=84362172 and retry2 00:05:56 game.time=84362222 "
    f"(neighbors @84361600 and @84361800 200 on first pass, hole 84361701..84361800 db {hole_w47n8_61700['distinct']}/100 live-only 84361756..84361800; "
    "first seen as just-published 404 at 23:40:24/23:41:43 last half-hour, not yet told by a 1h patrol; next 1h patrol should fold this). "
    f"Aged leftover official 404 W46N8@84360600 (hole 84360601..84360700 still db {hole_w46n8_60600['distinct']}/100 live-only 84360601..84360626; already told by the 22:30 patrol) aged out of this window start 84361401 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W45N7@84360200 (hole 84360201..84360300 still db {aged_w45n7_60200['distinct']}/100; already told) and W47N8@84359900 (hole 84359901..84360000 still db {aged_w47n8_59900['distinct']}/100 live-only 84359901..84359906; already told) also sit outside this window and were not retried (still unfilled). "
    "Aged leftover official 404 W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) were not retried this pass "
    "(already outside this 40-min window). "
    "This window has empty_no_creep=134 (W47N7 official 200 with no owned creeps 84361854..84361987)."
)
confirm_summary = (
    "confirm 00:02:29 game.time=84362172 still official 404 W47N8@84361700 (inserted=0); "
    "retry2 00:05:56 game.time=84362222 still official 404 W47N8@84361700 (inserted=0); "
    "just-published 84362100 attempted at 00:07:20 game.time=84362243 (typically publishable around game.time>=84362240) and was 200 for all 5 rooms (inserted=3073); "
    "ticks 84362101..84362200 sit just after this reconstructed window; "
    "this pass newly wrote 84361800..84362000 for all 5, filling the 23:47:48-23:55:08 freeze STATS gap"
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
    f"later-mean-robust {TICK_S_LATER:.5f} (raw later-mean also 4.06418) is worse than live-anchor-best all_mean {TICK_S_IN_USE:.5f} "
    f"(delta first-robust {TICK_S_FIRST-TICK_S_LATER:.5f} s/tick, ~{(GT_FIRST-TMIN)*abs(TICK_S_FIRST-TICK_S_LATER):.1f}s at tmin; "
    f"over45 later={vs_later_before} vs first={vs_first_over45} vs all_mean={all_vs.get('over45')} vs prev_later={prev_vs.get('over45')}, "
    f"over15 later={vs_later_over15_before} vs first={vs_first_over15} vs all_mean={all_vs.get('over15')} vs prev_later={prev_vs.get('over15')}; "
    f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')}; "
    f"lowest_over45 among sane was {tick_s.get('lowest_over45_sane')} {TICK_S_IN_USE:.5f} "
    f"(mean_off {all_vs.get('mean_off')} closer to the live anchor than later {later_vs.get('mean_off')}, first {first_vs.get('mean_off')} or prev_later {prev_vs.get('mean_off')}); "
    f"first-pass realign moved {TS_REALIGNED_FIRST} rows; "
    f"tick_s_check did not apply a corrective realign (live-anchor-best all_mean already inside the 45s gate with over45=0; later-mean-robust was refused as worse than all_mean); "
    f"still_over_45s_vs_later={tick_s.get('still_over_45s_vs_later')}; skipped_cross_chunk={tick_s.get('skipped_cross_chunk')}; "
    f"in-use all_mean {TICK_S_IN_USE:.5f}; "
    f"confirm and retry2 still official 404 W47N8@84361700; just-published 84362100 written for all 5 rooms this pass"
)

stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
f2347 = ", ".join(f"{r} {freeze2347[r]['distinct']}/119" for r in ROOMS)
freeze_para = (
    f"NEW box freeze 23:47:48-23:55:08 Asia/Hong_Kong (439s) caused run_listener.sh auto-restart 23:55:11 (listener.py pid 1023301 started 23:55:21; this run found the listener already fresh and did not itself restart it). "
    f"room_stats gap 84361951..84362069 (119): official-filled 119/119 in W46N8/W47N8/W45N8/W45N7 and 82/119 in W47N7 "
    f"(W47N7 miss 37 ticks 84361951..84361987 is official empty-no-creep, part of 84361854..84361987; counts {f2347}). "
    f"Prior box freeze 23:20:04-23:24:46 Asia/Hong_Kong (276s; run_listener.sh auto-restart 23:24:49, listener.py pid 1008796 started 23:24:58 then; not this run) "
    f"room_stats gap 84361541..84361619 (79) remains official-filled 79/79 in all 5. "
    f"Prior box freeze 22:55:09-23:02:20 Asia/Hong_Kong (431s; restart 23:02:24) room_stats gap 84361171..84361289 (119) has aged out of this window start 84361401 "
    f"(already official-filled 119/119 in all 5). "
    f"Prior 22:17:13-22:25:45, 21:45:22-22:04:19, 21:12:19-21:17:18 and 20:42:14-21:03:05 freeze STATS gaps have also aged out of this window. "
    f"Aged official 404 W46N8@84360600, W45N7@84360200, W47N8@84359900, W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300 (and older) remain outside this window. "
    f"This window empty_no_creep=134 (W47N7 84361854..84361987). "
    f"live.json / stats.t were fresh at pre-check 23:59:56 (age ~1.9s, tip stats.t=84362130, roomSlot W46N8 objects_n=261, live.json gameTime=84362135) after the 23:55:11 auto-reconnect; "
    f"CPU/path buffers were already flowing (creep_cpu through 84362120 / path_arrivals through 84362111); "
    f"this pass wrote 84361800..84362000 for all 5 and just-published 84362100 was attempted at gt=84362243 (200 for all 5); "
    f"single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84362120 / path_arrivals through 84362111 at pre-check; through {cpu_tip} / {path_tip} at wrapup); this run did not restart the listener."
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
        "base": 84362100,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "2026-11-20 00:07:20 Asia/Hong_Kong",
        "recovered_game_time": 84362243,
        "inserted": INSERTED_JUST,
        "note": "attempted at 00:07:20 game.time=84362243 (typically publishable around game.time>=84362240); 200 for all 5 rooms; inserted=3073; ticks 84362101..84362200 sit just after this reconstructed window 84361401..84362100 and will be overlap for the next half-hour",
        "first_try_all_404": False,
        "first_try_at": "2026-11-20 00:07:20 Asia/Hong_Kong",
        "first_try_game_time": 84362243,
        "first_try_recovered": ["W46N8@84362100", "W47N8@84362100", "W45N8@84362100", "W45N7@84362100", "W47N7@84362100"],
        "first_try_still_404": [],
        "retry_at": None,
        "retry_game_time": None,
        "retry_inserted": 0,
        "ticks": [84362101, 84362200],
        "all_five_official_200": True,
        "still_404": [],
        "in_window_still_404": ["W47N8@84361700"],
        "w45n7_empty_no_creep": [],
        "w47n7_empty_no_creep": [[84361854, 84361987]],
        "distinct": just_pub,
        "skipped": False,
        "raw": just_pub_payload,
    },
    "confirm": {
        "at": "2026-11-20 00:02:28 Asia/Hong_Kong",
        "game_time": 84362172,
        "inserted": 0,
        "script_reported_inserted": 0,
        "ssl_abort_first": None,
        "targets": 1,
        "recovered": [],
        "still_404": ["W47N8@84361700"],
        "skipped": False,
        "neighbors_at": None,
        "neighbors_game_time": None,
        "neighbors": {"W47N8@84361600": 200, "W47N8@84361700": 404, "W47N8@84361800": 200},
        "note": "confirm still official 404 W47N8@84361700 (inserted=0); neighbors @84361600 and @84361800 200 on first pass",
        "raw": confirm_payload,
    },
    "retry2": {
        "at": "2026-11-20 00:05:55 Asia/Hong_Kong",
        "game_time": 84362222,
        "inserted": 0,
        "script_reported_inserted": 0,
        "skipped": False,
        "recovered": [],
        "still_404": ["W47N8@84361700"],
        "note": "retry2 still official 404 W47N8@84361700; hole 84361701..84361800 db 45/100 live-only 84361756..84361800; first seen as just-published 404 at 23:40:24/23:41:43 last half-hour, not yet told by a 1h patrol",
    },
    "listener": {
        "single_slot": True,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 1023301,
        "pid_at_precheck": 1023301,
        "loop_pid": 4035476,
        "restart_at": "23:55:11",
        "listener_started": "23:55:21",
        "earlier_restart_this_hour": "23:24:49",
        "wrapup_ws_timeout": None,
        "wrapup_autorestart": None,
        "wrapup_listener_started": None,
        "this_run_restarted": False,
        "waited_for_reconnect": False,
        "live_objects_empty_after_reconnect": False,
        "live_gameTime_none_after_reconnect": False,
        "pre_cpu_path_after_wait": (
            f"creep_cpu through 84362120 / path_arrivals through 84362111 at pre-check 23:59:58; "
            f"live.json gameTime=84362135 and objects_n=261 at pre-check (roomSlot W46N8) after the 23:55:11 auto-reconnect; "
            f"by wrapup roomSlot {live.get('roomSlot')} objects_n={len(live.get('objects') or [])}, "
            f"live.json gameTime={live.get('gameTime')} stats.t={stats.get('t')}, "
            f"creep_cpu through {cpu_tip} / path_arrivals through {path_tip}"
        ),
    },
    "box_freeze": {
        "from": "2026-11-19 23:47:48",
        "to": "2026-11-19 23:55:08",
        "sec": 439,
        "restart_at": "23:55:11",
        "room_stats_gap": "84361951..84362069",
        "official_filled": "official-filled 119/119 in W46N8/W47N8/W45N8/W45N7 and 82/119 in W47N7 (W47N7 miss 84361951..84361987 is official empty-no-creep, part of 84361854..84361987); 84361900 and 84362000 both official 200 this pass",
        "counts": freeze2347,
        "earlier_restart_gap": "23:24:49 after 23:20:04-23:24:46; 23:02:24 after 22:55:09-23:02:20; 22:25:48 after 22:17:13-22:25:45",
        "earlier_freeze": {
            "from": "2026-11-19 23:20:04",
            "to": "2026-11-19 23:24:46",
            "sec": 276,
            "restart_at": "23:24:49",
            "room_stats_gap": "84361541..84361619",
            "official_filled": "remains official-filled 79/79 in all 5",
            "counts": freeze2320,
        },
        "earlier_freeze_2255": {
            "from": "2026-11-19 22:55:09",
            "to": "2026-11-19 23:02:20",
            "sec": 431,
            "restart_at": "23:02:24",
            "room_stats_gap": "84361171..84361289",
            "official_filled": "aged out of this window start 84361401 (already official-filled 119/119 in all 5)",
            "counts": freeze2255,
        },
        "new_freeze_this_run": True,
        "already_recorded_by_patrol": False,
        "missed_halfhours": None,
    },
    "new_official_404_not_yet_told": [
        {
            "room": "W47N8",
            "base": 84361700,
            "hole": [84361701, 84361800],
            "db_distinct": hole_w47n8_61700["distinct"],
            "db_note": "live-only 84361756..84361800; still in-window; still 404 after first pass, confirm 00:02:29 gt=84362172 and retry2 00:05:56 gt=84362222; first seen as just-published 404 at 23:40:24 gt=84361843 and retry 23:41:43 gt=84361864 last half-hour; not yet told by a 1h patrol",
            "in_window": True,
        },
    ],
    "already_told_still_unfilled": [
        {
            "room": "W46N8",
            "base": 84360600,
            "hole": [84360601, 84360700],
            "db_distinct": hole_w46n8_60600["distinct"],
            "db_note": "live-only 84360601..84360626; aged out of this window start 84361401, not retried, still unfilled; already told by the 22:30 patrol",
            "in_window": False,
        },
        {
            "room": "W45N7",
            "base": 84360200,
            "hole": [84360201, 84360300],
            "db_distinct": aged_w45n7_60200["distinct"],
            "db_note": "db 0/100; aged out, not retried, still unfilled; already told by the 22:30 patrol",
            "in_window": False,
        },
        {
            "room": "W47N8",
            "base": 84359900,
            "hole": [84359901, 84360000],
            "db_distinct": aged_w47n8_59900["distinct"],
            "db_note": "live-only 84359901..84359906; aged out, not retried, still unfilled; already told by the 22:30 patrol",
            "in_window": False,
        },
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
    f"{finished_hkt_sec} verify 00:00 half-hour official-history backfill",
    f"window ticks {TMIN}..{TMAX} published_bases {PUB_BASES} game.time_first={GT_FIRST}",
    f"inserted_first={INSERTED_FIRST} confirm={INSERTED_CONFIRM} retry2={INSERTED_RETRY2} just_published={INSERTED_JUST} total={INSERTED_TOTAL}",
    f"coverage {recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}",
    f"tick_s_first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} in_use={TICK_S_IN_USE:.5f} later_mean_robust={TICK_S_LATER:.5f} corrective={tick_s.get('corrective_applied')} nfix={NFIX_CORR} later_mean_applied_then_reverted=False",
    f"{inwin_txt}",
    f"{leftover_txt}",
    freeze_para,
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 23:55:11 (listener.py pid 1023301 started 23:55:21) after the new box freeze 23:47:48-23:55:08 (439s, room_stats gap 84361951..84362069). Earlier: 23:24:49 after 23:20:04-23:24:46; 23:02:24 after 22:55:09-23:02:20. This run found the listener already fresh; by pre-check 23:59:56 live.json was fresh (gameTime=84362135, stats.t=84362130, roomSlot W46N8, objects_n=261) and CPU/path buffers were flowing (creep_cpu through 84362120 / path_arrivals through 84362111); single_slot held.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_note = DIR / "backfill_retry2.txt"
shutil.copyfile(retry2_note, ROOT / "state" / "_halfhour_backfill_retry2_0000.txt")
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
