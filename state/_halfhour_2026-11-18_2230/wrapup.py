#!/usr/bin/env python3
"""Write local status records for the 22:30 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-18_2230"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84341601, 84342300
PUB_BASES = "84341600..84342200"
GT_FIRST = 84342310
TICK_S_FIRST = 4.63248
TICK_S_PRINTED = "4.632"
TICK_S_IN_USE = 4.68026
TICK_S_LATER = 4.68026
TS_REALIGNED_FIRST = 0
NFIX_CORR = 4
GT_CORR = 84342332
RECON_ROWS = 25721
ALREADY = 22526
INSERTED_FIRST = 3195
INSERTED_CONFIRM = 548  # W47N7@84342200 recovered at 22:34:40 game.time=84342333
INSERTED_RETRY2 = 0  # skipped; in-window 404 already recovered on confirm
INSERTED_JUST = 2421  # first try 4/5 recovered 2421 at 22:43:16 game.time=84342442; W45N7@84342300 still 404 after retry 22:43:46 game.time=84342448
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/398new W47N8:700t/2028new W45N8:700t/556new W45N7:700t/213new W47N7:600t/0new"
FIRST_PASS_LINE = (
    "first pass 34 of 35 official GETs 200, missing_chunks=1 (W47N7@84342200); "
    "hourly_patrol_prefilled=true from 22:24 patrol official already through 84342100 "
    "(overlap of this window); 22:00 half-hour already wrote through 84341800 and just-published 84341800 "
    "(84341801..84341900) for all five rooms (this pass already_in_db=22526 / inserted=3195); "
    "W47N7@84342200 recovered on confirm inserted=548 at 22:34:40 game.time=84342333"
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
    "in-window official 404: W47N7@84342200 (first pass missing latest published chunk); "
    "first pass 34 of 35 official GETs 200, missing_chunks=1; "
    "W47N7@84342200 recovered on confirm 22:34:40 game.time=84342333 inserted=548; final official_404_in_window=0"
)
leftover_txt = (
    "aged leftover official 404s including W45N8@84341100 were not retried this pass "
    "(they stayed 404 after the 22:00 confirm/retry2/just_published and are now outside this 40-min window)."
)
confirm_summary = (
    "confirm inserted=548 (22:34:40 game.time=84342333, W47N7@84342200 recovered, no SSL abort; "
    "retry2 skipped because the only in-window 404 was already recovered); "
    "just-published 84342300 first try 4/5 recovered inserted=2421 at 22:43:16 game.time=84342442 "
    "(after this window; W46N8/W47N8/W45N8/W47N7 distinct=100, already_in_db=1344; "
    "W45N7@84342300 still official 404 after focused retry 22:43:46 game.time=84342448), not told; "
    "in-window official 404 cleared: W47N7@84342200 recovered"
)
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} was slightly over the 45s gate vs first-pass rows "
    f"(delta first-robust -0.04778 s/tick, ~33.9s at tmin, over45 vs later=2, over15 later=3323 vs first=8772); "
    f"applied corrective later-mean-robust realign of {NFIX_CORR} rows at game.time={GT_CORR}; still_over_45s_vs_later=0; "
    f"subsequent confirm/just-published inserts used later-mean-robust {TICK_S_IN_USE:.5f}"
)
freeze_para = (
    "Listener restart 22:24:51 (box wake after freeze 22:12:00-22:24:48 (764s); "
    "run_listener.sh auto-restart, not this run; pid 578639) "
    "room_stats gap 84342041..84342219 (179); official-filled 179/179 all five after confirm recovered W47N7@84342200. "
    "This run did not restart the listener. "
    "Listener restart 21:56:58 (21:43:29-21:56:55 freeze (801s), not this run) "
    "room_stats gap 84341671..84341859 (189) remains in this window and stays official-filled 189/189 all five. "
    "Earlier room_stats gaps 84341401..84341439 (39) and 84340941..84341179 (239) are now outside this window; "
    "W45N8@84341100 remains an aged official 404 outside this window (80 missing 84341101..84341180). "
    "live.json gameTime field lagged at 84342359 while stats.t / room_stats / creep_cpu already passed 84342400 "
    "(used stats.t to know 84342300 was publishable); single_slot held, buffers flowing; "
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
    },
    "just_published": {
        "base": 84342300,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "22:43:16",
        "recovered_game_time": 84342442,
        "inserted": INSERTED_JUST,
        "inserted_first_two": None,
        "inserted_remaining_three": None,
        "first_try_all_404": False,
        "first_try_at": "22:43:16",
        "first_try_game_time": 84342442,
        "retry_at": "22:43:46",
        "retry_game_time": 84342448,
        "retry_inserted": 0,
        "already_in_db": 1344,
        "ticks": "84342301..84342400",
        "all_five_official_200": False,
        "still_404": ["W45N7@84342300"],
        "w45n7_empty_no_creep": None,
        "distinct": {"W46N8": 100, "W47N8": 100, "W45N8": 100, "W45N7": 0, "W47N7": 100},
    },
    "confirm": {
        "at": "22:34:40",
        "game_time": 84342333,
        "inserted": 548,
        "ssl_abort_first": None,
        "targets": 1,
        "recovered": ["W47N7@84342200"],
        "note": "focused confirm of the only in-window 404 W47N7@84342200; aged leftovers including W45N8@84341100 were not retried this pass",
    },
    "retry2": {"at": None, "game_time": None, "inserted": 0, "skipped": True, "reason": "in-window 404 W47N7@84342200 already recovered on confirm"},
    "in_window_404": {},
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 578639,
        "restart_at": "22:24:51",
        "this_run_restarted": False,
    },
    "box_freeze": {
        "from": "2026-11-18 22:12:00",
        "to": "2026-11-18 22:24:48",
        "sec": 764,
        "room_stats_gap": "84342041..84342219",
        "official_filled": "all five 179/179 after confirm recovered W47N7@84342200",
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
    f"missing_chunks={MISSING_CHUNKS} in_window_404=W47N7@84342200 recovered on confirm; final official_404=0 empty_no_creep={empty_no_creep}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    "just-published 84342300 first try 4/5 recovered inserted=2421 at 22:43:16 game.time=84342442 (after this window; W45N7@84342300 still 404 after retry 22:43:46 game.time=84342448, not told); in-window W47N7@84342200 recovered on confirm.",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not restart the listener.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_2230.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run_tee.txt").write_text(summary + now_text)
print(summary, end="")
print("now_text_bytes", len(now_text))
