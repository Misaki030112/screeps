#!/usr/bin/env python3
"""Write local status records for the 23:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-18_2300"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84342001, 84342700
PUB_BASES = "84342000..84342600"
GT_FIRST = 84342728
TICK_S_FIRST = 4.66596
TICK_S_PRINTED = "4.666"
TICK_S_IN_USE = 4.72311
TICK_S_LATER = 4.72311
TS_REALIGNED_FIRST = 0
NFIX_CORR = 0
GT_CORR = None
RECON_ROWS = 29400
ALREADY = 17607
INSERTED_FIRST = 11793
INSERTED_CONFIRM = 0  # both in-window 404s still 404 at 23:07:23 game.time=84342747
INSERTED_RETRY2 = 0  # still 404 at 23:07:42 game.time=84342751
INSERTED_JUST = 2799  # first try all 5 official 404 at 23:11:52 game.time=84342802; all five recovered 2799 at 23:15:05 game.time=84342841
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/2354new W47N8:700t/5666new W45N8:700t/1417new W45N7:600t/1017new W47N7:600t/1339new"
FIRST_PASS_LINE = (
    "first pass 33 of 35 official GETs 200, missing_chunks=2 (W45N7@84342300, W47N7@84342500); "
    "hourly_patrol_prefilled=true from 22:24 patrol official already through 84342100 "
    "(overlap of this window); 22:30 half-hour already wrote through 84342200 and just-published 84342300 "
    "(84342301..84342400) for 4/5 rooms (W45N7@84342300 still official 404 after 22:43:46) "
    "(this pass already_in_db=17607 / inserted=11793); "
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
    "in-window official 404: W45N7@84342300 (leftover from 22:30 just-published, still 404 first pass) "
    "and W47N7@84342500; first pass 33 of 35 official GETs 200, missing_chunks=2; "
    "still official 404 after confirm 23:07:23 game.time=84342747, retry2 23:07:42 game.time=84342751, "
    "and just-published retry 23:15:05 game.time=84342841; final official_404_in_window=200"
)
leftover_txt = (
    "aged leftover official 404s including W45N8@84341100 were not retried this pass "
    "(they stayed 404 after earlier confirm/retry2/just_published and are now outside this 40-min window)."
)
confirm_summary = (
    "confirm inserted=0 (23:07:23 game.time=84342747, W45N7@84342300 and W47N7@84342500 still official 404, no SSL abort; "
    "retry2 23:07:42 game.time=84342751 also still 404); "
    "just-published 84342700 first try all five official 404 at 23:11:52 game.time=84342802 (too soon after the publish threshold); "
    "recovered all five inserted=2799 at 23:15:05 game.time=84342841 "
    "(after this window; W46N8/W47N8/W45N8/W45N7/W47N7 distinct=100, already_in_db=799), not told; "
    "in-window official 404 still open: W45N7@84342300 and W47N7@84342500"
)
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} already inside the 45s gate vs first-pass rows "
    f"(delta first-robust -0.06156 s/tick, ~44.8s at tmin, over45 vs later=0, over15 later=1318 vs first=17413, first over45=40); "
    f"no corrective realign; subsequent confirm/just-published inserts used later-mean-robust {TICK_S_IN_USE:.5f}"
)
freeze_para = (
    "Listener restart 23:04:28 (box wake after freeze 22:52:42-23:04:24 (696s); "
    "run_listener.sh auto-restart, not this run; pid 593872) "
    "room_stats gap 84342561..84342719 (159); official-filled 159/159 in W46N8/W47N8/W45N8/W45N7 after first pass + just-published 84342700; "
    "W47N7 119/159 missing 40 ticks 84342561..84342600 because W47N7@84342500 stayed official 404. "
    "This run did not restart the listener. "
    "Listener restart 22:24:51 (22:12:00-22:24:48 freeze (764s), not this run) "
    "room_stats gap 84342041..84342219 (179) remains in this window and stays official-filled 179/179 all five. "
    "Earlier room_stats gaps 84341671..84341859 (189) and 84341401..84341439 (39) are now outside this window; "
    "W45N8@84341100 remains an aged official 404 outside this window. "
    "live.json gameTime field lagged at 84342810 while stats.t already reached 84342840 "
    "(used stats.t to know 84342700 was publishable); single_slot held, buffers flowing; "
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
        "base": 84342700,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "23:15:05",
        "recovered_game_time": 84342841,
        "inserted": INSERTED_JUST,
        "inserted_first_two": None,
        "inserted_remaining_three": None,
        "first_try_all_404": True,
        "first_try_at": "23:11:52",
        "first_try_game_time": 84342802,
        "retry_at": "23:15:05",
        "retry_game_time": 84342841,
        "retry_inserted": INSERTED_JUST,
        "already_in_db": 799,
        "ticks": "84342701..84342800",
        "all_five_official_200": True,
        "still_404": [],
        "in_window_still_404": ["W45N7@84342300", "W47N7@84342500"],
        "w45n7_empty_no_creep": None,
        "distinct": {"W46N8": 100, "W47N8": 100, "W45N8": 100, "W45N7": 100, "W47N7": 100},
    },
    "confirm": {
        "at": "23:07:23",
        "game_time": 84342747,
        "inserted": 0,
        "ssl_abort_first": None,
        "targets": 2,
        "recovered": [],
        "still_404": ["W45N7@84342300", "W47N7@84342500"],
        "note": "focused confirm of in-window 404s W45N7@84342300 and W47N7@84342500; aged leftovers including W45N8@84341100 were not retried this pass",
    },
    "retry2": {"at": "23:07:42", "game_time": 84342751, "inserted": 0, "skipped": False, "still_404": ["W45N7@84342300", "W47N7@84342500"]},
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
    "just-published 84342700 first try all five 404 at 23:11:52 game.time=84342802; all five recovered inserted=2799 at 23:15:05 game.time=84342841 (after this window, not told); in-window W45N7@84342300 and W47N7@84342500 still official 404.",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not restart the listener.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_2300.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run_tee.txt").write_text(summary + now_text)
print(summary, end="")
print("now_text_bytes", len(now_text))
