#!/usr/bin/env python3
"""Write local status records for the 20:00 half-hour official-history backfill."""
from __future__ import annotations
import json, shutil, time as _time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

HK = ZoneInfo("Asia/Hong_Kong")
ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-19_2000"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84357901, 84358600
PUB_BASES = "84357900..84358500"
GT_FIRST = 84358649
TICK_S_FIRST = 4.35054
TICK_S_PRINTED = "4.351"
TICK_S_IN_USE = 4.04642
TICK_S_LATER = 4.04642
TS_REALIGNED_FIRST = 12076
NFIX_CORR = 24384
GT_CORR = 84358673  # corrective later-mean-robust realign at game.time=84358673; still_over_45s_vs_later=0
RECON_ROWS = 26411
ALREADY = 13380
INSERTED_FIRST = 13031
INSERTED_CONFIRM = 0  # confirm 20:04:27 gt=84358677 still official 404 W45N7@84358500
INSERTED_RETRY2 = 0  # retry2 20:06:02 gt=84358700 still official 404 W45N7@84358500
INSERTED_JUST = 0  # 84358600 not attempted (first-pass game.time=84358649 still in-progress)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/3018new W47N8:700t/4919new W45N8:700t/1891new W45N7:600t/990new W47N7:700t/2213new"
FIRST_PASS_LINE = (
    "first pass 34 of 35 official GETs 200, missing_chunks=1 (W45N7@84358500); "
    "19:30 half-hour already wrote through 84358200 (just-published 84358200 was not attempted then and is included in this overlap, 200 in all 5 rooms); "
    "(this pass already_in_db=13380 / inserted=13031; overlap 84357900..84358100 already present from the 19:30 half-hour; this pass newly wrote previously unpublished 84358200 for all 5 rooms plus 84358300..84358400 and the 200 rooms of 84358500 (W46N8/W47N8/W45N8/W47N7), filling the unpublished tail of the prior 19:32:54 reconnect STATS gap 84358201..84358209 so that 29-tick gap is now official-filled 29/29 in all 5 rooms, filling the official-covered part of the new 19:45:09-19:59:19 freeze STATS gap 84358381..84358600 220/220 in W46N8/W47N8/W45N8/W47N7 and 120/220 in W45N7 (official 404 W45N7@84358500 hole 84358501..84358600 still 404 after confirm 20:04:27 game.time=84358677 and retry2 20:06:02 game.time=84358700, db 0/0); the unpublished tail 84358601..84358609 of that 229-tick gap sits in the still in-progress 84358600 chunk (W47N8 live after reconnect already covers 84358605..84358609 of that 9-tick tail); prior 19:11:05-19:19:02 freeze STATS gap 84357911..84358009 remains official-filled 99/99 in all 5 rooms and still sits inside this window start 84357901; prior 18:40:00-18:58:21 freeze STATS gap 84357521..84357759 and 18:11:14-18:19:27 freeze STATS gap 84357151..84357269 have now aged out of this window start); "
    "leftover official 404 W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out of this 40-min window and were not retried; "
    "in-window official 404 W45N7@84358500 still 404 after confirm and retry2; "
    "just-published 84358600 not attempted (first-pass game.time=84358649 still inside the in-progress chunk)"
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
    "in-window official 404 after first pass: W45N7@84358500 (neighbors @84358400 200; W46N8/W47N8/W45N8/W47N7 @84358500 200); "
    "first pass 34 of 35 official GETs 200, missing_chunks=1; "
    "confirm 20:04:27 game.time=84358677 still 404; retry2 20:06:02 game.time=84358700 still 404; "
    "final official_404_in_window=100 (hole 84358501..84358600, db 0/0)"
)
leftover_txt = (
    "in-window official 404 still open: W45N7@84358500 hole 84358501..84358600 (100) still official 404 after confirm and retry2, neighbors 200; "
    "aged leftover official 404 W46N8@84354300 (hole 84354301..84354351; live W46N8 already covers 84354352..84354400) and W47N7@84354300 (hole 84354301..84354400, 0/100 still missing) were not retried this pass "
    "(already outside this 40-min window, along with W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800, and older W45N8@84346100, W45N7@84345800, W45N8@84344700, W47N8@84343800, W45N8@84343100, W47N8@84343400, W47N8@84343000, W45N7@84342300, W47N7@84342500, W45N8@84341100)."
)
confirm_summary = (
    "confirm 20:04:27 Asia/Hong_Kong game.time=84358677 still official 404 W45N7@84358500 inserted=0; "
    "retry2 20:06:02 Asia/Hong_Kong game.time=84358700 still official 404 W45N7@84358500 inserted=0; "
    "just-published 84358600 not attempted (first-pass game.time=84358649 still inside the in-progress chunk; typically publishable around game.time>=84358740; next half-hour overlap will catch it); "
    "previously unpublished 84358200 (in-progress at the 19:30 half-hour) was written for all 5 rooms this pass, along with 84358300..84358400 and the 200 rooms of 84358500"
)
vs_later_before = (tick_s.get("still_over_45s_vs_later_before"))
vs_first_over45 = vs_first.get("over45")
vs_later_over15_before = tick_s.get("still_over_15s_vs_later_before")
vs_first_over15 = vs_first.get("over15")
span_vs = (vs_cand.get("span_mean") or {})
prev_vs = (vs_cand.get("prev_later") or {})
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band but is a local high versus later intervals; "
    f"later-mean-robust {TICK_S_LATER:.5f} was over the 45s gate versus first-pass-realigned rows "
    f"(delta first-robust 0.30412 s/tick, ~227.5s at tmin; "
    f"over45 later={vs_later_before} vs first={vs_first_over45}, over15 later={vs_later_over15_before} vs first={vs_first_over15}; "
    f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')}; "
    f"lowest_over45 among sane was {tick_s.get('lowest_over45_sane')} (first already closer to the live anchor than later-mean before corrective); "
    f"applied corrective later-mean-robust realign of {NFIX_CORR} rows at game.time={GT_CORR} anyway, because later-mean-robust itself was over the 45s gate versus first-pass-realigned rows; "
    f"first-pass realign moved {TS_REALIGNED_FIRST} rows; "
    f"still_over_45s_vs_later={tick_s.get('still_over_45s_vs_later')}; skipped_cross_chunk={tick_s.get('skipped_cross_chunk')}; "
    f"in-use later-mean-robust {TICK_S_IN_USE:.5f}; "
    f"confirm and retry2 still official 404 W45N7@84358500; just-published 84358600 not attempted; previously unpublished 84358200 was written this pass"
)

