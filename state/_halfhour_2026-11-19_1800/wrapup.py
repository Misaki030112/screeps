#!/usr/bin/env python3
"""Write local status records for the 18:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-19_1800"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84356301, 84357000
PUB_BASES = "84356300..84356900"
GT_FIRST = 84357031
TICK_S_FIRST = 4.95466
TICK_S_PRINTED = "4.955"
TICK_S_IN_USE = 4.75297
TICK_S_LATER = 4.75297
TS_REALIGNED_FIRST = 13391
NFIX_CORR = 19180
GT_CORR = 84357050  # corrective later-mean-robust realign at game.time=84357050; still_over_45s_vs_later=0
RECON_ROWS = 25035
ALREADY = 12340
INSERTED_FIRST = 12695
INSERTED_CONFIRM = 0  # skipped: first pass 35/35 official GETs 200, missing_chunks=0
INSERTED_RETRY2 = 0
INSERTED_JUST = 0  # 84357000 not attempted (first-pass game.time=84357031 still in-progress)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/2923new W47N8:700t/5551new W45N8:700t/1983new W45N7:700t/1475new W47N7:700t/763new"
FIRST_PASS_LINE = (
    "first pass 35 of 35 official GETs 200, missing_chunks=0; "
    "17:30 half-hour already wrote through 84356600 (just-published 84356600 was not attempted then and is included in this overlap, 200 in all 5 rooms); "
    "(this pass already_in_db=12340 / inserted=12695; overlap 84356300..84356500 already present from the 17:30 half-hour; this pass newly wrote previously unpublished 84356600 for all 5 rooms plus 84356700..84356900, filling the official-covered part of the new 17:41:25-17:58:01 freeze STATS gap 84356781..84356999 219/219 in W46N8, W47N8, W45N8 and W45N7, and 115/219 in W47N7 with 104 official empty-no-creep 84356794..84356897 — official history had no our creeps, not a 404; the live tail 84357001.. sits in the still in-progress 84357000 chunk); "
    "leftover official 404 W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out of this 40-min window and were not retried; "
    "no in-window official 404, so confirm and retry2 were skipped; "
    "just-published 84357000 not attempted (first-pass game.time=84357031 still inside the in-progress chunk)"
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

db_lines = []
with db.connect() as c:
    for room in sorted(ROOMS):
        mn, mx, n, d = c.execute(
            "SELECT min(tick), max(tick), count(*), count(DISTINCT tick) "
            "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, TMIN, TMAX),
        ).fetchone()
        db_lines.append(f"  {room} ticks={mn}..{mx} rows={n} distinct={d}")
db_after_lines = "\n".join(db_lines)

def empty_ranges(room):
    return (coverage.get(room) or {}).get("official_empty_no_creep_ranges") or []

w45n8_empty = empty_ranges("W45N8")
w45n7_empty = empty_ranges("W45N7")
w47n7_empty = empty_ranges("W47N7")

inwin_txt = (
    "in-window official 404 after first pass: none; "
    "first pass 35 of 35 official GETs 200, missing_chunks=0; "
    "confirm skipped; retry2 skipped; final official_404_in_window=0"
)
leftover_txt = (
    "no in-window official 404 still open; "
    "W47N7 official empty-no-creep 104 ticks (84356794..84356897) — official history had no our creeps, not a 404 hole; this stretch sits inside the new 17:41:25-17:58:01 freeze STATS gap 84356781..84356999; the previous W45N7 official empty-no-creep 22 ticks (84355930..84355951) have now aged out of this window start 84356301; "
    "aged leftover official 404 W46N8@84354300 (hole 84354301..84354351; live W46N8 already covers 84354352..84354400) and W47N7@84354300 (hole 84354301..84354400, 0/100 still missing) were not retried this pass "
    "(already outside this 40-min window, along with W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800, and older W45N8@84346100, W45N7@84345800, W45N8@84344700, W47N8@84343800, W45N8@84343100, W47N8@84343400, W47N8@84343000, W45N7@84342300, W47N7@84342500, W45N8@84341100)."
)
confirm_summary = (
    "confirm skipped (first pass 35/35 official GETs 200, missing_chunks=0, no in-window official 404); "
    "retry2 skipped; "
    "just-published 84357000 not attempted (first-pass game.time=84357031 still inside the in-progress chunk; typically publishable around game.time>=84357140; next half-hour overlap will catch it); "
    "previously unpublished 84356600 (in-progress at the 17:30 half-hour) was written for all 5 rooms this pass, along with 84356700..84356900"
)
vs_later_before = (tick_s.get("still_over_45s_vs_later_before"))
vs_first_over45 = vs_first.get("over45")
vs_later_over15_before = tick_s.get("still_over_15s_vs_later_before")
vs_first_over15 = vs_first.get("over15")
span_vs = (vs_cand.get("span_mean") or {})
prev_vs = (vs_cand.get("prev_later") or {})
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band but is a local high versus later intervals; "
    f"later-mean-robust {TICK_S_LATER:.5f} was over the 45s gate versus first-pass-realigned rows "
    f"(delta first-robust 0.20169 s/tick, ~147.2s at tmin; "
    f"over45 later={vs_later_before} vs first={vs_first_over45}, over15 later={vs_later_over15_before} vs first={vs_first_over15}; "
    f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')}; "
    f"lowest_over45 among sane was {tick_s.get('lowest_over45_sane')} (first already closer to the live anchor than later-mean before corrective); "
    f"applied corrective later-mean-robust realign of {NFIX_CORR} rows at game.time={GT_CORR} anyway, because later-mean-robust itself was over the 45s gate versus first-pass-realigned rows; "
    f"first-pass realign moved {TS_REALIGNED_FIRST} rows; "
    f"still_over_45s_vs_later={tick_s.get('still_over_45s_vs_later')}; skipped_cross_chunk={tick_s.get('skipped_cross_chunk')}; "
    f"in-use later-mean-robust {TICK_S_IN_USE:.5f}; "
    f"confirm skipped; retry2 skipped; just-published 84357000 not attempted; previously unpublished 84356600 was written this pass"
)

freeze_para = (
    "New recorded box freeze this run: 17:41:25-17:58:01 (986s; box_pauses.jsonl). "
    "Listener auto-restart was 17:58:04 (current listener.py pid 899377 started 17:58:13; run_listener.sh pid 4035476). "
    "Earlier listener auto-restart after the previous recorded freeze was 17:23:45 (listener.py then pid 888991 started 17:23:55). "
    "Also earlier freezes 17:15:27-17:23:42 (488s), 16:43:38-17:02:18 (1119s), 15:37:56-15:57:12 (1155s), 15:21:03-15:24:59 (230s), 14:46:22-15:05:49 (1161s), 14:08:48-14:26:36 (1067s), 13:41:05-13:56:16 (905s), 13:17:39-13:22:41 (296s), 12:40:05-13:04:53 (1487s), 12:15:21-12:22:01 (400s), 11:36:36-11:58:55 (1339s), 11:11:06-11:18:54 (467s), 10:40:36-11:03:20 (1359s), 10:09:26-10:23:04 (818s), 09:45:54-09:57:01 (667s), 05:33:25-09:22:55 (13764s), 05:17:00-05:26:03 (542s), 04:45:45-04:58:24 (749s), 03:45:22-04:05:50 (1228s), 03:10:01-03:17:13 (431s), 02:45:55-02:57:12 (671s). "
    "This run did not restart the listener; after the 17:58:04 auto-reconnect this run waited for stats to resume and for the listener to pull segment-90 CPU/path buffers itself "
    "(pre-check 18:00:10, live.json age ~4.1s, stats.t=84357020 advancing, roomSlot W45N8 objects_n=0 / gameTime None after reconnect — live.json objects/gameTime stayed empty, but room ingest was already flowing: W45N8 live near tip >=84357000 already had 5 distinct ticks 84357022..84357026; "
    "creep_cpu through 84357010 / path_arrivals through 84356991; by wrapup live.json age fresh, stats.t advancing, roomSlot rotating through W45N7, objects_n still 0 / gameTime still None, creep_cpu and path_arrivals still flowing). "
    "17:30 half-hour already official-filled 84355901..84356600 (inserted_window=3546, coverage 3478/3500 with 22 W45N7 official empty-no-creep, missing_chunks=0; just-published 84356600 was not attempted then and is included in this overlap, 200 in all 5 rooms this pass). "
    "This half-hour first pass inserted 12695 new rows (already_in_db=12340) and wrote previously unpublished 84356600 for all 5 rooms plus 84356700..84356900; confirm/retry2 skipped. Leftover official 404 W46N8@84354300 and W47N7@84354300 remain aged out of this window and were not retried. "
    "New room_stats gap 84356781..84356999 (219, from the 17:41:25-17:58:01 box freeze) sits inside this 40-min window and is official-filled 219/219 in W46N8, W47N8, W45N8 and W45N7, and 115/219 in W47N7 (104 official empty-no-creep 84356794..84356897 — official history had no our creeps, not a 404). The live tail 84357001.. sits in the still unpublished 84357000 chunk until that chunk publishes. "
    "room_stats gap 84356451..84356569 (119, from the 17:15:27-17:23:42 freeze) still sits inside this window and remains official-filled 119/119 in all 5 rooms. "
    "room_stats gap 84356051..84356309 (259, from the 16:43:38-17:02:18 freeze) still has its 9-tick tail 84356301..84356309 inside this window start and remains official-filled 259/259 in all 5 rooms (9/9 in the tail). "
    "older room_stats gaps 84355651..84355759 (109) and 84355571..84355589 (19) have now aged out of this window (window starts at 84356301) and remain official-filled from earlier passes (W45N7 empty-no-creep covers most of 84355651..84355759). "
    "older room_stats gaps 84355231..84355489, 84355021..84355089, 84354931..84354959, 84354591..84354849, 84354121..84354349 and earlier remain aged out of this window. "
    "The tail of 84354121..84354349 remains official-filled 49/49 in W47N8, W45N8 and W45N7 but still missing 49/49 in W46N8 and all 100 ticks 84354301..84354400 in W47N7 because those rooms 404'd on official 84354300 (aged out, not retried this pass). "
    "Aged official 404 W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) remain outside this window. "
    "live.json / stats.t were fresh at pre-check (age ~4.1s, tip stats.t=84357020, gameTime None, roomSlot W45N8 objects_n=0) after the 17:58:04 auto-reconnect; W45N8 live creep_ticks and CPU/path buffers were flowing; previously unpublished 84356600 was written for all 5 rooms this pass along with 84356700..84356900; just-published 84357000 was not yet publishable (game.time=84357031 at first pass); single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84357010 / path_arrivals through 84356991 at pre-check); this run did not restart the listener."
)

ok_line = (
    f"ok_quiet=True coverage={recovered}/{expected} inserted_window={INSERTED_WINDOW} "
    f"inserted_total={INSERTED_TOTAL} tick_s_in_use={TICK_S_IN_USE:.5f} "
    "listener single_slot=True; no second listener; no war_cmd/pulse restart."
)
single = (not yield_present)
unique_n = unique_after.get("unique_creep_tick_rows") if isinstance(unique_after, dict) else unique_after
now_lines = [
    f"{finished_hkt} half-hour backfill OK (quiet)",
    f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
    f"  ({FIRST_PASS_LINE}; see history_backfill.txt)",
    f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST:.5f}; {tick_s_corr_txt}, in-use {TICK_S_IN_USE:.5f})",
    f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks={MISSING_CHUNKS}",
    f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
    f"per_room {PER_ROOM_LINE}",
    f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 +{INSERTED_RETRY2}, just_published +{INSERTED_JUST}, window {INSERTED_WINDOW}, run total {INSERTED_TOTAL})",
    f"ts_realigned_first={TS_REALIGNED_FIRST}; ts_realigned_corrective={NFIX_CORR} ({tick_s_corr_txt}; in-use {TICK_S_IN_USE:.5f})",
    "db_after",
    db_after_lines,
    f"coverage official_recovered={recovered}/{expected} unique_after={unique_n} empty_no_creep={empty_no_creep} official_404_in_window={official_404_missing}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    freeze_para,
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}",
    confirm_summary,
    ok_line,
]
now_text = "\n".join(now_lines) + "\n"

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
        "corrective_applied": tick_s.get("corrective_applied"),
        "later_mean_w46": tick_s.get("later_mean_w46"),
        "still_over_45s_vs_later": tick_s.get("still_over_45s_vs_later"),
        "reason": tick_s.get("reason"),
        "prev_later_over45_before_corrective": (prev_vs.get("over45")),
        "prev_later_mean": tick_s.get("prev_later_mean"),
        "note": (
            "first-interval 4.95466 printed 4.955 was sane but a local high; first-pass realign moved 13391 rows onto 4.95466; "
            "later-mean-robust 4.75297 was over the 45s gate versus those rows "
            f"(over45 later={vs_later_before} vs first={vs_first_over45}, delta 0.20169 s/tick ~147.2s at tmin); "
            f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')} "
            f"(lowest_over45 among sane was {tick_s.get('lowest_over45_sane')}, already closer to the live anchor before corrective); "
            "applied corrective later-mean-robust realign of 19180 rows at game.time=84357050; in-use later-mean-robust 4.75297; still_over_45s_vs_later=0"
        ),
    },
    "just_published": {
        "base": 84357000,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": None,
        "recovered_game_time": None,
        "inserted": INSERTED_JUST,
        "note": "not attempted; first-pass game.time=84357031 was still inside the in-progress 84357000 chunk (typically publishable around game.time>=84357140). Confirm was skipped (missing_chunks=0). This --minutes 40 pass wrote previously unpublished 84356600 (left in-progress at the 17:30 half-hour) for all 5 rooms plus 84356700..84356900. Next half-hour 10-min overlap will catch 84357000.",
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
        "w45n7_empty_no_creep": [],
        "w47n7_empty_no_creep": [],
        "distinct": None,
        "skipped": True,
    },
    "confirm": {
        "at": None,
        "game_time": None,
        "inserted": 0,
        "ssl_abort_first": None,
        "targets": 0,
        "recovered": [],
        "still_404": [],
        "skipped": True,
        "note": "skipped; first pass 35/35 official GETs 200, missing_chunks=0, no in-window official 404 to recover.",
    },
    "retry2": {
        "at": "2026-11-19 18:02 Asia/Hong_Kong",
        "game_time": None,
        "inserted": 0,
        "skipped": True,
        "still_404": [],
        "note": "skipped; first pass already 35/35 official 200, missing_chunks=0, still_404=[]",
    },
    "in_window_404": {},
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 899377,
        "pid_at_precheck": 899377,
        "loop_pid": 4035476,
        "restart_at": "17:58:04",
        "listener_started": "17:58:13",
        "wrapup_ws_timeout": None,
        "wrapup_autorestart": None,
        "wrapup_listener_started": None,
        "this_run_restarted": False,
        "waited_for_reconnect": True,
        "live_objects_empty_after_reconnect": True,
        "pre_cpu_path_after_wait": "creep_cpu through 84357010 / path_arrivals through 84356991 at pre-check 18:00:10; listener.py pid 899377 started 17:58:13 after run_listener.sh auto-restart 17:58:04 following box freeze 17:41:25-17:58:01 (986s). This run waited after that reconnect until stats.t and CPU/path buffers were flowing (live.json fresh, age ~4.1s, stats.t=84357020, roomSlot W45N8; live.json objects_n=0 / gameTime None after reconnect, but W45N8 live near tip already had 5 distinct ticks 84357022..84357026). This run did not itself restart the listener.",
    },
    "box_freeze": {
        "from": "2026-11-19 17:41:25",
        "to": "2026-11-19 17:58:01",
        "sec": 986,
        "restart_at": "17:58:04",
        "room_stats_gap": "84356781..84356999",
        "official_filled": "84356781..84356999 official-filled 219/219 in W46N8, W47N8, W45N8 and W45N7, and 115/219 in W47N7 (104 official empty-no-creep 84356794..84356897, not a 404). just-published 84357000 not attempted (first-pass game.time=84357031 still in-progress). Prior freeze 17:15:27-17:23:42 gap 84356451..84356569 remains official-filled 119/119 in all 5 rooms. Prior freeze 16:43:38-17:02:18 gap 84356051..84356309 remains official-filled 259/259 in all 5 rooms including the 9-tick tail still inside this window start.",
        "earlier_freeze": {
            "from": "2026-11-19 17:15:27",
            "to": "2026-11-19 17:23:42",
            "sec": 488,
            "restart_at": "17:23:45",
            "room_stats_gap": "84356451..84356569",
            "official_filled": "84356451..84356569 official-filled 119/119 in all 5 rooms (17:30 half-hour filled the gap after 84356500 published). Earlier 16:43:38-17:02:18 gap 84356051..84356309 official-filled 259/259 in all 5 rooms (9-tick tail 84356301..84356309 remains inside this window start, 9/9).",
        },
        "new_freeze_this_run": True,
        "missed_halfhours": None,
    },
    "ok_line": ok_line,
}

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
(DIR / "history_backfill_now.txt").write_text(now_text)
shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")
shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

verify = [
    f"{finished_hkt_sec} half-hour backfill verify",
    f"window {TMIN}..{TMAX} published_bases {PUB_BASES} game.time={GT_FIRST} inserted={INSERTED_TOTAL} coverage={recovered}/{expected}",
    f"missing_chunks={MISSING_CHUNKS} in_window_404=none; final official_404={official_404_missing} empty_no_creep={empty_no_creep}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    "just-published 84357000 not attempted (first-pass game.time=84357031 still inside the in-progress chunk); previously unpublished 84356600 was written for all 5 rooms this pass along with 84356700..84356900; confirm/retry2 skipped; leftover official 404 W46N8@84354300 (hole 84354301..84354351) and W47N7@84354300 (hole 84354301..84354400) had aged out of this window and were not retried.",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 17:58:04 (listener.py pid 899377 started 17:58:13) after box freeze 17:41:25-17:58:01, and had already recovered by pre-check 18:00:10 (live.json fresh, stats.t advancing, gameTime None / objects_n=0 after reconnect, single_slot held; W45N8 live ticks and CPU/path buffers were flowing).",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1800.txt")
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
