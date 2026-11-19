#!/usr/bin/env python3
"""Write local status records for the 12:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-19_1200"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84351801, 84352500
PUB_BASES = "84351800..84352400"
GT_FIRST = 84352559
TICK_S_FIRST = 4.70111
TICK_S_PRINTED = "4.701"
TICK_S_IN_USE = 4.70111
TICK_S_LATER = 4.73643
TS_REALIGNED_FIRST = 0
NFIX_CORR = 0
GT_CORR = 84352581  # tick_s check at game.time=84352581; no corrective realign
RECON_ROWS = 25317
ALREADY = 12072
INSERTED_FIRST = 13245
INSERTED_CONFIRM = 0  # confirm 12:06:08 gt=84352583 still official 404 W47N8@84352400
INSERTED_RETRY2 = 0  # retry2 12:08:35 gt=84352613 still official 404
INSERTED_JUST = 0  # 84352500 not attempted (first-pass game.time=84352559 still in-progress)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/4192new W47N8:600t/3130new W45N8:700t/2133new W45N7:700t/1640new W47N7:700t/2150new"
FIRST_PASS_LINE = (
    "first pass 34 of 35 official GETs 200, missing_chunks=1 W47N8@84352400; "
    "11:30 half-hour already wrote through 84352100 (just-published 84352100 was not attempted then and is included in this overlap); "
    "(this pass already_in_db=12072 / inserted=13245, including newly published 84352100..84352400 except W47N8@84352400); "
    "leftover official 404 W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out of this 40-min window; "
    "W47N8@84352400 still official 404 after confirm 12:06:08 game.time=84352583 and retry2 12:08:35 game.time=84352613 (neighbors @84352300 and other rooms @84352400 both official 200; live listener later wrote 6 ticks 84352495..84352500); "
    "just-published 84352500 not attempted (first-pass game.time=84352559 still inside the in-progress chunk)"
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
    "in-window official 404 after first pass: W47N8@84352400 hole 84352401..84352494 (94 ticks; live listener later wrote 84352495..84352500, db distinct=6/100 in that chunk before confirm); "
    "first pass 34 of 35 official GETs 200, missing_chunks=1; "
    "confirm 12:06:08 game.time=84352583 still official 404 (db 6/100, range 84352495..84352500); "
    "retry2 12:08:35 game.time=84352613 still official 404; "
    "neighbors @84352300 and other rooms @84352400 official 200; "
    "final official_404_in_window=94"
)
leftover_txt = (
    "in-window official 404 still open: W47N8@84352400 hole 84352401..84352494 (94 ticks, live 6 ticks 84352495..84352500) after confirm and retry2; "
    "no official empty-no-creep in this window; "
    "aged leftover official 404 W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 were not retried this pass "
    "(already outside this 40-min window, along with older W45N8@84346100, W45N7@84345800, W45N8@84344700, W47N8@84343800, W45N8@84343100, W47N8@84343400, W47N8@84343000, W45N7@84342300, W47N7@84342500, W45N8@84341100)."
)
confirm_summary = (
    "confirm 12:06:08 game.time=84352583 still official 404 W47N8@84352400 inserted=0; "
    "retry2 12:08:35 game.time=84352613 still official 404 inserted=0; "
    "just-published 84352500 not attempted (first-pass game.time=84352559 still inside the in-progress 84352500 chunk; next half-hour overlap will catch it)"
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
    f"(delta first-robust -0.03532 s/tick, ~26.8s at tmin; "
    f"over45 later={vs_later_before} vs first={vs_first_over45}, over15 later={vs_later_over15_before} vs first={vs_first_over15}; "
    f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')}; "
    f"lowest_over45 among sane was {tick_s.get('lowest_over45_sane')}); "
    f"no corrective realign (later-mean already inside 45s gate, nfix=0); "
    f"still_over_45s_vs_later={tick_s.get('still_over_45s_vs_later')}; skipped_cross_chunk={tick_s.get('skipped_cross_chunk')}; "
    f"in-use first-interval {TICK_S_IN_USE:.5f}; "
    f"subsequent confirm/retry2 used first-interval {TICK_S_IN_USE:.5f} (confirm/retry2 inserted=0; just-published not attempted)"
)
import time as _time
_live_age = _time.time() - (ROOT / "metrics" / "live.json").stat().st_mtime
_stats = live.get("stats") or {}
_cpu_tip = _path_tip = None
with db.connect() as _c:
    _cpu_tip = _c.execute("select max(tick) from creep_cpu").fetchone()[0]
    _path_tip = _c.execute("select max(tick) from path_arrivals").fetchone()[0]

freeze_para = (
    "New box freeze this run 11:36:36-11:58:55 (1339s); also earlier 11:11:06-11:18:54 (467s), 10:40:36-11:03:20 (1359s), 10:09:26-10:23:04 (818s), 09:45:54-09:57:01 (667s), 05:33:25-09:22:55 (13764s), 05:17:00-05:26:03 (542s), 04:45:45-04:58:24 (749s), 03:45:22-04:05:50 (1228s), 03:10:01-03:17:13 (431s), 02:45:55-02:57:12 (671s). "
    "Listener last auto-restart 12:02:12 after a ws ping/pong timeout at 12:02:09 (run_listener.sh auto-restart, not this run; listener.py pid 793156 started 12:02:22; run_listener.sh pid 4035476). Prior auto-restart 11:58:58 after the 11:36:36-11:58:55 freeze. "
    "This run did not restart the listener; it was already up after that auto-restart and pulling segment-90 CPU/path buffers itself "
    "(pre-check 12:02:53 live.json age ~2.2s, stats.t=84352540, roomSlot W45N7 objects_n=0 / gameTime None, mid 5:5:1:1 rotation; "
    "creep_cpu through 84352530 / path_arrivals through 84352513; "
    f"by wrapup live.json age ~{_live_age:.1f}s, stats.t={_stats.get('t')}, roomSlot {live.get('roomSlot')}, objects_n={len(live.get('objects') or [])} / gameTime {live.get('gameTime')}, creep_cpu through {_cpu_tip} / path_arrivals through {_path_tip}). "
    "11:30 half-hour already official-filled 84351401..84352100 (inserted_window=2840, coverage 3500/3500, missing_chunks=0; just-published 84352100 was not attempted then and is included in this overlap). "
    "room_stats gap 84352201..84352499 (299, from the 11:36:36-11:58:55 freeze) sits inside this 40-min window and is official-filled 299/299 in W46N8, W45N8, W45N7, W47N7; W47N8 205/299 because leftover official 404 W47N8@84352400 hole 84352401..84352494 (94 ticks; live later wrote 84352495..84352500); "
    "older room_stats gap 84351881..84351989 (109, from the 11:11:06-11:18:54 freeze) also sits inside this window and remains official-filled 109/109 in all 5 rooms (already filled last 11:30 half-hour); "
    "older room_stats gaps 84351491..84351789 and 84351101..84351289 have now aged out of this window (already official-filled earlier); "
    "older room_stats gap 84350801..84350959 was already official-filled earlier; older room_stats gaps 84347621..84350529, 84346261..84346529 and 84347021..84347189 remain outside this window. "
    "Aged official 404 W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) remain outside this window. "
    "live.json / stats.t were fresh at pre-check (age ~2.2s, tip stats.t=84352540); "
    "just-published 84352500 was not yet publishable (game.time=84352559 at first pass); this pass recovered published 84352100 (left unattempted last 11:30 run) plus 84352200..84352400 except W47N8@84352400; single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84352530 / path_arrivals through 84352513 at pre-check); "
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
            "first-interval 4.70111 printed 4.701 was sane and first-aligned rows already had over45=0 versus the live anchor; "
            "later-mean-robust 4.73643 was already inside the 45s gate versus those first-aligned rows "
            f"(over45 later={vs_later_before} vs first={vs_first_over45}, delta -0.03532 s/tick ~26.8s at tmin); "
            f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')} "
            f"(lowest_over45 among sane was {tick_s.get('lowest_over45_sane')}); "
            "no corrective realign; in-use first-interval 4.70111; still_over_45s_vs_later=0"
        ),
    },
    "just_published": {
        "base": 84352500,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": None,
        "recovered_game_time": None,
        "inserted": INSERTED_JUST,
        "note": "not attempted; first-pass game.time=84352559 was still inside the in-progress 84352500 chunk (typically publishable around game.time>=84352640). This --minutes 40 pass recovered published 84352100 (left unattempted last 11:30 run) plus 84352200..84352400 except W47N8@84352400. Next half-hour 10-min overlap will catch 84352500 and retry W47N8@84352400.",
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
        "in_window_still_404": ["W47N8@84352400"],
        "w45n7_empty_no_creep": [],
        "w47n7_empty_no_creep": [],
        "distinct": None,
        "skipped": True,
    },
    "confirm": {
        "at": "12:06:08",
        "game_time": 84352583,
        "inserted": 0,
        "ssl_abort_first": None,
        "targets": 1,
        "recovered": [],
        "still_404": ["W47N8@84352400"],
        "skipped": False,
        "note": "confirm 12:06:08 game.time=84352583 still official 404 W47N8@84352400; db already had live 6 ticks 84352495..84352500",
    },
    "retry2": {
        "at": "12:08:35",
        "game_time": 84352613,
        "inserted": 0,
        "skipped": False,
        "still_404": ["W47N8@84352400"],
        "note": "retry2 12:08:35 game.time=84352613 still official 404 W47N8@84352400",
    },
    "in_window_404": {"W47N8@84352400": "84352401..84352494"},
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 793156,
        "loop_pid": 4035476,
        "restart_at": "12:02:12",
        "listener_started": "12:02:22",
        "this_run_restarted": False,
        "waited_for_reconnect": False,
        "live_objects_empty_after_reconnect": False,
        "pre_cpu_path_after_wait": "creep_cpu through 84352530 / path_arrivals through 84352513 at pre-check 12:02:53; listener.py pid 793156 started 12:02:22 after run_listener.sh auto-restart 12:02:12 (following ws ping/pong timeout 12:02:09, itself after auto-restart 11:58:58 following the 11:36:36-11:58:55 freeze); wrapup creep_cpu/path tips recorded in freeze_para; live.json fresh (stats.t advancing, single_slot 5:5:1:1 rotating, objects_n=0 at pre-check mid-rotation) and buffers flowing",
    },
    "box_freeze": {
        "from": "2026-11-19 11:36:36",
        "to": "2026-11-19 11:58:55",
        "sec": 1339,
        "restart_at": "11:58:58",
        "room_stats_gap": "84352201..84352499",
        "official_filled": "gap 84352201..84352499 official-filled 299/299 in W46N8, W45N8, W45N7, W47N7; W47N8 205/299 because leftover official 404 W47N8@84352400 hole 84352401..84352494",
        "earlier_freeze": {
            "from": "2026-11-19 11:11:06",
            "to": "2026-11-19 11:18:54",
            "sec": 467,
            "restart_at": "11:18:57",
            "room_stats_gap": "84351881..84351989",
            "official_filled": "already official-filled last 11:30 half-hour (109/109 in all 5 rooms); gap still sits inside this 40-min window and remains official-filled 109/109",
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
    f"missing_chunks={MISSING_CHUNKS} in_window_404=W47N8@84352400 hole 84352401..84352494; final official_404={official_404_missing} empty_no_creep={empty_no_creep}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    "just-published 84352500 not attempted (first-pass game.time=84352559 still inside the in-progress chunk); leftover official 404 in window: W47N8@84352400 hole 84352401..84352494 after confirm/retry2.",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not restart the listener.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1200.txt")
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
