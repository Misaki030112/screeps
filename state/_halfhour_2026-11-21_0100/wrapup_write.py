#!/usr/bin/env python3
"""Write 01:00 half-hour backfill wrap artifacts (quiet success)."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-21_0100"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
now = datetime.now(HK)
now_s = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

tick = json.loads((DIR / "tick_s_realign.json").read_text())
cov = json.loads((DIR / "coverage_final.json").read_text())
post = json.loads((DIR / "just_published_post_summary.json").read_text())
confirm = json.loads((DIR / "backfill_confirm_gets.json").read_text())
jp = json.loads((DIR / "just_published_84383700.json").read_text())
live = json.loads((ROOT / "metrics/live.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()
stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}

want = (
    "First-pass realign with tick_s=4.16858 (printed 4.169) moved 7267 rows "
    "(ts_realigned_first=7267, inserted=6424, already_in_db=19096, missing_chunks=1 "
    "W45N7@84383500)."
)
if tick.get("ts_realigned_first_pass_error"):
    tick["ts_realigned_first_pass_error"] = want
reason = tick.get("reason") or ""
reason = reason.replace("printed 4.100", "printed 4.169")
reason = reason.replace(
    "moved 7267 rows (ts_realigned_first=7267, inserted=438, already_in_db=23933, missing_chunks=1 W47N8@84380300).",
    "moved 7267 rows (ts_realigned_first=7267, inserted=6424, already_in_db=19096, missing_chunks=1 W45N7@84383500).",
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
            (room, 84383001, 84383700),
        ).fetchone()
        win[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}

actual_by = post["actual_by_room"]
script_by = post["script_by_room"]
actual_sum = int(post["actual_sum"])
script_sum = int(post["script_sum"])
gaps = post["gaps"]
holes = post.get("holes") or {}
post_tips = post.get("tips") or {}

inserted_first = 6424
inserted_confirm = int(confirm.get("inserted") or 0)
inserted_retry2 = int((confirm.get("retry2") or {}).get("inserted") or confirm.get("retry2_inserted") or 0)
inserted_window = inserted_first + inserted_confirm + inserted_retry2
inserted_total = inserted_window + actual_sum

tick_s_first = float(tick.get("first_interval") or 4.16858)
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

payload = {
    "at": now_s,
    "ok_quiet": True,
    "game_time_first": 84383781,
    "published_bases": "84383000..84383600",
    "reconstructed": [84383001, 84383700],
    "ticks": 700,
    "creep_rows": 25520,
    "missing_chunks": 1,
    "already_in_db": 19096,
    "inserted_first": inserted_first,
    "inserted_confirm": inserted_confirm,
    "inserted_retry2": inserted_retry2,
    "inserted_just_script": script_sum,
    "inserted_just_actual": actual_sum,
    "inserted_window": inserted_window,
    "inserted_total": inserted_total,
    "first_pass_by": (
        "this run tools/history_backfill.py --minutes 40 (game.time=84383781, published_bases 84383000..84383600, "
        "reconstructed 84383001..84383700 missing_chunks=1 W45N7@84383500 inserted=6424 already_in_db=19096); "
        "34/35 official GETs 200. No concurrent 1h patrol. First pass included published bases through 84383600, "
        "covering the first 50 ticks of the NEW STATS hole 84383651..84383759 (box freeze 00:50:52-00:57:30); "
        "just-published 84383700 later filled 84383701..84383800, so all five ended 109/109."
    ),
    "tick_s_printed": 4.169,
    "tick_s_first": tick_s_first,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_in_use_name,
    "ts_realigned_first": 7267,
    "corrective": int(tick.get("ts_realigned_to_later_mean") or 0),
    "coverage_official_recovered": cov_rec,
    "coverage_expected": cov_exp,
    "empty_no_creep": empty_n,
    "official_404": off404,
    "per_room_new_first": {
        "W46N8": {"ticks": 700, "new": 2348},
        "W47N8": {"ticks": 700, "new": 1602},
        "W45N8": {"ticks": 700, "new": 823},
        "W45N7": {"ticks": 600, "new": 722},
        "W47N7": {"ticks": 700, "new": 929},
    },
    "per_room_new_window": {
        r: {"distinct": win[r]["distinct"], "rows": win[r]["rows"]} for r in ROOMS
    },
    "in_window_404_after_retry2": ["W45N7@84383500"],
    "first_pass_404_recovered_before_confirm": [],
    "first_pass_404_recovered_on_confirm": [],
    "just_published_base": 84383700,
    "just_published_at": jp.get("at"),
    "just_published_gt": jp.get("game_time"),
    "just_published_all_five_200": jp_all_five,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "just_published_still_404": jp_still,
    "just_published_retries": jp_retries,
    "just_published_actual_note": (
        f"script inserted={script_sum} (W46N8 +909, W47N8 +1279, W45N8 +462, W45N7 +358, W47N7 +337). "
        f"post-counts actual_sum={actual_sum}: W47N8/W47N7 match script 1279/337; "
        f"W46N8 script 909 vs actual 890; W45N8 script 462 vs actual 350; W45N7 script 358 vs actual 346. "
        f"All five ended 100/100."
    ),
    "new_box_freeze": {
        "from": "2026-11-21 00:50:52",
        "to": "2026-11-21 00:57:30",
        "sec": 393,
        "why": "box frozen ~393s since 2026-11-21 00:50:52 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "00:57:33",
        "listener_pid": 1587483,
        "listener_started": "00:57:42",
        "stats": "84383651..84383759",
        "span": 109,
        "stats_note": (
            "The 109-tick STATS hole is the box freeze alone; errors.log has no preceding no-STATS. "
            "last STATS 84383650 at 00:50:45, next STATS 84383760 at 00:58:28."
        ),
        "last_stats": "84383650 at 00:50:45",
        "next_stats": "84383760 at 00:58:28",
        "official_fill": {r: gaps["gap_0050_0057"][r]["fill"] for r in ROOMS},
        "official_fill_missing": {},
        "filled_by": (
            "This 30-min backfill _halfhour_2026-11-21_0100 official-filled 109/109 all five: "
            "first pass covered 84383651..84383700, just-published 84383700 covered 84383701..84383759."
        ),
        "told": False,
        "told_by": None,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-21_0100 (visible in box_pauses.jsonl / errors.log after listener auto-restart 00:57:33)",
        "note": "Already healed. This run did not itself restart the listener. Next 1h patrol should tell this NEW freeze. Fold only newer freezes than 00:50:52-00:57:30.",
    },
    "new_short_listener_gap": None,
    "already_told_box_freeze_in_window": {
        "from": "2026-11-21 00:19:22",
        "to": "2026-11-21 00:22:38",
        "sec": 195,
        "why": "box frozen ~195s since 2026-11-21 00:19:22 (VM hibernated; wall jumped, monotonic did not), plus preceding no-STATS after 00:14:38 (258s, reconnect 00:18:56)",
        "listener_restart": "00:18:56 (no STATS); 00:22:41 (box freeze)",
        "listener_pid": 1568924,
        "listener_started": "00:22:50",
        "stats": "84383131..84383249",
        "span": 119,
        "last_stats": "84383130 at 00:14:38",
        "next_stats": "84383250 at 00:23:00",
        "official_fill": {r: gaps["gap_0014_0022"][r]["fill"] for r in ROOMS},
        "filled_by": "Previous 00:30 backfill official-filled remaining unpublished tail; still 119/119 all five this run.",
        "told": True,
        "told_by": "1h patrol ~00:32 亚洲/香港 (_patrol_2026-11-21_0022)",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-21_0000 / 1h patrol _patrol_2026-11-21_0022 / confirmed 00:30 backfill",
        "note": "Already healed and already told. Still in window start 84383001.",
    },
    "already_told_older_box_freeze_in_window": None,
    "already_recorded_untold_box_freeze_in_window": None,
    "already_recorded_untold_short_listener_gap_in_window": None,
    "aged_out_already_told_short_listener_gap": {
        "from": "2026-11-20 23:40:44",
        "to": "2026-11-20 23:50:34",
        "combined_with_freeze": "23:50:34-23:57:00",
        "stats": "84382641..84382889",
        "span": 249,
        "aged_out_of_window_start": 84383001,
        "told": True,
        "told_by": "1h patrol ~00:32 亚洲/香港 (_patrol_2026-11-21_0022)",
        "note": "W46N8/W47N8/W47N7 249/249; W45N8 189/249 missing 84382641..84382700 (official 404 W45N8@84382600); W45N7 149/249 missing 84382701..84382800 (official 404 W45N7@84382700).",
    },
    "new_official_404": [
        {
            "chunk": "W45N7@84383500",
            "hole": "84383501..84383600",
            "confirm": f"still 404 at {confirm_at} gt={confirm_gt}",
            "retry2": f"still 404 at {retry2_at} gt={retry2_gt}",
            "db": "0/100 rows=0; trajectory hole",
            "note": (
                "Official history chunk stayed 404 after confirm and retry2. Neighboring chunks W45N7@84383400 and @84383600 were already 200. "
                "This hole is not inside the NEW freeze STATS gap 84383651..84383759. Next 1h patrol should retry the official GET and tell this hole."
            ),
        },
    ],
    "already_recorded_untold_in_window_404": [],
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
        "Already-told leftover official 404s W45N7@84382700 (hole 84382701..84382800, 0/100 trajectory hole) and "
        "W46N8@84382900 (hole 84382901..84383000, DB 67/100 from live listener missing 84382901..84382933) "
        "aged out of window start 84383001 and were not retried here (already told by 1h patrol _patrol_2026-11-21_0022). "
        "Already-told leftover W45N8@84382600 (hole 84382601..84382700, 0/100) also aged out. Older leftovers "
        "W47N8@84382100 (DB 100/100, not a trajectory hole), W47N7@84380900, W47N8@84380300, W47N8@84379500, W45N8@84378900 "
        "remain unfilled or listener-filled and were not retried here."
    ),
    "prior_told_box_freeze_aged_out": [
        {
            "from": "2026-11-20 23:50:34",
            "to": "2026-11-20 23:57:00",
            "sec": 385,
            "stats": "84382641..84382889",
            "span": 249,
            "official_fill": {r: gaps["gap_2340_2357"][r]["fill"] for r in ROOMS},
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-21_0022",
            "aged_out_of_window_start": 84383001,
            "note": "Combined with preceding 23:40 no-STATS. W46N8/W47N8/W47N7 249/249; W45N8 189/249; W45N7 149/249.",
        },
        {
            "from": "2026-11-20 23:11:55",
            "to": "2026-11-20 23:20:53",
            "sec": 537,
            "stats": "84382221..84382359",
            "span": 139,
            "official_fill": {r: gaps["freeze_2311"][r]["fill"] for r in ROOMS},
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-20_2320",
            "aged_out_of_window_start": 84383001,
            "note": "Still 139/139 all five.",
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
        "pid": 1587483,
        "started": "00:57:42",
        "parent": 4035476,
        "yield": (not yield_absent),
        "restarted_this_run": False,
        "auto_restart": "00:57:33 after box freeze 00:50:52-00:57:30; listener.py started 00:57:42",
        "live_gameTime": live.get("gameTime"),
        "live_stats_t": stats.get("t"),
        "live_objects_n": len(live.get("objects") or []),
        "note": "Listener auto-restarted on box wake and reconnected on its own (live.json fresh, creep_cpu/path_arrivals ingesting, W46N8 objects present after rotation). Single peacetime slot 5:5:1:1, no yield file. This run did not restart the listener or war_cmd/pulse.",
    },
    "war_cmd_pulse_restarted": False,
    "concurrent_1h_patrol": None,
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

g_new = gap_line("gap_0050_0057")
g_0014 = gap_line("gap_0014_0022")
g_2340 = gap_line("gap_2340_2357")
f2311 = gap_line("freeze_2311")

win_lines = "\n".join(
    f"  {r} {win[r]['distinct']}/700 rows={win[r]['rows']}"
    + (" official_404=100 hole 84383501..84383600" if r == "W45N7" else "")
    for r in ROOMS
)

script_mismatch = []
for r in ROOMS:
    if actual_by[r] != script_by[r]:
        script_mismatch.append(f"{r} script {script_by[r]} vs actual {actual_by[r]}")
mismatch_s = ("; " + "; ".join(script_mismatch) + ".") if script_mismatch else "."

first_txt = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip()
nl = "\n"
wrap_txt = f"""{first_txt}

