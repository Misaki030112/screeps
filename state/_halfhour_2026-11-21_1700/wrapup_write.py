#!/usr/bin/env python3
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-21_1700"
HK = ZoneInfo("Asia/Hong_Kong")
WIN_TMIN, WIN_TMAX = 84396701, 84397400
JUST_BASE = 84397400
inserted_first = 10638
inserted_confirm = 0
inserted_retry2 = 0

now_s = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
first_pass_txt = (DIR / "history_backfill_first_attempt.txt").read_text().rstrip() + "\n"
cov = json.loads((DIR / "coverage_final.json").read_text())
jp = json.loads((DIR / f"just_published_{JUST_BASE}.json").read_text())
post = json.loads((DIR / "just_published_post_summary.json").read_text())
tickj = json.loads((DIR / "tick_s_realign.json").read_text())
late1 = json.loads((DIR / "backfill_late_retry_w45n7_1.json").read_text())
late2 = json.loads((DIR / "backfill_late_retry_w45n7_2.json").read_text())

cov_rec = cov["official_recovered"]
cov_exp = cov["expected"]
empty_n = cov["empty_no_creep"]
off404 = cov["official_404_missing"]
script_by = post["script_by_room"]
actual_by = post["actual_by_room"]
script_sum = post["script_sum"]
actual_sum = post["actual_sum"]
jp_all_five = (not jp.get("still_404")) and all((g.get("code") == 200) for g in (jp.get("gets") or []))
jp_still = jp.get("still_404") or []
inserted_total = inserted_first + inserted_confirm + inserted_retry2 + actual_sum
tick_s_in_use = float(tickj["tick_s_in_use"])
tick_s_in_use_name = tickj.get("tick_s_in_use_name")
tick_s_first = float(tickj["tick_s_used_first_pass"])
corrective = bool(tickj.get("corrective_applied"))
tips = post["tips"]
win = post["first_pass_window"]
rot = json.loads((ROOT / "metrics" / "listener_rot.json").read_text())
rot_s = json.dumps(rot, ensure_ascii=False)
yield_absent = not (ROOT / "metrics" / "listener_yield_rooms").exists()
listener_pid = 1974391
listener_started = "17:04:54"
listener_parent = 4035476
slot = json.loads((ROOT / "metrics" / "live.json").read_text()).get("roomSlot")
restarted_this_run = False
hole956 = post["holes"].get("W47N7@84395600") or {}
hole951 = post["holes"].get("W47N8@84395100") or {}
hole943 = post["holes"].get("W46N8@84394300") or {}
# just-published leftover; not in the aged-out holes list from post_counts
with __import__("tools.db" if False else "db").connect() as c:
    d, mn, mx, n = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        ("W45N7", 84397401, 84397500),
    ).fetchone()
hole974 = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}
confirm_at = "2026-11-21 17:08:55 Asia/Hong_Kong"
retry2_at = "2026-11-21 17:08:55 Asia/Hong_Kong"
late1_at = late1.get("at")
late1_gt = late1.get("game_time")
late2_at = late2.get("at")
late2_gt = late2.get("game_time")
jp_at = jp.get("at")
jp_gt = jp.get("game_time")

