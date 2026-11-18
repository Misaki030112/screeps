#!/usr/bin/env python3
"""Write local status records for the 01:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-19_0100"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84343501, 84344200
PUB_BASES = "84343500..84344100"
GT_FIRST = 84344255
TICK_S_FIRST = 4.64805
TICK_S_PRINTED = "4.648"
TICK_S_IN_USE = 4.68990
TICK_S_LATER = 4.68990
TS_REALIGNED_FIRST = 2385
NFIX_CORR = 45
GT_CORR = 84344273  # corrective later-mean-robust realign nfix=45
RECON_ROWS = 26128
ALREADY = 15147
INSERTED_FIRST = 10981
INSERTED_CONFIRM = 0  # in-window 404 W47N8@84343800 still 404 at 01:07:20 game.time=84344275
INSERTED_RETRY2 = 0  # still 404 at 01:07:32 game.time=84344277
INSERTED_JUST = 2683  # first try 01:12:40 game.time=84344343 recovered 5/5; retry 01:14:53 game.time=84344370 still 404 on W47N8@84343800, +0
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/3101new W47N8:600t/4483new W45N8:700t/1553new W45N7:700t/277new W47N7:700t/1567new"
FIRST_PASS_LINE = (
    "first pass 34 of 35 official GETs 200, missing_chunks=1 (W47N8@84343800); "
    "hourly_patrol_prefilled=true from 00:19 patrol official already through 84343500 "
    "/ reconstructed through 84343600 and just-published 84343600 (84343601..84343700) for all 5 rooms "
    "(overlap of this window); 00:30 half-hour already wrote through 84343800 "
    "and just-published 84343800 (84343801..84343900) for 4 rooms (W47N8@84343800 still official 404) "
    "(this pass already_in_db=15147 / inserted=10981); "
    "W47N8@84343800 still official 404 after confirm/retry2/just-published retry; "
    "W45N8@84343100 and W47N8@84343400 aged out of this 40-min window"
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
    "in-window official 404: W47N8@84343800 (leftover from 00:30 just-published, still 404 first pass); "
    "first pass 34 of 35 official GETs 200, missing_chunks=1; "
    "still official 404 after confirm 01:07:20 game.time=84344275, retry2 01:07:32 game.time=84344277, "
    "and just-published retry 01:12:40 game.time=84344343 / 01:14:53 game.time=84344370; final official_404_in_window=100"
)
leftover_txt = (
    "aged leftover official 404s W45N8@84343100 and W47N8@84343400 were not retried this pass "
    "(they stayed 404 after earlier confirm/retry2/just_published and are now outside this 40-min window)."
)
confirm_summary = (
    "confirm inserted=0 (01:07:20 game.time=84344275, W47N8@84343800 still official 404, no SSL abort; "
    "retry2 01:07:32 game.time=84344277 also still 404); "
    "just-published 84344200 first try at 01:12:40 game.time=84344343 recovered 5/5 rooms inserted=2683 "
    "(after this window; W46N8/W47N8/W45N8/W47N7 distinct=100, W45N7 distinct=61 official empty-no-creep 84344201..84344239, already_in_db=1205); "
    "focused retry 01:14:53 game.time=84344370 W47N8@84343800 still official 404, inserted=0, not told; "
    "in-window official 404 still open: W47N8@84343800"
)
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} was over the 45s gate before corrective "
    f"(delta first-robust -0.04185 s/tick, ~31.6s at tmin, over45 later=30 vs first=312, over15 later=3375 vs first=11584); "
    f"applied corrective later-mean-robust realign of {NFIX_CORR} rows at game.time={GT_CORR}; "
    f"after over45 later=0, over15 later=4707; in-use later-mean-robust {TICK_S_IN_USE:.5f}; "
    f"subsequent confirm/just-published inserts used later-mean-robust {TICK_S_IN_USE:.5f}"
)
freeze_para = (
    "Listener restart 01:02:46 (box wake after freeze 00:47:42-01:02:42 (895s); also earlier restart 00:34:09 after freeze 00:31:59-00:34:06 (124s); "
    "run_listener.sh auto-restart, not this run; pid 640368). "
    "New room_stats gap 84344021..84344229 (209); official-filled 209/209 in W46N8/W47N8/W45N8/W47N7 "
    "(84344021..84344200 via this window, 84344201..84344229 via just-published 84344200); "
    "W45N7 0/209 because official empty-no-creep continues 84343972..84344200 in-window and 84344201..84344239 after this window. "
    "This run did not restart the listener. "
    "Earlier room_stats gap 84343821..84343859 (39, from the 00:31-00:34 freeze) is official-filled 39/39 in W46N8/W45N8/W45N7/W47N7; "
    "W47N8 0/39 missing all 39 because W47N8@84343800 stayed official 404 (now in-window). "
    "Earlier room_stats gap 84343611..84343669 (59) remains official-filled 59/59 all five. "
    "Aged official 404s W45N8@84343100 and W47N8@84343400 (and older W47N8@84343000, W45N7@84342300, W47N7@84342500, W45N8@84341100) remain outside this window. "
    "live.json / stats.t were fresh at pre-check (age ~2.7s, tip 84344250, roomSlot W47N8 so live gameTime/objects stayed empty as designed); "
    "used stats.t to know 84344200 was publishable; single_slot held, creep_cpu and path_arrivals flowing after reconnect (segment-90 pull at 01:04:58); "
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
        "base": 84344200,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "01:12:40",
        "recovered_game_time": 84344343,
        "inserted": INSERTED_JUST,
        "inserted_first_two": None,
        "inserted_remaining_three": None,
        "first_try_all_404": False,
        "first_try_at": "01:12:40",
        "first_try_game_time": 84344343,
        "first_try_recovered": ["W46N8", "W47N8", "W45N8", "W45N7", "W47N7"],
        "first_try_still_404": [],
        "retry_at": "01:14:53",
        "retry_game_time": 84344370,
        "retry_inserted": 0,
        "already_in_db": 1205,
        "ticks": "84344201..84344300",
        "all_five_official_200": True,
        "still_404": [],
        "in_window_still_404": ["W47N8@84343800"],
        "w45n7_empty_no_creep": [[84344201, 84344239]],
        "distinct": {"W46N8": 100, "W47N8": 100, "W45N8": 100, "W45N7": 61, "W47N7": 100},
    },
    "confirm": {
        "at": "01:07:20",
        "game_time": 84344275,
        "inserted": 0,
        "ssl_abort_first": None,
        "targets": 1,
        "recovered": [],
        "still_404": ["W47N8@84343800"],
        "note": "focused confirm of in-window 404 W47N8@84343800; aged leftovers W45N8@84343100 and W47N8@84343400 were not retried this pass",
    },
    "retry2": {"at": "01:07:32", "game_time": 84344277, "inserted": 0, "skipped": False, "still_404": ["W47N8@84343800"]},
    "in_window_404": {"W47N8@84343800": "still official 404 after confirm/retry2/just_published retry"},
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 640368,
        "restart_at": "01:02:46",
        "this_run_restarted": False,
    },
    "box_freeze": {
        "from": "2026-11-19 00:47:42",
        "to": "2026-11-19 01:02:42",
        "sec": 895,
        "earlier_freeze": {"from": "2026-11-19 00:31:59", "to": "2026-11-19 00:34:06", "sec": 124, "restart_at": "00:34:09", "room_stats_gap": "84343821..84343859", "official_filled": "W46N8/W45N8/W45N7/W47N7 39/39; W47N8 0/39 missing all 39 due to official 404 W47N8@84343800 (now in-window)"},
        "room_stats_gap": "84344021..84344229",
        "official_filled": "W46N8/W47N8/W45N8/W47N7 209/209 (180 in-window + 29 just-published 84344200); W45N7 0/209 official empty-no-creep (in-window 84343972..84344200 and just-published 84344201..84344239)",
        "prior_in_window_gap": "84343821..84343859 official-filled 39/39 in W46N8/W45N8/W45N7/W47N7; W47N8 0/39 missing all 39 due to official 404 W47N8@84343800 (now in-window)",
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
    f"missing_chunks={MISSING_CHUNKS} in_window_404=W47N8@84343800 still official 404 after confirm/retry2/just_published retry; final official_404={official_404_missing} empty_no_creep={empty_no_creep}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    "just-published 84344200 first try 01:12:40 game.time=84344343 recovered 5/5 inserted=2683 (W45N7 official empty-no-creep 84344201..84344239, distinct=61/100); focused retry 01:14:53 game.time=84344370 still 404 on in-window W47N8@84343800, inserted=0 (after this window, not told).",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not restart the listener.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0100.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run_tee.txt").write_text(summary + now_text)
print(summary, end="")
print("now_text_bytes", len(now_text))
