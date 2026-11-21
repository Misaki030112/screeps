#!/usr/bin/env python3
"""Write 15:30 half-hour backfill wrap artifacts (quiet success)."""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

HK = ZoneInfo("Asia/Hong_Kong")
ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-21_1530"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
WIN_TMIN, WIN_TMAX = 84395401, 84396100
JUST_BASE = 84396100
now = datetime.now(HK)
now_s = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")


def _load(name, default=None):
    path = DIR / name
    if path.exists():
        return json.loads(path.read_text())
    if default is not None:
        return default
    raise FileNotFoundError(path)

tick = _load("tick_s_realign.json")
cov = _load("coverage_final.json")
post = _load("just_published_post_summary.json")
confirm = _load("backfill_confirm_gets.json")
jp = _load(f"just_published_{JUST_BASE}.json")
live = json.loads((ROOT / "metrics/live.json").read_text())
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
yield_absent = not (ROOT / "metrics/listener_yield_rooms").exists()
late_txt = (DIR / "backfill_late_retry_W47N7_84395600.txt").read_text().strip() if (DIR / "backfill_late_retry_W47N7_84395600.txt").exists() else ""
late_j = _load("backfill_late_retry_W47N7_84395600.json", default={})

# Listener identity (do not restart; record current process after the 15:19 auto-restart)
listener_pid = 1932081
listener_started = "15:19:43"
listener_parent = 4035476
restarted_this_run = False

retry2_blob = confirm.get("retry2") or {}
inserted_first = 3401
inserted_confirm = int(confirm.get("inserted") or 0)
inserted_retry2 = int(confirm.get("retry2_inserted") or retry2_blob.get("inserted") or 0)
confirm_at = confirm.get("confirm_at") or confirm.get("at")
confirm_gt = confirm.get("confirm_game_time") or confirm.get("game_time")
confirm_still = list(confirm.get("still_404") or [])
confirm_rec = list(confirm.get("recovered") or [])
retry2_at = confirm.get("retry2_at") or retry2_blob.get("at")
retry2_gt = confirm.get("retry2_game_time") or retry2_blob.get("game_time")
retry2_still = list(confirm.get("retry2_still_404") or retry2_blob.get("still_404") or [])
retry2_rec = list(confirm.get("retry2_recovered") or retry2_blob.get("recovered") or [])
actual_by = post["actual_by_room"]
script_by = post["script_by_room"]
actual_sum = int(post["actual_sum"])
script_sum = int(post["script_sum"])
inserted_window = inserted_first + inserted_confirm + inserted_retry2
inserted_total = inserted_window + actual_sum

tick_s_first = float(tick.get("tick_s_used_first_pass") or 4.26890)
tick_s_in_use = float(tick.get("tick_s_in_use") or tick_s_first)
tick_s_in_use_name = tick.get("tick_s_in_use_name") or "first"
corrective = int(tick.get("ts_realigned_to_later_mean") or 0)
cov_rec = cov.get("official_recovered")
cov_exp = cov.get("expected")
empty_n = cov.get("empty_no_creep")
off404 = cov.get("official_404_missing")

slot = live.get("roomSlot")
rot_s = json.dumps(rot, ensure_ascii=False)
jp_still = list(jp.get("still_404") or [])
jp_rec = list(jp.get("recovered") or [])
jp_all_five = (not jp_still) and len(jp_rec) >= 5

script_mismatch = [f"{r} script {script_by[r]} vs actual {actual_by[r]}" for r in ROOMS if actual_by[r] != script_by[r]]
mismatch_s = ("; " + ", ".join(script_mismatch) + ". ") if script_mismatch else ". "

with db.connect() as c:
    tips = {}
    for table in ("room_stats", "creep_cpu", "path_arrivals"):
        tips[table] = c.execute(f"select max(tick) from {table}").fetchone()[0]
    win = {}
    for room in ROOMS:
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, WIN_TMIN, WIN_TMAX),
        ).fetchone()
        win[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}
    hole951_d, hole951_mn, hole951_mx, hole951_n = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        ("W47N8", 84395101, 84395200),
    ).fetchone()
    hole943_d, hole943_mn, hole943_mx, hole943_n = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        ("W46N8", 84394301, 84394400),
    ).fetchone()
    hole956_d, hole956_mn, hole956_mx, hole956_n = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        ("W47N7", 84395601, 84395700),
    ).fetchone()

first_pass_txt = (DIR / "history_backfill.txt").read_text().rstrip() + chr(10)

late_at = late_j.get("at") or "2026-11-21 15:41:14 Asia/Hong_Kong"
late_gt = late_j.get("game_time") or 84396251

