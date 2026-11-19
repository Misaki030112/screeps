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
DIR = ROOT / "state" / "_halfhour_2026-11-20_0130"
assert "_halfhour_2026-11-20_0130" in str(DIR), DIR
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84362801, 84363500
PUB_BASES = "84362800..84363400"
GT_FIRST = 84363533
TICK_S_FIRST = 3.98410
TICK_S_PRINTED = "3.984"
TICK_S_IN_USE = 3.98410  # first; later_raw/robust 4.10926 worse (over45=13303); all_mean 4.08798 also worse (over45=12464)
TICK_S_LATER = 4.10926
TS_REALIGNED_FIRST = 13303
NFIX_CORR = 2233
GT_CORR = 84363553
RECON_ROWS = 27871
ALREADY = 22445
INSERTED_FIRST = 5426
INSERTED_CONFIRM = 0  # no in-window official 404; confirm/retry2 skipped
INSERTED_RETRY2 = 0
PER_ROOM_LINE = "W46N8:700t/1484new W47N8:700t/762new W45N8:700t/986new W45N7:700t/844new W47N7:700t/1350new"
FIRST_PASS_CORE = (
    "first pass 35 of 35 official GETs 200, missing_chunks=0; "
    "01:11 half-hour already wrote through 84362900 / reconstructed through 84363000 (just-published 84363000 was attempted then at 01:08:36 gt=84363143 and was 200 for all 5, ticks 84363001..84363100); "
    "the 01:26 1h patrol already official-filled the 01:14:19-01:18:28 freeze STATS gap 84363221..84363299 (79/79 in all 5; published segment 84363220-84363300 official-filled 80/80); "
    "(this pass already_in_db=22445 / inserted=5426; overlap 84362801..84363100 already present from the 01:11 half-hour plus live rotation and the 01:26 patrol official fill; "
    "this pass newly wrote 84363100..84363400 for all 5, filling the official-covered portion of the NEW 01:30:52-01:33:08 freeze STATS gap 84363461..84363509 (84363461..84363500 in-window, tail 84363501..84363509 via just-published 84363500); "
    "prior 01:14:19-01:18:28 freeze STATS gap 84363221..84363299 remains official-filled 79/79 in all 5 (already filled by the 01:26 patrol); "
    "prior 00:45:20-01:01:07 freeze STATS gap 84362801..84363039 remains official-filled 239/239 in all 5 (already filled by the 01:11 half-hour and told by the 01:26 patrol); "
    "prior 00:31:21-00:32:40 freeze STATS gap 84362591..84362619 and 00:13:42-00:18:42 freeze STATS gap 84362331..84362419 have aged out of this window start 84362801); "
    "leftover official 404 W46N8@84362700 aged out of this 40-min window and was not retried (hole 84362701..84362800 still db 0/100; already told by the 01:26 1h patrol); "
    "leftover official 404 W47N8@84361700, W46N8@84360600, W45N7@84360200, W47N8@84359900, W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out and were not retried; "
    "in-window official 404: none"
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
just_pub_path = DIR / "just_published_84363500.json"
just_pub_payload = json.loads(just_pub_path.read_text()) if just_pub_path.exists() else {}

finished = datetime.now(HK)
finished_hkt = finished.strftime("%Y-%m-%d %H:%M Asia/Hong_Kong")
finished_hkt_sec = finished.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

def rng(c, room, t0, t1, expected):
    d, n, mn, mx = c.execute(
        "SELECT count(DISTINCT tick), count(*), min(tick), max(tick) "
        "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, t0, t1),
    ).fetchone()
    return {"distinct": d or 0, "rows": n or 0, "min": mn, "max": mx, "missing": expected - (d or 0)}

# Parse just-published result
INSERTED_JUST = int(just_pub_payload.get("inserted") or 0)
just_codes = just_pub_payload.get("gets") or just_pub_payload.get("results") or []
just_recovered = just_pub_payload.get("recovered") or just_pub_payload.get("first_try_recovered") or []
just_still_404 = just_pub_payload.get("still_404") or just_pub_payload.get("first_try_still_404") or []
just_gt = just_pub_payload.get("game_time") or just_pub_payload.get("recovered_game_time")
just_at = just_pub_payload.get("at") or just_pub_payload.get("recovered_at") or just_pub_payload.get("hk")
if not just_at and just_pub_payload:
    just_at = just_pub_payload.get("started") or ""
# tolerate various schema keys used by backfill_just_published.py
if not just_recovered and isinstance(just_pub_payload.get("recovered_rooms"), list):
    just_recovered = just_pub_payload["recovered_rooms"]
if just_pub_payload.get("inserted") is None and just_pub_payload.get("inserted_total") is not None:
    INSERTED_JUST = int(just_pub_payload["inserted_total"])

INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST

if just_pub_payload:
    n200 = 0
    still = []
    rec = []
    # flatten gets if present
    gets = just_pub_payload.get("gets") or []
    if gets and not just_recovered:
        for g in gets:
            room = g.get("room")
            code = g.get("code") or g.get("status")
            label = f"{room}@84363500"
            if code in (200, "200", "ok"):
                n200 += 1
                rec.append(label)
            else:
                still.append(label)
        if rec:
            just_recovered = rec
        if still:
            just_still_404 = still
    all_five = (len(just_recovered) == 5 and not just_still_404) or n200 == 5
else:
    all_five = False

just_note = (
    f"just-published 84363500 attempted at {just_at} game.time={just_gt} "
    f"(typically publishable around game.time>=84363640) and was "
    + ("200 for all 5 rooms" if all_five else f"not fully published (recovered={just_recovered or []} still_404={just_still_404 or []})")
    + f" (inserted={INSERTED_JUST}); ticks 84363501..84363600 sit just after this reconstructed window"
)
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
    freeze0130 = {room: rng(c, room, 84363461, 84363509, 49) for room in ROOMS}
    freeze0114 = {room: rng(c, room, 84363221, 84363299, 79) for room in ROOMS}
    freeze0045 = {room: rng(c, room, 84362801, 84363039, 239) for room in ROOMS}
    hole_w46n8_62700 = rng(c, "W46N8", 84362701, 84362800, 100)
    hole_w47n8_61700 = rng(c, "W47N8", 84361701, 84361800, 100)
    hole_w46n8_60600 = rng(c, "W46N8", 84360601, 84360700, 100)
    aged_w45n7_60200 = rng(c, "W45N7", 84360201, 84360300, 100)
    aged_w47n8_59900 = rng(c, "W47N8", 84359901, 84360000, 100)
    just_pub = {room: rng(c, room, 84363501, 84363600, 100) for room in ROOMS}
db_after_lines = "\n".join(db_lines)

inwin_txt = (
    "in-window official 404 after first pass: 35 of 35 official GETs 200, missing_chunks=0; "
    "no confirm/retry2 (no in-window official 404); "
    "final official_404_in_window=0"
)
leftover_txt = (
    f"Aged leftover official 404 W46N8@84362700 (hole 84362701..84362800 still db {hole_w46n8_62700['distinct']}/100, no live rows; already told by the 01:26 1h patrol) aged out of this window start 84362801 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W47N8@84361700 (hole 84361701..84361800 still db {hole_w47n8_61700['distinct']}/100 live-only; already told) aged out of this window start 84362801 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W46N8@84360600 (hole 84360601..84360700 still db {hole_w46n8_60600['distinct']}/100 live-only; already told) aged out and was not retried (still unfilled). "
    f"Aged leftover official 404 W45N7@84360200 (hole 84360201..84360300 still db {aged_w45n7_60200['distinct']}/100; already told) and W47N8@84359900 (hole 84359901..84360000 still db {aged_w47n8_59900['distinct']}/100; already told) also sit outside this window and were not retried (still unfilled). "
    "Aged leftover official 404 W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) were not retried this pass "
    "(already outside this 40-min window). "
    "This window has empty_no_creep=0."
)
confirm_summary = (
    "confirm/retry2 skipped (no in-window official 404); "
    + just_note
    + "; this pass newly wrote 84363100..84363400 for all 5, filling the official-covered portion of the 01:30:52-01:33:08 freeze (just-published fills the tail when 200)"
)

vs_later_before = tick_s.get("still_over_45s_vs_later_before")
vs_first_over45 = (vs_cand.get("first") or vs_first or {}).get("over45")
vs_later_over15_before = tick_s.get("still_over_15s_vs_later_before")
vs_first_over15 = (vs_cand.get("first") or vs_first or {}).get("over15")
span_vs = (vs_cand.get("span_mean") or {})
prev_vs = (vs_cand.get("prev_later") or {})
later_vs = (vs_cand.get("later_robust") or vs_cand.get("later_raw") or {})
first_vs = (vs_cand.get("first") or vs_first or {})
all_vs = (vs_cand.get("all_mean") or {})
tick_s_corr_txt = (
    f"script {TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} (raw later-mean also 4.10926) is worse than live-anchor-best first {TICK_S_IN_USE:.5f} "
    f"(delta first-robust {TICK_S_FIRST-TICK_S_LATER:.5f} s/tick, ~{(GT_FIRST-TMIN)*abs(TICK_S_FIRST-TICK_S_LATER):.1f}s at tmin; "
    f"over45 later={later_vs.get('over45')} vs first={vs_first_over45} vs all_mean={all_vs.get('over45')} vs prev_later={prev_vs.get('over45')}, "
    f"over15 later={later_vs.get('over15')} vs first={vs_first_over15} vs all_mean={all_vs.get('over15')} vs prev_later={prev_vs.get('over15')}; "
    f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')}; "
    f"lowest_over45 among sane was {tick_s.get('lowest_over45_sane')} {TICK_S_IN_USE:.5f} "
    f"(mean_off {first_vs.get('mean_off')} closer to the live anchor than later {later_vs.get('mean_off')}, all_mean {all_vs.get('mean_off')} or prev_later {prev_vs.get('mean_off')}); "
    f"first-pass realign moved {TS_REALIGNED_FIRST} rows; "
    f"tick_s_check applied corrective first realign of {NFIX_CORR} rows at game.time={GT_CORR} "
    f"(later-mean-robust was refused as worse than first; after corrective still_over_45s_vs_target=0); "
    f"still_over_45s_vs_later={tick_s.get('still_over_45s_vs_later')}; skipped_cross_chunk={tick_s.get('skipped_cross_chunk')}; "
    f"in-use first {TICK_S_IN_USE:.5f}; "
    f"no in-window official 404; {just_note}"
)

stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
f0130 = ", ".join(f"{r} {freeze0130[r]['distinct']}/49" for r in ROOMS)
f0114 = ", ".join(f"{r} {freeze0114[r]['distinct']}/79" for r in ROOMS)
f0045 = ", ".join(f"{r} {freeze0045[r]['distinct']}/239" for r in ROOMS)
objs = live.get("objects") or {}
objects_n = len(objs) if isinstance(objs, (list, dict)) else 0
tail_note = (
    "just-published 84363500 filled tail 84363501..84363509"
    if all_five
    else "tail 84363501..84363509 still depends on just-published 84363500"
)
freeze_para = (
    f"NEW box freeze 01:30:52-01:33:08 Asia/Hong_Kong (131s) caused run_listener.sh auto-restart 01:33:11 (listener.py pid 1061385 started 01:33:21; this run found the listener after reconnect and did not itself restart it). "
    f"room_stats gap 84363461..84363509 (49): official-filled head 84363461..84363500 written in this first pass; {tail_note}; counts {f0130}. "
    f"Prior box freeze 01:14:19-01:18:28 Asia/Hong_Kong (248s; run_listener.sh auto-restart 01:18:31; already told by the 01:26 1h patrol) "
    f"room_stats gap 84363221..84363299 (79) remains official-filled 79/79 in all 5 "
    f"(01:26 patrol official-filled the published segment; counts {f0114}). "
    f"Prior box freeze 00:45:20-01:01:07 Asia/Hong_Kong (943s; restart 01:01:10; already told by the 01:26 1h patrol) "
    f"room_stats gap 84362801..84363039 (239) remains official-filled 239/239 in all 5 "
    f"(01:11 half-hour wrote 84362800..84362900 and just-published 84363000; counts {f0045}). "
    f"Prior box freezes 00:31:21-00:32:40, 00:13:42-00:18:42, 23:47:48-23:55:08, 23:20:04-23:24:46 and 22:55:09-23:02:20 have aged out of this window start 84362801. "
    f"Aged official 404 W46N8@84362700, W47N8@84361700, W46N8@84360600, W45N7@84360200, W47N8@84359900, W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300 (and older) remain outside this window. "
    f"This window empty_no_creep=0. "
    f"live.json / stats.t were fresh at pre-check 01:34:48 (age ~3.4s, tip stats.t=84363520, roomSlot W45N8 objects_n=0, live.json gameTime=None) after the 01:33:11 auto-reconnect and a short wait for CPU/path buffers; "
    f"CPU/path buffers were already flowing (creep_cpu through 84363520 / path_arrivals through 84363512); "
    f"this pass wrote 84363100..84363400 for all 5, and {just_note}; "
    f"single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84363520 / path_arrivals through 84363512 at pre-check; through {cpu_tip} / {path_tip} at wrapup); this run did not restart the listener."
)

single = True
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
    "later_mean_applied_nfix": 0,
    "later_mean_reverted_nfix": 0,
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
        "corrective_applied": True,
        "later_mean_w46": tick_s.get("later_mean_w46"),
        "later_mean_applied_then_reverted": False,
        "tick_s_in_use": TICK_S_IN_USE,
        "tick_s_in_use_name": tick_s.get("tick_s_in_use_name"),
        "still_over_45s_vs_later": tick_s.get("still_over_45s_vs_later"),
        "reason": tick_s.get("reason"),
        "prev_later_over45_before_corrective": (prev_vs or {}).get("over45"),
        "prev_later_mean": tick_s.get("prev_later_mean"),
        "lowest_over45_sane": tick_s.get("lowest_over45_sane"),
        "note": tick_s_corr_txt,
        "corrective_nfix": NFIX_CORR,
        "corrective_note": "corrective first realign of 2233 rows at gt=84363553; later refused as worse than first; after corrective still_over_45s_vs_target=0; skipped_cross_chunk=0",
    },
    "just_published": {
        "base": 84363500,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": just_at,
        "recovered_game_time": just_gt,
        "inserted": INSERTED_JUST,
        "note": just_note,
        "first_try_all_404": (not all_five and not just_recovered),
        "first_try_at": just_at,
        "first_try_game_time": just_gt,
        "first_try_recovered": list(just_recovered) if just_recovered else [],
        "first_try_still_404": list(just_still_404) if just_still_404 else [],
        "retry_at": None,
        "retry_game_time": None,
        "retry_inserted": 0,
        "ticks": [84363501, 84363600],
        "all_five_official_200": all_five,
        "still_404": list(just_still_404) if just_still_404 else [],
        "in_window_still_404": [],
        "w45n7_empty_no_creep": [],
        "w47n7_empty_no_creep": [],
        "distinct": just_pub,
        "skipped": not bool(just_pub_payload),
        "raw": just_pub_payload,
    },
    "confirm": {
        "at": None,
        "game_time": None,
        "inserted": 0,
        "script_reported_inserted": 0,
        "ssl_abort_first": None,
        "targets": 0,
        "recovered": [],
        "still_404": [],
        "skipped": True,
        "neighbors_at": None,
        "neighbors_game_time": None,
        "neighbors": {},
        "note": "confirm/retry2 skipped; no in-window official 404 (first pass 35/35 official 200)",
        "raw": {},
    },
    "retry2": {
        "at": None,
        "game_time": None,
        "inserted": 0,
        "script_reported_inserted": 0,
        "skipped": True,
        "recovered": [],
        "still_404": [],
        "note": "retry2 skipped; no in-window official 404",
    },
    "listener": {
        "single_slot": True,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 1061385,
        "pid_at_precheck": 1061385,
        "loop_pid": 4035476,
        "restart_at": "01:33:11",
        "listener_started": "01:33:21",
        "earlier_restart_this_hour": "01:18:31",
        "wrapup_ws_timeout": None,
        "wrapup_autorestart": None,
        "wrapup_listener_started": None,
        "this_run_restarted": False,
        "waited_for_reconnect": True,
        "live_objects_empty_after_reconnect": True,
        "live_gameTime_none_after_reconnect": True,
        "pre_cpu_path_after_wait": (
            f"creep_cpu through 84363520 / path_arrivals through 84363512 at pre-check 01:34:48 after a short wait following the 01:33:11 auto-reconnect; "
            f"live.json gameTime=None and objects_n=0 at pre-check (roomSlot W45N8, mid-rotation after reconnect); "
            f"stats.t and listener_rot were advancing (stats.t=84363520); "
            f"by wrapup roomSlot {live.get('roomSlot')} objects_n={objects_n}, "
            f"live.json gameTime={live.get('gameTime')} stats.t={stats.get('t')}, "
            f"creep_cpu through {cpu_tip} / path_arrivals through {path_tip}"
        ),
    },
    "box_freeze": {
        "from": "2026-11-20 01:30:52",
        "to": "2026-11-20 01:33:08",
        "sec": 131,
        "restart_at": "01:33:11",
        "room_stats_gap": "84363461..84363509",
        "official_filled": (
            "official-filled head 84363461..84363500 in all 5 rooms (this pass wrote 84363400 covering 84363401..84363500); "
            + ("just-published 84363500 filled tail 84363501..84363509" if all_five else "tail 84363501..84363509 awaits just-published 84363500")
        ),
        "counts": freeze0130,
        "earlier_restart_gap": "01:18:31 after 01:14:19-01:18:28; 01:01:10 after 00:45:20-01:01:07; 00:32:43 after 00:31:21-00:32:40; 00:18:45 after 00:13:42-00:18:42",
        "earlier_freeze": {
            "from": "2026-11-20 01:14:19",
            "to": "2026-11-20 01:18:28",
            "sec": 248,
            "restart_at": "01:18:31",
            "room_stats_gap": "84363221..84363299",
            "official_filled": "still official-filled 79/79 in all 5 rooms (already told / official-filled by the 01:26 1h patrol)",
            "counts": freeze0114,
        },
        "earlier_freeze_0045": {
            "from": "2026-11-20 00:45:20",
            "to": "2026-11-20 01:01:07",
            "sec": 943,
            "restart_at": "01:01:10",
            "room_stats_gap": "84362801..84363039",
            "official_filled": "still official-filled 239/239 in all 5 rooms (already told by the 01:26 1h patrol; filled by the 01:11 half-hour)",
            "counts": freeze0045,
        },
        "new_freeze_this_run": True,
        "already_recorded_by_patrol": False,
        "missed_halfhours": None,
    },
    "new_official_404_not_yet_told": [],
    "already_told_still_unfilled": [
        {"room": "W46N8", "base": 84362700, "hole": [84362701, 84362800], "db_distinct": hole_w46n8_62700["distinct"], "db_note": "db 0/100, no live rows; aged out of this window start 84362801, not retried, still unfilled; already told by the 01:26 1h patrol", "in_window": False},
        {"room": "W47N8", "base": 84361700, "hole": [84361701, 84361800], "db_distinct": hole_w47n8_61700["distinct"], "db_note": "aged out of this window start 84362801, not retried, still unfilled; already told", "in_window": False},
        {"room": "W46N8", "base": 84360600, "hole": [84360601, 84360700], "db_distinct": hole_w46n8_60600["distinct"], "db_note": "aged out, not retried, still unfilled; already told", "in_window": False},
        {"room": "W45N7", "base": 84360200, "hole": [84360201, 84360300], "db_distinct": aged_w45n7_60200["distinct"], "db_note": "aged out, not retried, still unfilled; already told", "in_window": False},
        {"room": "W47N8", "base": 84359900, "hole": [84359901, 84360000], "db_distinct": aged_w47n8_59900["distinct"], "db_note": "aged out, not retried, still unfilled; already told", "in_window": False},
    ],
}

