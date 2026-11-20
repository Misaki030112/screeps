#!/usr/bin/env python3
"""Write 01:30 half-hour backfill wrap artifacts (quiet success)."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-21_0130"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
now = datetime.now(HK)
now_s = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

tick = json.loads((DIR / "tick_s_realign.json").read_text())
cov = json.loads((DIR / "coverage_final.json").read_text())
post = json.loads((DIR / "just_published_post_summary.json").read_text())
confirm = json.loads((DIR / "backfill_confirm_gets.json").read_text())
jp = json.loads((DIR / "just_published_84384200.json").read_text())
live = json.loads((ROOT / "metrics/live.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()
stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}

want = (
    "First-pass realign with tick_s=4.19988 (printed 4.200) moved 30 rows "
    "(ts_realigned_first=30, inserted=200, already_in_db=24302, missing_chunks=2 "
    "W45N7@84383500, W45N7@84383900)."
)
if tick.get("ts_realigned_first_pass_error"):
    tick["ts_realigned_first_pass_error"] = want
reason = tick.get("reason") or ""
reason = reason.replace("printed 4.100", "printed 4.200")
reason = reason.replace(
    "moved 30 rows (ts_realigned_first=30, inserted=438, already_in_db=23933, missing_chunks=1 W47N8@84380300).",
    "moved 30 rows (ts_realigned_first=30, inserted=200, already_in_db=24302, missing_chunks=2 W45N7@84383500, W45N7@84383900).",
)
tick["reason"] = reason
(DIR / "tick_s_realign.json").write_text(json.dumps(tick, indent=2) + "\n")

with db.connect() as c:
    tips = {}
    for table in ("room_stats", "creep_cpu", "path_arrivals"):
        tips[table] = c.execute(f"select max(tick) from {table}").fetchone()[0]
    win = {}
    for room in ROOMS:
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, 84383501, 84384200),
        ).fetchone()
        win[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}

actual_by = post["actual_by_room"]
script_by = post["script_by_room"]
actual_sum = int(post["actual_sum"])
script_sum = int(post["script_sum"])
gaps = post["gaps"]
holes = post.get("holes") or {}
post_tips = post.get("tips") or {}

inserted_first = 200
inserted_confirm = int(confirm.get("inserted") or 0)
inserted_retry2 = int((confirm.get("retry2") or {}).get("inserted") or confirm.get("retry2_inserted") or 0)
inserted_window = inserted_first + inserted_confirm + inserted_retry2
inserted_total = inserted_window + actual_sum

tick_s_first = float(tick.get("first_interval") or 4.19988)
tick_s_in_use = float(tick.get("tick_s_in_use") or tick_s_first)
tick_s_in_use_name = tick.get("tick_s_in_use_name") or "first"
cov_rec = cov.get("official_recovered")
cov_exp = cov.get("expected")
empty_n = cov.get("empty_no_creep")
off404 = cov.get("official_404_missing")

confirm_at = confirm.get("confirm_at") or confirm.get("at")
confirm_gt = confirm.get("confirm_game_time") or confirm.get("game_time")
retry2 = confirm.get("retry2") or {}
retry2_at = retry2.get("at") or confirm.get("retry2_at")
retry2_gt = retry2.get("game_time") or confirm.get("retry2_game_time")

slot = live.get("roomSlot")
rot_s = json.dumps(rot, ensure_ascii=False)
jp_retries = jp.get("retries") or []
jp_still = jp.get("still_404") or []
jp_all_five = (not jp_still) and len(jp.get("recovered") or []) >= 4

script_mismatch = []
for r in ROOMS:
    if actual_by[r] != script_by[r]:
        script_mismatch.append(f"{r} script {script_by[r]} vs actual {actual_by[r]}")
mismatch_s = ("; " + "; ".join(script_mismatch) + ".") if script_mismatch else "."
script_parts = ", ".join(f"{r} +{script_by[r]}" for r in ROOMS)

payload = {
    "at": now_s,
    "ok_quiet": True,
    "game_time_first": 84384282,
    "published_bases": "84383500..84384100",
    "reconstructed": [84383501, 84384200],
    "ticks": 700,
    "creep_rows": 24502,
    "missing_chunks": 2,
    "already_in_db": 24302,
    "inserted_first": inserted_first,
    "inserted_confirm": inserted_confirm,
    "inserted_retry2": inserted_retry2,
    "inserted_just_script": script_sum,
    "inserted_just_actual": actual_sum,
    "inserted_window": inserted_window,
    "inserted_total": inserted_total,
    "first_pass_by": (
        "this run tools/history_backfill.py --minutes 40 (game.time=84384282, published_bases 84383500..84384100, "
        "reconstructed 84383501..84384200 missing_chunks=2 W45N7@84383500 and W45N7@84383900 inserted=200 already_in_db=24302); "
        "33/35 official GETs 200. Concurrent 1h patrol _patrol_2026-11-21_0124 already ran the same official backfill first "
        "at game.time=84384161 (published_bases 84383400..84384000, reconstructed 84383401..84384100, inserted=9575, "
        "ts_realigned=0) and later inserted just-published 84384100 at 01:33:24 gt=84384258 (all_five_200=True). "
        "This run's first pass included published bases through 84384100, covering the NEW STATS hole 84383931..84384100 "
        "except W45N7@84383900; the patrol just-published 84384100 covered 84384101..84384149, so four rooms ended 219/219 "
        "and W45N7 149/219 missing 84383931..84384000."
    ),
    "tick_s_printed": 4.200,
    "tick_s_first": tick_s_first,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_in_use_name,
    "ts_realigned_first": 30,
    "corrective": int(tick.get("ts_realigned_to_later_mean") or 0),
    "coverage_official_recovered": cov_rec,
    "coverage_expected": cov_exp,
    "empty_no_creep": empty_n,
    "official_404": off404,
    "per_room_new_first": {
        "W46N8": {"ticks": 700, "new": 200},
        "W47N8": {"ticks": 700, "new": 0},
        "W45N8": {"ticks": 700, "new": 0},
        "W45N7": {"ticks": 500, "new": 0},
        "W47N7": {"ticks": 700, "new": 0},
    },
    "per_room_new_window": {
        r: {"distinct": win[r]["distinct"], "rows": win[r]["rows"]} for r in ROOMS
    },
    "in_window_404_after_retry2": ["W45N7@84383500", "W45N7@84383900"],
    "first_pass_404_recovered_before_confirm": [],
    "first_pass_404_recovered_on_confirm": [],
    "just_published_base": 84384200,
    "just_published_at": jp.get("at"),
    "just_published_gt": jp.get("game_time"),
    "just_published_all_five_200": jp_all_five,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "just_published_still_404": jp_still,
    "just_published_retries": jp_retries,
    "just_published_actual_note": (
        f"script inserted={script_sum} ({script_parts}). "
        f"post-counts actual_sum={actual_sum}{mismatch_s} "
        f"All five ended 100/100."
    ),
    "new_box_freeze": {
        "from": "2026-11-21 01:10:46",
        "to": "2026-11-21 01:24:59",
        "sec": 846,
        "why": "box frozen ~846s since 2026-11-21 01:10:46 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "01:25:02",
        "listener_pid": 1594422,
        "listener_started": "01:25:12",
        "stats": "84383931..84384149",
        "span": 219,
        "stats_note": (
            "The 219-tick STATS hole is the box freeze alone; errors.log has no preceding no-STATS. "
            "last STATS 84383930 at 01:10:36, next STATS 84384150 at 01:25:52."
        ),
        "last_stats": "84383930 at 01:10:36",
        "next_stats": "84384150 at 01:25:52",
        "official_fill": {r: gaps["gap_0110_0124"][r]["fill"] for r in ROOMS},
        "official_fill_missing": {"W45N7": "84383931..84384000 (70)"},
        "filled_by": (
            "Concurrent 1h patrol _patrol_2026-11-21_0124 official-filled through 84384100, then inserted "
            "just-published 84384100 at 01:33:24 covering 84384101..84384149. This run confirmed the same coverage. "
            "Four rooms 219/219; W45N7 149/219 missing 84383931..84384000 because official 404 W45N7@84383900 "
            "(hole 84383901..84384000) is still unpublished."
        ),
        "told": False,
        "told_by": None,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-21_0130 (visible in box_pauses.jsonl / errors.log after listener auto-restart 01:25:02; concurrent 1h patrol _patrol_2026-11-21_0124 also saw this freeze)",
        "note": "Already healed. This run did not itself restart the listener. Next 1h patrol should tell this NEW freeze (the concurrent _patrol_2026-11-21_0124 may already be telling it). Fold only newer freezes than 01:10:46-01:24:59.",
    },
    "new_short_listener_gap": None,
    "already_told_box_freeze_in_window": None,
    "already_told_older_box_freeze_in_window": None,
    "already_recorded_untold_box_freeze_in_window": {
        "from": "2026-11-21 00:50:52",
        "to": "2026-11-21 00:57:30",
        "sec": 393,
        "why": "box frozen ~393s since 2026-11-21 00:50:52 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "00:57:33",
        "listener_pid": 1587483,
        "listener_started": "00:57:42",
        "stats": "84383651..84383759",
        "span": 109,
        "last_stats": "84383650 at 00:50:45",
        "next_stats": "84383760 at 00:58:28",
        "official_fill": {r: gaps["gap_0050_0057"][r]["fill"] for r in ROOMS},
        "filled_by": "Previous 01:00 backfill official-filled 109/109 all five; still 109/109 all five this run.",
        "told": False,
        "told_by": None,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-21_0100",
        "note": "Already healed. Still in window start 84383501. Concurrent 1h patrol _patrol_2026-11-21_0124 should tell it if not already delivered. Fold only newer freezes than 01:10:46-01:24:59 (this 00:50 freeze is older and already recorded).",
    },
    "already_recorded_untold_short_listener_gap_in_window": None,
    "aged_out_already_told_short_listener_gap": {
        "from": "2026-11-21 00:14:38",
        "to": "2026-11-21 00:19:22",
        "combined_with_freeze": "00:19:22-00:22:38",
        "stats": "84383131..84383249",
        "span": 119,
        "aged_out_of_window_start": 84383501,
        "told": True,
        "told_by": "1h patrol ~00:32 亚洲/香港 (_patrol_2026-11-21_0022)",
        "note": "Still 119/119 all five. Combined no-STATS after 00:14:38 + box freeze 00:19:22-00:22:38.",
    },
    "new_official_404": [
        {
            "chunk": "W45N7@84383900",
            "hole": "84383901..84384000",
            "confirm": f"still 404 at {confirm_at} gt={confirm_gt}",
            "retry2": f"still 404 at {retry2_at} gt={retry2_gt}",
            "db": "0/100 rows=0; trajectory hole",
            "note": (
                "Official history chunk stayed 404 after confirm and retry2. Neighboring chunks W45N7@84383800 and @84384000 were already 200. "
                "The last 70 ticks of this hole (84383931..84384000) sit inside the NEW freeze STATS gap 84383931..84384149. "
                "Concurrent 1h patrol also still saw 404 at 01:28:51 and 01:33:41. Next 1h patrol should retry the official GET and tell this hole."
            ),
        },
    ],
    "already_recorded_untold_in_window_404": [
        {
            "chunk": "W45N7@84383500",
            "hole": "84383501..84383600",
            "confirm": f"still 404 at {confirm_at} gt={confirm_gt}",
            "retry2": f"still 404 at {retry2_at} gt={retry2_gt}",
            "db": "0/100 rows=0; trajectory hole",
            "first_recorded_by": "30-min backfill _halfhour_2026-11-21_0100",
            "note": "Still official 404 and empty in DB. Still in window start 84383501. Concurrent 1h patrol also still saw 404 at 01:28:50 and 01:33:42 and should tell it.",
        },
    ],
    "already_told_in_window_404": [],
    "already_recorded_untold_just_published_404": [],
    "aged_out_already_told_404_not_retried": [
        "W45N7@84382700",
        "W46N8@84382900",
        "W45N8@84382600",
        "W47N8@84382100",
        "W47N7@84380900",
        "W47N8@84380300",
        "W47N8@84379500",
        "W45N8@84378900",
    ],
    "aged_out_leftover_note": (
        "Already-told leftover official 404s W45N7@84382700 (hole 84382701..84382800, 0/100 trajectory hole), "
        "W46N8@84382900 (hole 84382901..84383000, DB 67/100 from live listener missing 84382901..84382933), and "
        "W45N8@84382600 (hole 84382601..84382700, 0/100) aged out of window start 84383501 and were not retried here "
        "(already told by 1h patrol _patrol_2026-11-21_0022). Older leftovers "
        "W47N8@84382100 (DB 100/100, not a trajectory hole), W47N7@84380900, W47N8@84380300, W47N8@84379500, W45N8@84378900 "
        "remain unfilled or listener-filled and were not retried here."
    ),
    "prior_told_box_freeze_aged_out": [
        {
            "from": "2026-11-21 00:19:22",
            "to": "2026-11-21 00:22:38",
            "sec": 195,
            "stats": "84383131..84383249",
            "span": 119,
            "official_fill": {r: gaps["gap_0014_0022"][r]["fill"] for r in ROOMS},
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-21_0022",
            "aged_out_of_window_start": 84383501,
            "note": "Combined with preceding no-STATS after 00:14:38. Still 119/119 all five.",
        },
        {
            "from": "2026-11-20 23:50:34",
            "to": "2026-11-20 23:57:00",
            "sec": 385,
            "stats": "84382641..84382889",
            "span": 249,
            "official_fill": {r: gaps["gap_2340_2357"][r]["fill"] for r in ROOMS},
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-21_0022",
            "aged_out_of_window_start": 84383501,
            "note": "Combined with preceding 23:40 no-STATS. W46N8/W47N8/W47N7 249/249; W45N8 189/249; W45N7 149/249.",
        },
        {
            "from": "2026-11-20 23:11:55",
            "to": "2026-11-20 23:20:53",
            "sec": 537,
            "stats": "84382221..84382359",
            "span": 139,
            "official_fill": "not re-queried this run (aged out of window start 84383501); previously 139/139 all five",
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-20_2320",
            "aged_out_of_window_start": 84383501,
            "note": "Previously 139/139 all five; not re-measured in this 01:30 post_counts.",
        },
    ],
    "w47n7_official_empty_no_creep": {
        "distinct": 700,
        "empty_n": 0,
        "ranges": "",
        "note": "Not present in this first-pass window (W47N7 700/700).",
    },
    "listener": {
        "single_slot": True,
        "roomSlot": slot,
        "rot": rot,
        "pid": 1594422,
        "started": "01:25:12",
        "parent": 4035476,
        "yield": (not yield_absent),
        "restarted_this_run": False,
        "auto_restart": "01:25:02 after box freeze 01:10:46-01:24:59; listener.py started 01:25:12",
        "live_gameTime": live.get("gameTime"),
        "live_stats_t": stats.get("t"),
        "live_objects_n": len(live.get("objects") or []),
        "note": "Listener auto-restarted on box wake and reconnected on its own (live.json fresh, creep_cpu/path_arrivals ingesting). Single peacetime slot 5:5:1:1, no yield file. This run did not restart the listener or war_cmd/pulse.",
    },
    "war_cmd_pulse_restarted": False,
    "concurrent_1h_patrol": {
        "dir": "_patrol_2026-11-21_0124",
        "note": (
            "Concurrent 1h patrol was already running during this backfill. It finished official history_backfill "
            "at 01:28:36 (rc=0, inserted=9575, reconstructed 84383401..84384100, missing_chunks=2 W45N7@84383500 and "
            "W45N7@84383900) and later inserted just-published 84384100 at 01:33:24. This run did not write the patrol folder."
        ),
    },
    "cpu_tip": tips["creep_cpu"],
    "path_tip": tips["path_arrivals"],
    "room_stats_tip": tips["room_stats"],
    "tick_s_reason": tick.get("reason"),
    "post_counts_tips_at": post.get("at"),
    "post_counts_tips": post_tips,
}

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

prev = ROOT / "state" / "history_backfill.json"
if prev.exists():
    shutil.copy2(prev, ROOT / "state" / "history_backfill.prev.json")
shutil.copy2(DIR / "history_backfill.json", prev)

jp_lines = []
for room in ROOMS:
    p = post["post"][room]
    act = actual_by[room]
    scr = script_by[room]
    extra = f" (script {scr})" if act != scr else ""
    jp_lines.append(f"  {room} distinct={p['distinct']} rows={p['rows']} actual={act}{extra}")

def gap_line(key):
    return "  " + "  ".join(
        f"{r} {gaps[key][r]['fill']}"
        + (f" missing {gaps[key][r]['missing_range']}" if gaps[key][r]["missing_n"] else "")
        for r in ROOMS
    )

g_new = gap_line("gap_0110_0124")
g_0050 = gap_line("gap_0050_0057")
g_0014 = gap_line("gap_0014_0022")
g_2340 = gap_line("gap_2340_2357")

win_lines = "\n".join(
    f"  {r} {win[r]['distinct']}/700 rows={win[r]['rows']}"
    + (" official_404=200 holes 84383501..84383600 and 84383901..84384000" if r == "W45N7" else "")
    for r in ROOMS
)

first_txt = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip()
nl = "\n"
wrap_txt = f"""{first_txt}

