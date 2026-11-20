#!/usr/bin/env python3
import json, shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "tools")
import db

NL = chr(10)
HK = ZoneInfo("Asia/Hong_Kong")
ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-20_1600"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
JUST_BASE = 84376100
JUST_T0, JUST_T1 = JUST_BASE + 1, JUST_BASE + 100
# NEW box freeze 15:44:21-16:03:39
GAP_S, GAP_E, GAP_SPAN = 84375811, 84376109, 299
# Already-told (15:29 1h patrol) freeze 15:15:12-15:26:38, overlaps this window from 84375401
PRIOR_S, PRIOR_E, PRIOR_SPAN = 84375391, 84375569, 179

coverage_payload = json.loads((DIR / "coverage_final.json").read_text())
jp = json.loads((DIR / f"just_published_{JUST_BASE}.json").read_text())
pre = json.loads((DIR / "just_published_pre_counts.json").read_text())
live = json.loads((ROOT / "metrics" / "live.json").read_text())
rot = json.loads((ROOT / "metrics" / "listener_rot.json").read_text())
tickj = json.loads((DIR / "tick_s_realign.json").read_text())

post = {}
official_fill = {}
prior_gap_fill = {}
with db.connect() as c:
    for room in ROOMS:
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, JUST_T0, JUST_T1),
        ).fetchone()
        post[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}
        gd = c.execute(
            "SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, GAP_S, GAP_E),
        ).fetchone()[0] or 0
        official_fill[room] = f"{int(gd)}/{GAP_SPAN}"
        pd = c.execute(
            "SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, PRIOR_S, PRIOR_E),
        ).fetchone()[0] or 0
        prior_gap_fill[room] = f"{int(pd)}/{PRIOR_SPAN}"
    d, mn, mx, n = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        ("W46N8", 84376101, 84376200),
    ).fetchone()
    w46n8_404_live = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}
    tips = {
        "cpu": c.execute("select max(tick) from creep_cpu").fetchone()[0],
        "path": c.execute("select max(tick) from path_arrivals").fetchone()[0],
        "room_stats": c.execute("select max(tick) from room_stats").fetchone()[0],
    }
(DIR / "just_published_post_counts.json").write_text(json.dumps(post, indent=2) + NL)

script_by = {g["room"]: g["inserted"] for g in jp["gets"]}
actual_by = {room: post[room]["rows"] - pre[room]["rows"] for room in ROOMS}
actual_total = sum(actual_by.values())
script_total = int(jp["inserted"])
all_five_200 = all(g.get("code") == 200 and g.get("ok") for g in jp["gets"]) and not jp.get("still_404")
jp_distinct = ", ".join(f"{room} {post[room]['distinct']}/100" for room in ROOMS)
mismatch = [room for room in ROOMS if script_by.get(room, 0) != actual_by[room]]
mismatch_s = ", ".join(f"{r} script {script_by[r]} vs actual {actual_by[r]}" for r in mismatch)
just_note = (
    f"just-published {JUST_BASE} at {jp.get('at')} game.time={jp.get('game_time')} "
    f"all_five_200={all_five_200} actual_inserted={actual_total} ticks {JUST_T0}..{JUST_T1} "
    f"({jp_distinct}); script inserted={script_total}"
    + (f" ({mismatch_s})." if mismatch_s else ".")
)

finished = datetime.now(HK)
finished_hkt = finished.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

per_room_new_first = {"W46N8": 3850, "W47N8": 2986, "W45N8": 2386, "W45N7": 1079, "W47N7": 1873}
INSERTED_WINDOW = 12174
TICK_S_FIRST = 4.14626
TICK_S_IN_USE = float(tickj["tick_s_in_use"])
TICK_S_IN_USE_NAME = tickj.get("tick_s_in_use_name") or "all_mean"
fill_s = ", ".join(f"{r} {official_fill[r]}" for r in ROOMS)
prior_s = ", ".join(f"{r} {prior_gap_fill[r]}" for r in ROOMS)