ok_line = (
    f"ok_quiet=True coverage={recovered}/{expected} inserted_window={INSERTED_WINDOW} "
    f"inserted_total={INSERTED_TOTAL} tick_s_in_use={TICK_S_IN_USE:.5f} "
    f"listener single_slot=True; no second listener; no war_cmd/pulse restart."
)
payload["ok_line"] = ok_line

now_text = "\n".join([
    f"{finished_hkt} half-hour backfill OK (quiet)",
    f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
    f"  ({FIRST_PASS_LINE}; see history_backfill.txt)",
    f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST:.5f}; {tick_s_corr_txt})",
    f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks={MISSING_CHUNKS}",
    f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
    f"per_room {PER_ROOM_LINE}",
    f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 +{INSERTED_RETRY2}, just_published +{INSERTED_JUST}, window {INSERTED_WINDOW}, run total {INSERTED_TOTAL})",
    f"ts_realigned_first={TS_REALIGNED_FIRST} ts_realigned_corrective={NFIX_CORR} tick_s_in_use={TICK_S_IN_USE:.5f}",
    "db_after",
    db_after_lines,
    f"coverage official_recovered={recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing} unique_room_ticks={unique_after.get('distinct_room_ticks')}",
    f"{inwin_txt}",
    f"{leftover_txt}",
    freeze_para,
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    confirm_summary,
    ok_line,
]) + "\n"

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
(DIR / "history_backfill_now.txt").write_text(now_text)
shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")
shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

