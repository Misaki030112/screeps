#!/usr/bin/env python3
"""Write local status records for the 13:30 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-19_1330"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84352901, 84353600
PUB_BASES = "84352900..84353500"
GT_FIRST = 84353642
TICK_S_FIRST = 4.86031
TICK_S_PRINTED = "4.860"
TICK_S_IN_USE = 4.75346
TICK_S_LATER = 4.75346
TS_REALIGNED_FIRST = 16319
NFIX_CORR = 12201
GT_CORR = 84353659  # tick_s check/realign at game.time=84353659; later-mean-robust corrective nfix=12201
RECON_ROWS = 24799
ALREADY = 24796
INSERTED_FIRST = 3
INSERTED_CONFIRM = 0  # confirm skipped (no in-window official 404s)
INSERTED_RETRY2 = 0  # retry2 skipped (no in-window official 404s)
INSERTED_JUST = 0  # 84353600 not attempted (first-pass game.time=84353642 still in-progress)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/0new W47N8:700t/0new W45N8:700t/0new W45N7:700t/3new W47N7:700t/0new"
FIRST_PASS_LINE = (
    "first pass 35 of 35 official GETs 200, missing_chunks=0; "
    "13:00 half-hour already wrote through 84353300 (just-published 84353300 was not attempted then and is included in this overlap); "
    "concurrent 13:22 hourly patrol had already official-filled through 84353600 including previously unpublished 84353300 plus 84353400..84353500; "
    "(this pass already_in_db=24796 / inserted=3, only 3 new W45N7 rows; overlap 84352900..84353200 already present from the 13:00 half-hour, and 84353300..84353500 from the 13:22 patrol); "
    "leftover official 404 W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out of this 40-min window and were not retried; "
    "no in-window official 404s, so confirm/retry2 were skipped; "
    "just-published 84353600 not attempted (first-pass game.time=84353642 still inside the in-progress chunk)"
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
    "confirm/retry2 skipped (no in-window official 404s); "
    "final official_404_in_window=0"
)
leftover_txt = (
    "no in-window official 404 still open; "
    "no official empty-no-creep in this window; "
    "aged leftover official 404 W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 were not retried this pass "
    "(already outside this 40-min window, along with older W45N8@84346100, W45N7@84345800, W45N8@84344700, W47N8@84343800, W45N8@84343100, W47N8@84343400, W47N8@84343000, W45N7@84342300, W47N7@84342500, W45N8@84341100)."
)
confirm_summary = (
    "confirm/retry2 skipped (no in-window official 404s, inserted=0); "
    "just-published 84353600 not attempted (first-pass game.time=84353642 still inside the in-progress 84353600 chunk; next half-hour overlap will catch it)"
)
vs_later_before = (tick_s.get("still_over_45s_vs_later_before"))
vs_first_over45 = vs_first.get("over45")
vs_later_over15_before = tick_s.get("still_over_15s_vs_later_before")
vs_first_over15 = vs_first.get("over15")
span_vs = (vs_cand.get("span_mean") or {})
prev_vs = (vs_cand.get("prev_later") or {})
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} was over the 45s gate versus current rows after the first-pass realign "
    f"(delta first-robust 0.10685 s/tick, ~79.2s at tmin; "
    f"over45 later={vs_later_before} vs first={vs_first_over45}, over15 later={vs_later_over15_before} vs first={vs_first_over15}; "
    f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')}; "
    f"lowest_over45 among sane was {tick_s.get('lowest_over45_sane')}); "
    f"applied corrective later-mean-robust realign of {NFIX_CORR} rows at game.time={GT_CORR} "
    f"(first-pass realign had moved {TS_REALIGNED_FIRST} rows with first-interval); "
    f"still_over_45s_vs_later={tick_s.get('still_over_45s_vs_later')}; skipped_cross_chunk={tick_s.get('skipped_cross_chunk')}; "
    f"in-use later-mean-robust {TICK_S_IN_USE:.5f}; "
    f"confirm/retry2 skipped (no in-window official 404s); just-published not attempted"
)
import time as _time
_live_age = _time.time() - (ROOT / "metrics" / "live.json").stat().st_mtime
_stats = live.get("stats") or {}
_cpu_tip = _path_tip = None
with db.connect() as _c:
    _cpu_tip = _c.execute("select max(tick) from creep_cpu").fetchone()[0]
    _path_tip = _c.execute("select max(tick) from path_arrivals").fetchone()[0]

freeze_para = (
    "New box freeze this run 13:17:39-13:22:41 (296s); also earlier 12:40:05-13:04:53 (1487s), 12:15:21-12:22:01 (400s), 11:36:36-11:58:55 (1339s), 11:11:06-11:18:54 (467s), 10:40:36-11:03:20 (1359s), 10:09:26-10:23:04 (818s), 09:45:54-09:57:01 (667s), 05:33:25-09:22:55 (13764s), 05:17:00-05:26:03 (542s), 04:45:45-04:58:24 (749s), 03:45:22-04:05:50 (1228s), 03:10:01-03:17:13 (431s), 02:45:55-02:57:12 (671s). "
    "Listener last auto-restart 13:22:44 after that freeze (run_listener.sh auto-restart around the 13:22 hourly patrol, not this run; listener.py pid 818590 started 13:22:53; run_listener.sh pid 4035476). Prior auto-restarts 13:04:56 after the 12:40:05-13:04:53 freeze, 12:22:04 after the 12:15:21-12:22:01 freeze, 12:02:12 after a ws ping/pong timeout at 12:02:09, and 11:58:58 after the 11:36:36-11:58:55 freeze. "
    "This run did not restart the listener; it was already up after that auto-restart and pulling segment-90 CPU/path buffers itself "
    "(pre-check 13:29:52 live.json age ~1.4s, stats.t=84353630, roomSlot W46N8 objects_n=264 / gameTime 84353638, mid 5:5:1:1 rotation; "
    "creep_cpu through 84353620 / path_arrivals through 84353619; "
    f"by wrapup live.json age ~{_live_age:.1f}s, stats.t={_stats.get('t')}, roomSlot {live.get('roomSlot')}, objects_n={len(live.get('objects') or [])} / gameTime {live.get('gameTime')}, creep_cpu through {_cpu_tip} / path_arrivals through {_path_tip}). "
    "13:00 half-hour already official-filled 84352601..84353300 (inserted_window=17344, coverage 3500/3500, missing_chunks=0; just-published 84353300 was not attempted then and is included in this overlap). "
    "Concurrent 13:22 hourly patrol had already official-filled through 84353600, including previously unpublished 84353300 plus 84353400..84353500 (patrol first pass inserted 5990 through 84353500, then tip-filled published 84353500 with +3325). "
    "This half-hour first pass inserted only 3 new W45N7 rows (already_in_db=24796) and confirmed published 84353300 (left unattempted last 13:00 run) plus 84353400..84353500 already written by the patrol. "
    "room_stats gap 84353481..84353559 (79, from the 13:17:39-13:22:41 freeze) sits inside this 40-min window and is official-filled 79/79 in all 5 rooms (filled by the 13:22 hourly patrol). "
    "older room_stats gap 84353001..84353329 (329, from the 12:40:05-13:04:53 freeze) still sits inside this window and is official-filled 329/329 in all 5 rooms (13:00 half-hour filled through 84353300; 13:22 patrol filled the remaining 84353301..84353329); "
    "older room_stats gaps 84352691..84352789, 84352521..84352539 and 84352201..84352499 have now aged out of this window (already official-filled earlier, except leftover official 404 W47N8@84352400 in the aged 84352201..84352499 gap); "
    "older room_stats gaps 84347621..84350529, 84346261..84346529 and 84347021..84347189 remain outside this window. "
    "Aged official 404 W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) remain outside this window. "
    "live.json / stats.t were already fresh at pre-check (age ~1.4s, tip stats.t=84353630) after the 13:22:44 auto-reconnect; this run did not need to wait for buffers; "
    "just-published 84353600 was not yet publishable (game.time=84353642 at first pass); this pass confirmed published 84353300 (left unattempted last 13:00 run) plus 84353400..84353500; single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84353620 / path_arrivals through 84353619 at pre-check); "
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
            "first-interval 4.86031 printed 4.860 was sane; first-pass realign moved 16319 rows with first-interval; "
            "later-mean-robust 4.75346 was over the 45s gate versus those current rows "
            f"(over45 later={vs_later_before} vs first={vs_first_over45}, delta 0.10685 s/tick ~79.2s at tmin); "
            f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')} "
            f"(lowest_over45 among sane was {tick_s.get('lowest_over45_sane')}); "
            "applied corrective later-mean-robust realign of 12201 rows at game.time=84353659; in-use later-mean-robust 4.75346; still_over_45s_vs_later=0"
        ),
    },
    "just_published": {
        "base": 84353600,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": None,
        "recovered_game_time": None,
        "inserted": INSERTED_JUST,
        "note": "not attempted; first-pass game.time=84353642 was still inside the in-progress 84353600 chunk (typically publishable around game.time>=84353740). This --minutes 40 pass confirmed published 84353300 (left unattempted last 13:00 run) plus 84353400..84353500 already written by the concurrent 13:22 hourly patrol. Next half-hour 10-min overlap will catch 84353600.",
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
        "note": "skipped; no in-window official 404s after first pass 35/35 official GETs 200",
    },
    "retry2": {
        "at": None,
        "game_time": None,
        "inserted": 0,
        "skipped": True,
        "still_404": [],
        "note": "skipped; no in-window official 404s",
    },
    "in_window_404": {},
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 818590,
        "loop_pid": 4035476,
        "restart_at": "13:22:44",
        "listener_started": "13:22:53",
        "this_run_restarted": False,
        "waited_for_reconnect": False,
        "live_objects_empty_after_reconnect": False,
        "pre_cpu_path_after_wait": "creep_cpu through 84353620 / path_arrivals through 84353619 at pre-check 13:29:52; listener.py pid 818590 started 13:22:53 after run_listener.sh auto-restart 13:22:44 (following box freeze 13:17:39-13:22:41 296s; prior auto-restarts 13:04:56 after 12:40:05-13:04:53 freeze, 12:22:04 after 12:15:21-12:22:01 freeze, 12:02:12 after ws ping/pong timeout 12:02:09, and 11:58:58 after the 11:36:36-11:58:55 freeze); this run did not wait — live.json was already fresh at pre-check (age ~1.4s, stats.t=84353630 advancing, single_slot 5:5:1:1 rotating, objects_n=264, gameTime=84353638) and buffers flowing",
    },
    "box_freeze": {
        "from": "2026-11-19 13:17:39",
        "to": "2026-11-19 13:22:41",
        "sec": 296,
        "restart_at": "13:22:44",
        "room_stats_gap": "84353481..84353559",
        "official_filled": "in-window gap 84353481..84353559 official-filled 79/79 in all 5 rooms (already written by the concurrent 13:22 hourly patrol)",
        "earlier_freeze": {
            "from": "2026-11-19 12:40:05",
            "to": "2026-11-19 13:04:53",
            "sec": 1487,
            "restart_at": "13:04:56",
            "room_stats_gap": "84353001..84353329",
            "official_filled": "already official-filled 329/329 in all 5 rooms (13:00 half-hour through 84353300; 13:22 patrol filled 84353301..84353329); gap still sits inside this 40-min window",
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
    "just-published 84353600 not attempted (first-pass game.time=84353642 still inside the in-progress chunk); no leftover official 404 in this window (confirm/retry2 skipped).",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not restart the listener.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1330.txt")
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
