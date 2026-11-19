#!/usr/bin/env python3
"""Write local status records for the 05:30 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-20_0530"
assert "_halfhour_2026-11-20_0530" in str(DIR), DIR
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84366301, 84367000
PUB_BASES = "84366300..84366900"
GT_FIRST = 84367038
TICK_S_FIRST = 3.93473
TICK_S_PRINTED = "3.935"
TICK_S_IN_USE = 4.11311  # prev_later; first-pass 3.93473 poisoned the live-anchor comparison; override after independent room_stats / post-window listener check
TICK_S_LATER = 4.17005
TS_REALIGNED_FIRST = 18072
NFIX_CORR = 18114  # override onto prev_later at gt=84367085 (tick_s_check had first applied nfix=34 onto poisoned 3.93473)
GT_CORR = 84367085
RECON_ROWS = 27574
ALREADY = 24620
INSERTED_FIRST = 2954
INSERTED_CONFIRM = 0  # W47N7@84366500 stayed 404 after confirm and retry2
INSERTED_RETRY2 = 0
# just_published script reported 2525 (W47N7 119) but db shows W47N7 +1 row only
# (official 200, empty_no_creep 84367001..84367099, w8rhauler at 84367100). Use actual db inserts.
INSERTED_JUST_SCRIPT = 2525
INSERTED_JUST = 2407  # 770+639+498+499+1
PER_ROOM_LINE = "W46N8:700t/616new W47N8:700t/1123new W45N8:700t/509new W45N7:700t/492new W47N7:600t/214new"
FIRST_PASS_CORE = (
    "first pass 34 of 35 official GETs 200, missing_chunks=1 W47N7@84366500; "
    "05:00 half-hour already wrote through 84366400 / reconstructed through 84366500 (just-published 84366500 was attempted then at 05:07:50 gt=84366641 and recovered W46N8/W47N8/W45N8/W45N7, ticks 84366501..84366600; W47N7@84366500 stayed official 404); "
    "concurrent 1h patrol was delivered ~05:23 (next ~06:17); "
    "(this pass already_in_db=24620 / inserted=2954; overlap 84366301..84367000 already partly present from the 05:00 half-hour official fill, just-published 84366500 for 4 rooms, and live rotation; "
    "this pass inserted 2954 additional rows: W46N8 616, W47N8 1123, W45N8 509, W45N7 492, W47N7 214; W47N7 600t because of the 404 hole; "
    "box freeze 04:42:44-05:00:03 STATS gap 84366271..84366539 (269) still overlaps the start of this window: official-filled 269/269 in W46N8/W45N8/W45N7, W47N8 239/269 missing 84366271..84366300 because leftover official 404 W47N8@84366200 aged out of this window start 84366301, W47N7 230/269 missing 84366501..84366539 because in-window official 404 W47N7@84366500; already told by the 05:23 1h patrol; "
    "box freeze 05:18:07-05:19:42 STATS gap 84366781..84366819 (39) is fully inside this window and official-filled 39/39 in all 5 (already told by the 05:23 1h patrol); "
    "listener auto-restart 05:34:07 (pid 1149422 started 05:34:17) is not a box freeze (not in box_pauses.jsonl); its STATS gap 84367001..84367029 sits in just-published 84367000; "
    "leftover official 404 W47N8@84366200 aged out of this 40-min window and was not retried (hole 84366201..84366300 still unfilled, db 0/100; already told by the 05:23 1h patrol); "
    "leftover official 404 W45N7@84365200, W47N8@84363900, W46N8@84362700, W47N8@84361700, W46N8@84360600, W45N7@84360200, W47N8@84359900, W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out and were not retried; "
    "in-window official 404: W47N7@84366500 (hole 84366501..84366600, confirm 05:38:35 gt=84367087 and retry2 05:40:31 gt=84367115 both stayed official 404; already told by the 05:23 1h patrol); "
    "this window empty_no_creep=0"
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
just_pub_path = DIR / "just_published_84367000.json"
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
    f"just-published 84367000 attempted at {just_at} game.time={just_gt} "
    f"(typically publishable around game.time>=84367140) and was "
    + ("200 for all 5 rooms" if all_five else f"not fully published (recovered={just_recovered or []} still_404={just_still_404 or []})")
    + f" (script inserted={INSERTED_JUST_SCRIPT}, actual db inserted={INSERTED_JUST}; "
    "W47N7 official empty_no_creep 84367001..84367099 with only w8rhauler84365861 at 18,1 on 84367100, "
    "script counted 119 but db +1; the other four rooms matched the script counts); "
    "ticks 84367001..84367100 sit just after this reconstructed window"
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
    just_pub = {room: rng(c, room, 84367001, 84367100, 100) for room in ROOMS}
    freeze0442 = {room: rng(c, room, 84366271, 84366539, 269) for room in ROOMS}
    freeze0518 = {room: rng(c, room, 84366781, 84366819, 39) for room in ROOMS}
    restart0534 = {room: rng(c, room, 84367001, 84367029, 29) for room in ROOMS}
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
    "in-window official 404 after first pass: 34 of 35 official GETs 200, missing_chunks=1 W47N7@84366500 "
    f"(hole 84366501..84366600, db {hole_w47n7_66500['distinct']}/100); "
    "confirm 05:38:35 gt=84367087 and retry2 05:40:31 gt=84367115 both stayed official 404; "
    "final official_404_in_window=100 (W47N7 100 ticks); already told by the 05:23 1h patrol"
)
leftover_txt = (
    f"Leftover official 404 W47N8@84366200 (hole 84366201..84366300 still db {hole_w47n8_66200['distinct']}/100, no rows; already told by the 05:23 1h patrol) aged out of this window start 84366301 and was not retried this pass (still unfilled). "
    f"Leftover official 404 W45N7@84365200 (hole 84365201..84365300 still db {hole_w45n7_65200['distinct']}/100, no rows; already told by the 04:21 1h patrol) aged out of this window start 84366301 and was not retried this pass (still unfilled). "
    f"Leftover official 404 W47N8@84363900 (hole 84363901..84364000 still db {hole_w47n8_63900['distinct']}/100 live-only 84363951..84364000, missing 84363901..84363950; already told by the 02:34 1h patrol) aged out of this window start 84366301 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W46N8@84362700 (hole 84362701..84362800 still db {hole_w46n8_62700['distinct']}/100, no live rows; already told by the 01:26 1h patrol) aged out of this window start 84366301 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W47N8@84361700 (hole 84361701..84361800 still db {hole_w47n8_61700['distinct']}/100 live-only; already told) aged out of this window start 84366301 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W46N8@84360600 (hole 84360601..84360700 still db {hole_w46n8_60600['distinct']}/100 live-only; already told) aged out and was not retried (still unfilled). "
    f"Aged leftover official 404 W45N7@84360200 (hole 84360201..84360300 still db {aged_w45n7_60200['distinct']}/100; already told) and W47N8@84359900 (hole 84359901..84360000 still db {aged_w47n8_59900['distinct']}/100; already told) also sit outside this window and were not retried (still unfilled). "
    "Aged leftover official 404 W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) were not retried this pass "
    "(already outside this 40-min window). "
    "This window has empty_no_creep=0 (just-published W47N7 empty_no_creep 84367001..84367099 sits just after the reconstructed window)."
)
confirm_summary = (
    "confirm 05:38:35 gt=84367087 and retry2 05:40:31 gt=84367115 both stayed official 404 on W47N7@84366500 (first pass 34/35 official GETs 200, missing_chunks=1); "
    + just_note
    + "; this pass inserted 2954 additional rows in the reconstructed window (W46N8 616 / W47N8 1123 / W45N8 509 / W45N7 492 / W47N7 214) on top of the 05:00 half-hour official fill and just-published 84366500 for 4 rooms"
)

vs_first_over45 = (vs_cand.get("first") or vs_first or {}).get("over45")
vs_first_over15 = (vs_cand.get("first") or vs_first or {}).get("over15")
span_vs = (vs_cand.get("span_mean") or {})
prev_vs = (vs_cand.get("prev_later") or {})
later_vs = (vs_cand.get("later_raw") or vs_cand.get("later_robust") or {})
first_vs = (vs_cand.get("first") or vs_first or {})
all_vs = (vs_cand.get("all_mean") or {})
after_ov = tick_s.get("after_override_vs_prev_later") or {}
tick_s_corr_txt = (
    f"script {TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is a short first-interval blip in the sane 3-6s band "
    f"(same 84366300..84366400 interval was 3.93473 in the 05:00 run); "
    f"later-mean-robust {TICK_S_LATER:.5f} is pulled high by the compensating 4.34978 interval after the blip; "
    f"all_mean {tick_s.get('all_mean_w46'):.5f}; prev_later {TICK_S_IN_USE:.5f}. "
    f"First-pass realign moved {TS_REALIGNED_FIRST} rows onto 3.93473, which poisoned the live-anchor comparison "
    f"(tick_s_check then chose first and applied nfix=34 more onto 3.93473). "
    f"Independent check: room_stats in-window (not moved by history backfill) had over45=50/88 mean_off=-59s vs first, "
    f"but over45=0 mean_off=-3.67s vs prev_later 4.11311 and over45=0 mean_off=1.84s vs all_mean 4.13083; "
    f"post-window listener creep_ticks >84367000 also prefer ~4.11-4.13. "
    f"Override realigned {NFIX_CORR} official-window rows onto prev_later {TICK_S_IN_USE:.5f} at 05:38:26 gt={GT_CORR} "
    f"for continuity with the 05:00 half-hour; after over45={after_ov.get('over45')} mean_off={after_ov.get('mean_off')}; "
    f"in-use prev_later {TICK_S_IN_USE:.5f}; "
    f"in-window official 404 W47N7@84366500; {just_note}"
)

f0442 = ", ".join(f"{r} {freeze0442[r]['distinct']}/269" for r in ROOMS)
f0518 = ", ".join(f"{r} {freeze0518[r]['distinct']}/39" for r in ROOMS)
f0534 = ", ".join(f"{r} {restart0534[r]['distinct']}/29" for r in ROOMS)
just_fill = ", ".join(f"{r} {just_pub[r]['distinct']}/100" for r in ROOMS)

freeze_para = (
    f"Box freeze 04:42:44-05:00:03 Asia/Hong_Kong (1033s; run_listener.sh auto-restart 05:00:06; already told by the 05:23 1h patrol) "
    f"room_stats gap 84366271..84366539 (269): official-filled 269/269 in W46N8/W45N8/W45N7; W47N8 239/269 missing 84366271..84366300 because leftover official 404 W47N8@84366200 aged out of this window start 84366301; W47N7 230/269 missing 84366501..84366539 because in-window official 404 W47N7@84366500 (counts {f0442}). "
    f"Box freeze 05:18:07-05:19:42 Asia/Hong_Kong (89s; run_listener.sh auto-restart 05:19:45, then listener.py was later auto-restarted again at 05:34:07 / pid 1149422 started 05:34:17; already told by the 05:23 1h patrol) "
    f"room_stats gap 84366781..84366819 (39) is fully inside this window and official-filled 39/39 in all 5 (counts {f0518}). "
    f"Listener auto-restart 05:34:07 is not a box freeze (absent from box_pauses.jsonl). Its room_stats gap 84367001..84367029 (29) sits in just-published 84367000: official-filled 29/29 in W46N8/W47N8/W45N8/W45N7; W47N7 official empty_no_creep 0/29 (counts {f0534}). "
    f"This run found the listener already auto-restarted (pid 1149422) and did not itself restart it. "
    f"Prior box freeze 03:46:06-04:06:15 and earlier freezes have aged out of this window start 84366301 (already told). "
    f"In-window official 404 W47N7@84366500 (hole 84366501..84366600 still db {hole_w47n7_66500['distinct']}/100; confirm 05:38:35 and retry2 05:40:31 stayed official 404; already told by the 05:23 1h patrol). "
    f"Leftover official 404 W47N8@84366200 (hole 84366201..84366300 still db {hole_w47n8_66200['distinct']}/100; already told by the 05:23 1h patrol) aged out of this window and was not retried. "
    f"Leftover official 404 W45N7@84365200 (hole 84365201..84365300 still db {hole_w45n7_65200['distinct']}/100; already told by the 04:21 1h patrol) aged out of this window and was not retried. "
    f"Leftover official 404 W47N8@84363900 (hole 84363901..84363950 still db {hole_w47n8_63900['distinct']}/100 live-only 84363951..84364000; already told by the 02:34 1h patrol) aged out of this window and was not retried. "
    f"Aged official 404 W46N8@84362700, W47N8@84361700, W46N8@84360600, W45N7@84360200, W47N8@84359900, W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300 (and older) remain outside this window. "
    f"This window empty_no_creep=0. Just-published 84367000 was 200 for all 5 (db fill {just_fill}); W47N7 official empty_no_creep 84367001..84367099. "
    f"live.json / stats.t were fresh at pre-check 05:34:46 (age ~1.2s, tip stats.t=84367030, roomSlot W47N8 objects_n=0 just after the 05:34:07 auto-restart / gameTime=None, CPU/path were flowing); "
    f"this pass inserted 2954 additional rows in 84366301..84367000, and {just_note}; "
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
    "override_poisoned_first": True,
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
        "pid": 1149422,
        "started": "2026-11-20 05:34:17",
        "auto_restart_at": "2026-11-20 05:34:07",
    },
    "box_freeze": {
        "from": "2026-11-20 05:18:07",
        "to": "2026-11-20 05:19:42",
        "sec": 89,
        "restart_at": ["2026-11-20 05:19:45", "2026-11-20 05:34:07"],
        "listener_pid": 1149422,
        "listener_started": "2026-11-20 05:34:17",
        "room_stats_gap": [84366781, 84366819, 39],
        "official_fill": {r: freeze0518[r] for r in ROOMS},
        "told_by": "05:23 1h patrol",
        "prior_0442": {"gap": [84366271, 84366539, 269], "fill": {r: freeze0442[r] for r in ROOMS}, "told_by": "05:23 1h patrol"},
        "listener_autorestart_0534_not_a_box_freeze": {
            "restart_at": "2026-11-20 05:34:07",
            "pid": 1149422,
            "started": "2026-11-20 05:34:17",
            "room_stats_gap": [84367001, 84367029, 29],
            "official_fill": {r: restart0534[r] for r in ROOMS},
            "in_box_pauses": False,
        },
    },
    "new_official_404_not_yet_told": [],
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
    "hole_w47n8_66200": hole_w47n8_66200,
    "hole_w47n7_66500": hole_w47n7_66500,
}

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
(DIR / "history_backfill_now.txt").write_text(now_text)
shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")
shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

verify = [
    f"{finished_hkt_sec} verify 05:30 half-hour official-history backfill",
    f"window ticks {TMIN}..{TMAX} published_bases {PUB_BASES} game.time_first={GT_FIRST}",
    f"inserted_first={INSERTED_FIRST} confirm={INSERTED_CONFIRM} retry2={INSERTED_RETRY2} just_published={INSERTED_JUST} (script {INSERTED_JUST_SCRIPT}) total={INSERTED_TOTAL}",
    f"coverage {recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}",
    f"tick_s_in_use={TICK_S_IN_USE:.5f} ts_realigned_first={TS_REALIGNED_FIRST} ts_realigned_corrective={NFIX_CORR}",
    f"{inwin_txt}",
    f"{leftover_txt}",
    freeze_para,
    listener_line,
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 05:34:07 (listener.py pid 1149422 started 05:34:17), after 05:19:45 following the already-told box freeze 05:18:07-05:19:42. The 05:34:07 restart is not a box freeze (not in box_pauses.jsonl). Earlier: 05:00:06 after 04:42:44-05:00:03 (already told by the 05:23 1h patrol). By pre-check 05:34:46 live.json was fresh (stats.t=84367030, roomSlot W47N8, objects_n=0 / gameTime=None just after the 05:34 restart) and CPU/path buffers were flowing; single_slot held.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0530.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
print(summary, end="")
print("ok_line", ok_line)
