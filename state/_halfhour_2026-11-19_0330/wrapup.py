#!/usr/bin/env python3
"""Write local status records for the 03:30 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-19_0330"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84345301, 84346000
PUB_BASES = "84345300..84345900"
GT_FIRST = 84346087
TICK_S_FIRST = 4.67351
TICK_S_PRINTED = "4.674"
TICK_S_IN_USE = 4.77931
TICK_S_LATER = 4.77931
TS_REALIGNED_FIRST = 15982
NFIX_CORR = 15982
GT_CORR = 84346106  # corrective later-mean-robust realign of 15982 rows
RECON_ROWS = 25626
ALREADY = 22600
INSERTED_FIRST = 3026
INSERTED_CONFIRM = 0  # confirm 03:33:45 gt=84346117 still official 404 W45N7@84345800
INSERTED_RETRY2 = 0  # retry2 03:34:43 gt=84346129 still official 404 W45N7@84345800
INSERTED_JUST = 2833  # first try 03:35:46 game.time=84346143 recovered 5/5 just-base; leftover W45N7@84345800 still 404
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/905new W47N8:700t/935new W45N8:700t/363new W45N7:600t/313new W47N7:700t/510new"
FIRST_PASS_LINE = (
    "first pass 34 of 35 official GETs 200, missing_chunks=1 W45N7@84345800; "
    "hourly_patrol_prefilled=true from 03:17 patrol official already through 84345800 / reconstructed through 84345900 "
    "(W47N7@84345800 recovered on patrol retry2; W45N7@84345800 still official 404 after patrol retry2) "
    "(overlap of this window); "
    "03:00 half-hour already wrote through 84345500 and just-published 84345600 (84345601..84345700) for all 5 rooms "
    "(this pass already_in_db=22600 / inserted=3026); "
    "leftover official 404 W45N8@84344700 already aged out of this 40-min window; "
    "W45N7@84345800 still official 404 after confirm/retry2/just-published retry"
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
    "in-window official 404: W45N7@84345800 hole 84345801..84345900; "
    "first pass 34 of 35 official GETs 200, missing_chunks=1; "
    "confirm 03:33:45 game.time=84346117 still 404; retry2 03:34:43 game.time=84346129 still 404; "
    "just-published 84346000 first try 03:35:46 game.time=84346143 recovered 5/5, leftover W45N7@84345800 still official 404 (neighbors @84345700/@84345900 both 200, db 0/0); "
    "final official_404_in_window=100"
)
leftover_txt = (
    "in-window official 404 still open: W45N7@84345800 (84345801..84345900) after confirm/retry2/just_published; "
    "aged leftover official 404 W45N8@84344700 was not retried this pass "
    "(already outside this 40-min window, along with older W47N8@84343800, W45N8@84343100, W47N8@84343400, W47N8@84343000, W45N7@84342300, W47N7@84342500, W45N8@84341100)."
)
confirm_summary = (
    "confirm 03:33:45 game.time=84346117 still official 404 W45N7@84345800 inserted=0; "
    "retry2 03:34:43 game.time=84346129 still 404 inserted=0; "
    "just-published 84346000 first try at 03:35:46 game.time=84346143 recovered 5/5 rooms inserted=2833 "
    "(after this window; W46N8/W47N8/W45N8/W45N7/W47N7 distinct=100, already_in_db=960); "
    "leftover retry W45N7@84345800 still official 404; in-window official 404 still open: W45N7@84345800"
)
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} was outside the 45s gate versus first-aligned rows "
    f"(delta first-robust -0.10326 s/tick from W46 first 4.67605, ~81.2s at tmin; min-all first 4.67351 vs later is -0.10580 s/tick, ~83.2s; "
    f"over45 later=15982 vs first=0, over15 later=19254 vs first=9517; "
    f"prev_later 4.82433 also over45=15982 with worse mean_off; lowest_over45 among sane was first); "
    f"applied corrective later-mean-robust realign of 15982 rows at game.time=84346106; still_over_45s_vs_later=0; skipped_cross_chunk=0; "
    f"in-use later-mean-robust {TICK_S_IN_USE:.5f}; "
    f"subsequent just-published inserts used later-mean-robust {TICK_S_IN_USE:.5f} (ts_realigned=0)"
)
freeze_para = (
    "Listener restart 03:17:16 (box wake after freeze 03:10:01-03:17:13 (431s); also earlier restarts 02:57:15 after freeze 02:45:55-02:57:12 (671s), 02:17:50 after freeze 02:16:19-02:17:47 (79s), 01:58:08 after freeze 01:48:36-01:58:05 (564s) and 01:35:48 after freeze 01:31:02-01:35:45 (283s); "
    "run_listener.sh auto-restart, not this run; pid 696769). "
    "New room_stats gap 84345811..84345919 (109); official-filled 109/109 in W46N8/W47N8/W45N8/W47N7; "
    "W45N7 19/109 missing 90 because official 404 W45N7@84345800 covers 84345811..84345900 (84345901..84345919 official-filled). "
    "This run did not restart the listener. "
    "Earlier room_stats gap 84345511..84345659 (149) remains official-filled 149/149 all five. "
    "Earlier room_stats gap 84345141..84345169 (29) remains official-filled 29/29 all five (now aged out of this 40-min window). "
    "Earlier room_stats gap 84344781..84344919 (139) remains official-filled 139/139 in W46N8/W47N8/W45N7; "
    "W45N8 119/139 missing 20 because official 404 W45N8@84344700 covers 84344781..84344800 (now aged out of this 40-min window); "
    "W47N7 26/139 because official empty-no-creep covers 84344804..84344842, 84344844..84344878, 84344880..84344916 (plus 84344918..84344919; this gap is now aged out of this 40-min window). "
    "Aged official 404 W45N8@84344700 (and older W47N8@84343800, W45N8@84343100, W47N8@84343400, W47N8@84343000, W45N7@84342300, W47N7@84342500, W45N8@84341100) remain outside this window. "
    "live.json / stats.t were fresh at pre-check (age ~0.0s, tip stats.t=84346080, roomSlot W46N8, objects_n=262, gameTime 84346083); "
    "used stats.t to know 84346000 was publishable; single_slot held, creep_cpu and path_arrivals flowing after reconnect (creep_cpu through 84346070 / path_arrivals through 84346070 at pre-check); "
    "this run did not restart the listener."
)
ok_line = (
    f"ok_quiet=True coverage={recovered}/{expected} inserted_window={INSERTED_WINDOW} "
    f"inserted_total={INSERTED_TOTAL} tick_s_in_use={TICK_S_IN_USE:.5f} "
    "listener single_slot=True; no second listener; no war_cmd/pulse restart."
)
single = (not yield_present)
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
    f"coverage official_recovered={recovered}/{expected} unique_after={unique_after.get('unique_creep_tick_rows') or unique_after} empty_no_creep={empty_no_creep} official_404_in_window={official_404_missing}",
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
        "prev_later_over45_before_corrective": 15982,
        "prev_later_mean": 4.82433,
        "note": "first-interval 4.67351 was sane (over45=0, lowest_over45 among sane); later-mean-robust 4.77931 had over45=15982 vs first-aligned rows (prev_later 4.82433 also over45=15982); established check applied corrective later-mean-robust realign of 15982 rows at game.time=84346106; after later over45=0; in-use later-mean-robust 4.77931",
    },
    "just_published": {
        "base": 84346000,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "03:35:46",
        "recovered_game_time": 84346143,
        "inserted": INSERTED_JUST,
        "inserted_first_two": None,
        "inserted_remaining_three": None,
        "first_try_all_404": False,
        "first_try_at": "03:35:46",
        "first_try_game_time": 84346143,
        "first_try_recovered": ["W46N8", "W47N8", "W45N8", "W45N7", "W47N7"],
        "first_try_still_404": ["W45N7@84345800"],
        "retry_at": None,
        "retry_game_time": None,
        "retry_inserted": 0,
        "already_in_db": 960,
        "ticks": "84346001..84346100",
        "all_five_official_200": True,
        "still_404": ["W45N7@84345800"],
        "in_window_still_404": ["W45N7@84345800"],
        "w45n7_empty_no_creep": [],
        "w47n7_empty_no_creep": [],
        "distinct": {"W46N8": 100, "W47N8": 100, "W45N8": 100, "W45N7": 100, "W47N7": 100},
    },
    "confirm": {
        "at": "03:33:45",
        "game_time": 84346117,
        "inserted": 0,
        "ssl_abort_first": None,
        "targets": 1,
        "recovered": [],
        "still_404": ["W45N7@84345800"],
        "note": "confirm still official 404 W45N7@84345800 at 03:33:45 game.time=84346117; neighbors @84345700/@84345900 both 200; db 0/0 hole 84345801..84345900; leftover from 03:17 patrol still in-window",
    },
    "retry2": {"at": "03:34:43", "game_time": 84346129, "inserted": 0, "skipped": False, "still_404": ["W45N7@84345800"]},
    "in_window_404": {"W45N7@84345800": "84345801..84345900 still official 404 after confirm/retry2/just_published"},
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 696769,
        "restart_at": "03:17:16",
        "this_run_restarted": False,
    },
    "box_freeze": {
        "from": "2026-11-19 03:10:01",
        "to": "2026-11-19 03:17:13",
        "sec": 431,
        "earlier_freeze": {
            "from": "2026-11-19 02:45:55",
            "to": "2026-11-19 02:57:12",
            "sec": 671,
            "restart_at": "02:57:15",
            "room_stats_gap": "84345511..84345659",
            "official_filled": "all five 149/149",
        },
        "room_stats_gap": "84345811..84345919",
        "official_filled": "W46N8/W47N8/W45N8/W47N7 109/109; W45N7 19/109 missing 90 due to official 404 W45N7@84345800 covering 84345811..84345900",
        "prior_in_window_gap": "84345511..84345659 official-filled 149/149 all five; 84345141..84345169 official-filled 29/29 all five (aged out of this window); 84344781..84344919 official-filled 139/139 in W46N8/W47N8/W45N7, W45N8 119/139 missing 20 due to aged official 404 W45N8@84344700 (hole now outside this window), W47N7 26/139 official empty-no-creep (gap now aged out of this window)",
        "new_freeze_this_run": True,
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
    f"missing_chunks={MISSING_CHUNKS} in_window_404=W45N7@84345800; final official_404={official_404_missing} empty_no_creep={empty_no_creep}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    "just-published 84346000 first try 03:35:46 game.time=84346143 recovered 5/5 inserted=2833 (W46N8/W47N8/W45N8/W45N7/W47N7 distinct=100/100); leftover W45N7@84345800 still official 404 after confirm/retry2/just_published (db 0/0).",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not restart the listener.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0330.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run_tee.txt").write_text(summary + now_text)
(DIR / "wrapup_run_stdout.txt").write_text(summary + f"now_text_bytes {len(now_text)}\n")
print(summary, end="")
print("now_text_bytes", len(now_text))
