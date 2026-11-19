#!/usr/bin/env python3
"""Write local status records for the 09:30 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-19_0930"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84350001, 84350700
PUB_BASES = "84350000..84350600"
GT_FIRST = 84350708
TICK_S_FIRST = 4.66934
TICK_S_PRINTED = "4.669"
TICK_S_IN_USE = 4.765928
TICK_S_LATER = 4.765928
TS_REALIGNED_FIRST = 12295
NFIX_CORR = 12818
GT_CORR = 84350729
RECON_ROWS = 24074
ALREADY = 23141
INSERTED_FIRST = 933
INSERTED_CONFIRM = 2022  # confirm 09:40:18 gt=84350741 recovered W47N8@84350600 + W47N7@84350600
INSERTED_RETRY2 = 0  # skipped; both leftovers already recovered on confirm
INSERTED_JUST = 0  # just-published base 84350600 was already inside the first-pass window (3/5 rooms 200 then; remaining 2 on confirm)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/417new W47N8:600t/0new W45N8:700t/282new W45N7:700t/234new W47N7:600t/0new"
FIRST_PASS_LINE = (
    "first pass 33 of 35 official GETs 200, missing_chunks=2 W47N8@84350600,W47N7@84350600; "
    "09:22 patrol already wrote through 84350400 and just-published 84350500 (84350501..84350600) for all 5 rooms; "
    "(this pass already_in_db=23141 / inserted=933); "
    "leftover official 404 W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out of this 40-min window; "
    "W47N8@84350600, W47N7@84350600 recovered on confirm 09:40:18 game.time=84350741"
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
    "in-window official 404 after first pass: W47N8@84350600 hole 84350601..84350700; "
    "W47N7@84350600 hole 84350601..84350700; "
    "first pass 33 of 35 official GETs 200, missing_chunks=2; "
    "confirm 09:40:18 game.time=84350741 recovered both (W47N8 inserted=1618, W47N7 inserted=404, total 2022); "
    "retry2 skipped; no separate just-published pass (base 84350600 already in the first-pass window, 3/5 rooms 200 on first try); "
    "final official_404_in_window=0"
)
leftover_txt = (
    "in-window official 404 still open: none after confirm; "
    "aged leftover official 404 W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 were not retried this pass "
    "(already outside this 40-min window, along with older W45N8@84346100, W45N7@84345800, W45N8@84344700, W47N8@84343800, W45N8@84343100, W47N8@84343400, W47N8@84343000, W45N7@84342300, W47N7@84342500, W45N8@84341100)."
)
confirm_summary = (
    "confirm 09:40:18 game.time=84350741 recovered W47N8@84350600 and W47N7@84350600 inserted=2022; "
    "retry2 skipped (both leftovers already official 200); "
    "just-published 84350600 was already inside the first-pass window "
    "(W46N8/W45N8/W45N7 official 200 on first pass, W47N8/W47N7 recovered on confirm); "
    "in-window official 404 still open: none"
)
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} was over the 45s gate versus first-aligned rows "
    f"(delta first-robust -0.09659 s/tick, ~68.3s at tmin; "
    f"over45 later=11496 vs first=1737, over15 later=23984 vs first=12122; "
    f"span_mean 4.74983 over45=10788 and prev_later 4.79485 over45=17851; lowest_over45 among sane was first); "
    f"applied corrective later-mean-robust realign of {NFIX_CORR} rows at game.time={GT_CORR}; "
    f"still_over_45s_vs_later=0; skipped_cross_chunk=0; "
    f"in-use later-mean-robust {TICK_S_IN_USE:.5f}; "
    f"subsequent confirm inserts used later-mean-robust {TICK_S_IN_USE:.5f} (ts_realigned=0)"
)
freeze_para = (
    "Long box freeze this run 05:33:25-09:22:55 (13764s); also earlier 05:17:00-05:26:03 (542s), 04:45:45-04:58:24 (749s), 03:45:22-04:05:50 (1228s), 03:10:01-03:17:13 (431s), 02:45:55-02:57:12 (671s). "
    "05:30-09:00 half-hour backfills were missed during that long freeze. "
    "Listener last auto-restart 09:22:58 after that wake (run_listener.sh auto-restart, not this run; listener.py pid 748054 started 09:23:07; run_listener.sh pid 4035476). "
    "This run did not restart the listener; it was already up after that auto-restart and pulling segment-90 CPU/path buffers itself "
    "(pre-check 09:37:20 live.json age ~0.1s, stats.t=84350700, roomSlot W46N8 objects_n=261 / gameTime 84350703; "
    "creep_cpu through 84350690 / path_arrivals through 84350687; "
    "by wrapup live.json gameTime=84350750, roomSlot W46N8, objects_n=263, creep_cpu through 84350740 / path_arrivals through 84350736). "
    "Concurrent 09:22 patrol already official-filled a long catch-up window 84346201..84350500 (inserted=146553, missing_chunks=5) and just-published 84350500 (84350501..84350600, inserted=2356, 5/5 rooms). "
    "room_stats gap 84347621..84350529 (2909, from the long freeze) overlaps this 40-min window at 84350001..84350529 (529) and is official-filled 529/529 in all 5 rooms; "
    "the earlier portion of that gap and official 404 W47N8@84347800 (84347801..84347900, 100 ticks missing in W47N8 only) are already outside this 40-min window; "
    "older room_stats gaps 84346261..84346529 and 84347021..84347189 also remain outside this window. "
    "Aged official 404 W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) remain outside this window. "
    "live.json / stats.t were fresh at pre-check (age ~0.1s, tip stats.t=84350700); "
    "used stats.t/game.time to know 84350600 was publishable (waited until live gameTime>=84350740); single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84350690 / path_arrivals through 84350687 at pre-check); "
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
        "prev_later_over45_before_corrective": 17851,
        "prev_later_mean": 4.79485,
        "note": "first-interval 4.66934 printed 4.669 was sane (lowest_over45=first, over45=1737 vs first); later-mean-robust 4.765928 was over the 45s gate versus first-aligned rows (over45=11496, delta -0.09659 s/tick ~68.3s at tmin); span_mean 4.74983 over45=10788 and prev_later 4.79485 over45=17851; applied corrective later-mean-robust realign of 12818 rows at game.time=84350729; still_over_45s_vs_later=0; in-use later-mean-robust 4.765928",
    },
    "just_published": {
        "base": 84350600,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "09:40:18",
        "recovered_game_time": 84350741,
        "inserted": INSERTED_JUST,
        "note": "base 84350600 was already the latest published base in the first-pass 40-min window; 3/5 rooms official 200 on first pass (part of inserted=933); remaining W47N8/W47N7 recovered on confirm (inserted=2022). No newer just-published base (84350700 still in progress).",
        "first_try_all_404": False,
        "first_try_at": "first_pass ~09:38",
        "first_try_game_time": 84350708,
        "first_try_recovered": ["W46N8", "W45N8", "W45N7"],
        "first_try_still_404": ["W47N8@84350600", "W47N7@84350600"],
        "retry_at": "09:40:18",
        "retry_game_time": 84350741,
        "retry_inserted": 2022,
        "ticks": "84350601..84350700",
        "all_five_official_200": True,
        "still_404": [],
        "in_window_still_404": [],
        "w45n7_empty_no_creep": [],
        "w47n7_empty_no_creep": [],
        "distinct": {"W46N8": 100, "W47N8": 100, "W45N8": 100, "W45N7": 100, "W47N7": 100},
    },
    "confirm": {
        "at": "09:40:18",
        "game_time": 84350741,
        "inserted": 2022,
        "ssl_abort_first": None,
        "targets": 2,
        "recovered": ["W47N8@84350600", "W47N7@84350600"],
        "still_404": [],
        "note": "confirm recovered both at 09:40:18 game.time=84350741 after waiting until game.time>=84350740; W47N8 inserted=1618 (pre distinct=3 live ticks 84350601..84350603), W47N7 inserted=404; neighbors @84350500 both 200 and W46N8/W45N8/W45N7 @84350600 already 200 from first pass",
    },
    "retry2": {"at": None, "game_time": None, "inserted": 0, "skipped": True, "still_404": [], "note": "skipped; confirm already recovered both in-window 404s"},
    "in_window_404": {},
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 748054,
        "loop_pid": 4035476,
        "restart_at": "09:22:58",
        "listener_started": "09:23:07",
        "this_run_restarted": False,
        "waited_for_reconnect": True,
        "pre_cpu_path_after_wait": "creep_cpu through 84350690 / path_arrivals through 84350687 at pre-check 09:37:20; listener.py pid 748054 started 09:23:07 after run_listener.sh auto-restart 09:22:58; wrapup creep_cpu through 84350740 / path_arrivals through 84350736",
    },
    "box_freeze": {
        "from": "2026-11-19 05:33:25",
        "to": "2026-11-19 09:22:55",
        "sec": 13764,
        "restart_at": "09:22:58",
        "room_stats_gap": "84347621..84350529",
        "official_filled": "in-window overlap 84350001..84350529 official-filled 529/529 in all 5 rooms; earlier portion of 84347621..84349999 and official 404 W47N8@84347800 (100 ticks) are outside this 40-min window",
        "earlier_freeze": {
            "from": "2026-11-19 05:17:00",
            "to": "2026-11-19 05:26:03",
            "sec": 542,
            "restart_at": "05:26:06",
            "room_stats_gap": "84347411..84347539",
            "official_filled": "all 5 rooms 129/129 (outside this 40-min window)",
        },
        "new_freeze_this_run": True,
        "missed_halfhours": "05:30-09:00 half-hour backfills missed during 05:33:25-09:22:55 freeze; 09:22 patrol catch-up already official-filled 84346201..84350600 before this run",
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
    f"missing_chunks={MISSING_CHUNKS} in_window_404=none after confirm; final official_404={official_404_missing} empty_no_creep={empty_no_creep}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    "just-published 84350600 already in first-pass window: 3/5 rooms official 200 on first pass, remaining W47N8/W47N7 recovered on confirm 09:40:18 game.time=84350741 inserted=2022; no leftover official 404 in window.",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not restart the listener.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0930.txt")
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