# Official fill note for the NEW freeze: W45N7 empty-no-creep inside the gap is 84375818..84375843 (26t)
w45n7_gap_note = (
    "W46N8 missing 84376101..84376109 (9t) because official 404 W46N8@84376100 still unfilled after "
    "just-published GET 16:13:28 gt=84376240, retry 16:14:13 gt=84376251 and retry2 16:14:56 gt=84376261 "
    "(44 live ticks 84376157..84376200 present; hole 84376101..84376156). "
    "W45N7 shortfall is official empty-no-creep (84375818..84375843, 26t inside the STATS gap; "
    "also earlier empty 84375445 and 84375447..84375614 from the invader-core civilian withdrawal), not a 404."
)

payload = {
    "at": finished_hkt,
    "ok_quiet": True,
    "game_time_first": 84376148,
    "published_bases": "84375400..84376000",
    "reconstructed": [84375401, 84376100],
    "ticks": 700,
    "creep_rows": 22693,
    "missing_chunks": 0,
    "already_in_db": 10519,
    "inserted_first": 12174,
    "inserted_confirm": 0,
    "inserted_retry2": 0,
    "inserted_just_script": script_total,
    "inserted_just_actual": actual_total,
    "inserted_window": INSERTED_WINDOW,
    "inserted_total": INSERTED_WINDOW + actual_total,
    "tick_s_printed": 4.146,
    "tick_s_first": TICK_S_FIRST,
    "tick_s_in_use": TICK_S_IN_USE,
    "tick_s_in_use_name": TICK_S_IN_USE_NAME,
    "ts_realigned_first": 0,
    "corrective": 0,
    "coverage_official_recovered": coverage_payload["official_recovered"],
    "coverage_expected": coverage_payload["expected"],
    "empty_no_creep": coverage_payload["empty_no_creep"],
    "official_404": coverage_payload["official_404_missing"],
    "per_room_new_first": per_room_new_first,
    "per_room_new_window": per_room_new_first,
    "in_window_404_after_retry2": [],
    "just_published_base": JUST_BASE,
    "just_published_at": jp.get("at"),
    "just_published_gt": jp.get("game_time"),
    "just_published_all_five_200": all_five_200,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "new_box_freeze": {
        "from": "2026-11-20 15:44:21",
        "to": "2026-11-20 16:03:39",
        "sec": 1152,
        "why": "box frozen ~1152s since 2026-11-20 15:44:21 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "16:03:42",
        "listener_pid": 1380270,
        "listener_started": "16:03:51",
        "stats": "84375811..84376109",
        "span": 299,
        "last_stats": "84375810 at 15:43:36",
        "next_stats": "84376110 at 16:04:19",
        "wall_s": 1243,
        "official_fill": official_fill,
        "filled_by": (
            "first pass through 84376100 (published 84375800, 84375900 and 84376000 already 200 for all 5) "
            "plus just-published 84376100 (ticks 84376101..84376200) covering remainder 84376101..84376109. "
            + w45n7_gap_note
        ),
        "told": False,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1600",
        "note": "No concurrent 1h patrol during this backfill. Leave telling the freeze to the next 1h patrol.",
    },
    "new_short_listener_gap": None,
    "already_recorded_untold_short_listener_gap_in_window": None,
    "aged_out_already_told_short_listener_gap": {
        "why": "ws ping/pong timed out 15:02:26 (not a box freeze; box_pauses.jsonl unchanged)",
        "stats": "84374991..84375229",
        "span": 239,
        "official_fill": "239/239 all 5 (15:00 first pass through 84375200 plus just-published 84375200)",
        "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1526 ~15:29",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1500",
        "aged_out_of_window_start": 84375401,
        "also_aged_out": "14:34:16 STATS 84374801..84374819 (19t, official-filled 19/19 all 5) was already told by that same 15:29 patrol",
    },
    "new_official_404": [
        {
            "chunk": "W46N8@84376100",
            "hole": "84376101..84376200",
            "live_ticks_present": "84376157..84376200 (44t)",
            "still_404_after": "just-published 16:13:28 gt=84376240, retry 16:14:13 gt=84376251 and retry2 16:14:56 gt=84376261",
            "db": w46n8_404_live,
            "told": False,
            "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1600",
        }
    ],
    "already_recorded_untold_in_window_404": [],
    "already_told_in_window_404": [],
    "aged_out_already_told_404_not_retried": [
        "W45N8@84375300",
        "W45N7@84373700",
        "W47N8@84373800",
        "W45N7@84373300",
        "W47N7@84373200",
        "W46N8@84371600",
    ],
    "prior_told_box_freeze_in_window": {
        "from": "2026-11-20 15:15:12",
        "to": "2026-11-20 15:26:38",
        "sec": 686,
        "stats": "84375391..84375569",
        "span": 179,
        "official_fill": prior_gap_fill,
        "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1526 ~15:29",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1530",
        "note": "STATS gap starts 10 ticks before this window (84375391..84375400, W45N8 still missing those 10t because official 404 W45N8@84375300). Overlap 84375401..84375569 sits inside this window.",
    },
    "aged_out_already_told_box_freeze": {
        "from": "2026-11-20 13:53:22",
        "to": "2026-11-20 14:05:12",
        "sec": 702,
        "stats": "84374221..84374399",
        "span": 179,
        "told": True,
        "told_by": "1h patrol _patrol_2026-11-20_1421 ~14:28",
        "also_aged_out": "13:29:41-13:36:13 STATS 84373871..84373979 also already told by that patrol",
    },
    "listener": {
        "single_slot": True,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "pid": 1380270,
        "started": "16:03:51",
        "parent": 4035476,
        "yield": False,
        "restarted_this_run": False,
        "auto_restart": "16:03:42 after box freeze 15:44:21-16:03:39",
    },
    "war_cmd_pulse_restarted": False,
    "concurrent_1h_patrol": None,
    "cpu_tip": tips["cpu"],
    "path_tip": tips["path"],
    "room_stats_tip": tips["room_stats"],
}

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2) + NL)
shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")

