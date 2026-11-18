#!/usr/bin/env python3
"""Write local status records for the 00:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-19_0000"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84342701, 84343400
PUB_BASES = "84342700..84343300"
GT_FIRST = 84343479
TICK_S_FIRST = 4.69972
TICK_S_PRINTED = "4.700"
TICK_S_IN_USE = 4.69972
TICK_S_LATER = 4.68943
TS_REALIGNED_FIRST = 0
NFIX_CORR = 0
GT_CORR = None  # no corrective realign; check anchor game.time=84343496
RECON_ROWS = 23375
ALREADY = 13422
INSERTED_FIRST = 9953
INSERTED_CONFIRM = 0  # both in-window 404s still 404 at 00:06:22 game.time=84343498
INSERTED_RETRY2 = 0  # still 404 at 00:06:38 game.time=84343501
INSERTED_JUST = 1834  # first try 00:09:50 game.time=84343542 recovered 4/5 (W47N8@84343400 404); retry 00:12:08 game.time=84343571 still 404, +0
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/3021new W47N8:600t/2714new W45N8:600t/983new W45N7:700t/1658new W47N7:700t/1577new"
FIRST_PASS_LINE = (
    "first pass 33 of 35 official GETs 200, missing_chunks=2 (W47N8@84343000, W45N8@84343100); "
    "hourly_patrol_prefilled=true from 23:20 patrol official already through 84342800 "
    "/ reconstructed through 84342900 (overlap of this window); 23:30 half-hour already wrote through 84343000 "
    "and just-published 84343000 (84343001..84343100) for 4 rooms (W47N8@84343000 still official 404) "
    "(this pass already_in_db=13422 / inserted=9953); "
    "W47N8@84343000 and W45N8@84343100 still official 404 after confirm/retry2/just-published retry"
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
    "in-window official 404: W47N8@84343000 (leftover from 23:30, still 404 first pass) "
    "and W45N8@84343100 (new this window); first pass 33 of 35 official GETs 200, missing_chunks=2; "
    "still official 404 after confirm 00:06:22 game.time=84343498, retry2 00:06:38 game.time=84343501, "
    "and just-published retry 00:09:50 game.time=84343542 / 00:12:08 game.time=84343571; final official_404_in_window=200"
)
leftover_txt = (
    "aged leftover official 404s including W45N7@84342300, W47N7@84342500 and W45N8@84341100 were not retried this pass "
    "(they stayed 404 after earlier confirm/retry2/just_published and are now outside this 40-min window)."
)
confirm_summary = (
    "confirm inserted=0 (00:06:22 game.time=84343498, W47N8@84343000 and W45N8@84343100 still official 404, no SSL abort; "
    "retry2 00:06:38 game.time=84343501 also still 404); "
    "just-published 84343400 first try at 00:09:50 game.time=84343542 recovered 4/5 rooms inserted=1834 "
    "(after this window; W46N8/W45N8/W45N7/W47N7 distinct=100, already_in_db=315; W47N8@84343400 official 404); "
    "focused retry 00:12:08 game.time=84343571 W47N8@84343400 and the two in-window 404s still official 404, inserted=0, not told; "
    "in-window official 404 still open: W47N8@84343000 and W45N8@84343100"
)
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} already inside the 45s gate "
    f"(delta first-robust 0.01379 s/tick, ~10.7s at tmin, over45 later=0 vs first=0, over15 later=649 vs first=170); "
    f"no corrective realign; in-use remains first {TICK_S_IN_USE:.5f}; "
    f"subsequent confirm/just-published inserts used first {TICK_S_IN_USE:.5f}"
)
freeze_para = (
    "Listener restart 00:02:38 (box wake after freeze 23:50:35-00:02:35 (719s); "
    "run_listener.sh auto-restart, not this run; pid 618812). "
    "New room_stats gap 84343251..84343459 (209); official-filled 209/209 in W46N8/W45N8/W45N7/W47N7; "
    "W47N8 150/209 missing 59 ticks 84343401..84343459 because W47N8@84343400 stayed official 404 "
    "(just-published, after this window). In-window portion 84343251..84343400 is official-filled 150/150 all five. "
    "This run did not restart the listener. "
    "Earlier room_stats gap 84342561..84342719 (159) is now mostly outside this window; in-window tail 84342701..84342719 is official-filled; "
    "W47N7 still missing 40 ticks 84342561..84342600 (outside this window) because W47N7@84342500 stayed official 404. "
    "Earlier room_stats gap 84342041..84342219 (179) is outside this window and stays official-filled 179/179 all five. "
    "Aged official 404s W45N7@84342300, W47N7@84342500 and W45N8@84341100 remain outside this window. "
    "live.json / stats.t were fresh at pre-check (age ~2s, tip 84343470); used stats.t to know 84343400 was publishable; "
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
        "base": 84343400,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "00:09:50",
        "recovered_game_time": 84343542,
        "inserted": INSERTED_JUST,
        "inserted_first_two": None,
        "inserted_remaining_three": None,
        "first_try_all_404": False,
        "first_try_at": "00:09:50",
        "first_try_game_time": 84343542,
        "first_try_recovered": ["W46N8", "W45N8", "W45N7", "W47N7"],
        "first_try_still_404": ["W47N8@84343400"],
        "retry_at": "00:12:08",
        "retry_game_time": 84343571,
        "retry_inserted": 0,
        "already_in_db": 315,
        "ticks": "84343401..84343500",
        "all_five_official_200": False,
        "still_404": ["W47N8@84343400"],
        "in_window_still_404": ["W47N8@84343000", "W45N8@84343100"],
        "w45n7_empty_no_creep": None,
        "distinct": {"W46N8": 100, "W47N8": 0, "W45N8": 100, "W45N7": 100, "W47N7": 100},
    },
    "confirm": {
        "at": "00:06:22",
        "game_time": 84343498,
        "inserted": 0,
        "ssl_abort_first": None,
        "targets": 2,
        "recovered": [],
        "still_404": ["W47N8@84343000", "W45N8@84343100"],
        "note": "focused confirm of in-window 404s W47N8@84343000 and W45N8@84343100; aged leftovers including W45N7@84342300, W47N7@84342500 and W45N8@84341100 were not retried this pass",
    },
    "retry2": {"at": "00:06:38", "game_time": 84343501, "inserted": 0, "skipped": False, "still_404": ["W47N8@84343000", "W45N8@84343100"]},
    "in_window_404": {"W47N8@84343000": "still official 404 after confirm/retry2/just_published retry", "W45N8@84343100": "still official 404 after confirm/retry2/just_published retry"},
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 618812,
        "restart_at": "00:02:38",
        "this_run_restarted": False,
    },
    "box_freeze": {
        "from": "2026-11-18 23:50:35",
        "to": "2026-11-19 00:02:35",
        "sec": 719,
        "room_stats_gap": "84343251..84343459",
        "official_filled": "W46N8/W45N8/W45N7/W47N7 209/209; W47N8 150/209 missing 59 ticks 84343401..84343459 due to official 404 W47N8@84343400 (just-published, after this window); in-window 84343251..84343400 filled 150/150 all five",
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
    f"missing_chunks={MISSING_CHUNKS} in_window_404=W47N8@84343000,W45N8@84343100 still official 404 after confirm/retry2/just_published retry; final official_404={official_404_missing} empty_no_creep={empty_no_creep}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    "just-published 84343400 first try 00:09:50 game.time=84343542 recovered 4/5 inserted=1834 (W47N8@84343400 official 404); focused retry 00:12:08 game.time=84343571 still 404 on W47N8@84343400 and in-window W47N8@84343000 / W45N8@84343100, inserted=0 (after this window, not told).",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not restart the listener.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0000.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run_tee.txt").write_text(summary + now_text)
print(summary, end="")
print("now_text_bytes", len(now_text))
