#!/usr/bin/env python3
"""Write local status records for the 06:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-20_0600"
assert "_halfhour_2026-11-20_0600" in str(DIR), DIR
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84366701, 84367400
PUB_BASES = "84366700..84367300"
GT_FIRST = 84367466
TICK_S_FIRST = 4.08238
TICK_S_PRINTED = "4.082"
TICK_S_IN_USE = 4.08238  # first; later-mean-robust 4.08973 refused (worse abs mean_off); over45=0, no corrective
TICK_S_LATER = 4.08973
TS_REALIGNED_FIRST = 50
NFIX_CORR = 0
GT_CORR = None
RECON_ROWS = 29185
ALREADY = 17648
INSERTED_FIRST = 11537
INSERTED_CONFIRM = 0  # no in-window 404; confirm/retry2 skipped
INSERTED_RETRY2 = 0
INSERTED_JUST_SCRIPT = 2986
INSERTED_JUST = 2695  # 859+709+320+381+426 actual db; W47N7 script 717 vs db 426
PER_ROOM_LINE = "W46N8:700t/1333new W47N8:700t/5401new W45N8:700t/1617new W45N7:700t/1150new W47N7:700t/2036new"
FIRST_PASS_CORE = (
    "first pass 35 of 35 official GETs 200, missing_chunks=0; "
    "05:30 half-hour already wrote through 84366900 / reconstructed through 84367000 (just-published 84367000 was attempted then at 05:42:24 gt=84367143 and recovered all 5 rooms, ticks 84367001..84367100; last run classified W47N7 84367001..84367099 as official empty_no_creep with only +1 row at 84367100, but this first pass recovered W47N7 84367001..84367100 to 100/100 ticks / 101 rows); "
    "concurrent 1h patrol was delivered ~05:23 (next ~06:17); "
    "(this pass already_in_db=17648 / inserted=11537; overlap 84366701..84367400 already partly present from the 05:30 half-hour official fill, just-published 84367000 for all 5, and live rotation; "
    "this pass inserted 11537 additional rows: W46N8 1333, W47N8 5401, W45N8 1617, W45N7 1150, W47N7 2036; "
    "box freeze 05:18:07-05:19:42 STATS gap 84366781..84366819 (39) is fully inside this window and official-filled 39/39 in all 5 (already told by the 05:23 1h patrol); "
    "box freeze 04:42:44-05:00:03 STATS gap 84366271..84366539 (269) has aged out of this window start 84366701 (already told; still unfilled 30 ticks in W47N8@84366200 and 39 ticks in W47N7@84366500); "
    "new box freeze 05:53:08-05:56:59 (223s) STATS gap 84367301..84367369 (69) is fully inside this reconstructed window and official-filled 69/69 in all 5 (not yet told; for the next 1h patrol); "
    "new box freeze 05:59:54-06:01:32 (90s) STATS gap 84367401..84367429 (29) sits in just-published 84367400 (not yet told; for the next 1h patrol); "
    "listener auto-restarts 05:57:02 (after the 05:53 freeze) and 06:01:35 (pid 1159748 started 06:01:45, after the 05:59 freeze); this run did not itself restart the listener; "
    "leftover official 404 W47N7@84366500 aged out of this 40-min window and was not retried (hole 84366501..84366600 still unfilled, already told by the 05:23 1h patrol); "
    "leftover official 404 W47N8@84366200, W45N7@84365200, W47N8@84363900, W46N8@84362700, W47N8@84361700, W46N8@84360600, W45N7@84360200, W47N8@84359900, W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out and were not retried; "
    "no in-window official 404; "
    "this window empty_no_creep=0"
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
vs_first = tick_s.get("vs_first") or {}
vs_cand = tick_s.get("vs_candidates") or {}
live = json.loads((ROOT / "metrics" / "live.json").read_text())
rot = json.loads((ROOT / "metrics" / "listener_rot.json").read_text())
yield_present = (ROOT / "metrics" / "listener_yield_rooms").exists()
just_pub_path = DIR / "just_published_84367400.json"
just_pub_payload = json.loads(just_pub_path.read_text()) if just_pub_path.exists() else {}
confirm_payload = {}
try:
    confirm_payload = json.loads((DIR / "backfill_confirm_gets.json").read_text())
except Exception:
    confirm_payload = {}

finished = datetime.now(HK)
finished_hkt = finished.strftime("%Y-%m-%d %H:%M Asia/Hong_Kong")
finished_hkt_sec = finished.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

def rng(c, room, t0, t1, expected_n):
    d, n, mn, mx = c.execute(
        "SELECT count(DISTINCT tick), count(*), min(tick), max(tick) "
        "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, t0, t1),
    ).fetchone()
    return {"distinct": d or 0, "rows": n or 0, "min": mn, "max": mx, "missing": expected_n - (d or 0)}

just_recovered = just_pub_payload.get("recovered") or []
just_still_404 = just_pub_payload.get("still_404") or []
just_gt = just_pub_payload.get("game_time")
just_at = just_pub_payload.get("at")
all_five = (len(just_recovered) == 5 and not just_still_404)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
retry_note = just_pub_payload.get("retry_note") or ""
just_note = (
    f"just-published 84367400 attempted at {just_at} game.time={just_gt} "
    f"(typically publishable around game.time>=84367540) and was "
    + ("200 for all 5 rooms" if all_five else f"not fully published (recovered={just_recovered or []} still_404={just_still_404 or []})")
    + f" (script inserted={INSERTED_JUST_SCRIPT}, actual db inserted={INSERTED_JUST}; "
    "W47N7 script counted 717 but db +426 with db_distinct=100/100; "
    "the other four rooms matched the script counts); "
    "ticks 84367401..84367500 sit just after this reconstructed window"
    + (f"; {retry_note}" if retry_note else "")
)
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
FIRST_PASS_LINE = FIRST_PASS_CORE + "; " + just_note

db_lines = []
cpu_tip = path_tip = rs_tip = None
with db.connect() as c:
    for room in sorted(ROOMS):
        mn, mx, n, d = c.execute(
            "SELECT min(tick), max(tick), count(*), count(DISTINCT tick) "
            "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, TMIN, TMAX),
        ).fetchone()
        db_lines.append(f"  {room} ticks={mn}..{mx} rows={n} distinct={d}")
    cpu_tip = c.execute("SELECT max(tick) FROM creep_cpu").fetchone()[0]
    path_tip = c.execute("SELECT max(tick) FROM path_arrivals").fetchone()[0]
    rs_tip = c.execute("SELECT max(tick) FROM room_stats").fetchone()[0]
    just_pub = {room: rng(c, room, 84367401, 84367500, 100) for room in ROOMS}
    freeze0442 = {room: rng(c, room, 84366271, 84366539, 269) for room in ROOMS}
    freeze0518 = {room: rng(c, room, 84366781, 84366819, 39) for room in ROOMS}
    restart0534 = {room: rng(c, room, 84367001, 84367029, 29) for room in ROOMS}
    freeze0553 = {room: rng(c, room, 84367301, 84367369, 69) for room in ROOMS}
    freeze0559 = {room: rng(c, room, 84367401, 84367429, 29) for room in ROOMS}
    recovered_w47n7_67000 = rng(c, "W47N7", 84367001, 84367100, 100)
    hole_w47n7_66500 = rng(c, "W47N7", 84366501, 84366600, 100)
    hole_w47n8_66200 = rng(c, "W47N8", 84366201, 84366300, 100)
    hole_w45n7_65200 = rng(c, "W45N7", 84365201, 84365300, 100)
    hole_w47n8_63900 = rng(c, "W47N8", 84363901, 84364000, 100)
    hole_w46n8_62700 = rng(c, "W46N8", 84362701, 84362800, 100)
    hole_w47n8_61700 = rng(c, "W47N8", 84361701, 84361800, 100)
    hole_w46n8_60600 = rng(c, "W46N8", 84360601, 84360700, 100)
    aged_w45n7_60200 = rng(c, "W45N7", 84360201, 84360300, 100)
    aged_w47n8_59900 = rng(c, "W47N8", 84359901, 84360000, 100)
db_after_lines = "\n".join(db_lines)

inwin_txt = (
    "in-window official 404 after first pass: none (35 of 35 official GETs 200, missing_chunks=0); "
    "confirm/retry2 skipped; final official_404_in_window=0"
)
leftover_txt = (
    f"Leftover official 404 W47N7@84366500 (hole 84366501..84366600 still db {hole_w47n7_66500['distinct']}/100, no rows; already told by the 05:23 1h patrol) aged out of this window start 84366701 and was not retried this pass (still unfilled). "
    f"Leftover official 404 W47N8@84366200 (hole 84366201..84366300 still db {hole_w47n8_66200['distinct']}/100, no rows; already told by the 05:23 1h patrol) aged out of this window start 84366701 and was not retried this pass (still unfilled). "
    f"Leftover official 404 W45N7@84365200 (hole 84365201..84365300 still db {hole_w45n7_65200['distinct']}/100, no rows; already told by the 04:21 1h patrol) aged out of this window start 84366701 and was not retried this pass (still unfilled). "
    f"Leftover official 404 W47N8@84363900 (hole 84363901..84364000 still db {hole_w47n8_63900['distinct']}/100 live-only 84363951..84364000, missing 84363901..84363950; already told by the 02:34 1h patrol) aged out of this window start 84366701 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W46N8@84362700 (hole 84362701..84362800 still db {hole_w46n8_62700['distinct']}/100, no live rows; already told by the 01:26 1h patrol) aged out of this window start 84366701 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W47N8@84361700 (hole 84361701..84361800 still db {hole_w47n8_61700['distinct']}/100 live-only; already told) aged out of this window start 84366701 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W46N8@84360600 (hole 84360601..84360700 still db {hole_w46n8_60600['distinct']}/100 live-only; already told) aged out and was not retried (still unfilled). "
    f"Aged leftover official 404 W45N7@84360200 (hole 84360201..84360300 still db {aged_w45n7_60200['distinct']}/100; already told) and W47N8@84359900 (hole 84359901..84360000 still db {aged_w47n8_59900['distinct']}/100; already told) also sit outside this window and were not retried (still unfilled). "
    "Aged leftover official 404 W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) were not retried this pass "
    "(already outside this 40-min window). "
    "This window has empty_no_creep=0."
)
confirm_summary = (
    "confirm/retry2 skipped 2026-11-20 06:06 Asia/Hong_Kong "
    "(first pass 35/35 official GETs 200, missing_chunks=0; no in-window official 404 to confirm or retry); "
    + just_note
    + "; this pass inserted 11537 additional rows in the reconstructed window (W46N8 1333 / W47N8 5401 / W45N8 1617 / W45N7 1150 / W47N7 2036) on top of the 05:30 half-hour official fill and just-published 84367000 for all 5"
)

vs_first_over45 = (vs_cand.get("first") or vs_first or {}).get("over45")
vs_first_over15 = (vs_cand.get("first") or vs_first or {}).get("over15")
span_vs = (vs_cand.get("span_mean") or {})
prev_vs = (vs_cand.get("prev_later") or {})
later_vs = (vs_cand.get("later_raw") or vs_cand.get("later_robust") or {})
first_vs = (vs_cand.get("first") or vs_first or {})
all_vs = (vs_cand.get("all_mean") or {})
tick_s_corr_txt = (
    f"script {TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band and is live-anchor-best "
    f"(over45={first_vs.get('over45')} mean_off={float(first_vs.get('mean_off') or 0):.1f}, over15={first_vs.get('over15')}); "
    f"later-mean-robust {TICK_S_LATER:.5f} also over45=0 but worse abs mean_off "
    f"({float(later_vs.get('mean_off') or 0):.1f}) and was refused; "
    f"all_mean {tick_s.get('all_mean_w46'):.5f}; prev_later {tick_s.get('prev_later_mean'):.5f} "
    f"(over45={prev_vs.get('over45')} mean_off={float(prev_vs.get('mean_off') or 0):.1f}). "
    f"First-pass realign moved {TS_REALIGNED_FIRST} rows onto {TICK_S_FIRST:.5f}; "
    f"no corrective realign (already inside the 45s gate); in-use first {TICK_S_IN_USE:.5f}; "
    f"no in-window official 404; {just_note}"
)

f0442 = ", ".join(f"{r} {freeze0442[r]['distinct']}/269" for r in ROOMS)
f0518 = ", ".join(f"{r} {freeze0518[r]['distinct']}/39" for r in ROOMS)
f0534 = ", ".join(f"{r} {restart0534[r]['distinct']}/29" for r in ROOMS)
f0553 = ", ".join(f"{r} {freeze0553[r]['distinct']}/69" for r in ROOMS)
f0559 = ", ".join(f"{r} {freeze0559[r]['distinct']}/29" for r in ROOMS)
just_fill = ", ".join(f"{r} {just_pub[r]['distinct']}/100" for r in ROOMS)

freeze_para = (
    f"New box freeze 05:53:08-05:56:59 Asia/Hong_Kong (223s; run_listener.sh auto-restart 05:57:02; not yet told, for the next 1h patrol) "
    f"room_stats gap 84367301..84367369 (69) is fully inside this reconstructed window and official-filled 69/69 in all 5 (counts {f0553}). "
    f"New box freeze 05:59:54-06:01:32 Asia/Hong_Kong (90s; run_listener.sh auto-restart 06:01:35, listener.py pid 1159748 started 06:01:45; not yet told, for the next 1h patrol) "
    f"room_stats gap 84367401..84367429 (29) sits in just-published 84367400 and was official-filled 29/29 in all 5 (counts {f0559}). "
    f"Box freeze 05:18:07-05:19:42 Asia/Hong_Kong (89s; already told by the 05:23 1h patrol) "
    f"room_stats gap 84366781..84366819 (39) is fully inside this window and official-filled 39/39 in all 5 (counts {f0518}). "
    f"Box freeze 04:42:44-05:00:03 Asia/Hong_Kong (1033s; already told by the 05:23 1h patrol) "
    f"room_stats gap 84366271..84366539 (269) has aged out of this window start 84366701: official-filled 269/269 in W46N8/W45N8/W45N7; W47N8 239/269 missing 84366271..84366300 because leftover official 404 W47N8@84366200; W47N7 230/269 missing 84366501..84366539 because leftover official 404 W47N7@84366500 (counts {f0442}). "
    f"Listener auto-restart 05:34:07 is not a box freeze (absent from box_pauses.jsonl). Its room_stats gap 84367001..84367029 (29) is inside this reconstructed window and now official-filled 29/29 in all 5, including W47N7 (counts {f0534}; last run had classified W47N7 84367001..84367099 as official empty_no_creep, this pass recovered W47N7 84367001..84367100 to {recovered_w47n7_67000['distinct']}/100 ticks / {recovered_w47n7_67000['rows']} rows). "
    f"This run found the listener already auto-restarted (pid 1159748) and did not itself restart it. "
    f"Prior box freeze 03:46:06-04:06:15 and earlier freezes have aged out of this window start 84366701 (already told). "
    f"Leftover official 404 W47N7@84366500 (hole 84366501..84366600 still db {hole_w47n7_66500['distinct']}/100; already told by the 05:23 1h patrol) aged out of this window and was not retried. "
    f"Leftover official 404 W47N8@84366200 (hole 84366201..84366300 still db {hole_w47n8_66200['distinct']}/100; already told by the 05:23 1h patrol) aged out of this window and was not retried. "
    f"Leftover official 404 W45N7@84365200 (hole 84365201..84365300 still db {hole_w45n7_65200['distinct']}/100; already told by the 04:21 1h patrol) aged out of this window and was not retried. "
    f"Leftover official 404 W47N8@84363900 (hole 84363901..84363950 still db {hole_w47n8_63900['distinct']}/100 live-only 84363951..84364000; already told by the 02:34 1h patrol) aged out of this window and was not retried. "
    f"Aged official 404 W46N8@84362700, W47N8@84361700, W46N8@84360600, W45N7@84360200, W47N8@84359900, W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300 (and older) remain outside this window. "
    f"This window empty_no_creep=0. Just-published 84367400 was 200 for all 5 (db fill {just_fill}). "
    f"live.json / stats.t were fresh at pre-check 06:03:51 (age ~1.0s, tip stats.t=84367450, roomSlot W47N8 objects_n=0 just after the 06:01:35 auto-restart / gameTime=None, CPU/path were flowing); "
    f"this pass inserted 11537 additional rows in 84366701..84367400, and {just_note}; "
    f"single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through {cpu_tip} / path_arrivals through {path_tip} at wrapup); this run did not restart the listener."
)

listener_line = (
    f"listener single_slot={not yield_present} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; "
    "no second listener started; no war_cmd/pulse restart."
)
ok_line = (
    f"ok_quiet=True coverage={recovered}/{expected} inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_TOTAL} "
    f"tick_s_in_use={TICK_S_IN_USE} listener single_slot={not yield_present}; no second listener; no war_cmd/pulse restart."
)

now_text = "\n".join([
    f"{finished_hkt} half-hour backfill OK (quiet)",
    f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
    f"  ({FIRST_PASS_LINE}; see history_backfill.txt)",
    f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST:.5f}; {tick_s_corr_txt})",
    f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks={MISSING_CHUNKS}",
    f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
    f"per_room {PER_ROOM_LINE}",
    f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 +{INSERTED_RETRY2}, just_published +{INSERTED_JUST} actual / script {INSERTED_JUST_SCRIPT}, window {INSERTED_WINDOW}, run total {INSERTED_TOTAL})",
    f"ts_realigned_first={TS_REALIGNED_FIRST} ts_realigned_corrective={NFIX_CORR} tick_s_in_use={TICK_S_IN_USE:.5f}",
    "db_after",
    db_after_lines,
    f"coverage official_recovered={recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing} unique_room_ticks={unique_after.get('distinct_room_ticks')}",
    f"{inwin_txt}",
    f"{leftover_txt}",
    freeze_para,
    listener_line,
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
    "later_mean_applied_then_reverted": False,
    "override_poisoned_first": False,
    "reconstructed_rows": RECON_ROWS,
    "already_in_db": ALREADY,
    "inserted_first": INSERTED_FIRST,
    "inserted_confirm": INSERTED_CONFIRM,
    "inserted_retry2": INSERTED_RETRY2,
    "inserted_just_published": INSERTED_JUST,
    "inserted_just_published_script": INSERTED_JUST_SCRIPT,
    "inserted_window": INSERTED_WINDOW,
    "inserted_total": INSERTED_TOTAL,
    "missing_chunks": MISSING_CHUNKS,
    "first_pass": FIRST_PASS_LINE,
    "per_room": PER_ROOM_LINE,
    "coverage": coverage_payload,
    "tick_s_realign": tick_s,
    "just_published": just_pub_payload,
    "confirm": confirm_payload,
    "retry2": (confirm_payload.get("retry2") or {}),
    "listener": {
        "single_slot": not yield_present,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": yield_present,
        "pid": 1159748,
        "started": "2026-11-20 06:01:45",
        "auto_restart_at": "2026-11-20 06:01:35",
        "prior_auto_restart_at": "2026-11-20 05:57:02",
    },
    "box_freeze": {
        "from": "2026-11-20 05:59:54",
        "to": "2026-11-20 06:01:32",
        "sec": 90,
        "restart_at": ["2026-11-20 06:01:35"],
        "listener_pid": 1159748,
        "listener_started": "2026-11-20 06:01:45",
        "room_stats_gap": [84367401, 84367429, 29],
        "official_fill": {r: freeze0559[r] for r in ROOMS},
        "told_by": None,
        "not_yet_told": True,
        "prior_0553": {"from": "2026-11-20 05:53:08", "to": "2026-11-20 05:56:59", "sec": 223, "restart_at": "2026-11-20 05:57:02", "gap": [84367301, 84367369, 69], "fill": {r: freeze0553[r] for r in ROOMS}, "told_by": None, "not_yet_told": True},
        "prior_0518": {"gap": [84366781, 84366819, 39], "fill": {r: freeze0518[r] for r in ROOMS}, "told_by": "05:23 1h patrol"},
        "prior_0442": {"gap": [84366271, 84366539, 269], "fill": {r: freeze0442[r] for r in ROOMS}, "told_by": "05:23 1h patrol"},
        "listener_autorestart_0534_not_a_box_freeze": {
            "restart_at": "2026-11-20 05:34:07",
            "room_stats_gap": [84367001, 84367029, 29],
            "official_fill": {r: restart0534[r] for r in ROOMS},
            "in_box_pauses": False,
            "w47n7_recovered_this_pass": recovered_w47n7_67000,
        },
    },
    "new_official_404_not_yet_told": [],
    "new_box_freezes_not_yet_told": [
        {"from": "2026-11-20 05:53:08", "to": "2026-11-20 05:56:59", "sec": 223, "gap": [84367301, 84367369, 69], "fill": "69/69 all 5", "restart_at": "2026-11-20 05:57:02"},
        {"from": "2026-11-20 05:59:54", "to": "2026-11-20 06:01:32", "sec": 90, "gap": [84367401, 84367429, 29], "fill": "29/29 all 5", "restart_at": "2026-11-20 06:01:35"},
    ],
    "already_told_still_unfilled": [
        "W47N7@84366500",
        "W47N8@84366200",
        "W45N7@84365200",
        "W47N8@84363900",
        "W46N8@84362700",
        "W47N8@84361700",
        "W46N8@84360600",
        "W45N7@84360200",
        "W47N8@84359900",
    ],
    "inwin_txt": inwin_txt,
    "leftover_txt": leftover_txt,
    "freeze_para": freeze_para,
    "confirm_summary": confirm_summary,
    "listener_line": listener_line,
    "ok_line": ok_line,
    "wrapup_cpu_tip": cpu_tip,
    "wrapup_path_tip": path_tip,
    "wrapup_rs_tip": rs_tip,
    "just_pub_db": just_pub,
    "freeze0442_db": freeze0442,
    "freeze0518_db": freeze0518,
    "restart0534_db": restart0534,
    "freeze0553_db": freeze0553,
    "freeze0559_db": freeze0559,
    "hole_w47n8_66200": hole_w47n8_66200,
    "hole_w47n7_66500": hole_w47n7_66500,
    "recovered_w47n7_67000": recovered_w47n7_67000,
}

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
(DIR / "history_backfill_now.txt").write_text(now_text)
shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")
shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

verify = [
    f"{finished_hkt_sec} verify 06:00 half-hour official-history backfill",
    f"window ticks {TMIN}..{TMAX} published_bases {PUB_BASES} game.time_first={GT_FIRST}",
    f"inserted_first={INSERTED_FIRST} confirm={INSERTED_CONFIRM} retry2={INSERTED_RETRY2} just_published={INSERTED_JUST} (script {INSERTED_JUST_SCRIPT}) total={INSERTED_TOTAL}",
    f"coverage {recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}",
    f"tick_s_in_use={TICK_S_IN_USE:.5f} ts_realigned_first={TS_REALIGNED_FIRST} ts_realigned_corrective={NFIX_CORR}",
    f"{inwin_txt}",
    f"{leftover_txt}",
    freeze_para,
    listener_line,
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 06:01:35 (listener.py pid 1159748 started 06:01:45), after the new box freeze 05:59:54-06:01:32 (90s, room_stats gap 84367401..84367429; official-filled this pass in just-published 84367400; not yet told, for the next 1h patrol). Earlier this hour: 05:57:02 after the new box freeze 05:53:08-05:56:59 (223s, room_stats gap 84367301..84367369; official-filled 69/69 in this window; not yet told). The 05:34:07 restart is not a box freeze (not in box_pauses.jsonl). Earlier already-told: 05:19:45 after 05:18:07-05:19:42; 05:00:06 after 04:42:44-05:00:03 (both told by the 05:23 1h patrol). By pre-check 06:03:51 live.json was fresh (stats.t=84367450, roomSlot W47N8, objects_n=0 / gameTime=None just after the 06:01 restart) and CPU/path buffers were flowing; single_slot held.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0600.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
print(summary, end="")
print("ok_line", ok_line)