---- wrap {now_s} ----
confirm {confirm_at} gt={confirm_gt} and retry2 {retry2_at} gt={retry2_gt} still official 404 W45N7@84383500 and W45N7@84383900 (first pass 33/35 official GETs 200, missing_chunks=2). Both are empty in DB (0/100) so they are trajectory holes 84383501..84383600 and 84383901..84384000. Coverage official_404=200. W45N7@84383500 was already recorded untold by the 01:00 half-hour; W45N7@84383900 is NEW. Already-told leftover official 404s W45N7@84382700 (hole 84382701..84382800, 0/100), W46N8@84382900 (DB 67/100 missing 84382901..84382933) and W45N8@84382600 (0/100), plus older leftovers W47N8@84382100, W47N7@84380900, W47N8@84380300, W47N8@84379500, W45N8@84378900, aged out of window start 84383501 and were not retried here.
tick_s_first={tick_s_first:.5f} printed=4.200 in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=30 corrective={int(tick.get("ts_realigned_to_later_mean") or 0)}
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
just-published 84384200 at {jp.get("at")} game.time={jp.get("game_time")} all_five_200={jp_all_five} actual_inserted={actual_sum} ticks 84384201..84384300; script inserted={script_sum}{mismatch_s} All five ended 100/100.
inserted_window={inserted_window} inserted_total={inserted_total} (first {inserted_first} + confirm {inserted_confirm} + retry2 {inserted_retry2} + just 84384200 actual {actual_sum})
NEW box freeze 01:10:46-01:24:59 (846s; already healed; listener auto-restart 01:25:02; python 1594422 started 01:25:12). STATS hole 84383931..84384149 (219t; last STATS 84383930 at 01:10:36, next 84384150 at 01:25:52); no preceding no-STATS. Official-filled four rooms 219/219; W45N7 149/219 missing 84383931..84384000 (official 404 W45N7@84383900). Concurrent 1h patrol _patrol_2026-11-21_0124 filled this gap first (through 84384100 plus just-published 84384100). Next 1h patrol should tell this NEW freeze and the NEW official 404 trajectory hole W45N7@84383900, plus the already-recorded untold freeze 00:50:52-00:57:30 and official 404 W45N7@84383500. Already-recorded untold freeze 00:50:52-00:57:30 (STATS 84383651..84383759, 109t) remains in window and is still 109/109 all five (recorded by 01:00 half-hour). Already-told freeze 00:19:22-00:22:38 plus preceding no-STATS after 00:14:38 (STATS 84383131..84383249, 119t) and already-told 23:40 no-STATS + 23:50:34-23:57:00 freeze (STATS 84382641..84382889, 249t) aged out of window start 84383501. This run did not restart the listener or war_cmd/pulse. Peacetime single-slot 5:5:1:1, no yield file. Concurrent 1h patrol _patrol_2026-11-21_0124.
"""

(DIR / "history_backfill_now.txt").write_text(wrap_txt)
(DIR / "history_backfill.txt").write_text(wrap_txt)
shutil.copy2(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")
shutil.copy2(DIR / "backfill_retry2.txt", ROOT / "state" / "_halfhour_backfill_retry2_0130.txt")

verify = f"""{now_s}
first pass 33/35 official GETs 200 missing_chunks=2 W45N7@84383500, W45N7@84383900 reconstructed 84383501..84384200 (700)
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
{win_lines}
just-published 84384200 ticks 84384201..84384300 actual_inserted={actual_sum} script={script_sum} all_five_200={jp_all_five}
{nl.join(jp_lines)}
gap_0110_0124 STATS 84383931..84384149 (219) NEW box freeze 01:10:46-01:24:59; official-filled four rooms 219/219, W45N7 149/219 missing 84383931..84384000
{g_new}
gap_0050_0057 STATS 84383651..84383759 (109) already-recorded untold by 01:00 half-hour (box freeze 00:50:52-00:57:30); still 109/109 all five
{g_0050}
gap_0014_0022 STATS 84383131..84383249 (119) already-told by 00:32 patrol (no-STATS after 00:14:38 + box freeze 00:19:22-00:22:38); aged out of window start 84383501; still 119/119 all five
{g_0014}
gap_2340_2357 STATS 84382641..84382889 (249) already-told by 00:32 patrol; aged out of window start 84383501; official-filled three rooms 249/249, W45N8 189/249, W45N7 149/249
{g_2340}
leftover official 404 W45N7@84383500 still 404 after confirm/retry2; 0/100 (trajectory hole; already recorded untold by 01:00 half-hour)
NEW official 404 W45N7@84383900 still 404 after confirm/retry2; 0/100 (trajectory hole)
aged-out already-told official 404 W45N7@84382700 0/100, W46N8@84382900 67/100, W45N8@84382600 0/100 (not retried)
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.200 corrective={int(tick.get("ts_realigned_to_later_mean") or 0)} ts_realigned_first=30
tips room_stats={tips['room_stats']} creep_cpu={tips['creep_cpu']} path_arrivals={tips['path_arrivals']}
listener pid=1594422 started=01:25:12 parent=4035476 slot={slot} rot={rot_s} yield=absent restarted_this_run=false
ok_quiet=True
"""
(DIR / "verify.txt").write_text(verify)
shutil.copy2(DIR / "verify.txt", ROOT / "state" / "_halfhour_backfill_verify.txt")
summary = (
    f"wrote wrap {now_s}\n"
    f"inserted_window {inserted_window} inserted_total {inserted_total} just_actual {actual_sum}\n"
    f"slot {slot} tips {tips}\n"
    f"ok_quiet=True\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run.full.txt").write_text(summary)
print(summary, end="")
