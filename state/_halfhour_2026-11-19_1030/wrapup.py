#!/usr/bin/env python3
"""Write local status records for the 10:30 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-19_1030"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84350601, 84351300
PUB_BASES = "84350600..84351200"
GT_FIRST = 84351390
TICK_S_FIRST = 4.76190
TICK_S_PRINTED = "4.762"
TICK_S_IN_USE = 4.76190
TICK_S_LATER = 4.73175
TS_REALIGNED_FIRST = 7522
NFIX_CORR = 0
GT_CORR = None  # no corrective realign; check at game.time=84351406
RECON_ROWS = 26965
ALREADY = 23059
INSERTED_FIRST = 3906
INSERTED_CONFIRM = 0  # confirm 10:33:15 gt=84351407 still official 404 W47N7@84350700
INSERTED_RETRY2 = 0  # retry2 10:35:35 gt=84351435 still official 404
INSERTED_JUST = 3119  # just-published 84351300 5/5 rooms at 10:36:11 gt=84351443 (84351301..84351400)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/810new W47N8:700t/1895new W45N8:700t/592new W45N7:700t/340new W47N7:600t/269new"
FIRST_PASS_LINE = (
    "first pass 34 of 35 official GETs 200, missing_chunks=1 W47N7@84350700; "
    "10:00 half-hour already wrote through 84350900 and just-published 84350900 through 84351000; "
    "(this pass already_in_db=23059 / inserted=3906); "
    "leftover official 404 W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out of this 40-min window; "
    "W47N7@84350700 still official 404 after confirm 10:33:15 game.time=84351407, retry2 10:35:35 game.time=84351435, and just-published 10:36:11 game.time=84351443"
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
    "in-window official 404 after first pass: W47N7@84350700 hole 84350701..84350800; "
    "first pass 34 of 35 official GETs 200, missing_chunks=1; "
    "confirm 10:33:15 game.time=84351407 still official 404 (db 0/0); "
    "retry2 10:35:35 game.time=84351435 still official 404; "
    "just-published also retried W47N7@84350700 at 10:36:11 game.time=84351443 still official 404; "
    "neighbors @84350600/@84350800 both official 200; "
    "final official_404_in_window=100"
)
leftover_txt = (
    "in-window official 404 still open: W47N7@84350700 hole 84350701..84350800 (100 ticks, db 0/0) after confirm, retry2, and just-published retry; "
    "W47N7 official empty-no-creep 121 ticks [84351066..84351066], [84351068..84351187]; "
    "aged leftover official 404 W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 were not retried this pass "
    "(already outside this 40-min window, along with older W45N8@84346100, W45N7@84345800, W45N8@84344700, W47N8@84343800, W45N8@84343100, W47N8@84343400, W47N8@84343000, W45N7@84342300, W47N7@84342500, W45N8@84341100)."
)
confirm_summary = (
    "confirm 10:33:15 game.time=84351407 still official 404 W47N7@84350700 inserted=0; "
    "retry2 10:35:35 game.time=84351435 still official 404 inserted=0; "
    "just-published 84351300 first try 10:36:11 game.time=84351443 recovered 5/5 rooms inserted=3119 "
    "(waited until live stats.t>=84351440); leftover W47N7@84350700 still official 404"
)
vs_later_before = (tick_s.get("still_over_45s_vs_later_before"))
vs_first_over45 = vs_first.get("over45")
vs_later_over15_before = tick_s.get("still_over_15s_vs_later_before")
vs_first_over15 = vs_first.get("over15")
span_vs = (vs_cand.get("span_mean") or {})
prev_vs = (vs_cand.get("prev_later") or {})
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} already inside the 45s gate versus first-aligned rows "
    f"(delta first-robust 0.03015 s/tick, ~23.8s at tmin; "
    f"over45 later={vs_later_before} vs first={vs_first_over45}, over15 later={vs_later_over15_before} vs first={vs_first_over15}; "
    f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')}; "
    f"lowest_over45 among sane was {tick_s.get('lowest_over45_sane')}); "
    f"no corrective realign (later-mean already inside 45s gate, nfix=0); "
    f"still_over_45s_vs_later={tick_s.get('still_over_45s_vs_later')}; skipped_cross_chunk={tick_s.get('skipped_cross_chunk')}; "
    f"in-use first-interval {TICK_S_IN_USE:.5f}; "
    f"subsequent confirm/retry2/just-published inserts used first-interval {TICK_S_IN_USE:.5f} (confirm/retry2 inserted=0; just ts_realigned=0)"
)
freeze_para = (
    "New box freeze this run 10:09:26-10:23:04 (818s); also earlier 09:45:54-09:57:01 (667s), 05:33:25-09:22:55 (13764s), 05:17:00-05:26:03 (542s), 04:45:45-04:58:24 (749s), 03:45:22-04:05:50 (1228s), 03:10:01-03:17:13 (431s), 02:45:55-02:57:12 (671s). "
    "Listener last auto-restart 10:23:07 after that wake (run_listener.sh auto-restart, not this run; listener.py pid 767225 started 10:23:17; run_listener.sh pid 4035476). "
    "This run did not restart the listener; it was already up after that auto-restart and pulling segment-90 CPU/path buffers itself "
    "(pre-check 10:31:27 live.json age ~3.7s, stats.t=84351380, roomSlot W46N8 objects_n=264 / gameTime 84351386; "
    "creep_cpu through 84351380 / path_arrivals through 84351368; "
    "by wrapup live.json age ~1.5s, stats.t=84351450, roomSlot W47N8, objects_n=0 / gameTime 84351401 just after 5:5:1:1 rotation, creep_cpu through 84351440 / path_arrivals through 84351438). "
    "10:00 half-hour already official-filled 84350201..84350900 plus just-published 84350900 through 84351000 (inserted_window=6222, coverage 3400/3500 with leftover official 404 W47N7@84350700). "
    "room_stats gap 84351101..84351289 (189, from the 10:09:26-10:23:04 freeze) sits inside this 40-min window and is official-filled 189/189 in W46N8, W47N8, W45N8, W45N7; W47N7 102/189 because official empty-no-creep 84351101..84351187 (87 ticks, part of 84351068..84351187); "
    "older room_stats gap 84350801..84350959 was already official-filled last run; older room_stats gaps 84347621..84350529, 84346261..84346529 and 84347021..84347189 remain outside this window. "
    "Aged official 404 W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) remain outside this window. "
    "live.json / stats.t were fresh at pre-check (age ~3.7s, tip stats.t=84351380); "
    "used stats.t/game.time to know 84351300 was publishable (waited until live stats.t>=84351440); single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84351380 / path_arrivals through 84351368 at pre-check); "
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
            "first-interval 4.76190 printed 4.762 was sane; later-mean-robust 4.73175 already inside the 45s gate versus first-aligned rows "
            f"(over45 later={vs_later_before} vs first={vs_first_over45}, delta 0.03015 s/tick ~23.8s at tmin); "
            f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')} "
            f"(lowest_over45 among sane was {tick_s.get('lowest_over45_sane')}); "
            "no corrective realign; in-use first-interval 4.76190"
        ),
    },
    "just_published": {
        "base": 84351300,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "10:36:11",
        "recovered_game_time": 84351443,
        "inserted": INSERTED_JUST,
        "note": "waited until live stats.t>=84351440; first try 10:36:11 game.time=84351443 recovered all 5 rooms official 200, inserted=3119, already_in_db=1062, ticks 84351301..84351400. Also retried leftover W47N7@84350700, still official 404.",
        "first_try_all_404": False,
        "first_try_at": "10:36:11",
        "first_try_game_time": 84351443,
        "first_try_recovered": ["W46N8", "W47N8", "W45N8", "W45N7", "W47N7"],
        "first_try_still_404": [],
        "retry_at": None,
        "retry_game_time": None,
        "retry_inserted": 0,
        "ticks": "84351301..84351400",
        "all_five_official_200": True,
        "still_404": [],
        "in_window_still_404": ["W47N7@84350700"],
        "w45n7_empty_no_creep": [],
        "w47n7_empty_no_creep": [[84351066, 84351066], [84351068, 84351187]],
        "distinct": {"W46N8": 100, "W47N8": 100, "W45N8": 100, "W45N7": 100, "W47N7": 100},
    },
    "confirm": {
        "at": "10:33:15",
        "game_time": 84351407,
        "inserted": 0,
        "ssl_abort_first": None,
        "targets": 1,
        "recovered": [],
        "still_404": ["W47N7@84350700"],
        "note": "confirm 10:33:15 game.time=84351407 still official 404 W47N7@84350700 (neighbors @84350600/@84350800 both 200, db 0/0)",
    },
    "retry2": {
        "at": "10:35:35",
        "game_time": 84351435,
        "inserted": 0,
        "skipped": False,
        "still_404": ["W47N7@84350700"],
        "note": "retry2 10:35:35 game.time=84351435 still official 404 W47N7@84350700; just-published also retried it at 10:36:11 game.time=84351443 still 404",
    },
    "in_window_404": {
        "W47N7@84350700": {
            "ticks": "84350701..84350800",
            "neighbors_200": ["W47N7@84350600", "W47N7@84350800"],
            "db_distinct": 0,
            "retried": ["confirm 10:33:15 gt=84351407", "retry2 10:35:35 gt=84351435", "just_published 10:36:11 gt=84351443"],
            "still_official_404": True,
        }
    },
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 767225,
        "loop_pid": 4035476,
        "restart_at": "10:23:07",
        "listener_started": "10:23:17",
        "this_run_restarted": False,
        "waited_for_reconnect": False,
        "live_objects_empty_after_reconnect": False,
        "pre_cpu_path_after_wait": "creep_cpu through 84351380 / path_arrivals through 84351368 at pre-check 10:31:27; listener.py pid 767225 started 10:23:17 after run_listener.sh auto-restart 10:23:07; wrapup creep_cpu through 84351440 / path_arrivals through 84351438; live.json fresh (stats.t=84351450, roomSlot W47N8 after rotation, objects_n=0 / gameTime 84351401 at wrapup) and buffers flowing",
    },
    "box_freeze": {
        "from": "2026-11-19 10:09:26",
        "to": "2026-11-19 10:23:04",
        "sec": 818,
        "restart_at": "10:23:07",
        "room_stats_gap": "84351101..84351289",
        "official_filled": "gap 84351101..84351289 official-filled 189/189 in W46N8, W47N8, W45N8, W45N7; W47N7 102/189 because official empty-no-creep 84351101..84351187 (87 ticks, part of 84351068..84351187)",
        "earlier_freeze": {
            "from": "2026-11-19 09:45:54",
            "to": "2026-11-19 09:57:01",
            "sec": 667,
            "restart_at": "09:57:04",
            "room_stats_gap": "84350801..84350959",
            "official_filled": "already official-filled last 10:00 half-hour (159/159 in all 5 rooms)",
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
    f"missing_chunks={MISSING_CHUNKS} in_window_404=W47N7@84350700 still official 404 after confirm/retry2/just-published; final official_404={official_404_missing} empty_no_creep={empty_no_creep}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    "just-published 84351300 first try 10:36:11 game.time=84351443 recovered 5/5 rooms official 200 inserted=3119 ticks 84351301..84351400; leftover official 404 in window: W47N7@84350700 hole 84350701..84350800 (db 0/0) after confirm, retry2, and just-published retry.",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not restart the listener.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1030.txt")
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
