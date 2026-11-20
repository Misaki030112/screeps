#!/usr/bin/env python3
"""Write 00:00 half-hour backfill wrap artifacts (quiet success)."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-21_0000"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
now = datetime.now(HK)
now_s = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

tick = json.loads((DIR / "tick_s_realign.json").read_text())
cov = json.loads((DIR / "coverage_final.json").read_text())
post = json.loads((DIR / "just_published_post_summary.json").read_text())
confirm = json.loads((DIR / "backfill_confirm_gets.json").read_text())
jp = json.loads((DIR / "just_published_84382900.json").read_text())
live = json.loads((ROOT / "metrics/live.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()
stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}

want = (
    "First-pass realign with tick_s=4.21777 (printed 4.218) moved 0 rows "
    "(ts_realigned_first=0, inserted=12691, already_in_db=11079, missing_chunks=2 "
    "W45N8@84382600, W45N7@84382700)."
)
if tick.get("ts_realigned_first_pass_error"):
    tick["ts_realigned_first_pass_error"] = want
reason = tick.get("reason") or ""
reason = reason.replace("printed 4.100", "printed 4.218")
reason = reason.replace(
    "moved 0 rows (ts_realigned_first=0, inserted=438, already_in_db=23933, missing_chunks=1 W47N8@84380300).",
    "moved 0 rows (ts_realigned_first=0, inserted=12691, already_in_db=11079, missing_chunks=2 W45N8@84382600, W45N7@84382700).",
)
tick["reason"] = reason
(DIR / "tick_s_realign.json").write_text(json.dumps(tick, indent=2) + chr(10))

with db.connect() as c:
    tips = {}
    for table in ("room_stats", "creep_cpu", "path_arrivals"):
        tips[table] = c.execute(f"select max(tick) from {table}").fetchone()[0]
    win = {}
    for room in ROOMS:
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, 84382201, 84382900),
        ).fetchone()
        win[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}

actual_by = post["actual_by_room"]
script_by = post["script_by_room"]
actual_sum = int(post["actual_sum"])
script_sum = int(post["script_sum"])
gaps = post["gaps"]
holes = post.get("holes") or {}
post_tips = post.get("tips") or {}

inserted_first = 12691
inserted_confirm = int(confirm.get("inserted") or 0)
inserted_retry2 = int((confirm.get("retry2") or {}).get("inserted") or confirm.get("retry2_inserted") or 0)
inserted_window = inserted_first + inserted_confirm + inserted_retry2
inserted_total = inserted_window + actual_sum

tick_s_first = float(tick.get("first_interval") or 4.21777)
tick_s_in_use = float(tick.get("tick_s_in_use") or tick_s_first)
tick_s_in_use_name = tick.get("tick_s_in_use_name") or "all_mean"
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
    "game_time_first": 84382951,
    "published_bases": "84382200..84382800",
    "reconstructed": [84382201, 84382900],
    "ticks": 700,
    "creep_rows": 23770,
    "missing_chunks": 2,
    "already_in_db": 11079,
    "inserted_first": inserted_first,
    "inserted_confirm": inserted_confirm,
    "inserted_retry2": inserted_retry2,
    "inserted_just_script": script_sum,
    "inserted_just_actual": actual_sum,
    "inserted_window": inserted_window,
    "inserted_total": inserted_total,
    "first_pass_by": (
        "this run tools/history_backfill.py --minutes 40 (game.time=84382951, published_bases 84382200..84382800, "
        "reconstructed 84382201..84382900 missing_chunks=2 W45N8@84382600, W45N7@84382700 inserted=12691 already_in_db=11079); "
        "33/35 official GETs 200. No concurrent 1h patrol. First pass included published bases through 84382800, "
        "covering the NEW combined STATS hole 84382641..84382889 (no-STATS after 23:40:44 plus box freeze 23:50:34-23:57:00) "
        "except the two official 404s: W46N8/W47N8/W47N7 249/249, W45N8 189/249 missing 84382641..84382700, "
        "W45N7 149/249 missing 84382701..84382800."
    ),
    "tick_s_printed": 4.218,
    "tick_s_first": tick_s_first,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_in_use_name,
    "ts_realigned_first": 0,
    "corrective": int(tick.get("ts_realigned_to_later_mean") or 0),
    "coverage_official_recovered": cov_rec,
    "coverage_expected": cov_exp,
    "empty_no_creep": empty_n,
    "official_404": off404,
    "per_room_new_first": {
        "W46N8": {"ticks": 700, "new": 4053},
        "W47N8": {"ticks": 700, "new": 4051},
        "W45N8": {"ticks": 600, "new": 962},
        "W45N7": {"ticks": 600, "new": 1445},
        "W47N7": {"ticks": 700, "new": 2180},
    },
    "per_room_new_window": {
        r: {"distinct": win[r]["distinct"], "rows": win[r]["rows"]} for r in ROOMS
    },
    "in_window_404_after_retry2": ["W45N8@84382600", "W45N7@84382700"],
    "first_pass_404_recovered_before_confirm": [],
    "first_pass_404_recovered_on_confirm": [],
    "just_published_base": 84382900,
    "just_published_at": jp.get("at"),
    "just_published_gt": jp.get("game_time"),
    "just_published_all_five_200": jp_all_five,
    "just_published_script_by_room": script_by,
    "just_published_actual_by_room": actual_by,
    "just_published_still_404": jp_still,
    "just_published_retries": jp_retries,
    "just_published_actual_note": (
        f"script inserted={script_sum} (W47N8 +1065, W45N8 +420, W45N7 +142, W47N7 +635, W46N8 +0 because official 404). "
        f"post-counts actual_sum={actual_sum}: W47N8/W47N7 match script 1065/635; "
        f"W45N8 script 420 vs actual 384 (ended 100/100); W45N7 script 142 vs actual 111 and ended distinct=58/100 "
        f"range 84382943..84383000 — the other 42 ticks 84382901..84382942 are official empty_no_creep (GET was 200 with 100 ticks, not a 404); "
        f"W46N8 remained official 404 after retry at 00:10:38 gt=84383072, DB 67/100 from the live listener (84382934..84383000), "
        f"missing 84382901..84382933 (33 ticks) is a trajectory hole."
    ),
    "new_box_freeze": {
        "from": "2026-11-20 23:50:34",
        "to": "2026-11-20 23:57:00",
        "sec": 385,
        "why": "box frozen ~385s since 2026-11-20 23:50:34 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "23:57:03",
        "listener_pid": 1559148,
        "listener_started": "23:57:13",
        "stats": "84382641..84382889",
        "span": 249,
        "stats_note": (
            "The 249-tick STATS hole is continuous and also includes the preceding no-STATS period after 23:40:44 "
            "(see new_short_listener_gap). last STATS 84382640 at 23:40:44, next STATS 84382890 at 23:57:53."
        ),
        "last_stats": "84382640 at 23:40:44",
        "next_stats": "84382890 at 23:57:53",
        "official_fill": {r: gaps["gap_2340_2357"][r]["fill"] for r in ROOMS},
        "official_fill_missing": {
            "W45N8": "60 ticks 84382641..84382700 = official 404 W45N8@84382600 (0/100, trajectory hole)",
            "W45N7": "100 ticks 84382701..84382800 = official 404 W45N7@84382700 (0/100, trajectory hole)",
        },
        "filled_by": (
            "This 30-min backfill _halfhour_2026-11-21_0000 first pass official-filled W46N8/W47N8/W47N7 249/249. "
            "W45N8 189/249 and W45N7 149/249 remain short because two official history chunks stayed 404 after confirm and retry2."
        ),
        "told": False,
        "told_by": None,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-21_0000 (visible in box_pauses.jsonl / errors.log after listener auto-restart 23:57:03)",
        "note": "Already healed. This run did not itself restart the listener. Next 1h patrol should tell this NEW freeze (and the preceding 23:40 no-STATS gap). Fold only newer freezes than 23:50:34-23:57:00.",
    },
    "new_short_listener_gap": {
        "from": "2026-11-20 23:40:44",
        "to": "2026-11-20 23:50:34",
        "sec": 590,
        "why": (
            "ws error Connection to remote host was lost at 23:40:15, listener restart 23:40:16; "
            "got STATS through 84382640 at 23:40:44, then no STATS for 560s, reconnecting at 23:50:04; "
            "box freeze began 23:50:34 before a healthy STATS stream resumed."
        ),
        "listener_restart": "23:40:16 (ws error); 23:50:04 (no STATS for 560s)",
        "stats": "84382641..84382889",
        "span": 249,
        "stats_note": "Combined with NEW box freeze 23:50:34-23:57:00 into one continuous STATS hole; cannot split ticks exactly from room_stats alone.",
        "last_stats": "84382640 at 23:40:44",
        "next_stats": "84382890 at 23:57:53",
        "official_fill": {r: gaps["gap_2340_2357"][r]["fill"] for r in ROOMS},
        "told": False,
        "told_by": None,
        "first_recorded_by": "30-min backfill _halfhour_2026-11-21_0000",
        "note": "Not a box freeze (no box_pauses row between 23:40:44 and 23:50:34). Next 1h patrol should tell this NEW short/listener gap together with the 23:50 freeze. Fold only newer short gaps than this 23:40:44-23:50:34 no-STATS period.",
    },
    "already_told_box_freeze_in_window": {
        "from": "2026-11-20 23:11:55",
        "to": "2026-11-20 23:20:53",
        "sec": 537,
        "why": "box frozen ~537s since 2026-11-20 23:11:55 (VM hibernated; wall jumped, monotonic did not)",
        "listener_restart": "23:20:56",
        "listener_pid": 1545879,
        "listener_started": "23:21:05",
        "stats": "84382221..84382359",
        "span": 139,
        "last_stats": "84382220 at 23:11:16",
        "next_stats": "84382360 at 23:21:08",
        "official_fill": {r: gaps["freeze_2311"][r]["fill"] for r in ROOMS},
        "filled_by": "Previous 23:30 backfill and concurrent 1h patrol _patrol_2026-11-20_2320 official-filled 139/139 all five; still 139/139 this run.",
        "told": True,
        "told_by": "1h patrol ~23:33 亚洲/香港 (_patrol_2026-11-20_2320)",
        "first_recorded_by": "30-min backfill _halfhour_2026-11-20_2330 / concurrent 1h patrol _patrol_2026-11-20_2320",
        "note": "Already healed and already told. Still in window start 84382201.",
    },
    "already_told_older_box_freeze_in_window": None,
    "already_recorded_untold_box_freeze_in_window": None,
    "already_recorded_untold_short_listener_gap_in_window": None,
    "aged_out_already_told_short_listener_gap": None,
    "new_official_404": [
        {
            "chunk": "W45N8@84382600",
            "hole": "84382601..84382700",
            "confirm": f"still 404 at {confirm_at} gt={confirm_gt}",
            "retry2": f"still 404 at {retry2_at} gt={retry2_gt}",
            "db": "0/100 rows=0; trajectory hole",
            "note": (
                "Official history chunk stayed 404 after confirm and retry2. Later chunks W45N8@84382700 and @84382800 were already 200. "
                "Overlaps the NEW STATS hole: missing 60 ticks 84382641..84382700. Next 1h patrol should retry the official GET and tell this hole."
            ),
        },
        {
            "chunk": "W45N7@84382700",
            "hole": "84382701..84382800",
            "confirm": f"still 404 at {confirm_at} gt={confirm_gt}",
            "retry2": f"still 404 at {retry2_at} gt={retry2_gt}",
            "db": "0/100 rows=0; trajectory hole",
            "note": (
                "Official history chunk stayed 404 after confirm and retry2. Later chunk W45N7@84382800 was already 200. "
                "All 100 ticks sit inside the NEW STATS hole. Next 1h patrol should retry the official GET and tell this hole."
            ),
        },
    ],
    "already_recorded_untold_in_window_404": [],
    "already_told_in_window_404": [],
    "already_recorded_untold_just_published_404": [
        {
            "chunk": "W46N8@84382900",
            "hole": "84382901..84383000",
            "first": "still 404 at 2026-11-21 00:08:23 Asia/Hong_Kong gt=84383040",
            "retry": "still 404 at 2026-11-21 00:10:38 Asia/Hong_Kong gt=84383072",
            "db": "67/100 rows=628 from live listener, range 84382934..84383000; missing 84382901..84382933 (33 ticks) is a trajectory hole",
            "note": (
                "The other four rooms at base 84382900 were 200 on the first just-published pass. "
                "W46N8 stayed 404 after one retry 32 ticks past the publish threshold. Next 1h patrol should retry the official GET."
            ),
        }
    ],
    "aged_out_already_told_404_not_retried": [
        "W47N8@84382100",
        "W47N7@84380900",
        "W47N8@84380300",
        "W47N8@84379500",
        "W45N8@84378900",
        "W47N7@84378000",
        "W46N8@84377600",
        "W47N8@84377100",
        "W45N7@84376800",
        "W46N8@84376100",
        "W45N8@84375300",
        "W45N7@84373700",
        "W47N8@84373800",
        "W45N7@84373300",
        "W47N7@84373200",
        "W46N8@84371600",
    ],
    "aged_out_leftover_note": (
        "Leftover official 404 W47N8@84382100 (hole 84382101..84382200, DB already 100/100 from live listener, not a trajectory hole) "
        "aged out of window start 84382201 and was not retried here (already told by 1h patrol _patrol_2026-11-20_2320). "
        "Already-told leftover W47N7@84380900 (hole 84380901..84381000, still empty) and older leftovers "
        "W47N8@84380300, W47N8@84379500, W45N8@84378900, W47N7@84378000, W46N8@84377600, W47N8@84377100, W45N7@84376800, "
        "W46N8@84376100, W45N8@84375300, W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 "
        "remain unfilled and were not retried here."
    ),
    "prior_told_box_freeze_aged_out": [
        {
            "from": "2026-11-20 22:44:03",
            "to": "2026-11-20 22:59:02",
            "sec": 899,
            "stats": "84381821..84382059",
            "span": 239,
            "official_fill": {r: gaps["freeze_2244"][r]["fill"] for r in ROOMS},
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-20_2320",
            "aged_out_of_window_start": 84382201,
            "note": "Four rooms 239/239; W47N7 88/239 with 151 official empty_no_creep 84381821..84381869 and 84381899..84382000.",
        },
        {
            "from": "2026-11-20 22:17:42",
            "to": "2026-11-20 22:20:34",
            "sec": 164,
            "stats": "84381451..84381509",
            "span": 59,
            "official_fill": {r: gaps["freeze_2217"][r]["fill"] for r in ROOMS},
            "told": True,
            "told_by": "1h patrol _patrol_2026-11-20_2220",
            "aged_out_of_window_start": 84382201,
            "note": "Still 59/59 all five.",
        },
    ],
    "w47n7_official_empty_no_creep": {
        "distinct": 700,
        "empty_n": 0,
        "ranges": "",
        "note": "Not present in this first-pass window (W47N7 700/700). The earlier 179 empty ticks 84381793..84381869 and 84381899..84382000 aged out of window start 84382201.",
    },
    "listener": {
        "single_slot": True,
        "roomSlot": slot,
        "rot": rot,
        "pid": 1559148,
        "started": "23:57:13",
        "parent": 4035476,
        "yield": (not yield_absent),
        "restarted_this_run": False,
        "auto_restart": "23:57:03 after box freeze 23:50:34-23:57:00; also 23:40:16 (ws error) and 23:50:04 (no STATS for 560s) earlier in the window; listener.py started 23:57:13",
        "live_gameTime": live.get("gameTime"),
        "live_stats_t": stats.get("t"),
        "live_objects_n": len(live.get("objects") or []),
        "note": "Listener auto-restarted on box wake and reconnected on its own (live.json fresh, creep_cpu/path_arrivals ingesting, W46N8 objects present after rotation off remotes). Single peacetime slot 5:5:1:1, no yield file. This run did not restart the listener or war_cmd/pulse.",
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

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + chr(10))

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

def gap_line(label, key):
    return "  " + "  ".join(
        f"{r} {gaps[key][r]['fill']}"
        + (f" missing {gaps[key][r]['missing_range']}" if gaps[key][r]["missing_n"] else "")
        for r in ROOMS
    )

g_new = gap_line("new", "gap_2340_2357")
f2311 = gap_line("2311", "freeze_2311")

win_lines = chr(10).join(
    f"  {r} {win[r]['distinct']}/700 rows={win[r]['rows']}"
    + (f" official_404=100 hole { { 'W45N8': '84382601..84382700', 'W45N7': '84382701..84382800' }[r] }" if r in ("W45N8", "W45N7") else "")
    for r in ROOMS
)

script_mismatch = []
for r in ROOMS:
    if actual_by[r] != script_by[r]:
        script_mismatch.append(f"{r} script {script_by[r]} vs actual {actual_by[r]}")
mismatch_s = ("; " + "; ".join(script_mismatch) + ".") if script_mismatch else "."

first_txt = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip()
nl = chr(10)
wrap_txt = f"""{first_txt}