---- wrap {now_s} ----
confirm {confirm_at} gt={confirm_gt} and retry2 {retry2_at} gt={retry2_gt} still official 404 W45N7@84383500 (first pass 34/35 official GETs 200, missing_chunks=1). W45N7 is empty in DB (0/100) so it is a trajectory hole 84383501..84383600. Coverage official_404=100. Already-told leftover official 404s W45N7@84382700 (hole 84382701..84382800, 0/100) and W46N8@84382900 (DB 67/100 missing 84382901..84382933) and W45N8@84382600 (0/100), plus older leftovers W47N8@84382100, W47N7@84380900, W47N8@84380300, W47N8@84379500, W45N8@84378900, aged out of window start 84383001 and were not retried here.
tick_s_first={tick_s_first:.5f} printed=4.169 in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=7267 corrective={int(tick.get("ts_realigned_to_later_mean") or 0)}
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
just-published 84383700 at {jp.get("at")} game.time={jp.get("game_time")} all_five_200={jp_all_five} actual_inserted={actual_sum} ticks 84383701..84383800; script inserted={script_sum}{mismatch_s} All five ended 100/100.
inserted_window={inserted_window} inserted_total={inserted_total} (first {inserted_first} + confirm {inserted_confirm} + retry2 {inserted_retry2} + just 84383700 actual {actual_sum})
NEW box freeze 00:50:52-00:57:30 (393s; already healed; listener auto-restart 00:57:33; python 1587483 started 00:57:42). STATS hole 84383651..84383759 (109t; last STATS 84383650 at 00:50:45, next 84383760 at 00:58:28); no preceding no-STATS. Official-filled 109/109 all five (first pass through 84383700 plus just-published 84383701..84383800). Next 1h patrol should tell this NEW freeze and the in-window official 404 trajectory hole W45N7@84383500. Already-told freeze 00:19:22-00:22:38 plus preceding no-STATS after 00:14:38 (STATS 84383131..84383249, 119t) remains in window and is still 119/119 all five (told by 00:32 patrol). Already-told 23:40 no-STATS + 23:50:34-23:57:00 freeze (STATS 84382641..84382889, 249t) and already-told freeze 23:11:55-23:20:53 (139/139 all five) aged out of window start 84383001. This run did not restart the listener or war_cmd/pulse. Peacetime single-slot 5:5:1:1, no yield file. No concurrent 1h patrol.
"""

(DIR / "history_backfill_now.txt").write_text(wrap_txt)
(DIR / "history_backfill.txt").write_text(wrap_txt)
shutil.copy2(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")
shutil.copy2(DIR / "backfill_retry2.txt", ROOT / "state" / "_halfhour_backfill_retry2_0100.txt")

verify = f"""{now_s}
first pass 34/35 official GETs 200 missing_chunks=1 W45N7@84383500 reconstructed 84383001..84383700 (700)
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
{win_lines}
just-published 84383700 ticks 84383701..84383800 actual_inserted={actual_sum} script={script_sum} all_five_200={jp_all_five}
{nl.join(jp_lines)}
gap_0050_0057 STATS 84383651..84383759 (109) NEW box freeze 00:50:52-00:57:30; official-filled 109/109 all five
{g_new}
gap_0014_0022 STATS 84383131..84383249 (119) already-told by 00:32 patrol (no-STATS after 00:14:38 + box freeze 00:19:22-00:22:38); still 119/119 all five
{g_0014}
gap_2340_2357 STATS 84382641..84382889 (249) already-told by 00:32 patrol; aged out of window start 84383001; official-filled three rooms 249/249, W45N8 189/249, W45N7 149/249
{g_2340}
freeze_2311 STATS 84382221..84382359 (139) already-told; aged out of window start 84383001; still 139/139 all five
{f2311}
leftover official 404 W45N7@84383500 still 404 after confirm/retry2; 0/100 (trajectory hole)
aged-out already-told official 404 W45N7@84382700 0/100, W46N8@84382900 67/100, W45N8@84382600 0/100 (not retried)
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.169 corrective={int(tick.get("ts_realigned_to_later_mean") or 0)} ts_realigned_first=7267
tips room_stats={tips['room_stats']} creep_cpu={tips['creep_cpu']} path_arrivals={tips['path_arrivals']}
listener pid=1587483 started=00:57:42 parent=4035476 slot={slot} rot={rot_s} yield=absent restarted_this_run=false
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