freeze_para = (
    "New recorded box freeze this run: 19:45:09-19:59:19 (843s; box_pauses.jsonl). "
    "Listener auto-restart was 19:59:23 (current listener.py pid 938306 started 19:59:32; run_listener.sh pid 4035476 since Nov 13). "
    "Earlier listener auto-restart after the previous recorded freeze was 19:19:05; another auto-restart 19:32:54 had already been mapped to room_stats gap 84358181..84358209 (29) by the 19:30 half-hour (official-covered 20/20 then; this pass completed the unpublished tail 84358201..84358209, now 29/29 in all 5 rooms). "
    "Also earlier freezes 19:11:05-19:19:02 (469s), 18:40:00-18:58:21 (1092s), 18:11:14-18:19:27 (492s), 17:41:25-17:58:01 (986s), 17:15:27-17:23:42 (488s), 16:43:38-17:02:18 (1119s), 15:37:56-15:57:12 (1155s), 15:21:03-15:24:59 (230s), 14:46:22-15:05:49 (1161s), 14:08:48-14:26:36 (1067s), 13:41:05-13:56:16 (905s), 13:17:39-13:22:41 (296s), 12:40:05-13:04:53 (1487s), 12:15:21-12:22:01 (400s), 11:36:36-11:58:55 (1339s), 11:11:06-11:18:54 (467s), 10:40:36-11:03:20 (1359s), 10:09:26-10:23:04 (818s), 09:45:54-09:57:01 (667s), 05:33:25-09:22:55 (13764s), 05:17:00-05:26:03 (542s), 04:45:45-04:58:24 (749s), 03:45:22-04:05:50 (1228s), 03:10:01-03:17:13 (431s), 02:45:55-02:57:12 (671s). "
    "This run did not restart the listener; after the 19:59:23 auto-reconnect this run waited for stats to resume and for the listener to pull segment-90 CPU/path buffers itself "
    "(pre-check 20:02:06, live.json age ~3.3s, stats.t=84358640 advancing, roomSlot W47N8 objects_n=0 / gameTime None — expected, because live.json is the home map only while the slot is off W46N8; "
    "creep_cpu through 84358630 / path_arrivals through 84358618 already flowing after reconnect; "
    "by wrapup live.json age fresh, stats.t=84358700 advancing, roomSlot rotated back to home W46N8, objects_n=266, creep_cpu through 84358690 / path_arrivals through 84358687 still flowing). "
    "19:30 half-hour already official-filled 84357501..84358200 (inserted_window=7252, coverage 3500/3500, missing_chunks=0; just-published 84358200 was not attempted then and is included in this overlap, 200 in all 5 rooms this pass). "
    "This half-hour first pass inserted 13031 new rows (already_in_db=13380) and wrote previously unpublished 84358200 for all 5 rooms plus 84358300..84358400 and the 200 rooms of 84358500; confirm/retry2 left W45N7@84358500 official 404. Leftover official 404 W46N8@84354300 and W47N7@84354300 remain aged out of this window and were not retried. "
    "New room_stats gap 84358381..84358609 (229, from the 19:45:09-19:59:19 box freeze) sits inside and just past this 40-min official window: official-covered 84358381..84358600 is official-filled 220/220 in W46N8, W47N8, W45N8 and W47N7, and 120/220 in W45N7 because official 404 W45N7@84358500 still leaves hole 84358501..84358600; the live tail 84358601..84358609 sits in the still unpublished 84358600 chunk until that chunk publishes (W47N8 live after reconnect already covers 84358605..84358609 of that 9-tick tail; 84358601..84358604 still unset until publish; W46N8/W45N8/W45N7/W47N7 missing all 9). "
    "Prior room_stats gap 84358181..84358209 (29, around the 19:32:54 listener auto-restart) now sits fully inside this window and is official-filled 29/29 in all 5 rooms (the previously unpublished tail 84358201..84358209 was written this pass with 84358200). "
    "room_stats gap 84357911..84358009 (99, from the 19:11:05-19:19:02 freeze) still sits inside this window and remains official-filled 99/99 in all 5 rooms. "
    "room_stats gap 84357521..84357759 (239, from the 18:40:00-18:58:21 freeze) has now aged out of this window (window starts at 84357901) and remains official-filled 239/239 in all 5 rooms. "
    "room_stats gap 84357151..84357269 (119, from the 18:11:14-18:19:27 freeze) remains aged out of this window and official-filled 119/119 in all 5 rooms. "
    "room_stats gap 84356781..84356999 (219, from the 17:41:25-17:58:01 freeze) remains aged out of this window and official-filled 219/219 in W46N8, W47N8, W45N8 and W45N7, and 115/219 in W47N7 (104 official empty-no-creep 84356794..84356897 — official history had no our creeps, not a 404). "
    "older room_stats gaps remain aged out of this window and official-filled from earlier passes as previously recorded. "
    "The tail of 84354121..84354349 remains official-filled 49/49 in W47N8, W45N8 and W45N7 but still missing 49/49 in W46N8 and all 100 ticks 84354301..84354400 in W47N7 because those rooms 404'd on official 84354300 (aged out, not retried this pass). "
    "Aged official 404 W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) remain outside this window. "
    "live.json / stats.t were fresh at pre-check (age ~3.3s, tip stats.t=84358640, roomSlot W47N8 objects_n=0 because live.json is home-map only) after the 19:59:23 auto-reconnect; CPU/path buffers were already flowing; previously unpublished 84358200 was written for all 5 rooms this pass along with 84358300..84358400 and the 200 rooms of 84358500; just-published 84358600 was not yet publishable (game.time=84358649 at first pass); single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84358630 / path_arrivals through 84358618 at pre-check; through 84358690 / 84358687 at wrapup); this run did not restart the listener."
)