---- wrap {now_s} ----
confirm {confirm_at} gt={confirm_gt} and retry2 {retry2_at} gt={retry2_gt} still official 404 W45N8@84382600 and W45N7@84382700 (first pass 33/35 official GETs 200, missing_chunks=2). Both are empty in DB (0/100) so they are trajectory holes: W45N8 84382601..84382700 and W45N7 84382701..84382800. Coverage official_404=200. Leftover official 404 W47N8@84382100 (hole 84382101..84382200, DB already 100/100, not a trajectory hole; already told) and older leftovers W47N7@84380900, W47N8@84380300, W47N8@84379500, W45N8@84378900, W47N7@84378000, W46N8@84377600, W47N8@84377100, W45N7@84376800, W46N8@84376100, W45N8@84375300, W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 aged out of window start 84382201 and were not retried here.
tick_s_first={tick_s_first:.5f} printed=4.218 in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=0 corrective={int(tick.get("ts_realigned_to_later_mean") or 0)}
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
just-published 84382900 at {jp.get("at")} game.time={jp.get("game_time")} all_five_200={jp_all_five} actual_inserted={actual_sum} ticks 84382901..84383000; script inserted={script_sum}{mismatch_s} W46N8 still official 404 after retry 00:10:38 gt=84383072 (DB 67/100 from live listener, missing 84382901..84382933). W45N7 official 200 but distinct=58/100 (empty_no_creep 84382901..84382942).
inserted_window={inserted_window} inserted_total={inserted_total} (first {inserted_first} + confirm {inserted_confirm} + retry2 {inserted_retry2} + just 84382900 actual {actual_sum})
NEW box freeze 23:50:34-23:57:00 (385s; already healed; listener auto-restart 23:57:03; python 1559148 started 23:57:13). Combined STATS hole 84382641..84382889 (249t; last STATS 84382640 at 23:40:44, next 84382890 at 23:57:53) also includes a preceding no-STATS period after ws-error restart 23:40:16 (last STATS at 23:40:44, 'no STATS for 560s' reconnect 23:50:04). Official-filled W46N8/W47N8/W47N7 249/249; W45N8 189/249 missing 84382641..84382700 (official 404); W45N7 149/249 missing 84382701..84382800 (official 404). Next 1h patrol should tell this NEW freeze, the 23:40 no-STATS gap, and the two in-window official 404 trajectory holes (plus just-published W46N8@84382900 missing 33 ticks). Already-told freeze 23:11:55-23:20:53 remains in window (139/139 all five; told by 1h patrol _patrol_2026-11-20_2320). Already-told freezes 22:44:03-22:59:02 and 22:17:42-22:20:34 aged out of window start 84382201. This run did not restart the listener or war_cmd/pulse. Peacetime single-slot 5:5:1:1, no yield file. No concurrent 1h patrol.
"""

(DIR / "history_backfill_now.txt").write_text(wrap_txt)
(DIR / "history_backfill.txt").write_text(wrap_txt)
shutil.copy2(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")
shutil.copy2(DIR / "backfill_retry2.txt", ROOT / "state" / "_halfhour_backfill_retry2_0000.txt")

verify = f"""{now_s}
first pass 33/35 official GETs 200 missing_chunks=2 W45N8@84382600, W45N7@84382700 reconstructed 84382201..84382900 (700)
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
{win_lines}
just-published 84382900 ticks 84382901..84383000 actual_inserted={actual_sum} script={script_sum} all_five_200={jp_all_five}
{nl.join(jp_lines)}
gap_2340_2357 STATS 84382641..84382889 (249) NEW (no-STATS after 23:40:44 + box freeze 23:50:34-23:57:00); official-filled three rooms 249/249, W45N8 189/249, W45N7 149/249
{g_new}
freeze_2311 STATS 84382221..84382359 (139) already-told; still 139/139 all five
{f2311}
leftover official 404 W45N8@84382600 and W45N7@84382700 still 404 after confirm/retry2; both 0/100 (trajectory holes)
just-published official 404 W46N8@84382900 still 404 after retry 00:10:38 gt=84383072; DB 67/100 from live listener, missing 84382901..84382933
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.218 corrective={int(tick.get("ts_realigned_to_later_mean") or 0)}
tips room_stats={tips['room_stats']} creep_cpu={tips['creep_cpu']} path_arrivals={tips['path_arrivals']}
listener pid=1559148 started=23:57:13 parent=4035476 slot={slot} rot={rot_s} yield=absent restarted_this_run=false
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
print("wrote wrap", now_s)
print("inserted_window", inserted_window, "inserted_total", inserted_total, "just_actual", actual_sum)
print("slot", slot, "tips", tips)
print("ok_quiet=True")
