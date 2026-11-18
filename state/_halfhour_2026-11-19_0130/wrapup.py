#!/usr/bin/env python3
"""Write local status records for the 01:30 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-19_0130"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84343901, 84344600
PUB_BASES = "84343900..84344500"
GT_FIRST = 84344657
TICK_S_FIRST = 4.67845
TICK_S_PRINTED = "4.678"
TICK_S_IN_USE = 4.79049
TICK_S_LATER = 4.79049
TS_REALIGNED_FIRST = 13161
NFIX_CORR = 12244
GT_CORR = 84344676  # corrective later-mean-robust realign nfix=12244
RECON_ROWS = 27124
ALREADY = 21105
INSERTED_FIRST = 6019
INSERTED_CONFIRM = 0  # confirm skipped: first pass missing_chunks=0, no in-window official 404
INSERTED_RETRY2 = 0  # skipped with confirm
INSERTED_JUST = 3050  # first try 01:44:40 game.time=84344740 recovered 5/5; no leftover 404 retry
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/1291new W47N8:700t/1647new W45N8:700t/1327new W45N7:700t/863new W47N7:700t/891new"
FIRST_PASS_LINE = (
    "first pass 35 of 35 official GETs 200, missing_chunks=0; "
    "hourly_patrol_prefilled=true from 00:19 patrol official already through 84343500 "
    "/ reconstructed through 84343600 and just-published 84343600 (84343601..84343700) for all 5 rooms "
    "(overlap of this window); 01:00 half-hour already wrote through 84344200 "
    "and just-published 84344200 (84344201..84344300) for all 5 rooms "
    "(this pass already_in_db=21105 / inserted=6019); "
    "01:17 hourly patrol analyzed live tip ~84344450 but did not write a new official-history fill; "
    "W47N8@84343800 aged out of this 40-min window"
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
    "in-window official 404: none; "
    "first pass 35 of 35 official GETs 200, missing_chunks=0; "
    "confirm/retry2 skipped (no in-window 404); "
    "just-published 84344600 first try 01:44:40 game.time=84344740 recovered 5/5, no leftover 404 retry; final official_404_in_window=0"
)
leftover_txt = (
    "aged leftover official 404 W47N8@84343800 was not retried this pass "
    "(it stayed 404 after earlier confirm/retry2/just_published and is now outside this 40-min window, "
    "along with older W45N8@84343100, W47N8@84343400, W47N8@84343000, W45N7@84342300, W47N7@84342500, W45N8@84341100)."
)
confirm_summary = (
    "confirm skipped (first pass missing_chunks=0, no in-window official 404); "
    "just-published 84344600 first try at 01:44:40 game.time=84344740 recovered 5/5 rooms inserted=3050 "
    "(after this window; all 5 rooms distinct=100, already_in_db=773); "
    "no focused leftover retry; in-window official 404 still open: none"
)
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} was over the 45s gate before corrective "
    f"(delta first-robust -0.11204 s/tick, ~84.7s at tmin, over45 later=11467 vs first=2135, over15 later=19556 vs first=9038); "
    f"applied corrective later-mean-robust realign of {NFIX_CORR} rows at game.time={GT_CORR}; "
    f"after over45 later=0, over15 later=7697; in-use later-mean-robust {TICK_S_IN_USE:.5f}; "
    f"subsequent just-published inserts used later-mean-robust {TICK_S_IN_USE:.5f} (ts_realigned=0)"
)
freeze_para = (
    "Listener restart 01:35:48 (box wake after freeze 01:31:02-01:35:45 (283s); also earlier restart 01:02:46 after freeze 00:47:42-01:02:42 (895s); "
    "run_listener.sh auto-restart, not this run; pid 655780). "
    "New room_stats gap 84344561..84344639 (79); official-filled 79/79 all five "
    "(84344561..84344600 via this window, 84344601..84344639 via just-published 84344600). "
    "This run did not restart the listener. "
    "Earlier room_stats gap 84344021..84344229 (209, from the 00:47-01:02 freeze) remains official-filled 209/209 in W46N8/W47N8/W45N8/W47N7; "
    "W45N7 0/209 because official empty-no-creep continues 84343972..84344239 (covers this gap). "
    "Earlier room_stats gap 84343821..84343859 (39, from the 00:31-00:34 freeze) is official-filled 39/39 in W46N8/W45N8/W45N7/W47N7; "
    "W47N8 0/39 missing all 39 because W47N8@84343800 stayed official 404 (now aged out of this window). "
    "Earlier room_stats gap 84343611..84343669 (59) remains official-filled 59/59 all five. "
    "Aged official 404 W47N8@84343800 (and older W45N8@84343100, W47N8@84343400, W47N8@84343000, W45N7@84342300, W47N7@84342500, W45N8@84341100) remain outside this window. "
    "live.json / stats.t were fresh at pre-check (age ~0s, tip 84344650, roomSlot W47N8 so live gameTime/objects stayed empty as designed); "
    "used stats.t to know 84344600 was publishable; single_slot held, creep_cpu and path_arrivals flowing after reconnect (segment-90 pull at 01:36:00); "
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
        "prev_later_over45_before_corrective": 7,
        "prev_later_mean": 4.68990,
        "note": "prev_later 4.68990 had over45=7 before corrective; established check still applied later-mean-robust because later was over the 45s gate; after over45 later=0",
    },
    "just_published": {
        "base": 84344600,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "01:44:40",
        "recovered_game_time": 84344740,
        "inserted": INSERTED_JUST,
        "inserted_first_two": None,
        "inserted_remaining_three": None,
        "first_try_all_404": False,
        "first_try_at": "01:44:40",
        "first_try_game_time": 84344740,
        "first_try_recovered": ["W46N8", "W47N8", "W45N8", "W45N7", "W47N7"],
        "first_try_still_404": [],
        "retry_at": None,
        "retry_game_time": None,
        "retry_inserted": 0,
        "already_in_db": 773,
        "ticks": "84344601..84344700",
        "all_five_official_200": True,
        "still_404": [],
        "in_window_still_404": [],
        "w45n7_empty_no_creep": [],
        "distinct": {"W46N8": 100, "W47N8": 100, "W45N8": 100, "W45N7": 100, "W47N7": 100},
    },
    "confirm": {
        "at": None,
        "game_time": None,
        "inserted": 0,
        "ssl_abort_first": None,
        "targets": 0,
        "recovered": [],
        "still_404": [],
        "note": "confirm/retry2 skipped; first pass 35/35 official GETs 200, missing_chunks=0, no in-window official 404; aged leftover W47N8@84343800 was not retried",
    },
    "retry2": {"at": None, "game_time": None, "inserted": 0, "skipped": True, "still_404": []},
    "in_window_404": {},
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 655780,
        "restart_at": "01:35:48",
        "this_run_restarted": False,
    },
    "box_freeze": {
        "from": "2026-11-19 01:31:02",
        "to": "2026-11-19 01:35:45",
        "sec": 283,
        "earlier_freeze": {
            "from": "2026-11-19 00:47:42",
            "to": "2026-11-19 01:02:42",
            "sec": 895,
            "restart_at": "01:02:46",
            "room_stats_gap": "84344021..84344229",
            "official_filled": "W46N8/W47N8/W45N8/W47N7 209/209; W45N7 0/209 official empty-no-creep 84343972..84344239",
        },
        "room_stats_gap": "84344561..84344639",
        "official_filled": "all five 79/79 (40 in-window 84344561..84344600 + 39 just-published 84344601..84344639)",
        "prior_in_window_gap": "84343821..84343859 official-filled 39/39 in W46N8/W45N8/W45N7/W47N7; W47N8 0/39 missing all 39 due to official 404 W47N8@84343800 (now aged out)",
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
    f"missing_chunks={MISSING_CHUNKS} in_window_404=none; final official_404={official_404_missing} empty_no_creep={empty_no_creep}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    "just-published 84344600 first try 01:44:40 game.time=84344740 recovered 5/5 inserted=3050 (all 5 rooms distinct=100/100); no leftover 404 retry (W47N8@84343800 aged out, not told).",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not restart the listener.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0130.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run_tee.txt").write_text(summary + now_text)
print(summary, end="")
print("now_text_bytes", len(now_text))