verify = [
    f"{finished_hkt_sec} verify 01:30 half-hour official-history backfill",
    f"window ticks {TMIN}..{TMAX} published_bases {PUB_BASES} game.time_first={GT_FIRST}",
    f"inserted_first={INSERTED_FIRST} confirm={INSERTED_CONFIRM} retry2={INSERTED_RETRY2} just_published={INSERTED_JUST} total={INSERTED_TOTAL}",
    f"coverage {recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}",
    f"tick_s_first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} in_use={TICK_S_IN_USE:.5f} later_mean_robust={TICK_S_LATER:.5f} corrective={tick_s.get('corrective_applied')} nfix={NFIX_CORR} later_mean_applied_then_reverted=False",
    f"{inwin_txt}",
    f"{leftover_txt}",
    freeze_para,
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 01:33:11 (listener.py pid 1061385 started 01:33:21) after the new box freeze 01:30:52-01:33:08 (131s, room_stats gap 84363461..84363509). Earlier: 01:18:31 after 01:14:19-01:18:28; 01:01:10 after 00:45:20-01:01:07; 00:32:43 after 00:31:21-00:32:40; 00:18:45 after 00:13:42-00:18:42. This run found the listener after the auto-reconnect and waited briefly for CPU/path buffers; by pre-check 01:34:48 live.json was fresh (gameTime=None, stats.t=84363520, roomSlot W45N8, objects_n=0) and CPU/path buffers were flowing (creep_cpu through 84363520 / path_arrivals through 84363512); single_slot held.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
# no retry2 file this pass; write a short skip note for the patrol convention
retry2_note = DIR / "backfill_retry2.txt"
retry2_note.write_text("retry2 skipped; no in-window official 404 (first pass 35/35 official 200)\n")
shutil.copyfile(retry2_note, ROOT / "state" / "_halfhour_backfill_retry2_0130.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
print(summary, end="")
print("ok_line", ok_line)