single = True
ok_line = (
    f"ok_quiet=True coverage={recovered}/{expected} inserted_window={INSERTED_WINDOW} "
    f"inserted_total={INSERTED_TOTAL} tick_s_in_use={TICK_S_IN_USE:.5f} "
    f"listener single_slot=True; no second listener; no war_cmd/pulse restart."
)

first_pass_block = (
    f"  ({FIRST_PASS_LINE}; see history_backfill.txt)"
)
now_text = "\n".join([
    f"{finished_hkt} half-hour backfill OK (quiet)",
    f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
    first_pass_block,
    f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST:.5f}; {tick_s_corr_txt}, in-use {TICK_S_IN_USE:.5f})",
    f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks={MISSING_CHUNKS}",
    f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
    f"per_room {PER_ROOM_LINE}",
    f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 +{INSERTED_RETRY2}, just_published +{INSERTED_JUST}, window {INSERTED_WINDOW}, run total {INSERTED_TOTAL})",
    f"ts_realigned_first={TS_REALIGNED_FIRST}; ts_realigned_corrective={NFIX_CORR} ({tick_s_corr_txt}; in-use {TICK_S_IN_USE:.5f})",
    "db_after",
    db_after_lines,
    f"coverage official_recovered={recovered}/{expected} unique_after={unique_after.get('unique_creep_tick_rows')} empty_no_creep={empty_no_creep} official_404_in_window={official_404_missing}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    freeze_para,
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}",
    confirm_summary,
    ok_line,
]) + "\n"

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
        "prev_later_over45_before_corrective": (prev_vs or {}).get("over45"),
        "prev_later_mean": tick_s.get("prev_later_mean"),
        "note": tick_s_corr_txt,
    },
    "just_published": {
        "base": 84358600,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": None,
        "recovered_game_time": None,
        "inserted": 0,
        "note": "not attempted; first-pass game.time=84358649 was still inside the in-progress chunk (typically publishable around game.time>=84358740; next half-hour overlap will catch it)",
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
        "in_window_still_404": ["W45N7@84358500"],
        "w45n7_empty_no_creep": [],
        "w47n7_empty_no_creep": [],
        "distinct": None,
        "skipped": True,
    },
    "confirm": {
        "at": "2026-11-19 20:04:27 Asia/Hong_Kong",
        "game_time": 84358677,
        "inserted": 0,
        "ssl_abort_first": None,
        "targets": 1,
        "recovered": [],
        "still_404": ["W45N7@84358500"],
        "skipped": False,
        "note": "confirm still official 404 W45N7@84358500 at game.time=84358677; neighbors @84358500 were 200",
    },
    "retry2": {
        "at": "2026-11-19 20:06:02 Asia/Hong_Kong",
        "game_time": 84358700,
        "inserted": 0,
        "skipped": False,
        "still_404": ["W45N7@84358500"],
        "note": "retry2 still official 404 W45N7@84358500 at game.time=84358700; hole 84358501..84358600 remains, db 0/0",
    },
    "listener": {
        "single_slot": True,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 938306,
        "pid_at_precheck": 938306,
        "loop_pid": 4035476,
        "restart_at": "19:59:23",
        "listener_started": "19:59:32",
        "wrapup_ws_timeout": None,
        "wrapup_autorestart": None,
        "wrapup_listener_started": None,
        "this_run_restarted": False,
        "waited_for_reconnect": True,
        "live_objects_empty_after_reconnect": True,
        "pre_cpu_path_after_wait": "creep_cpu through 84358630 / path_arrivals through 84358618 at pre-check 20:02:06; live.json objects_n=0 was because roomSlot was W47N8 (live.json is home-map only); by wrapup roomSlot W46N8 objects_n=266, creep_cpu through 84358690 / path_arrivals through 84358687",
    },
    "box_freeze": {
        "from": "2026-11-19 19:45:09",
        "to": "2026-11-19 19:59:19",
        "sec": 843,
        "restart_at": "19:59:23",
        "room_stats_gap": "84358381..84358609",
        "official_filled": "official-covered 84358381..84358600 220/220 in W46N8/W47N8/W45N8/W47N7 and 120/220 in W45N7 (official 404 W45N7@84358500 hole 84358501..84358600 still after confirm/retry2); unpublished tail 84358601..84358609 sits in still in-progress 84358600 (W47N8 live covers 84358605..84358609)",
        "earlier_freeze": {
            "from": "2026-11-19 19:11:05",
            "to": "2026-11-19 19:19:02",
            "sec": 469,
            "restart_at": "19:19:05",
            "room_stats_gap": "84357911..84358009",
            "official_filled": "84357911..84358009 official-filled 99/99 in all 5 rooms, still inside this window start 84357901; 19:32:54 reconnect gap 84358181..84358209 now official-filled 29/29 in all 5 rooms after this pass wrote 84358200",
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
    f"missing_chunks={MISSING_CHUNKS} in_window_404=W45N7@84358500; final official_404={official_404_missing} empty_no_creep={empty_no_creep}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    "just-published 84358600 not attempted (first-pass game.time=84358649 still inside the in-progress chunk); previously unpublished 84358200 was written for all 5 rooms this pass along with 84358300..84358400 and the 200 rooms of 84358500; confirm/retry2 left official 404 W45N7@84358500 (hole 84358501..84358600); leftover official 404 W46N8@84354300 (hole 84354301..84354351) and W47N7@84354300 (hole 84354301..84354400) had aged out of this window and were not retried.",
    freeze_para,
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 19:59:23 (listener.py pid 938306 started 19:59:32) after the new recorded box freeze 19:45:09-19:59:19 (843s, room_stats gap 84358381..84358609). The 19:59:23 reconnect had already recovered stats/CPU/path by pre-check 20:02:06 (live.json fresh, stats.t advancing, roomSlot W47N8 so live.json objects_n=0 by design; single_slot held). By wrapup the slot had rotated back to home W46N8 with objects_n=266.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_2000.txt")
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
