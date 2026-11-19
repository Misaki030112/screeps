#!/usr/bin/env python3
"""Write local status records for the 21:30 half-hour official-history backfill."""
from __future__ import annotations
import json, shutil, time as _time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

HK = ZoneInfo("Asia/Hong_Kong")
ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-19_2130"
assert "_halfhour_2026-11-19_2130" in str(DIR), DIR
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84359201, 84359900
PUB_BASES = "84359200..84359800"
GT_FIRST = 84359916
TICK_S_FIRST = 4.13709
TICK_S_PRINTED = "4.137"
TICK_S_IN_USE = 4.13709  # first-pass; later-mean-robust 4.11423 already inside 45s gate, no corrective
TICK_S_LATER = 4.11423
TS_REALIGNED_FIRST = 39
NFIX_CORR = 0
GT_CORR = None  # no corrective; tick_s_check at game.time=84359944, over45 later=0 and first=0
RECON_ROWS = 25127  # first-pass reconstructed (missing W47N8@84359500 and W47N7@84359800); confirm later added W47N7@84359800 308 unique rows
ALREADY = 19725
INSERTED_FIRST = 5402
INSERTED_CONFIRM = 308  # confirm 21:31:06 gt=84359947 recovered W47N7@84359800 (script reported inserted=400; db_rows after insert=308 unique / 100 distinct ticks). W47N8@84359500 still 404.
INSERTED_RETRY2 = 0  # retry2 21:33:05 gt=84359976 W47N7@84359800 still 200 (script reported +92; db_rows stayed 308). W47N8@84359500 still official 404.
INSERTED_JUST = 0  # 84359900 not attempted (first-pass game.time=84359916 still in-progress)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/2865new W47N8:600t/1333new W45N8:700t/775new W45N7:700t/117new W47N7:600t/312new first-pass; after confirm W47N7:700t/620new"
FIRST_PASS_LINE = (
    "first pass 33 of 35 official GETs 200, missing_chunks=2 (W47N8@84359500, W47N7@84359800); "
    "21:00 half-hour already wrote through 84359400 / reconstructed through 84359500 (just-published 84359500 was not attempted then at gt=84359568, typically publishable around game.time>=84359640); "
    "the 21:25 1h patrol already wrote previously unpublished 84359500 except W47N8 and 84359600 through 84359700 at gt=84359765 (inserted=5057, tick_s=4.118) and is included in this overlap; "
    "(this pass already_in_db=19725 / inserted=5402; overlap 84359201..84359700 already present from the 21:00 half-hour plus the 21:25 patrol plus live rotation after reconnect; "
    "this pass newly wrote previously unpublished 84359700 for all 5 rooms and 84359800 for W46N8/W47N8/W45N8/W45N7 (W47N7 404 at first pass, recovered at confirm), completing official coverage of the 21:12:19-21:17:18 freeze STATS gap including previously unpublished 84359701..84359750 50/50 in all 5 rooms (full patrol-recorded gap 84359660..84359750 91/91 in all 5); "
    "the previously unpublished tail 84359501..84359549 of the prior 20:42:14-21:03:05 freeze STATS gap is now published and official-filled 49/49 in W46N8/W45N8/W45N7/W47N7; W47N8 0/49 remains inside official 404 W47N8@84359500 hole 84359501..84359600; "
    "prior 20:12:27-20:23:40 freeze STATS gap 84358791..84358969, 20:09:23 reconnect STATS gap 84358741..84358759, 19:45:09-19:59:19 freeze STATS gap 84358381..84358609 and earlier gaps have now aged out of this window start 84359201); "
    "leftover official 404 W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out of this 40-min window and were not retried; "
    "in-window official 404 W47N8@84359500 still 404 after confirm 21:31:04 game.time=84359947 and retry2 21:33:04 game.time=84359976 (neighbors @84359400 and @84359600 200 at 21:31:23 gt=84359952, hole 84359501..84359600 db 0/100; already told by the 21:25 1h patrol); "
    "in-window official 404 W47N7@84359800 recovered 200 at confirm 21:31:06 game.time=84359947 (first-pass gt=84359916 was still short of the typical publish threshold ~84359940; db 308 rows / 100 distinct ticks); "
    "just-published 84359900 not attempted (first-pass game.time=84359916 still inside the in-progress chunk)"
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
    # unpublished tail of the still in-progress 84359900 chunk, plus remaining 404 / freeze fills
    tail = {}
    for room in ROOMS:
        d, n, mn, mx = c.execute(
            "SELECT count(DISTINCT tick), count(*), min(tick), max(tick) "
            "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, 84359901, 84359950),
        ).fetchone()
        tail[room] = {"distinct": d or 0, "rows": n or 0, "min": mn, "max": mx, "missing": 50 - (d or 0)}
    freeze2112 = {}
    for room in ROOMS:
        d, n, mn, mx = c.execute(
            "SELECT count(DISTINCT tick), count(*), min(tick), max(tick) "
            "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, 84359660, 84359750),
        ).fetchone()
        freeze2112[room] = {"distinct": d or 0, "rows": n or 0, "min": mn, "max": mx, "missing": 91 - (d or 0)}
    tail2042 = {}
    for room in ROOMS:
        d, n, mn, mx = c.execute(
            "SELECT count(DISTINCT tick), count(*), min(tick), max(tick) "
            "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, 84359501, 84359549),
        ).fetchone()
        tail2042[room] = {"distinct": d or 0, "rows": n or 0, "min": mn, "max": mx, "missing": 49 - (d or 0)}
db_after_lines = "\n".join(db_lines)

def empty_ranges(room):
    return (coverage.get(room) or {}).get("official_empty_no_creep_ranges") or []

inwin_txt = (
    "in-window official 404 after first pass: 33 of 35 official GETs 200, missing_chunks=2; "
    "W47N7@84359800 recovered 200 at confirm 21:31:06 game.time=84359947 (retry2 21:33:05 still 200; db 308 rows / 100 distinct); "
    "W47N8@84359500 still official 404 after confirm 21:31:04 game.time=84359947 and retry2 21:33:04 game.time=84359976 "
    "(neighbors @84359400 and @84359600 200 at 21:31:23 gt=84359952, hole 84359501..84359600 db 0/100; already told by the 21:25 1h patrol); "
    "final official_404_in_window=1 (W47N8@84359500)"
)
leftover_txt = (
    "in-window official 404 remaining: W47N8@84359500 (hole 84359501..84359600 db 0/100, including the 20:42:14-21:03:05 freeze unpublished tail 84359501..84359549 in W47N8). "
    "Aged leftover official 404 W45N7@84358500 (hole 84358501..84358600) and W47N8@84358700 (hole 84358701..84358800) were not retried this pass "
    "(already outside this 40-min window, along with W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800, and older). "
    "W45N7 official empty-no-creep 84359756..84359900 (145) after remote workers fled the W45N7 Invader Core threat (since 84359712); last our-creep tick 84359755."
)
confirm_summary = (
    "confirm 21:31:04 game.time=84359947 recovered W47N7@84359800 (script inserted=400, db 308 unique rows / 100 distinct) and still_404 W47N8@84359500; "
    "retry2 21:33:03 game.time=84359976 W47N7@84359800 still 200 (script +92, db stayed 308) and W47N8@84359500 still official 404; "
    "just-published 84359900 not attempted (first-pass game.time=84359916 still inside the in-progress chunk; typically publishable around game.time>=84360040; next half-hour overlap will catch it); "
    "previously unpublished 84359700 (in-progress at the 21:25 1h patrol / not fully published then at gt=84359765) was written for all 5 rooms this pass, and 84359800 for four rooms at first pass plus W47N7 at confirm"
)
vs_later_before = tick_s.get("still_over_45s_vs_later_before")
vs_first_over45 = vs_first.get("over45")
vs_later_over15_before = tick_s.get("still_over_15s_vs_later_before")
vs_first_over15 = vs_first.get("over15")
span_vs = (vs_cand.get("span_mean") or {})
prev_vs = (vs_cand.get("prev_later") or {})
later_vs = (vs_cand.get("later_robust") or vs_cand.get("later_raw") or {})
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} was already inside the 45s gate versus first-pass-realigned rows "
    f"(delta first-robust 0.01834 s/tick, ~13.1s at tmin; "
    f"over45 later={vs_later_before} vs first={vs_first_over45}, over15 later={vs_later_over15_before} vs first={vs_first_over15}; "
    f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')}; "
    f"lowest_over45 among sane was {tick_s.get('lowest_over45_sane')} (later_raw/later_robust mean_off closer to the live anchor than first, over15 {later_vs.get('over15')} vs first {vs_first_over15}); "
    f"no corrective later-mean-robust realign (later already inside the 45s gate); "
    f"first-pass realign moved {TS_REALIGNED_FIRST} rows; "
    f"still_over_45s_vs_later={tick_s.get('still_over_45s_vs_later')}; skipped_cross_chunk={tick_s.get('skipped_cross_chunk')}; "
    f"in-use first-pass {TICK_S_IN_USE:.5f}; "
    f"confirm recovered W47N7@84359800; retry2 still official 404 W47N8@84359500; just-published 84359900 not attempted; previously unpublished 84359700 and 84359800 were written this pass"
)