wrap_body = (
    f"confirm at {confirm_at} game.time={confirm_gt} still_404={confirm_still} inserted={inserted_confirm} recovered={confirm_rec} skipped=False; "
    f"retry2 at {retry2_at} game.time={retry2_gt} still_404={retry2_still} inserted={inserted_retry2} recovered={retry2_rec} skipped=False. "
    f"First pass 34/35 official GETs 200, missing_chunks=1 W47N7@84395600. "
    f"Confirm 15:33:53 and retry2 15:34:31 still 404; late retry 15:41:14 gt={late_gt} also still 404, inserted=0. "
    f"Already-told leftover official 404 W47N7@84395600 remains in window start 84395401 and was retried (still 404; listener 0/100, hole 100 ticks 84395601..84395700). "
    f"Already-told leftover official 404s W47N8@84395100 / W46N8@84394300 / W45N8@84392600 / W46N8@84390800 / W47N7@84390900 / W46N8@84390400 / W45N7@84388500 / W45N8@84386600 aged out of window start 84395401 and were not retried. "
    f"Just-published {JUST_BASE} at {jp.get('at')} gt={jp.get('game_time')} all_five_200={jp_all_five} script={script_sum} actual={actual_sum}{mismatch_s}"
    f"Coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404} "
    f"(W47N7 leftover official 404 hole 84395601..84395700, listener 0/100; W45N7 evac empty-no-creep 171 ticks 84395930..84396100, official 200 not a 404). "
    f"The delivered 15:28 1h patrol had already official-filled 84395201..84395900 before this run. "
    f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} just_actual={actual_sum} total={inserted_total}. "
    f"tick_s_printed=4.269 first={tick_s_first:.5f} in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=0 corrective={corrective}. "
    f"Listener pid={listener_pid} started={listener_started} parent={listener_parent} slot={slot} rot={rot_s} yield={'absent' if yield_absent else 'present'} restarted_this_run={str(restarted_this_run).lower()}. "
    f"Peacetime single-slot 5:5:1:1. This run did not restart the listener or war_cmd/pulse. No concurrent 1h patrol (15:28 patrol finished 15:29:01 before this run)."
)

told_para = (
    "NEW not-yet-told for the next 1h patrol: (none). "
    "Already told by the delivered 15:28 亚洲/香港 1h patrol and still in official window start 84395401: "
    "leftover official 404 W47N7@84395600 (confirm 15:33:53 gt=84396149, retry2 15:34:31 gt=84396157, and late retry 15:41:14 gt=84396251 still 404; listener 0/100; hole 100 ticks 84395601..84395700); "
    "box freeze 15:14:38-15:19:30 (292s; STATS 84395871..84395959, 89t; official-filled W46N8/W47N8/W45N8/W47N7 89/89, W45N7 59/89 evac empty tail 84395930..84395959 official 200 not a 404; listener auto-restart 15:19:33, python 1932081 started 15:19:43); "
    "box freeze 14:40:53-14:56:54 (952s; STATS 84395401..84395639, 239t; official-filled four rooms 239/239, W47N7 200/239 missing 84395601..84395639 because of leftover official 404 W47N7@84395600; listener auto-restart 14:56:57). "
    "Already told by the 15:28 patrol and now age out of window start 84395401: leftover official 404 W47N8@84395100 (listener 0/100, hole 100 ticks 84395101..84395200), leftover official 404 W46N8@84394300 (listener 79/100 84394301..84394379, hole 21 ticks 84394380..84394400), box freeze 14:15:50-14:23:29 (450s; STATS 84395061..84395179, 119t; official-filled four rooms 119/119, W47N8 40/119 missing 84395101..84395179 because of leftover official 404 W47N8@84395100), box freeze 13:49:01-13:56:56 (475s; STATS 84394681..84394809, 129t; official-filled all five 129/129), box freeze 13:09:46-13:21:14, earlier already-told freezes 12:48:14-12:57:17 / 12:30:42-12:35:35 / 11:49:12-11:57:31 / 11:19:06-11:20:43, short WS gaps 12:10 / 12:18 / 11:12, and older leftover official 404s W45N8@84392600 / W46N8@84390800 / W47N7@84390900 / W46N8@84390400 / W45N7@84388500 / W45N8@84386600. "
    "Fold only newer freezes, short WS gaps, or leftover official 404s than the 15:28-told set; do not re-tell W47N7@84395600, W47N8@84395100, the 15:14 or 14:40 freezes, or earlier already-told items."
)

now_txt = first_pass_txt + f"\n---- wrap {now_s} ----\n" + wrap_body + "\n" + told_para + "\n"
(DIR / "history_backfill_now.txt").write_text(now_txt)
(DIR / "_halfhour_backfill_now.txt").write_text(now_txt)
(ROOT / "state" / "_halfhour_backfill_now.txt").write_text(now_txt)