wrap_body = (
    f"confirm at {confirm_at} skipped no targets inserted=0 recovered=[] skipped=True; "
    f"retry2 at {retry2_at} skipped no targets inserted=0 recovered=[] skipped=True. "
    f"First pass 35/35 official GETs 200, missing_chunks=0. Confirm 17:08:55 and retry2 17:08:55 skipped (no in-window 404s). "
    f"Already-told leftover official 404s W47N7@84395600 / W47N8@84395100 / W46N8@84394300 / W45N8@84392600 / W46N8@84390800 / "
    f"W47N7@84390900 / W46N8@84390400 / W45N7@84388500 / W45N8@84386600 aged out of window start 84396701 and were not retried. "
    f"Just-published 84397400 at {jp_at} gt={jp_gt} all_five_200={jp_all_five} script={script_sum} actual={actual_sum}; "
    f"W46N8 script {script_by.get('W46N8')} vs actual {actual_by.get('W46N8')}, "
    f"W47N8 script {script_by.get('W47N8')} vs actual {actual_by.get('W47N8')}, "
    f"W45N8 script {script_by.get('W45N8')} vs actual {actual_by.get('W45N8')}, "
    f"W45N7 script {script_by.get('W45N7')} vs actual {actual_by.get('W45N7')}, "
    f"W47N7 script {script_by.get('W47N7')} vs actual {actual_by.get('W47N7')}. "
    f"W45N7@84397400 first-pass just-published still 404 at 17:12:44 gt={jp_gt}; "
    f"late_retry at {late1_at} gt={late1_gt} still 404 inserted=0; "
    f"retry2 at {late2_at} gt={late2_gt} still 404 inserted=0. "
    f"Coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404} "
    f"(no in-window official 404 on first-pass 84396701..84397400; leftover official 404 W45N7@84397400 is the just-published chunk, listener 0/100, hole 100 ticks 84397401..84397500). "
    f"NEW box freeze 16:48:46-17:04:41 (954s; STATS 84397201..84397439, 239t) official-filled four rooms 239/239, "
    f"W45N7 200/239 missing tail 84397401..84397439 because of leftover official 404 W45N7@84397400; "
    f"listener auto-restart 17:04:44, python 1974391 started 17:04:54 (before this run's first pass; this run did not restart it). "
    f"Already-told by the delivered 16:32 1h patrol and still in this window: "
    f"box freeze 16:16:43-16:19:24 (161s; STATS 84396751..84396799, 49t) official-filled all five 49/49; "
    f"short WS ping/pong 16:22:02 (STATS 84396821..84396839, 19t) official-filled all five 19/19. "
    f"The delivered 16:32 1h patrol had already official-filled 84396101..84396800 plus late retry just-published 84396800 at 16:31:38 gt=84396964; "
    f"the 16:30 backfill already official-filled 84396301..84397000 plus just-published 84397000. "
    f"inserted_first={inserted_first} confirm=0 retry2=0 just_actual={actual_sum} total={inserted_total}. "
    f"tick_s_printed=4.239 first={tick_s_first:.5f} in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=0 corrective={int(corrective)}. "
    f"First-pass overlap compared=16178 match=15314 differ=864 (samples are several W47N8 creeps at chunk 84396801; existing listener/patrol rows kept, official not overwritten). "
    f"Listener pid={listener_pid} started={listener_started} parent={listener_parent} slot={slot} rot={rot_s} yield=absent restarted_this_run=false. "
    f"Peacetime single-slot 5:5:1:1. This run did not restart the listener or war_cmd/pulse. "
    f"No concurrent 1h patrol during this run (last delivered 16:32 finished 16:33:39); this run did not write a patrol folder."
)