w46_tail = tail["W46N8"]
f2112 = freeze2112["W46N8"]
freeze_para = (
    f"Box freeze 21:12:19-21:17:18 Asia/Hong_Kong (298s) caused run_listener.sh auto-restart 21:17:21 (listener.py pid 961358 started 21:17:31; not this run). "
    f"room_stats gap 84359661..84359749 (89) / patrol-recorded 84359660..84359750 (91): now official-filled 91/91 in all 5 rooms this pass "
    f"(patrol had already official-filled published 84359672..84359700 29/29; this pass wrote previously unpublished 84359701..84359750 50/50 in all 5). "
    f"Prior 20:42:14-21:03:05 freeze STATS gap 84359231..84359549 (319): official-covered 84359231..84359500 remains official-filled 270/270 in all 5 rooms; "
    f"previously unpublished tail 84359501..84359549 is now published and official-filled 49/49 in W46N8/W45N8/W45N7/W47N7; W47N8 0/49 still missing inside official 404 W47N8@84359500 hole 84359501..84359600 (db 0/100 after confirm and retry2). "
    f"Prior 20:12:27-20:23:40 freeze STATS gap 84358791..84358969, 20:09:23 reconnect STATS gap 84358741..84358759 and 19:45:09-19:59:19 freeze STATS gap 84358381..84358609 have aged out of this window start 84359201 and were official-filled from earlier passes as previously recorded, except the still-open official 404 holes W45N7@84358500 and W47N8@84358700 which remain outside this window. "
    f"Aged official 404 W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) remain outside this window. "
    f"W45N7 official empty-no-creep 84359756..84359900 (145) after they fled the Invader Core (threat since 84359712; last our-creep tick 84359755). "
    f"live.json / stats.t were fresh at pre-check (age ~1s, tip stats.t=84359910, roomSlot W45N8 objects_n=0 just after rotation) after the 21:17:21 auto-reconnect; CPU/path buffers were already flowing; "
    f"previously unpublished 84359700 (all 5) and 84359800 (four rooms + W47N7 at confirm) were written this pass; just-published 84359900 was not yet publishable (game.time=84359916 at first pass); "
    f"unpublished live tail of the in-progress 84359900 chunk starts at 84359901 "
    f"(W46N8 live already has {w46_tail['distinct']} ticks {w46_tail['min']}..{w46_tail['max'] if w46_tail['max'] else ''} in 84359901..84359950 after rotation; other rooms depend on later rotation / live ingest); "
    f"single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84359890 / path_arrivals through 84359890 at pre-check; through {cpu_tip} / {path_tip} at wrapup); this run did not restart the listener."
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
        "corrective_applied": bool(tick_s.get("corrective_applied")),
        "later_mean_w46": tick_s.get("later_mean_w46"),
        "still_over_45s_vs_later": tick_s.get("still_over_45s_vs_later"),
        "reason": tick_s.get("reason"),
        "prev_later_over45_before_corrective": (prev_vs or {}).get("over45"),
        "prev_later_mean": tick_s.get("prev_later_mean"),
        "note": tick_s_corr_txt,
    },
    "just_published": {
        "base": 84359900,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": None,
        "recovered_game_time": None,
        "inserted": 0,
        "note": "not attempted; first-pass game.time=84359916 was still inside the in-progress chunk (typically publishable around game.time>=84360040; next half-hour overlap will catch it)",
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
        "in_window_still_404": [],
        "w45n7_empty_no_creep": empty_ranges("W45N7"),
        "w47n7_empty_no_creep": empty_ranges("W47N7"),
        "distinct": None,
        "skipped": True,
    },
    "confirm": {
        "at": "2026-11-19 21:31:04 Asia/Hong_Kong",
        "game_time": 84359947,
        "inserted": 308,
        "script_reported_inserted": 400,
        "ssl_abort_first": None,
        "targets": 2,
        "recovered": ["W47N7@84359800"],
        "still_404": ["W47N8@84359500"],
        "skipped": False,
        "neighbors_at": "2026-11-19 21:31:23 Asia/Hong_Kong",
        "neighbors_game_time": 84359952,
        "neighbors": {"W47N8@84359400": 200, "W47N8@84359500": 404, "W47N8@84359600": 200, "W47N7@84359700": 200, "W47N7@84359800": 200},
        "note": "confirm recovered W47N7@84359800 200 (script inserted=400, db 308 unique rows / 100 distinct ticks); W47N8@84359500 still 404; neighbors of the remaining hole 200",
    },
    "retry2": {
        "at": "2026-11-19 21:33:03 Asia/Hong_Kong",
        "game_time": 84359976,
        "inserted": 0,
        "script_reported_inserted": 92,
        "skipped": False,
        "recovered": ["W47N7@84359800"],
        "still_404": ["W47N8@84359500"],
        "note": "retry2 W47N7@84359800 still 200 (script +92, db_rows stayed 308); W47N8@84359500 still official 404, hole 84359501..84359600 db 0/100",
    },
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 961358,
        "pid_at_precheck": 961358,
        "loop_pid": 4035476,
        "restart_at": "21:17:21",
        "listener_started": "21:17:31",
        "earlier_restart_this_hour": "21:03:08",
        "wrapup_ws_timeout": None,
        "wrapup_autorestart": None,
        "wrapup_listener_started": None,
        "this_run_restarted": False,
        "waited_for_reconnect": True,
        "live_objects_empty_after_reconnect": False,
        "pre_cpu_path_after_wait": (
            f"creep_cpu through 84359890 / path_arrivals through 84359890 at pre-check 21:28:37; "
            f"live.json objects_n={len(live.get('objects') or {})} because roomSlot was {live.get('roomSlot')} (home-map); "
            f"by wrapup roomSlot {live.get('roomSlot')} objects_n={len(live.get('objects') or {})}, stats.t={stats.get('t')}, "
            f"creep_cpu through {cpu_tip} / path_arrivals through {path_tip}"
        ),
    },
    "box_freeze": {
        "from": "2026-11-19 21:12:19",
        "to": "2026-11-19 21:17:18",
        "sec": 298,
        "restart_at": "21:17:21",
        "room_stats_gap": "84359660..84359750",
        "official_filled": (
            "official-filled 91/91 of patrol-recorded gap 84359660..84359750 in all 5 rooms "
            f"(W46N8 {f2112['distinct']}/91); previously unpublished 84359701..84359750 50/50 in all 5 this pass"
        ),
        "earlier_restart_gap": "21:03:08 after 20:42:14-21:03:05",
        "earlier_freeze": {
            "from": "2026-11-19 20:42:14",
            "to": "2026-11-19 21:03:05",
            "sec": 1244,
            "restart_at": "21:03:08",
            "room_stats_gap": "84359231..84359549",
            "official_filled": (
                "official-covered 84359231..84359500 still 270/270 in all 5 rooms; "
                "previously unpublished tail 84359501..84359549 now published and official-filled 49/49 in W46N8/W45N8/W45N7/W47N7; "
                "W47N8 0/49 still missing inside official 404 W47N8@84359500 hole 84359501..84359600 (db 0/100)"
            ),
        },
        "new_freeze_this_run": False,
        "already_recorded_by_patrol": True,
        "missed_halfhours": None,
    },
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
    f"{finished_hkt_sec} verify 21:30 half-hour official-history backfill",
    f"window ticks {TMIN}..{TMAX} published_bases {PUB_BASES} game.time_first={GT_FIRST}",
    f"inserted_first={INSERTED_FIRST} confirm={INSERTED_CONFIRM} retry2={INSERTED_RETRY2} just_published={INSERTED_JUST} total={INSERTED_TOTAL}",
    f"coverage {recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}",
    f"tick_s_first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} in_use={TICK_S_IN_USE:.5f} later_mean_robust={TICK_S_LATER:.5f} corrective={tick_s.get('corrective_applied')} nfix={NFIX_CORR}",
    f"{inwin_txt}",
    f"{leftover_txt}",
    freeze_para,
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 21:17:21 (listener.py pid 961358 started 21:17:31) after the recorded box freeze 21:12:19-21:17:18 (298s, room_stats gap 84359660..84359750). Earlier this hour: 21:03:08 after 20:42:14-21:03:05. The 21:17:21 reconnect had already recovered stats/CPU/path by pre-check 21:28:37 (live.json fresh, stats.t=84359910 advancing, roomSlot W45N8; single_slot held).",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_note = DIR / "backfill_retry2.txt"
if not retry2_note.exists():
    retry2_note.write_text("retry2 21:33:03 gt=84359976: W47N8@84359500 still official 404; W47N7@84359800 still 200\n")
shutil.copyfile(retry2_note, ROOT / "state" / "_halfhour_backfill_retry2_2130.txt")
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