first = (DIR / "history_backfill.txt").read_text().rstrip()
now_txt = (
    first + NL + NL
    + f"---- wrap {finished_hkt} ----" + NL
    + "confirm skipped (no in-window official 404s; first pass 35/35 200, missing_chunks=0). retry2 skipped. Just-published 84376100: W46N8 still 404 after 16:13:28 / 16:14:13 / 16:14:56 (gt=84376240/84376251/84376261); 44 live ticks 84376157..84376200 present, hole 84376101..84376156. Leftover official 404 W45N8@84375300 and older already-told 404s aged out of window start 84375401 and were not retried." + NL
    + f"tick_s_first=4.14626 printed=4.146 in_use={TICK_S_IN_USE:.5f} ({TICK_S_IN_USE_NAME}) ts_realigned_first=0 corrective=0" + NL
    + f"coverage official_recovered={coverage_payload['official_recovered']}/{coverage_payload['expected']} empty_no_creep={coverage_payload['empty_no_creep']} official_404={coverage_payload['official_404_missing']}" + NL
    + just_note + NL
    + f"inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_WINDOW + actual_total}" + NL
    + "ok_quiet=True" + NL
)
(DIR / "history_backfill_now.txt").write_text(now_txt)
shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

verify = (
    f"{finished_hkt} verify" + NL
    + "first pass game.time=84376148 published_bases=84375400..84376000 reconstructed 84375401..84376100 (700) creep_rows=22693 missing_chunks=0" + NL
    + f"already_in_db=10519 inserted_first=12174 confirm=0 retry2=0 just_script={script_total} just_actual={actual_total} inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_WINDOW + actual_total}" + NL
    + "per_room first W46N8:700t/3850new W47N8:700t/2986new W45N8:700t/2386new W45N7:700t/1079new W47N7:700t/1873new. No in-window official 404. W45N7 official empty-no-creep 195t (84375445, 84375447..84375614, 84375818..84375843)." + NL
    + f"tick_s_first=4.14626 printed=4.146 in_use={TICK_S_IN_USE:.5f} ({TICK_S_IN_USE_NAME}) ts_realigned_first=0 corrective=0" + NL
    + f"coverage official_recovered={coverage_payload['official_recovered']}/{coverage_payload['expected']} empty_no_creep={coverage_payload['empty_no_creep']} official_404={coverage_payload['official_404_missing']} unique_room_ticks={coverage_payload['official_recovered']}" + NL
    + "Official 404 in this first-pass window after confirm+retry2: none. Official empty-no-creep: W45N7 195t. W46N8/W47N8/W45N8/W47N7 700/700; W45N7 505/700 (195 empty). NEW leftover official 404 on just-published 84376100: W46N8 still 404 after 16:13:28/16:14:13/16:14:56; 44 live ticks 84376157..84376200 present, hole 56t 84376101..84376156." + NL
    + just_note + NL
    + f"NEW box freeze 15:44:21-16:03:39 (1152s; box_pauses.jsonl); listener auto-restart 16:03:42, pid 1380270 started 16:03:51. STATS 84375811..84376109 (299t) wall ~1243s from last STATS 84375810 at 15:43:36 to next 84376110 at 16:04:19. Official-filled {fill_s} via first pass through 84376100 plus just-published 84376100 (ticks 84376101..84376200 covering remainder 84376101..84376109). {w45n7_gap_note} told=false, first recorded by this 16:00 half-hour, left to 1h patrol. This run did not itself restart the listener. No concurrent 1h patrol." + NL
    + f"Prior box freeze 15:15:12-15:26:38 STATS 84375391..84375569 overlaps this window from 84375401 and remains official-filled {prior_s}; already recorded by the 15:30 half-hour and already told by the 15:29 1h patrol. Prior short listener gap 15:02:26 STATS 84374991..84375229 aged out of window start 84375401 (already official-filled 239/239 all 5; recorded by the 15:00 half-hour, told by the 15:29 1h patrol). Prior short gap 14:34:16 and prior freezes 13:53:22-14:05:12 / 13:29:41-13:36:13 also aged out and were already told." + NL
    + "NEW leftover official 404 W46N8@84376100 (just-published; hole 84376101..84376200, 44 live ticks 84376157..84376200 present, still 404 after 16:13:28/16:14:13/16:14:56); told=false, first recorded by this 16:00 half-hour, left to 1h patrol. Already-told leftover official 404 W45N8@84375300 (hole 84375301..84375400) aged out of window start 84375401 and was not retried (still unfilled; already told by the 15:29 1h patrol). Older already-told leftovers W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 also aged out and were not retried." + NL
    + f"listener single_slot=True roomSlot={live.get('roomSlot')} pid=1380270 started 16:03:51 after auto-restart 16:03:42; parent run_listener.sh pid 4035476 from Nov 13; this run did not restart listener or war_cmd/pulse; no second listener; yield absent. cpu_tip={tips['cpu']} path_tip={tips['path']} room_stats_tip={tips['room_stats']}." + NL
)
(DIR / "verify.txt").write_text(verify)
shutil.copyfile(DIR / "verify.txt", ROOT / "state" / "_halfhour_backfill_verify.txt")

wrap = (
    f"{finished_hkt} wrapup ok" + NL
    + "wrote history_backfill.json history_backfill_now.txt verify.txt" + NL
    + f"inserted=12174+0+0+just{actual_total} coverage={coverage_payload['official_recovered']}/{coverage_payload['expected']} tick_s_in_use={TICK_S_IN_USE:.5f}" + NL
    + f"ok_line ok_quiet=True coverage={coverage_payload['official_recovered']}/{coverage_payload['expected']} inserted_total={INSERTED_WINDOW + actual_total}" + NL
)
(DIR / "wrapup_run.txt").write_text(wrap)
(DIR / "wrapup_run_live.txt").write_text(wrap)
(DIR / "wrapup_run_stdout.txt").write_text(wrap)
(DIR / "wrapup_run.err").write_text("")
print(wrap)
print("actual_by", actual_by, "total", actual_total)
print("official_fill", official_fill)
print("prior_gap_fill", prior_gap_fill)
print("wrote status files")
print("just_note", just_note)
