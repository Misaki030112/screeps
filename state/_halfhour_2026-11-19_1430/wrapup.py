#!/usr/bin/env python3
"""Write local status records for the 14:30 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-19_1430"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84353701, 84354400
PUB_BASES = "84353700..84354300"
GT_FIRST = 84354426
TICK_S_FIRST = 4.66982
TICK_S_PRINTED = "4.670"
TICK_S_IN_USE = 4.85282
TICK_S_LATER = 4.85282
TS_REALIGNED_FIRST = 16822
NFIX_CORR = 16822
GT_CORR = 84354454  # corrective later-mean-robust realign at game.time=84354454; still_over_45s_vs_later=0
RECON_ROWS = 25291
ALREADY = 22821
INSERTED_FIRST = 2470
INSERTED_CONFIRM = 0  # confirm 14:35:22 gt=84354455 still 404 W46N8@84354300 and W47N7@84354300
INSERTED_RETRY2 = 0  # retry2 14:38:19 gt=84354492 still 404 both
INSERTED_JUST = 0  # 84354400 not attempted (first-pass game.time=84354426 still in-progress)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:600t/0new W47N8:700t/1526new W45N8:700t/544new W45N7:700t/400new W47N7:600t/0new"
FIRST_PASS_LINE = (
    "first pass 33 of 35 official GETs 200, missing_chunks=2 (W46N8@84354300, W47N7@84354300); "
    "14:00 half-hour already wrote through 84354000 (just-published 84354000 was not attempted then and is included in this overlap); "
    "concurrent 14:26 hourly patrol had already official-filled 84353601..84354300 including previously unpublished 84354000 plus 84354100..84354200 (at gt=84354349); "
    "(this pass already_in_db=22821 / inserted=2470; overlap 84353700..84354200 already present from the 14:00 half-hour / 14:26 patrol; this pass newly wrote just-published 84354300 for W47N8, W45N8 and W45N7, filling the 14:08:48-14:26:36 freeze-gap tail 84354301..84354349 in those three rooms); "
    "leftover official 404 W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out of this 40-min window and were not retried; "
    "in-window official 404 W46N8@84354300 and W47N7@84354300 remained after confirm 14:35:22 (gt=84354455) and retry2 14:38:19 (gt=84354492); "
    "just-published 84354400 not attempted (first-pass game.time=84354426 still inside the in-progress chunk)"
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
    "in-window official 404 after first pass: W46N8@84354300, W47N7@84354300; "
    "first pass 33 of 35 official GETs 200, missing_chunks=2; "
    "confirm 14:35:22 gt=84354455 still 404 both (inserted=0); retry2 14:38:19 gt=84354492 still 404 both (inserted=0); "
    "final official_404_in_window=151 (W46N8 84354301..84354351=51, live already had 84354352..84354400; W47N7 84354301..84354400=100)"
)
leftover_txt = (
    "in-window official 404 still open: W46N8@84354300 (hole 84354301..84354351; live W46N8 already covers 84354352..84354400) and W47N7@84354300 (hole 84354301..84354400); "
    "no official empty-no-creep in this window; "
    "aged leftover official 404 W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 were not retried this pass "
    "(already outside this 40-min window, along with older W45N8@84346100, W45N7@84345800, W45N8@84344700, W47N8@84343800, W45N8@84343100, W47N8@84343400, W47N8@84343000, W45N7@84342300, W47N7@84342500, W45N8@84341100)."
)
confirm_summary = (
    "confirm 14:35:22 gt=84354455 still 404 W46N8@84354300 and W47N7@84354300 (inserted=0); "
    "retry2 14:38:19 gt=84354492 still 404 both (inserted=0); "
    "just-published 84354400 not attempted (first-pass game.time=84354426 still inside the in-progress 84354400 chunk; next half-hour overlap will catch it)"
)
vs_later_before = (tick_s.get("still_over_45s_vs_later_before"))
vs_first_over45 = vs_first.get("over45")
vs_later_over15_before = tick_s.get("still_over_15s_vs_later_before")
vs_first_over15 = vs_first.get("over15")
span_vs = (vs_cand.get("span_mean") or {})
prev_vs = (vs_cand.get("prev_later") or {})
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band but is a local dip versus later intervals; "
    f"later-mean-robust {TICK_S_LATER:.5f} was over the 45s gate versus first-pass-realigned rows "
    f"(delta first-robust -0.18300 s/tick, ~132.7s at tmin; "
    f"over45 later={vs_later_before} vs first={vs_first_over45}, over15 later={vs_later_over15_before} vs first={vs_first_over15}; "
    f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')}; "
    f"lowest_over45 among sane was {tick_s.get('lowest_over45_sane')}, because first-pass had already realigned 16822 rows onto 4.66982); "
    f"applied corrective later-mean-robust realign of {NFIX_CORR} rows at game.time={GT_CORR}; "
    f"first-pass realign moved {TS_REALIGNED_FIRST} rows; "
    f"still_over_45s_vs_later={tick_s.get('still_over_45s_vs_later')}; skipped_cross_chunk={tick_s.get('skipped_cross_chunk')}; "
    f"in-use later-mean-robust {TICK_S_IN_USE:.5f}; "
    f"confirm/retry2 still 404 on W46N8@84354300 and W47N7@84354300; just-published 84354400 not attempted"
)
import time as _time
_live_age = _time.time() - (ROOT / "metrics" / "live.json").stat().st_mtime
_stats = live.get("stats") or {}
_cpu_tip = _path_tip = None
with db.connect() as _c:
    _cpu_tip = _c.execute("select max(tick) from creep_cpu").fetchone()[0]
    _path_tip = _c.execute("select max(tick) from path_arrivals").fetchone()[0]

freeze_para = (
    "New box freeze this run 14:08:48-14:26:36 (1067s); also earlier 13:41:05-13:56:16 (905s), 13:17:39-13:22:41 (296s), 12:40:05-13:04:53 (1487s), 12:15:21-12:22:01 (400s), 11:36:36-11:58:55 (1339s), 11:11:06-11:18:54 (467s), 10:40:36-11:03:20 (1359s), 10:09:26-10:23:04 (818s), 09:45:54-09:57:01 (667s), 05:33:25-09:22:55 (13764s), 05:17:00-05:26:03 (542s), 04:45:45-04:58:24 (749s), 03:45:22-04:05:50 (1228s), 03:10:01-03:17:13 (431s), 02:45:55-02:57:12 (671s). "
    "Listener last auto-restart 14:26:39 after that freeze (run_listener.sh auto-restart, not this run; listener.py pid 835653 started 14:26:48; run_listener.sh pid 4035476). Prior auto-restarts 13:56:19 after the 13:41:05-13:56:16 freeze, 13:22:44 after the 13:17:39-13:22:41 freeze, 13:04:56 after the 12:40:05-13:04:53 freeze, 12:22:04 after the 12:15:21-12:22:01 freeze, 12:02:12 after a ws ping/pong timeout at 12:02:09, and 11:58:58 after the 11:36:36-11:58:55 freeze. "
    "This run did not restart the listener; the 14:26:39 auto-reconnect had already been up ~6 min by pre-check and had pulled segment-90 CPU/path buffers itself "
    "(pre-check 14:32:38, live.json age ~1.9s, stats.t=84354420 advancing, roomSlot W46N8 objects_n=262 / gameTime 84354422, mid 5:5:1:1 rotation; "
    "creep_cpu through 84354410 / path_arrivals through 84354385; W46N8 live near tip >=84354400 had 25 distinct ticks; "
    f"by wrapup live.json age ~{_live_age:.1f}s, stats.t={_stats.get('t')}, roomSlot {live.get('roomSlot')}, objects_n={len(live.get('objects') or [])} / gameTime {live.get('gameTime')}, creep_cpu through {_cpu_tip} / path_arrivals through {_path_tip}). "
    "14:00 half-hour already official-filled 84353301..84354000 (inserted_window=13777, coverage 3500/3500, missing_chunks=0; just-published 84354000 was not attempted then and is included in this overlap). "
    "Concurrent 14:26 hourly patrol had already official-filled 84353601..84354300, including previously unpublished 84354000 plus 84354100..84354200 (at gt=84354349). "
    "This half-hour first pass inserted 2470 new rows (already_in_db=22821) and wrote just-published 84354300 for W47N8, W45N8 and W45N7; W46N8@84354300 and W47N7@84354300 stayed official 404 after confirm and retry2. "
    "room_stats gap 84354121..84354349 (229, from the 14:08:48-14:26:36 freeze) sits inside this 40-min window: 84354121..84354300 is official-filled 180/180 in all 5 rooms (14:26 patrol); the tail 84354301..84354349 is official-filled 49/49 in W47N8, W45N8 and W45N7 (this pass) but still missing 49/49 in W46N8 and W47N7 because those rooms 404'd on official 84354300. "
    "older room_stats gap 84353771..84353979 (209, from the 13:41:05-13:56:16 freeze) still sits inside this window and is official-filled 209/209 in all 5 rooms (14:00 half-hour); "
    "older room_stats gaps 84353481..84353559 and 84353001..84353329 have now aged out of this window (already official-filled earlier); "
    "older room_stats gaps 84347621..84350529, 84346261..84346529 and 84347021..84347189 remain outside this window. "
    "Aged official 404 W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) remain outside this window. "
    "live.json / stats.t were fresh at pre-check (age ~1.9s, tip stats.t=84354420) after the 14:26:39 auto-reconnect; "
    "just-published 84354400 was not yet publishable (game.time=84354426 at first pass); this pass wrote just-published 84354300 for three rooms (W46N8 and W47N7 still official 404 after confirm/retry2); single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84354410 / path_arrivals through 84354385 at pre-check); "
    "this run did not restart the listener."
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
            "first-interval 4.66982 printed 4.670 was sane but a local dip; first-pass realign moved 16822 rows onto 4.66982; "
            "later-mean-robust 4.85282 was over the 45s gate versus those rows "
            f"(over45 later={vs_later_before} vs first={vs_first_over45}, delta -0.18300 s/tick ~132.7s at tmin); "
            f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')} "
            f"(lowest_over45 among sane was {tick_s.get('lowest_over45_sane')}, because rows already sat on first); "
            "applied corrective later-mean-robust realign of 16822 rows at game.time=84354454; in-use later-mean-robust 4.85282; still_over_45s_vs_later=0"
        ),
    },
    "just_published": {
        "base": 84354400,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": None,
        "recovered_game_time": None,
        "inserted": INSERTED_JUST,
        "note": "not attempted; first-pass game.time=84354426 was still inside the in-progress 84354400 chunk (typically publishable around game.time>=84354540). This --minutes 40 pass wrote just-published 84354300 for W47N8, W45N8 and W45N7 (W46N8 and W47N7 still official 404 after confirm/retry2). Next half-hour 10-min overlap will catch 84354400 and can retry W46N8@84354300 / W47N7@84354300.",
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
        "in_window_still_404": ["W46N8@84354300", "W47N7@84354300"],
        "w45n7_empty_no_creep": [],
        "w47n7_empty_no_creep": [],
        "distinct": None,
        "skipped": True,
    },
    "confirm": {
        "at": "2026-11-19 14:35:22 Asia/Hong_Kong",
        "game_time": 84354455,
        "inserted": 0,
        "ssl_abort_first": None,
        "targets": 2,
        "recovered": [],
        "still_404": ["W46N8@84354300", "W47N7@84354300"],
        "skipped": False,
        "note": "retried first-pass official 404s W46N8@84354300 and W47N7@84354300; both still 404 at game.time=84354455 (neighbors W47N8/W45N8/W45N7 @84354300 were already 200 on first pass)",
    },
    "retry2": {
        "at": "2026-11-19 14:38:18 Asia/Hong_Kong",
        "game_time": 84354492,
        "inserted": 0,
        "skipped": False,
        "still_404": ["W46N8@84354300", "W47N7@84354300"],
        "note": "retry2 still 404 on W46N8@84354300 and W47N7@84354300 at game.time=84354492; W46N8 live already covers 84354352..84354400 (hole 84354301..84354351); W47N7 hole 84354301..84354400",
    },
    "in_window_404": {
        "W46N8@84354300": {"hole": "84354301..84354351", "missing": 51, "live_tail": "84354352..84354400"},
        "W47N7@84354300": {"hole": "84354301..84354400", "missing": 100},
    },
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 835653,
        "loop_pid": 4035476,
        "restart_at": "14:26:39",
        "listener_started": "14:26:48",
        "this_run_restarted": False,
        "waited_for_reconnect": False,
        "live_objects_empty_after_reconnect": False,
        "pre_cpu_path_after_wait": "creep_cpu through 84354410 / path_arrivals through 84354385 at pre-check 14:32:38; listener.py pid 835653 started 14:26:48 after run_listener.sh auto-restart 14:26:39 (following box freeze 14:08:48-14:26:36 1067s; prior auto-restarts 13:56:19 after 13:41:05-13:56:16 freeze, 13:22:44 after 13:17:39-13:22:41 freeze, 13:04:56 after 12:40:05-13:04:53 freeze, 12:22:04 after 12:15:21-12:22:01 freeze, 12:02:12 after ws ping/pong timeout 12:02:09, and 11:58:58 after the 11:36:36-11:58:55 freeze); this run did not wait or restart — listener had already been up ~6 min, live.json fresh (age ~1.9s at pre-check) with stats.t=84354420, gameTime=84354422, roomSlot W46N8 objects_n=262, and W46N8 creep_ticks near tip already ingesting (25 distinct ticks >=84354400 at pre-check)",
    },
    "box_freeze": {
        "from": "2026-11-19 14:08:48",
        "to": "2026-11-19 14:26:36",
        "sec": 1067,
        "restart_at": "14:26:39",
        "room_stats_gap": "84354121..84354349",
        "official_filled": "84354121..84354300 official-filled 180/180 in all 5 rooms (14:26 patrol); tail 84354301..84354349 official-filled 49/49 in W47N8, W45N8, W45N7 (this pass) but still missing 49/49 in W46N8 and W47N7 (official 404 on 84354300 after confirm/retry2)",
        "earlier_freeze": {
            "from": "2026-11-19 13:41:05",
            "to": "2026-11-19 13:56:16",
            "sec": 905,
            "restart_at": "13:56:19",
            "room_stats_gap": "84353771..84353979",
            "official_filled": "already official-filled 209/209 in all 5 rooms (14:00 half-hour); gap still sits inside this 40-min window",
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
    f"missing_chunks={MISSING_CHUNKS} in_window_404=W46N8@84354300,W47N7@84354300; final official_404={official_404_missing} empty_no_creep={empty_no_creep}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    "just-published 84354400 not attempted (first-pass game.time=84354426 still inside the in-progress chunk); leftover official 404 W46N8@84354300 (hole 84354301..84354351) and W47N7@84354300 (hole 84354301..84354400) still open after confirm/retry2.",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not restart the listener.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1430.txt")
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
