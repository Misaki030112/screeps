#!/usr/bin/env python3
"""Write local status records for the 10:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-19_1000"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84350201, 84350900
PUB_BASES = "84350200..84350800"
GT_FIRST = 84350985
TICK_S_FIRST = 4.81040
TICK_S_PRINTED = "4.810"
TICK_S_IN_USE = 4.73430
TICK_S_LATER = 4.73430
TS_REALIGNED_FIRST = 13898
NFIX_CORR = 8381
GT_CORR = 84351007
RECON_ROWS = 26011
ALREADY = 19789
INSERTED_FIRST = 6222
INSERTED_CONFIRM = 0  # confirm 10:01:19 gt=84351009 still official 404 W47N7@84350700
INSERTED_RETRY2 = 0  # retry2 10:03:21 gt=84351034 still official 404
INSERTED_JUST = 3529  # just-published 84350900 5/5 rooms at 10:03:57 gt=84351042 (84350901..84351000)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/1229new W47N8:700t/2841new W45N8:700t/996new W45N7:700t/736new W47N7:600t/420new"
FIRST_PASS_LINE = (
    "first pass 34 of 35 official GETs 200, missing_chunks=1 W47N7@84350700; "
    "09:30 half-hour already wrote through 84350700 and confirm-recovered W47N8/W47N7@84350600; "
    "(this pass already_in_db=19789 / inserted=6222); "
    "leftover official 404 W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out of this 40-min window; "
    "W47N7@84350700 still official 404 after confirm 10:01:19 game.time=84351009, retry2 10:03:21 game.time=84351034, and just-published 10:03:57 game.time=84351042"
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
    "confirm 10:01:19 game.time=84351009 still official 404 (db 0/0); "
    "retry2 10:03:21 game.time=84351034 still official 404; "
    "just-published also retried W47N7@84350700 at 10:03:57 game.time=84351042 still official 404; "
    "neighbors @84350600/@84350800 both official 200; "
    "final official_404_in_window=100"
)
leftover_txt = (
    "in-window official 404 still open: W47N7@84350700 hole 84350701..84350800 (100 ticks, db 0/0) after confirm, retry2, and just-published retry; "
    "aged leftover official 404 W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 were not retried this pass "
    "(already outside this 40-min window, along with older W45N8@84346100, W45N7@84345800, W45N8@84344700, W47N8@84343800, W45N8@84343100, W47N8@84343400, W47N8@84343000, W45N7@84342300, W47N7@84342500, W45N8@84341100)."
)
confirm_summary = (
    "confirm 10:01:19 game.time=84351009 still official 404 W47N7@84350700 inserted=0; "
    "retry2 10:03:21 game.time=84351034 still official 404 inserted=0; "
    "just-published 84350900 first try 10:03:57 game.time=84351042 recovered 5/5 rooms inserted=3529 "
    "(waited until live stats.t>=84351040); leftover W47N7@84350700 still official 404"
)
vs_later_before = (tick_s.get("still_over_45s_vs_later_before"))
vs_first_over45 = vs_first.get("over45")
vs_later_over15_before = tick_s.get("still_over_15s_vs_later_before")
vs_first_over15 = vs_first.get("over15")
span_vs = (vs_cand.get("span_mean") or {})
prev_vs = (vs_cand.get("prev_later") or {})
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} was over the 45s gate versus first-aligned rows "
    f"(delta first-robust 0.06076 s/tick, ~47.6s at tmin; "
    f"over45 later={vs_later_before} vs first={vs_first_over45}, over15 later={vs_later_over15_before} vs first={vs_first_over15}; "
    f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')}; "
    f"lowest_over45 among sane was {tick_s.get('lowest_over45_sane')}); "
    f"applied corrective later-mean-robust realign of {NFIX_CORR} rows at game.time={GT_CORR}; "
    f"still_over_45s_vs_later={tick_s.get('still_over_45s_vs_later')}; skipped_cross_chunk={tick_s.get('skipped_cross_chunk')}; "
    f"in-use later-mean-robust {TICK_S_IN_USE:.5f}; "
    f"subsequent confirm/retry2/just-published inserts used later-mean-robust {TICK_S_IN_USE:.5f} (confirm/retry2 inserted=0; just ts_realigned=0)"
)
freeze_para = (
    "New box freeze this run 09:45:54-09:57:01 (667s); also earlier 05:33:25-09:22:55 (13764s), 05:17:00-05:26:03 (542s), 04:45:45-04:58:24 (749s), 03:45:22-04:05:50 (1228s), 03:10:01-03:17:13 (431s), 02:45:55-02:57:12 (671s). "
    "Listener last auto-restart 09:57:04 after that wake (run_listener.sh auto-restart, not this run; listener.py pid 760828 started 09:57:13; run_listener.sh pid 4035476). "
    "This run did not restart the listener; it was already up after that auto-restart and pulling segment-90 CPU/path buffers itself "
    "(pre-check 09:59:10 live.json age ~4.6s, stats.t=84350980, roomSlot W47N8 objects_n=0 / gameTime None; "
    "creep_cpu through 84350970 / path_arrivals through 84350953; "
    "by wrapup live.json age ~3s, stats.t=84351040, roomSlot W47N8, objects_n=0 / gameTime still None, creep_cpu through 84351040 / path_arrivals through 84351033). "
    "live.json gameTime/objects stayed empty after the reconnect, but stats.t, room_stats, creep_cpu and path_arrivals were flowing and the single W47N8 slot was held. "
    "09:30 half-hour already official-filled 84350001..84350700 (inserted_window=2955, coverage 3500/3500). "
    "room_stats gap 84350801..84350959 (159, from the 09:45:54-09:57:01 freeze) sits inside this 40-min window plus the just-published 84350900 chunk and is official-filled 159/159 in all 5 rooms; "
    "older room_stats gaps 84347621..84350529, 84346261..84346529 and 84347021..84347189 remain outside this window. "
    "Aged official 404 W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) remain outside this window. "
    "live.json / stats.t were fresh at pre-check (age ~4.6s, tip stats.t=84350980); "
    "used stats.t/game.time to know 84350900 was publishable (waited until live stats.t>=84351040); single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84350970 / path_arrivals through 84350953 at pre-check); "
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
            "first-interval 4.81040 printed 4.810 was sane; later-mean-robust 4.73430 was over the 45s gate versus first-aligned rows "
            f"(over45 later={vs_later_before} vs first={vs_first_over45}, delta 0.06076 s/tick ~47.6s at tmin); "
            f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')} "
            f"(lowest_over45 among sane was {tick_s.get('lowest_over45_sane')}); "
            "applied corrective later-mean-robust realign of 8381 rows at game.time=84351007; still_over_45s_vs_later=0; in-use later-mean-robust 4.73430"
        ),
    },
    "just_published": {
        "base": 84350900,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "10:03:57",
        "recovered_game_time": 84351042,
        "inserted": INSERTED_JUST,
        "note": "waited until live stats.t>=84351040; first try 10:03:57 game.time=84351042 recovered all 5 rooms official 200, inserted=3529, already_in_db=699, ticks 84350901..84351000. Also retried leftover W47N7@84350700, still official 404.",
        "first_try_all_404": False,
        "first_try_at": "10:03:57",
        "first_try_game_time": 84351042,
        "first_try_recovered": ["W46N8", "W47N8", "W45N8", "W45N7", "W47N7"],
        "first_try_still_404": [],
        "retry_at": None,
        "retry_game_time": None,
        "retry_inserted": 0,
        "ticks": "84350901..84351000",
        "all_five_official_200": True,
        "still_404": [],
        "in_window_still_404": ["W47N7@84350700"],
        "w45n7_empty_no_creep": [],
        "w47n7_empty_no_creep": [],
        "distinct": {"W46N8": 100, "W47N8": 100, "W45N8": 100, "W45N7": 100, "W47N7": 100},
    },
    "confirm": {
        "at": "10:01:19",
        "game_time": 84351009,
        "inserted": 0,
        "ssl_abort_first": None,
        "targets": 1,
        "recovered": [],
        "still_404": ["W47N7@84350700"],
        "note": "confirm 10:01:19 game.time=84351009 still official 404 W47N7@84350700 (neighbors @84350600/@84350800 both 200, db 0/0)",
    },
    "retry2": {
        "at": "10:03:21",
        "game_time": 84351034,
        "inserted": 0,
        "skipped": False,
        "still_404": ["W47N7@84350700"],
        "note": "retry2 10:03:21 game.time=84351034 still official 404 W47N7@84350700; just-published also retried it at 10:03:57 game.time=84351042 still 404",
    },
    "in_window_404": {
        "W47N7@84350700": {
            "ticks": "84350701..84350800",
            "neighbors_200": ["W47N7@84350600", "W47N7@84350800"],
            "db_distinct": 0,
            "retried": ["confirm 10:01:19 gt=84351009", "retry2 10:03:21 gt=84351034", "just_published 10:03:57 gt=84351042"],
            "still_official_404": True,
        }
    },
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 760828,
        "loop_pid": 4035476,
        "restart_at": "09:57:04",
        "listener_started": "09:57:13",
        "this_run_restarted": False,
        "waited_for_reconnect": True,
        "live_objects_empty_after_reconnect": True,
        "pre_cpu_path_after_wait": "creep_cpu through 84350970 / path_arrivals through 84350953 at pre-check 09:59:10; listener.py pid 760828 started 09:57:13 after run_listener.sh auto-restart 09:57:04; wrapup creep_cpu through 84351040 / path_arrivals through 84351033; live.json gameTime/objects still empty at wrapup but stats.t fresh and buffers flowing",
    },
    "box_freeze": {
        "from": "2026-11-19 09:45:54",
        "to": "2026-11-19 09:57:01",
        "sec": 667,
        "restart_at": "09:57:04",
        "room_stats_gap": "84350801..84350959",
        "official_filled": "gap 84350801..84350959 official-filled 159/159 in all 5 rooms (first-pass 84350800 chunk plus just-published 84350900)",
        "earlier_freeze": {
            "from": "2026-11-19 05:33:25",
            "to": "2026-11-19 09:22:55",
            "sec": 13764,
            "restart_at": "09:22:58",
            "room_stats_gap": "84347621..84350529",
            "official_filled": "already outside this 40-min window; 09:22 patrol / 09:30 half-hour covered the in-window portion then",
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
    "just-published 84350900 first try 10:03:57 game.time=84351042 recovered 5/5 rooms official 200 inserted=3529 ticks 84350901..84351000; leftover official 404 in window: W47N7@84350700 hole 84350701..84350800 (db 0/0) after confirm, retry2, and just-published retry.",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not restart the listener.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1000.txt")
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