told_para = (
    "NEW not-yet-told for the next 1h patrol: "
    "box freeze 16:48:46-17:04:41 (954s; STATS 84397201..84397439, 239t; official-filled four rooms 239/239, "
    "W45N7 200/239 missing tail 84397401..84397439 because of leftover official 404 W45N7@84397400; "
    "listener auto-restart 17:04:44, python 1974391 started 17:04:54); "
    "leftover official 404 W45N7@84397400 (first recorded this 17:00 backfill; just-published 17:12:44 gt=84397541, "
    "late_retry 17:15:01 gt=84397576 and retry2 17:17:16 gt=84397607 still 404; listener 0/100, hole 100 ticks 84397401..84397500). "
    "Already told by the delivered 16:32 亚洲/香港 1h patrol and still in official window start 84396701: "
    "box freeze 16:16:43-16:19:24 (161s; STATS 84396751..84396799, 49t; official-filled all five 49/49; listener auto-restart 16:19:27), "
    "short WS ping/pong 16:22:02 (not a box freeze; STATS 84396821..84396839, 19t; official-filled all five 19/19; listener restart 16:22:05). "
    "Already told by the 16:32/15:28 patrols and now age out of window start 84396701: "
    "box freeze 15:47:29-15:58:30 (655s; STATS 84396331..84396509, 179t; official-filled four rooms 179/179, W45N7 173/179 evac empty tail 84396331..84396336 official 200 not a 404), "
    "box freeze 15:14:38-15:19:30 (292s; STATS 84395871..84395959, 89t; official-filled W46N8/W47N8/W45N8/W47N7 89/89, W45N7 59/89 evac empty tail 84395930..84395959 official 200 not a 404), "
    "leftover official 404 W47N7@84395600 (listener 0/100, hole 100 ticks 84395601..84395700; last retried 15:41:14 gt=84396251 still 404, not retried this run), "
    "leftover official 404 W47N8@84395100 (listener 0/100, hole 100 ticks 84395101..84395200), "
    "leftover official 404 W46N8@84394300 (listener 79/100 84394301..84394379, hole 21 ticks 84394380..84394400), "
    "box freeze 14:40:53-14:56:54 (952s; STATS 84395401..84395639, 239t; official-filled four rooms 239/239, W47N7 200/239 missing 84395601..84395639 because of leftover official 404 W47N7@84395600), "
    "box freeze 14:15:50-14:23:29 (450s; STATS 84395061..84395179, 119t; official-filled four rooms 119/119, W47N8 40/119 missing 84395101..84395179 because of leftover official 404 W47N8@84395100), "
    "box freeze 13:49:01-13:56:56 (475s; STATS 84394681..84394809, 129t; official-filled all five 129/129), "
    "box freeze 13:09:46-13:21:14, earlier already-told freezes 12:48:14-12:57:17 / 12:30:42-12:35:35 / 11:49:12-11:57:31 / 11:19:06-11:20:43, "
    "short WS gaps 12:10 / 12:18 / 11:12, and older leftover official 404s W45N8@84392600 / W46N8@84390800 / W47N7@84390900 / W46N8@84390400 / W45N7@84388500 / W45N8@84386600. "
    "Fold only newer freezes, short WS gaps, or leftover official 404s than the 16:32-told set plus this run's NEW 16:48:46-17:04:41 freeze and W45N7@84397400 once those are told; "
    "do not re-tell 16:16:43-16:19:24, the 16:22:02 short WS, 15:47:29-15:58:30, W47N7@84395600, or earlier already-told items."
)

now_txt = first_pass_txt + f"---- wrap {now_s} ----\n" + wrap_body + "\n" + told_para + "\n"
(DIR / "history_backfill_now.txt").write_text(now_txt)
(DIR / "_halfhour_backfill_now.txt").write_text(now_txt)
(ROOT / "state" / "_halfhour_backfill_now.txt").write_text(now_txt)

def hole_line(name, h, extra):
    return (
        f"{name} hole distinct={h.get('distinct')} rows={h.get('rows')} "
        f"range={h.get('min')}..{h.get('max')} ({extra})"
    )

verify = (
    f"wrap {now_s}\n"
    f"window {WIN_TMIN}..{WIN_TMAX} first_pass 35/35 missing_chunks=0\n"
    f"db_window {json.dumps(win, ensure_ascii=False)}\n"
    + hole_line("W45N7@84397400 NEW leftover just-published", hole974, "listener 0/100, late_retry+retry2 still 404") + "\n"
    + hole_line("W47N7@84395600 aged-out", hole956, "listener 0/100, not retried this run") + "\n"
    + hole_line("W47N8@84395100 aged-out", hole951, "listener 0/100, not retried this run") + "\n"
    + hole_line("W46N8@84394300 aged-out", hole943, "listener 79/100, not retried this run") + "\n"
    + f"just_published {JUST_BASE} all_five_200={jp_all_five} script={script_sum} actual={actual_sum} by_actual={actual_by} by_script={script_by} still_404={jp_still}\n"
    + f"coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}\n"
    + f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} just_actual={actual_sum} total={inserted_total}\n"
    + f"tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} ts_realigned_first=0 corrective={int(corrective)}\n"
    + f"new_freeze=16:48:46-17:04:41 four_rooms=239/239 W45N7=200/239 missing_tail=84397401..84397439 due_to_W45N7@84397400; already_told_in_window 16:16:43-16:19:24 all_five=49/49; 16:22:02 all_five=19/19\n"
    + f"overlap_differ=864 kept_existing_listener_rows\n"
    + f"tips {tips}\n"
    + f"listener pid={listener_pid} started={listener_started} parent={listener_parent} slot={slot} rot={rot_s} yield_absent={yield_absent} restarted_this_run={restarted_this_run}\n"
    + f"ok_quiet=True new_official_404_untold=['W45N7@84397400'] new_box_freeze_untold=['16:48:46-17:04:41']\n"
    + f"{told_para}\n"
)
(DIR / "verify.txt").write_text(verify)
(DIR / "_halfhour_backfill_verify.txt").write_text(verify)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify)

