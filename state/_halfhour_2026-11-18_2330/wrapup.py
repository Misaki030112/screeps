#!/usr/bin/env python3
"""Write local status records for the 23:30 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-18_2330"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84342301, 84343000
PUB_BASES = "84342300..84342900"
GT_FIRST = 84343055
TICK_S_FIRST = 4.72049
TICK_S_PRINTED = "4.720"
TICK_S_IN_USE = 4.72049
TICK_S_LATER = 4.78031
TS_REALIGNED_FIRST = 20
NFIX_CORR = 0
GT_CORR = 84343068  # later-mean corrective attempted, nfix=0
RECON_ROWS = 27019
ALREADY = 23522
INSERTED_FIRST = 3497
INSERTED_CONFIRM = 0  # both in-window 404s still 404 at 23:33:15 game.time=84343072
INSERTED_RETRY2 = 0  # still 404 at 23:33:42 game.time=84343078
INSERTED_JUST = 1517  # first try 23:38:46 game.time=84343143 recovered 4/5 (W47N8@84343000 404); retry 23:41:04 game.time=84343173 still 404, +0
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/856new W47N8:700t/1284new W45N8:700t/447new W45N7:600t/398new W47N7:600t/512new"
FIRST_PASS_LINE = (
    "first pass 33 of 35 official GETs 200, missing_chunks=2 (W45N7@84342300, W47N7@84342500); "
    "hourly_patrol_prefilled=true from 23:20 patrol official already through 84342800 "
    "/ reconstructed through 84342900 (overlap of this window); 23:00 half-hour already wrote through 84342600 "
    "and just-published 84342700 (84342701..84342800) for all 5 rooms "
    "(this pass already_in_db=23522 / inserted=3497); "
    "W45N7@84342300 and W47N7@84342500 still official 404 after confirm/retry2/just-published retry"
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
    "in-window official 404: W45N7@84342300 (leftover, still 404 first pass) "
    "and W47N7@84342500; first pass 33 of 35 official GETs 200, missing_chunks=2; "
    "still official 404 after confirm 23:33:15 game.time=84343072, retry2 23:33:42 game.time=84343078, "
    "and just-published retry 23:38:46 game.time=84343143 / 23:41:04 game.time=84343173; final official_404_in_window=200"
)
leftover_txt = (
    "aged leftover official 404s including W45N8@84341100 were not retried this pass "
    "(they stayed 404 after earlier confirm/retry2/just_published and are now outside this 40-min window)."
)
confirm_summary = (
    "confirm inserted=0 (23:33:15 game.time=84343072, W45N7@84342300 and W47N7@84342500 still official 404, no SSL abort; "
    "retry2 23:33:42 game.time=84343078 also still 404); "
    "just-published 84343000 first try at 23:38:46 game.time=84343143 recovered 4/5 rooms inserted=1517 "
    "(after this window; W46N8/W45N8/W45N7/W47N7 distinct=100, already_in_db=808; W47N8@84343000 official 404); "
    "focused retry 23:41:04 game.time=84343173 W47N8@84343000 and the two in-window 404s still official 404, inserted=0, not told; "
    "in-window official 404 still open: W45N7@84342300 and W47N7@84342500"
)
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} had over45=100 vs first over45=0 at the check anchor "
    f"(delta first-robust -0.05982 s/tick, ~45.1s at tmin, over15 later=12280 vs first=8935; prev_later 4.72311 was lowest-over45 sane); "
    f"corrective later-mean realign attempted at game.time=84343068 but moved 0 rows "
    f"(anchor slipped under the 45s gate, after later over45=0); in-use remains first {TICK_S_IN_USE:.5f}; "
    f"subsequent confirm/just-published inserts used first {TICK_S_IN_USE:.5f}"
)
freeze_para = (
    "Listener restart 23:04:28 (box wake after freeze 22:52:42-23:04:24 (696s); "
    "run_listener.sh auto-restart, not this run; pid 593872) "
    "room_stats gap 84342561..84342719 (159) remains in this window; official-filled 159/159 in W46N8/W47N8/W45N8/W45N7; "
    "W47N7 119/159 missing 40 ticks 84342561..84342600 because W47N7@84342500 stayed official 404. "
    "This run did not restart the listener. "
    "Earlier room_stats gap 84342041..84342219 (179) is now outside this window (starts 84342301) and stays official-filled 179/179 all five. "
    "W45N8@84341100 remains an aged official 404 outside this window. "
    "No new box freeze this run (last pause still 22:52:42-23:04:24). "
    "live.json / stats.t were fresh at pre-check (age ~3s, tip 84343050); used stats.t to know 84343000 was publishable; "
    "single_slot held, creep_cpu and path_arrivals flowing; this run did not restart the listener."
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
        "base": 84343000,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "23:38:46",
        "recovered_game_time": 84343143,
        "inserted": INSERTED_JUST,
        "inserted_first_two": None,
        "inserted_remaining_three": None,
        "first_try_all_404": False,
        "first_try_at": "23:38:46",
        "first_try_game_time": 84343143,
        "first_try_recovered": ["W46N8", "W45N8", "W45N7", "W47N7"],
        "first_try_still_404": ["W47N8@84343000"],
        "retry_at": "23:41:04",
        "retry_game_time": 84343173,
        "retry_inserted": 0,
        "already_in_db": 808,
        "ticks": "84343001..84343100",
        "all_five_official_200": False,
        "still_404": ["W47N8@84343000"],
        "in_window_still_404": ["W45N7@84342300", "W47N7@84342500"],
        "w45n7_empty_no_creep": None,
        "distinct": {"W46N8": 100, "W47N8": 0, "W45N8": 100, "W45N7": 100, "W47N7": 100},
    },
    "confirm": {
        "at": "23:33:15",
        "game_time": 84343072,
        "inserted": 0,
        "ssl_abort_first": None,
        "targets": 2,
        "recovered": [],
        "still_404": ["W45N7@84342300", "W47N7@84342500"],
        "note": "focused confirm of in-window 404s W45N7@84342300 and W47N7@84342500; aged leftovers including W45N8@84341100 were not retried this pass",
    },
    "retry2": {"at": "23:33:42", "game_time": 84343078, "inserted": 0, "skipped": False, "still_404": ["W45N7@84342300", "W47N7@84342500"]},
    "in_window_404": {"W45N7@84342300": "still official 404 after confirm/retry2/just_published retry", "W47N7@84342500": "still official 404 after confirm/retry2/just_published retry"},
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 593872,
        "restart_at": "23:04:28",
        "this_run_restarted": False,
    },
    "box_freeze": {
        "from": "2026-11-18 22:52:42",
        "to": "2026-11-18 23:04:24",
        "sec": 696,
        "room_stats_gap": "84342561..84342719",
        "official_filled": "W46N8/W47N8/W45N8/W45N7 159/159; W47N7 119/159 missing 40 ticks 84342561..84342600 due to official 404 W47N7@84342500",
        "new_freeze_this_run": False,
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
    f"missing_chunks={MISSING_CHUNKS} in_window_404=W45N7@84342300,W47N7@84342500 still official 404 after confirm/retry2/just_published retry; final official_404={official_404_missing} empty_no_creep={empty_no_creep}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    "just-published 84343000 first try 23:38:46 game.time=84343143 recovered 4/5 inserted=1517 (W47N8@84343000 official 404); focused retry 23:41:04 game.time=84343173 still 404 on W47N8@84343000 and in-window W45N7@84342300 / W47N7@84342500, inserted=0 (after this window, not told).",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not restart the listener.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_2330.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run_tee.txt").write_text(summary + now_text)
print(summary, end="")
print("now_text_bytes", len(now_text))
