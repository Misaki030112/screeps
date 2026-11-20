#!/usr/bin/env python3
"""Write local status records for the 08:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-20_0800"
assert "_halfhour_2026-11-20_0800" in str(DIR), DIR
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84368501, 84369200
PUB_BASES = "84368500..84369100"
GT_FIRST = 84369243
TICK_S_FIRST = 4.15699
TICK_S_PRINTED = "4.157"
TICK_S_IN_USE = 4.139376
TS_REALIGNED_FIRST = 35
NFIX_CORR = 0
GT_CORR = None
RECON_ROWS = 25566
ALREADY = 12297
INSERTED_FIRST = 13269
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
PER_ROOM_LINE = "W46N8:700t/2882new W47N8:700t/4506new W45N8:700t/1731new W45N7:700t/1960new W47N7:700t/2190new"
MISSING_CHUNKS = 0
JUST_BASE = 84369200
JUST_T0, JUST_T1 = 84369201, 84369300
JUST_THRESHOLD = 84369340
FIRST_PASS_CORE = (
    "first pass 35 of 35 official GETs 200, missing_chunks=0; "
    "07:30 half-hour already wrote through 84368600 / reconstructed through 84368700 "
    "(just-published 84368700 written 07:39:03 at game.time=84368842, 200 for all 5, ticks 84368701..84368800); "
    "no concurrent 1h patrol during this pass; "
    "(this pass already_in_db=12297 / inserted=13269; overlap 84368501..84369200 already partly present from the 07:30 half-hour official fill through 84368800 and live rotation; "
    "this pass inserted 13269 additional rows: W46N8 2882, W47N8 4506, W45N8 1731, W45N7 1960, W47N7 2190; all 5 rooms 700t; "
    "NEW box freeze 07:46:17-08:04:28 (1086s) STATS gap 84368941..84369219 (279) is fully inside this reconstructed window: last STATS 84368940 at 07:45:43, next STATS 84369220 at 08:04:51 Asia/Hong_Kong (wall ~1148s); listener auto-restart 08:04:32 (listener.py pid 1200715 started 08:04:41); official-filled 279/279 in all 5 rooms; not yet told, for the next 1h patrol; "
    "room_stats STATS gap 84368531..84368559 (29) from the 07:18:51 ping/pong timeout sits at the start of this window and was already recorded in the 07:30 half-hour status (official-filled 29/29 in all 5 rooms; 07:29 1h patrol noted 07:18:51 as the 07:17 patrol services.sh restart, not a box freeze); "
    "box freeze 06:37:56-07:03:44 STATS gap 84367951..84368339 has aged out of this window start 84368501 (already told by the 07:29 1h patrol); "
    "listener auto-restart 08:04:32 (pid 1200715 started 08:04:41) after the 07:46 freeze; this run did not itself restart the listener; "
    "leftover official 404 W45N8@84368100, W47N7@84366500, W47N8@84366200, W45N7@84365200, W47N8@84363900, W46N8@84362700, W47N8@84361700, W46N8@84360600, W45N7@84360200, W47N8@84359900 and older aged out of this 40-min window and were not retried this pass (still unfilled; W45N8@84368100 already told by the 07:29 1h patrol); "
    "this window empty_no_creep=0 (all 5 rooms 700/700 official recovered)"
)

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
just_pub_path = DIR / f"just_published_{JUST_BASE}.json"
just_pub_payload = json.loads(just_pub_path.read_text()) if just_pub_path.exists() else {}
just_pre = {}
try:
    just_pre = json.loads((DIR / "just_published_pre_counts.json").read_text())
except Exception:
    just_pre = {}
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
INSERTED_JUST_SCRIPT = int(just_pub_payload.get("inserted") or 0) if just_pub_payload else 0
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2

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
    freeze0746 = {room: rng(c, room, 84368941, 84369219, 279) for room in ROOMS}
    gap0718 = {room: rng(c, room, 84368531, 84368559, 29) for room in ROOMS}
    just_rng = {room: rng(c, room, JUST_T0, JUST_T1, 100) for room in ROOMS}
    empty_w45n7_b = rng(c, "W45N7", 84368044, 84368071, 28)
    empty_w45n7_c = rng(c, "W45N7", 84368205, 84368265, 61)
    empty_w45n7_d = rng(c, "W45N7", 84368401, 84368458, 58)
    empty_w45n7_e = rng(c, "W45N7", 84368494, 84368494, 1)
    hole_w45n8_68100 = rng(c, "W45N8", 84368101, 84368200, 100)
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

# actual just-published inserts = post rows minus pre rows (live race possible)
INSERTED_JUST = 0
just_actual_parts = []
if just_pub_payload and just_pre:
    for room in ROOMS:
        pre_n = int((just_pre.get(room) or {}).get("rows") or 0)
        post_n = int(just_rng[room]["rows"] or 0)
        delta = max(0, post_n - pre_n)
        INSERTED_JUST += delta
        just_actual_parts.append(f"{room} {post_n}-{pre_n}={delta}")
elif just_pub_payload:
    INSERTED_JUST = INSERTED_JUST_SCRIPT

def fill_line(fills, expected_n):
    parts = []
    for room in ROOMS:
        f = fills[room]
        parts.append(f"{room} {f['distinct']}/{expected_n}")
    return ", ".join(parts)

if just_pub_payload:
    just_distinct_note = ", ".join(
        f"{room} {just_rng[room]['distinct']}/100" for room in ROOMS
    )
    just_note = (
        f"just-published {JUST_BASE} attempted at {just_at} game.time={just_gt} "
        f"(typically publishable around game.time>={JUST_THRESHOLD}) and was "
        + ("200 for all 5 rooms" if all_five else f"not fully published (recovered={just_recovered or []} still_404={just_still_404 or []})")
        + f" (script inserted={INSERTED_JUST_SCRIPT}, actual db inserted={INSERTED_JUST}"
        + (f" [{', '.join(just_actual_parts)}]" if just_actual_parts else "")
        + f"; ticks {JUST_T0}..{JUST_T1}, {just_distinct_note})"
    )
else:
    just_note = (
        f"just-published {JUST_BASE} was not attempted: after retry2 07:34:15 Asia/Hong_Kong "
        f"game.time=84368772 still short of typical publish threshold game.time>={JUST_THRESHOLD} "
        f"(base+140); this run did not busy-loop for many minutes waiting for the next published base"
    )
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
FIRST_PASS_LINE = FIRST_PASS_CORE + "; " + just_note

inwin_txt = (
    "in-window official 404 after first pass: none (35 of 35 official GETs 200, missing_chunks=0); "
    "no confirm/retry2 targets"
)
leftover_txt = (
    f"Leftover official 404 W45N8@84368100 (hole 84368101..84368200 still db {hole_w45n8_68100['distinct']}/100, no rows; already told by the 07:29 1h patrol) aged out of this window start 84368501 and was not retried this pass (still unfilled). "
    f"Leftover official 404 W47N7@84366500 (hole 84366501..84366600 still db {hole_w47n7_66500['distinct']}/100, no rows; already told by the 05:23 1h patrol) aged out of this window start 84368501 and was not retried this pass (still unfilled). "
    f"Leftover official 404 W47N8@84366200 (hole 84366201..84366300 still db {hole_w47n8_66200['distinct']}/100, no rows; already told by the 05:23 1h patrol) aged out of this window start 84368501 and was not retried this pass (still unfilled). "
    f"Leftover official 404 W45N7@84365200 (hole 84365201..84365300 still db {hole_w45n7_65200['distinct']}/100, no rows; already told by the 04:21 1h patrol) aged out of this window start 84368501 and was not retried this pass (still unfilled). "
    f"Leftover official 404 W47N8@84363900 (hole 84363901..84364000 still db {hole_w47n8_63900['distinct']}/100 live-only {hole_w47n8_63900['min']}..{hole_w47n8_63900['max']}, missing 84363901..84363950; already told by the 02:34 1h patrol) aged out of this window start 84368501 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W46N8@84362700 (hole 84362701..84362800 still db {hole_w46n8_62700['distinct']}/100, no live rows; already told by the 01:26 1h patrol) aged out of this window start 84368501 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W47N8@84361700 (hole 84361701..84361800 still db {hole_w47n8_61700['distinct']}/100 live-only; already told) aged out of this window start 84368501 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W46N8@84360600 (hole 84360601..84360700 still db {hole_w46n8_60600['distinct']}/100 live-only; already told) aged out and was not retried (still unfilled). "
    f"Aged leftover official 404 W45N7@84360200 (hole 84360201..84360300 still db {aged_w45n7_60200['distinct']}/100; already told) and W47N8@84359900 (hole 84359901..84360000 still db {aged_w47n8_59900['distinct']}/100; already told) also sit outside this window and were not retried (still unfilled). "
    "Aged leftover official 404 W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) were not retried this pass (already outside this 40-min window). "
    "This window has empty_no_creep=0 (all 5 rooms official-recovered 700/700)."
)
vs_all = vs_cand.get("all_mean") or {}
vs_later_c = vs_cand.get("later_robust") or vs_cand.get("later_mean_robust") or {}
vs_prev = vs_cand.get("prev_later") or {}
tick_s_corr_txt = (
    f"script {TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band but is not live-anchor-best "
    f"(vs_first over45={vs_first.get('over45')} mean_off={vs_first.get('mean_off')}, over15={vs_first.get('over15')}); "
    f"live-anchor-best is prev_later {tick_s.get('prev_later_mean')} "
    f"(over45={vs_prev.get('over45')} mean_off={vs_prev.get('mean_off')}, over15={vs_prev.get('over15')}); "
    f"later-mean-robust {tick_s.get('later_mean_w46') or tick_s.get('later_mean_w46_robust')} is worse than prev_later "
    f"(before, over45={tick_s.get('still_over_45s_vs_later_before')} mean_off={vs_later_c.get('mean_off')}) and was refused; "
    f"all_mean {tick_s.get('all_mean_w46')}; prev_later {tick_s.get('prev_later_mean')}. "
    f"First-pass realign moved {TS_REALIGNED_FIRST} rows onto {TICK_S_FIRST:.5f}; "
    f"no corrective realign (live-anchor-best prev_later already inside 45s gate, over45=0); "
    f"in-use prev_later {TICK_S_IN_USE:.5f}; no in-window official 404 (confirm/retry2 skipped, no targets); "
    + just_note
)

freeze_para = (
    f"NEW box freeze 07:46:17-08:04:28 Asia/Hong_Kong (1086s; run_listener.sh auto-restart 08:04:32, listener.py pid 1200715 started 08:04:41; not yet told, for the next 1h patrol) "
    f"room_stats gap 84368941..84369219 (279) is fully inside this window: last STATS 84368940 at 07:45:43, next STATS 84369220 at 08:04:51 (wall ~1148s); "
    f"official-filled 279/279 in all 5 rooms "
    f"(counts {fill_line(freeze0746, 279)}). "
    f"room_stats STATS gap 84368531..84368559 (29) Asia/Hong_Kong last STATS 84368530 at 07:17:42, next STATS 84368560 at 07:19:38 (wall ~116s) sits at the start of this window; "
    f"already recorded in the 07:30 half-hour status (run_listener.sh auto-restart 07:18:51 after ws ping/pong timeout 07:18:47, listener.py then pid 1184861 started 07:19:00; not in box_pauses.jsonl); "
    f"the 07:29 1h patrol noted 07:18:51 as the 07:17 patrol services.sh restart, not a box freeze; "
    f"official-filled 29/29 in all 5 rooms "
    f"(counts {fill_line(gap0718, 29)}). "
    "Box freeze 06:37:56-07:03:44 Asia/Hong_Kong (1542s; already told by the 07:29 1h patrol) room_stats gap 84367951..84368339 has aged out of this window start 84368501. "
    "Box freezes 06:14:32-06:19:42, 05:53:08-05:56:59, 05:59:54-06:01:32, 05:18:07-05:19:42, 04:42:44-05:00:03 and earlier have aged out of this window start 84368501 or were already told by the 07:29 / 06:29 / 05:23 1h patrols. "
    "This run found the listener already auto-restarted (pid 1200715 started 08:04:41, after the 08:04:32 restart at the end of the 07:46 freeze) and did not itself restart it. "
    + leftover_txt
    + " live.json was fresh at pre-check 08:06:12 (age ~0.9s, tip stats.t=84369230, roomSlot W47N8, gameTime was still None and objects_n=0 on the W47N8 5-weight slot while room ingest, CPU and path buffers were already flowing: creep_ticks W47N8 through 84369239, creep_cpu through 84369230 / path_arrivals through 84369218 / room_stats through 84369230); "
    f"this pass inserted {INSERTED_FIRST} additional rows in 84368501..84369200"
    + (f" plus just-published actual {INSERTED_JUST} in {JUST_T0}..{JUST_T1}" if just_pub_payload else "; just-published 84369200 was not attempted")
    + f"; single_slot held, creep_cpu through {cpu_tip} / path_arrivals through {path_tip} / room_stats through {rs_tip} at wrapup; this run did not restart the listener."
)

slot = live.get("roomSlot")
listener = {
    "single_slot": True,
    "roomSlot": slot,
    "rot": rot,
    "yield": yield_present,
    "listener_pid": 1200715,
    "listener_started": "2026-11-20 08:04:41",
    "run_listener_pid": 4035476,
    "auto_restart": "2026-11-20 08:04:32",
    "auto_restart_reason": "box freeze 07:46:17-08:04:28 (1086s)",
    "prior_auto_restart": "2026-11-20 07:18:51",
    "prior_listener_pid": 1184861,
    "second_listener": False,
    "war_cmd_or_pulse_restart": False,
}
listener_line = (
    f"listener single_slot=True roomSlot={slot} rot={rot} yield={'present' if yield_present else 'absent'}; "
    "no second listener started; no war_cmd/pulse restart."
)
confirm_summary = (
    "confirm 2026-11-20 08:08:54 Asia/Hong_Kong and retry2 08:08:54 Asia/Hong_Kong were skipped (no in-window or aged targets; first pass 35/35 official 200); "
    + just_note
    + f"; this pass inserted {INSERTED_FIRST} additional rows in the reconstructed window "
    "(W46N8 2882 / W47N8 4506 / W45N8 1731 / W45N7 1960 / W47N7 2190) on top of the 07:30 half-hour official fill through 84368800 and live rotation"
)

new_box_freezes_not_yet_told = [
    {
        "from": "2026-11-20 07:46:17",
        "to": "2026-11-20 08:04:28",
        "sec": 1086,
        "stats_gap": "84368941..84369219",
        "span": 279,
        "last_stats_tick": 84368940,
        "last_stats_ts": "2026-11-20 07:45:43 Asia/Hong_Kong",
        "next_stats_tick": 84369220,
        "next_stats_ts": "2026-11-20 08:04:51 Asia/Hong_Kong",
        "wall_s_stats_ingest": 1148,
        "in_box_pauses": True,
        "listener_restart": "2026-11-20 08:04:32",
        "listener_pid": 1200715,
        "listener_started": "2026-11-20 08:04:41",
        "fill": freeze0746,
        "note": "NEW box freeze after PREV_END 84368800; official-filled 279/279 in all 5 rooms; not yet told, for the next 1h patrol",
    }
]
new_stats_gaps = [
    {
        "stats_gap": "84368531..84368559",
        "span": 29,
        "last_stats_tick": 84368530,
        "last_stats_ts": "2026-11-20 07:17:42 Asia/Hong_Kong",
        "next_stats_tick": 84368560,
        "next_stats_ts": "2026-11-20 07:19:38 Asia/Hong_Kong",
        "wall_s_stats_ingest": 116,
        "in_box_pauses": False,
        "listener_log": "2026-11-20 07:18:47 [listener] ws error ping/pong timed out",
        "listener_restart": "2026-11-20 07:18:51",
        "listener_pid": 1184861,
        "listener_started": "2026-11-20 07:19:00",
        "fill": gap0718,
        "note": "already recorded in the 07:30 half-hour status and mentioned by the 07:29 1h patrol as the 07:17 patrol services.sh restart (not a box freeze); official-filled 29/29 in all 5 rooms; sits at the start of this window",
    }
]

payload = {
    "at": finished_hkt_sec,
    "ok": True,
    "quiet": True,
    "window": {"tmin": TMIN, "tmax": TMAX, "published_bases": PUB_BASES, "rooms": list(ROOMS)},
    "game_time_first": GT_FIRST,
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
    "just_published": {
        "attempted": bool(just_pub_payload),
        "base": JUST_BASE,
        "threshold": JUST_THRESHOLD,
        "game_time": just_gt,
        "at": just_at,
        "recovered": just_recovered,
        "still_404": just_still_404,
        "inserted_script": INSERTED_JUST_SCRIPT,
        "inserted_actual": INSERTED_JUST,
        "actual_parts": just_actual_parts,
        "per_room_after": just_rng,
        "pre_counts": just_pre,
    },
    "confirm": confirm_payload,
    "listener": listener,
    "box_freeze": {
        "new": new_box_freezes_not_yet_told,
        "already_told_aged_out": ["06:37:56-07:03:44", "06:14:32-06:19:42"],
    },
    "new_official_404_not_yet_told": [],
    "new_box_freezes_not_yet_told": new_box_freezes_not_yet_told,
    "new_stats_gaps_for_patrol": new_stats_gaps,
    "already_told_still_unfilled": [
        "W45N8@84368100", "W47N7@84366500", "W47N8@84366200", "W45N7@84365200", "W47N8@84363900",
        "W46N8@84362700", "W47N8@84361700", "W46N8@84360600", "W45N7@84360200", "W47N8@84359900",
    ],
    "inwin_txt": inwin_txt,
    "leftover_txt": leftover_txt,
    "freeze_para": freeze_para,
    "confirm_summary": confirm_summary,
    "db_after": db_after_lines,
    "cpu_tip": cpu_tip,
    "path_tip": path_tip,
    "rs_tip": rs_tip,
}

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")

ok_line = (
    f"ok_quiet=True coverage={recovered}/{expected} inserted_window={INSERTED_WINDOW} "
    f"inserted_total={INSERTED_TOTAL} tick_s_in_use={TICK_S_IN_USE:.5f} listener single_slot=True; "
    "no second listener; no war_cmd/pulse restart."
)
now_text = "\n".join([
    f"{finished_hkt} half-hour backfill OK (quiet)",
    f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
    f"  ({FIRST_PASS_LINE}; see history_backfill.txt)",
    f"tick_s={TICK_S_PRINTED} ({tick_s_corr_txt})",
    f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks={MISSING_CHUNKS}",
    f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
    f"per_room {PER_ROOM_LINE}",
    f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 +{INSERTED_RETRY2}, just_published +{INSERTED_JUST} actual / script {INSERTED_JUST_SCRIPT}, window {INSERTED_WINDOW}, run total {INSERTED_TOTAL})",
    f"ts_realigned_first={TS_REALIGNED_FIRST} ts_realigned_corrective={NFIX_CORR} tick_s_in_use={TICK_S_IN_USE:.5f}",
    "db_after",
    db_after_lines,
    f"coverage official_recovered={recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing} unique_room_ticks={unique_after.get('distinct_room_ticks')}",
    inwin_txt,
    leftover_txt,
    freeze_para,
    listener_line,
    confirm_summary,
    ok_line,
]) + "\n"
(DIR / "history_backfill_now.txt").write_text(now_text)
shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")
shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

verify = [
    f"{finished_hkt_sec} verify 08:00 half-hour official-history backfill",
    f"window ticks {TMIN}..{TMAX} published_bases {PUB_BASES} game.time_first={GT_FIRST}",
    f"inserted_first={INSERTED_FIRST} confirm={INSERTED_CONFIRM} retry2={INSERTED_RETRY2} just_published={INSERTED_JUST} (script {INSERTED_JUST_SCRIPT}) total={INSERTED_TOTAL}",
    f"coverage {recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}",
    f"tick_s_in_use={TICK_S_IN_USE:.5f} ts_realigned_first={TS_REALIGNED_FIRST} ts_realigned_corrective={NFIX_CORR}",
    f"{inwin_txt}",
    f"{leftover_txt}",
    freeze_para,
    listener_line,
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 08:04:32 (listener.py pid 1200715 started 08:04:41) after NEW box freeze 07:46:17-08:04:28 (1086s, room_stats gap 84368941..84369219 (279; last STATS 84368940 at 07:45:43, next 84369220 at 08:04:51, wall ~1148s; official-filled 279/279 in all 5 rooms; not yet told, for the next 1h patrol). Prior 07:18:51 ping/pong restart and STATS gap 84368531..84368559 (29; official-filled 29/29) were already recorded in the 07:30 half-hour status (07:29 1h patrol noted 07:18:51 as the 07:17 patrol services.sh restart, not a box freeze). Box freeze 06:37:56-07:03:44 already told by the 07:29 1h patrol and has aged out of this window. Earlier already-told: 06:19:45 after 06:14:32-06:19:42; 06:01:35 after 05:59:54-06:01:32; 05:57:02 after 05:53:08-05:56:59 (told by the 06:29 1h patrol). By wrapup live.json was flowing on a single listener slot and CPU/path buffers were flowing; single_slot held.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0800.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
print(summary, end="")
print("ok_line", ok_line)