payload = {
    "ok_quiet": True,
    "at": now_s,
    "window": [WIN_TMIN, WIN_TMAX],
    "published_bases": [84396700, 84397300],
    "game_time_first": 84397460,
    "first_pass": {
        "gets_200": 35,
        "gets_total": 35,
        "missing_chunks": [],
        "reconstructed": [WIN_TMIN, WIN_TMAX],
        "creep_rows": 27619,
        "already_in_db": 16981,
        "inserted": inserted_first,
        "ts_realigned": 0,
        "tick_s_printed": 4.239,
        "overlap_compared": 16178,
        "overlap_match": 15314,
        "overlap_differ": 864,
        "overlap_differ_samples": [
            "W47N8 w8miner84395357@84396801 energy db=36 hist=24",
            "W47N8 several haulers/upgraders at chunk 84396801 position/energy off-by-one",
        ],
    },
    "confirm": {"at": confirm_at, "skipped": True, "still_404": [], "inserted": 0, "recovered": [], "reason": "no targets"},
    "retry2": {"at": retry2_at, "skipped": True, "still_404": [], "inserted": 0, "recovered": [], "reason": "no targets"},
    "late_retry": {
        "target": "W45N7@84397400",
        "attempts": [
            {"at": late1_at, "game_time": late1_gt, "status": late1.get("status") or late1.get("code"), "inserted": late1.get("inserted", 0)},
            {"at": late2_at, "game_time": late2_gt, "status": late2.get("status") or late2.get("code"), "inserted": late2.get("inserted", 0)},
        ],
        "still_404": True,
        "inserted": 0,
    },
    "just_published": {
        "base": JUST_BASE,
        "at": jp_at,
        "game_time": jp_gt,
        "all_five_200": jp_all_five,
        "script_sum": script_sum,
        "actual_sum": actual_sum,
        "script_by_room": script_by,
        "actual_by_room": actual_by,
        "still_404": jp_still,
    },
    "coverage": {
        "official_recovered": cov_rec,
        "expected": cov_exp,
        "empty_no_creep": empty_n,
        "official_404_missing": off404,
    },
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
    "already_told_by_1632_patrol": {
        "box_freezes_in_window": ["16:16:43-16:19:24"],
        "short_ws_in_window": ["16:22:02"],
        "box_freezes_aged_out": ["15:47:29-15:58:30", "15:14:38-15:19:30", "14:40:53-14:56:54", "14:15:50-14:23:29", "13:49:01-13:56:56"],
        "official_404s_aged_out": ["W47N7@84395600", "W47N8@84395100", "W46N8@84394300", "W45N8@84392600"],
    },
    "new_untold_box_freezes": ["16:48:46-17:04:41"],
    "new_untold_official_404s": ["W45N7@84397400"],
    "concurrent_patrol": "none; last 16:32 patrol finished 16:33:39; this run did not write a patrol folder",
    "did_not_write_patrol_folder": True,
}
(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
# also refresh the shared state pointer used by later patrols
(ROOT / "state" / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
wrap_line = (
    f"wrap {now_s} ok_quiet=True inserted_total={inserted_total} "
    f"new_box_freeze=['16:48:46-17:04:41'] new_official_404=['W45N7@84397400'] "
    f"already_told_in_window=['16:16:43-16:19:24','16:22:02']"
)
(DIR / "wrapup_run.txt").write_text(wrap_line + "\n")
print(wrap_line)
print("wrote now/verify/json")
