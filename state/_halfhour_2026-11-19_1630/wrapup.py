#!/usr/bin/env python3
"""Write local status records for the 16:30 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-19_1630"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84355201, 84355900
PUB_BASES = "84355200..84355800"
GT_FIRST = 84355969
TICK_S_FIRST = 4.63253
TICK_S_PRINTED = "4.633"
TICK_S_IN_USE = 4.81892
TICK_S_LATER = 4.81892
TS_REALIGNED_FIRST = 21849
NFIX_CORR = 20523
GT_CORR = 84355992  # corrective later-mean-robust realign at game.time=84355992; still_over_45s_vs_later=0
RECON_ROWS = 25257
ALREADY = 22586
INSERTED_FIRST = 2671
INSERTED_CONFIRM = 0  # skipped: first pass 35/35 official GETs 200, missing_chunks=0
INSERTED_RETRY2 = 0
INSERTED_JUST = 0  # 84355900 not attempted (first-pass game.time=84355969 still in-progress)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/1293new W47N8:700t/478new W45N8:700t/409new W45N7:700t/19new W47N7:700t/472new"
FIRST_PASS_LINE = (
    "first pass 35 of 35 official GETs 200, missing_chunks=0; "
    "16:00 half-hour already wrote through 84355500 (just-published 84355500 was not attempted then and is included in this overlap, 200 in all 5 rooms; confirm had recovered W47N7@84355400); "
    "(this pass already_in_db=22586 / inserted=2671; overlap 84355200..84355400 already present from the 16:00 half-hour; this pass newly wrote previously unpublished 84355500 for all 5 rooms plus 84355600..84355800, filling the 16:05 ping/pong STATS gap 84355571..84355589 19/19 in all 5 rooms and covering room_stats gap 84355651..84355759 109/109 in W46N8/W47N8/W45N8/W47N7; W45N7 in that gap and later has official empty-no-creep, not a 404 hole); "
    "leftover official 404 W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out of this 40-min window and were not retried; "
    "no in-window official 404, so confirm and retry2 were skipped; "
    "just-published 84355900 not attempted (first-pass game.time=84355969 still inside the in-progress chunk); "
    "concurrent 16:19 hourly patrol had already finished before this run"
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
    "W45N7 official empty-no-creep 214 ticks (84355664, 84355666..84355829, 84355849..84355897) — official history had no our creeps, not a 404 hole, consistent with the W45N7 invader window ~16:08-16:26; "
    "aged leftover official 404 W46N8@84354300 (hole 84354301..84354351; live W46N8 already covers 84354352..84354400) and W47N7@84354300 (hole 84354301..84354400, 0/100 still missing) were not retried this pass "
    "(already outside this 40-min window, along with W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800, and older W45N8@84346100, W45N7@84345800, W45N8@84344700, W47N8@84343800, W45N8@84343100, W47N8@84343400, W47N8@84343000, W45N7@84342300, W47N7@84342500, W45N8@84341100)."
)
confirm_summary = (
    "confirm skipped (first pass 35/35 official GETs 200, missing_chunks=0, no in-window official 404); "
    "retry2 skipped; "
    "just-published 84355900 not attempted (first-pass game.time=84355969 still inside the in-progress chunk; typically publishable around game.time>=84356040; next half-hour overlap will catch it)"
)
vs_later_before = (tick_s.get("still_over_45s_vs_later_before"))
vs_first_over45 = vs_first.get("over45")
vs_later_over15_before = tick_s.get("still_over_15s_vs_later_before")
vs_first_over15 = vs_first.get("over15")
span_vs = (vs_cand.get("span_mean") or {})
prev_vs = (vs_cand.get("prev_later") or {})
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band but is a local low versus later intervals; "
    f"later-mean-robust {TICK_S_LATER:.5f} was over the 45s gate versus first-pass-realigned rows "
    f"(delta first-robust -0.18639 s/tick, ~143.1s at tmin; "
    f"over45 later={vs_later_before} vs first={vs_first_over45}, over15 later={vs_later_over15_before} vs first={vs_first_over15}; "
    f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')}; "
    f"lowest_over45 among sane was {tick_s.get('lowest_over45_sane')} (first already closer to the live anchor than later-mean before corrective); "
    f"applied corrective later-mean-robust realign of {NFIX_CORR} rows at game.time={GT_CORR} anyway, because later-mean-robust itself was over the 45s gate versus first-pass-realigned rows; "
    f"first-pass realign moved {TS_REALIGNED_FIRST} rows; "
    f"still_over_45s_vs_later={tick_s.get('still_over_45s_vs_later')}; skipped_cross_chunk={tick_s.get('skipped_cross_chunk')}; "
    f"in-use later-mean-robust {TICK_S_IN_USE:.5f}; "
    f"confirm skipped; retry2 skipped; just-published 84355900 not attempted"
)

_live_age = _time.time() - (ROOT / "metrics" / "live.json").stat().st_mtime
_stats = live.get("stats") or {}
_cpu_tip = _path_tip = None
with db.connect() as _c:
    _cpu_tip = _c.execute("select max(tick) from creep_cpu").fetchone()[0]
    _path_tip = _c.execute("select max(tick) from path_arrivals").fetchone()[0]

freeze_para = (
    "No new recorded box freeze this run (box_pauses.jsonl and errors.log still end at 15:37:56-15:57:12, 1155s). "
    "After that, listener auto-restarts were 16:05:37 (ws ping/pong timed out 16:05:34), 16:19:19 (ws ping/pong timed out 16:19:16), and 16:31:39 (no freeze or ping/pong line flushed to errors.log; current listener.py pid 876066 started 16:31:49; run_listener.sh pid 4035476). "
    "Also earlier freezes 15:21:03-15:24:59 (230s), 14:46:22-15:05:49 (1161s), 14:08:48-14:26:36 (1067s), 13:41:05-13:56:16 (905s), 13:17:39-13:22:41 (296s), 12:40:05-13:04:53 (1487s), 12:15:21-12:22:01 (400s), 11:36:36-11:58:55 (1339s), 11:11:06-11:18:54 (467s), 10:40:36-11:03:20 (1359s), 10:09:26-10:23:04 (818s), 09:45:54-09:57:01 (667s), 05:33:25-09:22:55 (13764s), 05:17:00-05:26:03 (542s), 04:45:45-04:58:24 (749s), 03:45:22-04:05:50 (1228s), 03:10:01-03:17:13 (431s), 02:45:55-02:57:12 (671s). "
    "This run did not restart the listener; after the 16:31:39 auto-reconnect this run waited for stats to resume and for the listener to pull segment-90 CPU/path buffers itself "
    "(pre-check 16:35:46, live.json age ~1.6s, stats.t=84355960 advancing, roomSlot W46N8 objects_n=262 / gameTime 84355962 at the start of a 5:5:1:1 rotation; "
    "creep_cpu through 84355950 / path_arrivals through 84355948; W46N8 live near tip >=84355940 already had 25 distinct ticks 84355940..84355964; "
    f"by wrapup live.json age ~{_live_age:.1f}s, stats.t={_stats.get('t')}, roomSlot {live.get('roomSlot')}, objects_n={len(live.get('objects') or {})} / gameTime {live.get('gameTime')}, creep_cpu through {_cpu_tip} / path_arrivals through {_path_tip}). "
    "16:00 half-hour already official-filled 84354801..84355500 (inserted_window=14027, coverage 3500/3500, missing_chunks=0 after confirm recovered W47N7@84355400; just-published 84355500 was not attempted then and is included in this overlap, 200 in all 5 rooms this pass). "
    "This half-hour first pass inserted 2671 new rows (already_in_db=22586) and wrote previously unpublished 84355500 for all 5 rooms plus 84355600..84355800; confirm/retry2 skipped. Leftover official 404 W46N8@84354300 and W47N7@84354300 remain aged out of this window and were not retried. "
    "room_stats gap 84355571..84355589 (19, from the 16:05:34 ping/pong timeout) sits inside this 40-min window and is official-filled 19/19 in all 5 rooms. "
    "room_stats gap 84355651..84355759 (109, STATS hole around the 16:19:16 ping/pong timeout; not a recorded box freeze — live creep_ticks already covered 109/109 in W46N8/W47N8/W45N8/W47N7 before this pass) sits inside this window: official 109/109 in those 4 rooms; W45N7 is official empty-no-creep for most of this gap and 84355666..84355829 / 84355849..84355897 (214 empty ticks total; invader in W45N7 ~16:08-16:26). "
    "older room_stats gap 84355231..84355489 (259, from the 15:37:56-15:57:12 freeze) still sits inside this window and remains official-filled 259/259 in all 5 rooms (16:00 half-hour). "
    "older room_stats gap 84355021..84355089 (69, from the 15:21:03-15:24:59 freeze) has now aged out of this window (window starts at 84355201) and remains official-filled 69/69 in all 5 rooms (15:30 half-hour). "
    "older room_stats gap 84354931..84354959 (29, short gap around the 15:15:04 listener restart; not a recorded box freeze) has now aged out of this window and remains official-filled 29/29 in all 5 rooms. "
    "older room_stats gap 84354591..84354849 (259, from the 14:46:22-15:05:49 freeze) has now aged out of this window: official-filled 259/259 in all 5 rooms earlier. "
    "older room_stats gap 84354121..84354349 (229, from the 14:08:48-14:26:36 freeze) remains aged out of this window: 84354121..84354300 is official-filled 180/180 in all 5 rooms from earlier runs; the tail 84354301..84354349 remains official-filled 49/49 in W47N8, W45N8 and W45N7 but still missing 49/49 in W46N8 and all 100 ticks 84354301..84354400 in W47N7 because those rooms 404'd on official 84354300 (aged out, not retried this pass). "
    "older room_stats gaps 84353771..84353979, 84353481..84353559 and 84353001..84353329 remain aged out of this window (already official-filled earlier); "
    "older room_stats gaps 84347621..84350529, 84346261..84346529 and 84347021..84347189 remain outside this window. "
    "Aged official 404 W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) remain outside this window. "
    "live.json / stats.t were fresh at pre-check (age ~1.6s, tip stats.t=84355960) after the 16:31:39 auto-reconnect; "
    "just-published 84355900 was not yet publishable (game.time=84355969 at first pass); this pass wrote previously unpublished 84355500 for all 5 rooms; single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84355950 / path_arrivals through 84355948 at pre-check); "
    "this run did not restart the listener. "
    "Concurrent 16:19 hourly patrol had already finished (~16:28 / 84355870) before this run."
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
            "first-interval 4.63253 printed 4.633 was sane but a local low; first-pass realign moved 21849 rows onto 4.63253; "
            "later-mean-robust 4.81892 was over the 45s gate versus those rows "
            f"(over45 later={vs_later_before} vs first={vs_first_over45}, delta -0.18639 s/tick ~143.1s at tmin); "
            f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')} "
            f"(lowest_over45 among sane was {tick_s.get('lowest_over45_sane')}, already closer to the live anchor before corrective); "
            "applied corrective later-mean-robust realign of 20523 rows at game.time=84355992; in-use later-mean-robust 4.81892; still_over_45s_vs_later=0"
        ),
    },
    "just_published": {
        "base": 84355900,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": None,
        "recovered_game_time": None,
        "inserted": INSERTED_JUST,
        "note": "not attempted; first-pass game.time=84355969 was still inside the in-progress 84355900 chunk (typically publishable around game.time>=84356040). Confirm was skipped (missing_chunks=0). This --minutes 40 pass wrote previously unpublished 84355500 for all 5 rooms plus 84355600..84355800. Next half-hour 10-min overlap will catch 84355900.",
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
        "at": "2026-11-19 16:38 Asia/Hong_Kong",
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
        "pid": 876066,
        "pid_at_precheck": 876066,
        "loop_pid": 4035476,
        "restart_at": "16:31:39",
        "listener_started": "16:31:49",
        "wrapup_ws_timeout": None,
        "wrapup_autorestart": None,
        "wrapup_listener_started": None,
        "this_run_restarted": False,
        "waited_for_reconnect": True,
        "live_objects_empty_after_reconnect": False,
        "pre_cpu_path_after_wait": "creep_cpu through 84355950 / path_arrivals through 84355948 at pre-check 16:35:46; listener.py pid 876066 started 16:31:49 after run_listener.sh auto-restart 16:31:39 (no freeze or ping/pong line flushed to errors.log; prior auto-restarts 16:19:19 after ping/pong 16:19:16 and 16:05:37 after ping/pong 16:05:34; last recorded box freeze 15:37:56-15:57:12). This run waited after that reconnect until stats.t and CPU/path buffers were flowing (live.json fresh, age ~1.6s, stats.t=84355960, roomSlot W46N8 objects_n=262 / gameTime 84355962, W46N8 live near tip already had 25 distinct ticks 84355940..84355964). This run did not itself restart the listener.",
    },
    "box_freeze": {
        "from": "2026-11-19 15:37:56",
        "to": "2026-11-19 15:57:12",
        "sec": 1155,
        "restart_at": "15:57:15",
        "room_stats_gap": "84355231..84355489",
        "official_filled": "84355231..84355489 official-filled 259/259 in all 5 rooms (16:00 half-hour); still inside this overlap. No new recorded box freeze this run. New in-window room_stats gaps: 84355571..84355589 (19, 16:05:34 ping/pong) official-filled 19/19 all 5 rooms; 84355651..84355759 (109, STATS hole around 16:19:16 ping/pong, not a recorded freeze) official 109/109 in 4 rooms, W45N7 official empty-no-creep. just-published 84355900 not attempted (first-pass game.time=84355969 still in-progress)",
        "earlier_freeze": {
            "from": "2026-11-19 15:21:03",
            "to": "2026-11-19 15:24:59",
            "sec": 230,
            "restart_at": "15:25:03",
            "room_stats_gap": "84355021..84355089",
            "official_filled": "84355021..84355089 official-filled 69/69 in all 5 rooms (15:30 half-hour); now aged out of this window (starts 84355201)",
        },
        "new_freeze_this_run": False,
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
    "just-published 84355900 not attempted (first-pass game.time=84355969 still inside the in-progress chunk); previously unpublished 84355500 was written for all 5 rooms this pass; confirm/retry2 skipped; leftover official 404 W46N8@84354300 (hole 84354301..84354351) and W47N7@84354300 (hole 84354301..84354400) had aged out of this window and were not retried.",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 16:31:39 (listener.py pid 876066 started 16:31:49) and had already recovered by pre-check 16:35:46 (live.json fresh, single_slot held). Earlier auto-restarts this hour: 16:19:19 after ping/pong 16:19:16, 16:05:37 after ping/pong 16:05:34.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1630.txt")
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
