#!/usr/bin/env python3
"""Write local status records for the 17:30 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-19_1730"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84355901, 84356600
PUB_BASES = "84355900..84356500"
GT_FIRST = 84356654
TICK_S_FIRST = 4.7249
TICK_S_PRINTED = "4.725"
TICK_S_IN_USE = 4.7249
TICK_S_LATER = 4.78003
TS_REALIGNED_FIRST = 9056
NFIX_CORR = 0
GT_CORR = None  # no corrective; later-mean-robust already inside 45s gate
RECON_ROWS = 24796
ALREADY = 21250
INSERTED_FIRST = 3546
INSERTED_CONFIRM = 0  # skipped: first pass 35/35 official GETs 200, missing_chunks=0
INSERTED_RETRY2 = 0
INSERTED_JUST = 0  # 84356600 not attempted (first-pass game.time=84356654 still in-progress)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/742new W47N8:700t/1383new W45N8:700t/565new W45N7:700t/434new W47N7:700t/422new"
FIRST_PASS_LINE = (
    "first pass 35 of 35 official GETs 200, missing_chunks=0; "
    "17:00 half-hour already wrote through 84356300 (just-published 84356300 was not attempted then); "
    "concurrent 17:23 hourly patrol already wrote 84355801..84356500 including 84356300 and 84356400 at game.time=84356580 (inserted=5713, missing_chunks=0; 84356500 still in-progress then and is included in this overlap, 200 in all 5 rooms); "
    "(this pass already_in_db=21250 / inserted=3546; overlap 84355900..84356400 already present from the 17:00 half-hour plus the 17:23 patrol; this pass newly wrote previously unpublished 84356500 for all 5 rooms, filling the official-covered part of the new 17:15:27-17:23:42 freeze STATS gap 84356451..84356569 119/119 in all 5 rooms, and the previously unpublished 9-tick tail 84356301..84356309 of the prior 16:43:38-17:02:18 freeze gap is now official-filled 9/9 in all 5 rooms as well; the live tail 84356601.. sits in the still in-progress 84356600 chunk: live W46N8 only until that chunk publishes); "
    "leftover official 404 W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out of this 40-min window and were not retried; "
    "no in-window official 404, so confirm and retry2 were skipped; "
    "just-published 84356600 not attempted (first-pass game.time=84356654 still inside the in-progress chunk)"
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
    "W45N7 official empty-no-creep 22 ticks (84355930..84355951) — official history had no our creeps, not a 404 hole; this is the later 22-tick stretch that was already noted last half-hour (the earlier 214 empty ticks from the W45N7 invader window ~16:08-16:26 have now aged out of this window start 84355901); "
    "aged leftover official 404 W46N8@84354300 (hole 84354301..84354351; live W46N8 already covers 84354352..84354400) and W47N7@84354300 (hole 84354301..84354400, 0/100 still missing; 17:23 patrol hist_pull still 404) were not retried this pass "
    "(already outside this 40-min window, along with W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800, and older W45N8@84346100, W45N7@84345800, W45N8@84344700, W47N8@84343800, W45N8@84343100, W47N8@84343400, W47N8@84343000, W45N7@84342300, W47N7@84342500, W45N8@84341100)."
)
confirm_summary = (
    "confirm skipped (first pass 35/35 official GETs 200, missing_chunks=0, no in-window official 404); "
    "retry2 skipped; "
    "just-published 84356600 not attempted (first-pass game.time=84356654 still inside the in-progress chunk; typically publishable around game.time>=84356740; next half-hour overlap will catch it)"
)
vs_later_before = (tick_s.get("still_over_45s_vs_later_before"))
vs_first_over45 = vs_first.get("over45")
vs_later_over15_before = tick_s.get("still_over_15s_vs_later_before")
vs_first_over15 = vs_first.get("over15")
span_vs = (vs_cand.get("span_mean") or {})
prev_vs = (vs_cand.get("prev_later") or {})
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} was already inside the 45s gate versus first-pass-realigned rows "
    f"(delta first-robust -0.05513 s/tick, ~41.5s at tmin; "
    f"over45 later={vs_later_before} vs first={vs_first_over45}, over15 later={vs_later_over15_before} vs first={vs_first_over15}; "
    f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')}; "
    f"lowest_over45 among sane was {tick_s.get('lowest_over45_sane')} (all candidates already over45=0; prev_later mean_off closest to 0); "
    f"no corrective realign; first-pass realign moved {TS_REALIGNED_FIRST} rows; "
    f"still_over_45s_vs_later={tick_s.get('still_over_45s_vs_later')}; skipped_cross_chunk={tick_s.get('skipped_cross_chunk')}; "
    f"in-use first-interval {TICK_S_IN_USE:.5f}; "
    f"confirm skipped; retry2 skipped; just-published 84356600 not attempted"
)

freeze_para = (
    "New recorded box freeze this run: 17:15:27-17:23:42 (488s; box_pauses.jsonl). "
    "Listener auto-restart was 17:23:45 (current listener.py pid 888991 started 17:23:55; run_listener.sh pid 4035476). "
    "Earlier listener auto-restart after the previous recorded freeze was 17:02:21. "
    "Also earlier freezes 16:43:38-17:02:18 (1119s), 15:37:56-15:57:12 (1155s), 15:21:03-15:24:59 (230s), 14:46:22-15:05:49 (1161s), 14:08:48-14:26:36 (1067s), 13:41:05-13:56:16 (905s), 13:17:39-13:22:41 (296s), 12:40:05-13:04:53 (1487s), 12:15:21-12:22:01 (400s), 11:36:36-11:58:55 (1339s), 11:11:06-11:18:54 (467s), 10:40:36-11:03:20 (1359s), 10:09:26-10:23:04 (818s), 09:45:54-09:57:01 (667s), 05:33:25-09:22:55 (13764s), 05:17:00-05:26:03 (542s), 04:45:45-04:58:24 (749s), 03:45:22-04:05:50 (1228s), 03:10:01-03:17:13 (431s), 02:45:55-02:57:12 (671s). "
    "This run did not restart the listener; after the 17:23:45 auto-reconnect this run waited for stats to resume and for the listener to pull segment-90 CPU/path buffers itself "
    "(pre-check 17:30:05, live.json age ~1.8s, gameTime=84356644, stats.t=84356640 advancing, roomSlot W46N8 objects_n=265; "
    "W46N8 live near tip >=84356620 already had 27 distinct ticks 84356620..84356646; "
    "creep_cpu through 84356640 / path_arrivals through 84356637; by wrapup live.json age fresh, stats.t advancing, roomSlot W46N8, objects and gameTime present, creep_cpu and path_arrivals still flowing). "
    "17:00 half-hour already official-filled 84355601..84356300 (inserted_window=16330, coverage 3264/3500 with 236 W45N7 official empty-no-creep, missing_chunks=0; just-published 84356300 was not attempted then). "
    "Concurrent 17:23 hourly patrol already wrote 84355801..84356500 (inserted=5713 at game.time=84356580, missing_chunks=0), including previously unpublished 84356300 and 84356400; 84356500 was still in-progress then and is included in this first pass (200 in all 5 rooms). "
    "This half-hour first pass inserted 3546 new rows (already_in_db=21250) and wrote previously unpublished 84356500 for all 5 rooms; confirm/retry2 skipped. Leftover official 404 W46N8@84354300 and W47N7@84354300 remain aged out of this window and were not retried. "
    "New room_stats gap 84356451..84356569 (119, from the 17:15:27-17:23:42 box freeze) sits inside this 40-min window and is official-filled 119/119 in all 5 rooms (the newly published 84356500 chunk covers 84356501..84356600 100/100 in all 5 rooms; the live tail 84356601.. sits in the still unpublished 84356600 chunk: live W46N8 only until that chunk publishes). "
    "room_stats gap 84356051..84356309 (259, from the 16:43:38-17:02:18 freeze) still sits inside this window and is now official-filled 259/259 in all 5 rooms (17:00 half-hour filled 84356051..84356300 250/250; the 9-tick tail 84356301..84356309 is official-filled 9/9 in all 5 rooms this overlap after 84356300 published). "
    "older room_stats gaps 84355651..84355759 (109), 84355571..84355589 (19) and 84355231..84355489 (259) have now aged out of this window (window starts at 84355901) and remain official-filled from earlier passes (W45N7 empty-no-creep covers most of 84355651..84355759). "
    "older room_stats gaps 84355021..84355089, 84354931..84354959, 84354591..84354849, 84354121..84354349 and earlier remain aged out of this window. "
    "The tail of 84354121..84354349 remains official-filled 49/49 in W47N8, W45N8 and W45N7 but still missing 49/49 in W46N8 and all 100 ticks 84354301..84354400 in W47N7 because those rooms 404'd on official 84354300 (aged out, not retried this pass). "
    "Aged official 404 W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) remain outside this window. "
    "live.json / stats.t were fresh at pre-check (age ~1.8s, tip stats.t=84356640, gameTime=84356644, roomSlot W46N8 objects_n=265) after the 17:23:45 auto-reconnect; W46N8 live creep_ticks and CPU/path buffers were flowing; just-published 84356600 was not yet publishable (game.time=84356654 at first pass); this pass wrote previously unpublished 84356500 for all 5 rooms; single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84356640 / path_arrivals through 84356637 at pre-check); this run did not restart the listener."
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
            "first-interval 4.72490 printed 4.725 was sane; first-pass realign moved 9056 rows onto 4.72490; "
            "later-mean-robust 4.78003 was already inside the 45s gate versus those rows "
            f"(over45 later={vs_later_before} vs first={vs_first_over45}, delta -0.05513 s/tick ~41.5s at tmin); "
            f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')} "
            f"(lowest_over45 among sane was {tick_s.get('lowest_over45_sane')}; all candidates already over45=0); "
            "no corrective realign; in-use first-interval 4.72490; still_over_45s_vs_later=0"
        ),
    },
    "just_published": {
        "base": 84356600,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": None,
        "recovered_game_time": None,
        "inserted": INSERTED_JUST,
        "note": "not attempted; first-pass game.time=84356654 was still inside the in-progress 84356600 chunk (typically publishable around game.time>=84356740). Confirm was skipped (missing_chunks=0). This --minutes 40 pass wrote previously unpublished 84356500 for all 5 rooms. The 17:23 patrol plus this overlap already wrote previously unpublished 84356300 (left in-progress at the 17:00 half-hour). Next half-hour 10-min overlap will catch 84356600.",
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
        "at": "2026-11-19 17:32 Asia/Hong_Kong",
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
        "pid": 888991,
        "pid_at_precheck": 888991,
        "loop_pid": 4035476,
        "restart_at": "17:23:45",
        "listener_started": "17:23:55",
        "wrapup_ws_timeout": None,
        "wrapup_autorestart": None,
        "wrapup_listener_started": None,
        "this_run_restarted": False,
        "waited_for_reconnect": True,
        "live_objects_empty_after_reconnect": False,
        "pre_cpu_path_after_wait": "creep_cpu through 84356640 / path_arrivals through 84356637 at pre-check 17:30:05; listener.py pid 888991 started 17:23:55 after run_listener.sh auto-restart 17:23:45 following box freeze 17:15:27-17:23:42 (488s). This run waited after that reconnect until stats.t and CPU/path buffers were flowing (live.json fresh, age ~1.8s, gameTime=84356644, stats.t=84356640, roomSlot W46N8 objects_n=265; W46N8 live near tip already had 27 distinct ticks 84356620..84356646). This run did not itself restart the listener. Concurrent 17:23 hourly patrol was running; this run waited for its hist_pull to finish before official GETs.",
    },
    "box_freeze": {
        "from": "2026-11-19 17:15:27",
        "to": "2026-11-19 17:23:42",
        "sec": 488,
        "restart_at": "17:23:45",
        "room_stats_gap": "84356451..84356569",
        "official_filled": "84356451..84356569 official-filled 119/119 in all 5 rooms this pass (newly published 84356500 covers 84356501..84356600 100/100 in all 5 rooms). just-published 84356600 not attempted (first-pass game.time=84356654 still in-progress). Prior freeze 16:43:38-17:02:18 gap 84356051..84356309 is now official-filled 259/259 in all 5 rooms including the 9-tick tail.",
        "earlier_freeze": {
            "from": "2026-11-19 16:43:38",
            "to": "2026-11-19 17:02:18",
            "sec": 1119,
            "restart_at": "17:02:21",
            "room_stats_gap": "84356051..84356309",
            "official_filled": "84356051..84356309 official-filled 259/259 in all 5 rooms (17:00 half-hour filled 84356051..84356300 250/250; this overlap plus the 17:23 patrol filled the 9-tick tail 84356301..84356309 9/9 in all 5 rooms after 84356300 published)",
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
    "just-published 84356600 not attempted (first-pass game.time=84356654 still inside the in-progress chunk); previously unpublished 84356500 was written for all 5 rooms this pass; confirm/retry2 skipped; leftover official 404 W46N8@84354300 (hole 84354301..84354351) and W47N7@84354300 (hole 84354301..84354400) had aged out of this window and were not retried.",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 17:23:45 (listener.py pid 888991 started 17:23:55) after box freeze 17:15:27-17:23:42, and had already recovered by pre-check 17:30:05 (live.json fresh, stats.t advancing, gameTime present, objects_n=265, single_slot held; W46N8 live ticks and CPU/path buffers were flowing).",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1730.txt")
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