verify = (
    f"wrap {now_s}\n"
    f"window {WIN_TMIN}..{WIN_TMAX} first_pass 34/35 missing_chunks=1 W47N7@84395600\n"
    f"db_window {json.dumps(win, ensure_ascii=False)}\n"
    f"W47N7@84395600 hole distinct={hole956_d} rows={hole956_n} range={hole956_mn}..{hole956_mx} (listener 0/100; already told by 15:28 patrol; retried confirm/retry2/late still 404)\n"
    f"W47N8@84395100 aged-out hole distinct={hole951_d} rows={hole951_n} range={hole951_mn}..{hole951_mx} (listener 0/100, not retried this run)\n"
    f"W46N8@84394300 aged-out hole distinct={hole943_d} rows={hole943_n} range={hole943_mn}..{hole943_mx} (listener 79/100, not retried this run)\n"
    f"just_published {JUST_BASE} all_five_200={jp_all_five} script={script_sum} actual={actual_sum} by_actual={actual_by} by_script={script_by}\n"
    f"coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}\n"
    f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} just_actual={actual_sum} total={inserted_total}\n"
    f"tick_s_in_use={tick_s_in_use} ({tick_s_in_use_name}) first={tick_s_first} ts_realigned_first=0 corrective={corrective}\n"
    f"tips {tips}\n"
    f"listener pid={listener_pid} started={listener_started} parent={listener_parent} slot={slot} rot={rot_s} yield_absent={yield_absent} restarted_this_run={restarted_this_run}\n"
    f"ok_quiet=True new_official_404_untold=[] new_box_freeze_untold=[]\n"
    f"{told_para}\n"
)
(DIR / "verify.txt").write_text(verify)
(DIR / "_halfhour_backfill_verify.txt").write_text(verify)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify)

payload = {
    "ok_quiet": True,
    "at": now_s,
    "window": [WIN_TMIN, WIN_TMAX],
    "published_bases": [84395400, 84396000],
    "game_time_first": 84396130,
    "first_pass": {
        "gets_200": 34,
        "gets_total": 35,
        "missing_chunks": ["W47N7@84395600"],
        "reconstructed": [WIN_TMIN, WIN_TMAX],
        "creep_rows": 24109,
        "already_in_db": 20708,
        "inserted": inserted_first,
        "ts_realigned": 0,
        "tick_s_printed": 4.269,
    },
    "confirm": {"at": confirm_at, "game_time": confirm_gt, "still_404": confirm_still, "inserted": inserted_confirm, "recovered": confirm_rec},
    "retry2": {"at": retry2_at, "game_time": retry2_gt, "still_404": retry2_still, "inserted": inserted_retry2, "recovered": retry2_rec},
    "late_retry": {"text": late_txt, "still_404": ["W47N7@84395600"], "inserted": 0, "at": late_at, "game_time": late_gt},
    "just_published": {
        "base": JUST_BASE,
        "at": jp.get("at"),
        "game_time": jp.get("game_time"),
        "all_five_200": jp_all_five,
        "script_sum": script_sum,
        "actual_sum": actual_sum,
        "script_by_room": script_by,
        "actual_by_room": actual_by,
        "still_404": jp_still,
    },
    "coverage": {"official_recovered": cov_rec, "expected": cov_exp, "empty_no_creep": empty_n, "official_404_missing": off404},
    "inserted_total": inserted_total,
    "tick_s_in_use": tick_s_in_use,
    "tick_s_in_use_name": tick_s_in_use_name,
    "tick_s_first": tick_s_first,
    "ts_realigned_first": 0,
    "corrective": corrective,
    "tips": tips,
    "window_db": win,
    "listener": {
        "pid": listener_pid,
        "started": listener_started,
        "parent": listener_parent,
        "slot": slot,
        "rot": rot,
        "yield_absent": yield_absent,
        "restarted_this_run": restarted_this_run,
    },
    "already_told_by_1528_patrol": {
        "box_freezes": ["15:14:38-15:19:30", "14:40:53-14:56:54", "14:15:50-14:23:29", "13:49:01-13:56:56"],
        "official_404s": ["W47N7@84395600", "W47N8@84395100", "W46N8@84394300", "W45N8@84392600"],
    },
    "new_untold_box_freezes": [],
    "new_untold_official_404s": [],
    "concurrent_patrol": None,
    "did_not_write_patrol_folder": True,
}
(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")

wrap_line = (
    f"wrap {now_s} ok_quiet=True inserted_total={inserted_total} "
    f"new_box_freeze=[] new_official_404=[] "
    f"already_told_by_15:28_patrol=['15:14:38-15:19:30','14:40:53-14:56:54','W47N7@84395600']"
)
(DIR / "wrapup_run.txt").write_text(wrap_line + "\n")
print(wrap_line)
print("wrote now/verify/json")
