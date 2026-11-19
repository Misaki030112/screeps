"""Write local status records for the 05:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-19_0500"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84346501, 84347200
PUB_BASES = "84346500..84347100"
GT_FIRST = 84347215
TICK_S_FIRST = 4.69553
TICK_S_PRINTED = "4.696"
TICK_S_IN_USE = 4.794848
TICK_S_LATER = 4.794848
TS_REALIGNED_FIRST = 5273
NFIX_CORR = 5237
GT_CORR = 84347233
RECON_ROWS = 26691
ALREADY = 16737
INSERTED_FIRST = 9954
INSERTED_CONFIRM = 0  # confirm 05:03:09 gt=84347242 still official 404 both in-window chunks
INSERTED_RETRY2 = 0  # retry2 05:04:52 gt=84347264 still official 404 both
INSERTED_JUST = 2350  # first try 05:11:03 game.time=84347341 recovered 5/5 just-base; leftovers still 404
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/2363new W47N8:700t/4378new W45N8:600t/974new W45N7:600t/1021new W47N7:700t/1218new"
FIRST_PASS_LINE = (
    "first pass 33 of 35 official GETs 200, missing_chunks=2 W45N7@84347000,W45N8@84347100; "
    "04:30 half-hour already wrote through 84346700 and just-published 84346800 (84346801..84346900) for all 5 rooms; "
    "(this pass already_in_db=16737 / inserted=9954); "
    "leftover official 404 W45N8@84346100, W46N8@84346200, W47N8@84346200 already aged out of this 40-min window; "
    "W45N7@84347000, W45N8@84347100 still official 404 after confirm/retry2/just-published retry"
)
MISSING_CHUNKS = 2

coverage_payload = json.loads((DIR / "coverage_final.json").read_text())
coverage = coverage_payload["coverage"]
recovered = coverage_payload["official_recovered"]
expected = coverage_payload["expected"]
empty_no_creep = coverage_payload["empty_no_creep"]
official_404_missing = coverage_payload["official_404_missing"]
unique_after = coverage_payload["unique_after"]
tick_s = json.loads((DIR / "tick_s_realign.json").read_text())
vs_later_after = tick_s.get("vs_later_after") or {}
live = json.loads((ROOT / "metrics" / "live.json").read_text())
rot = json.loads((ROOT / "metrics" / "listener_rot.json").read_text())
yield_present = (ROOT / "metrics" / "listener_yield_rooms").exists()

finished = datetime.now(HK)
finished_hkt = finished.strftime("%Y-%m-%d %H:%M Asia/Hong_Kong")
finished_hkt_sec = finished.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

db_lines = []
with db.connect() as c:
    for room in sorted(ROOMS):
        mn, mx, n, d = c.execute(
            "SELECT min(tick), max(tick), count(*), count(DISTINCT tick) "
            "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, TMIN, TMAX),
        ).fetchone()
        db_lines.append(f"  {room} ticks={mn}..{mx} rows={n} distinct={d}")
db_after_lines = "\n".join(db_lines)

def empty_ranges(room):
    return (coverage.get(room) or {}).get("official_empty_no_creep_ranges") or []

w45n8_empty = empty_ranges("W45N8")
w45n7_empty = empty_ranges("W45N7")
w47n7_empty = empty_ranges("W47N7")

inwin_txt = (
    "in-window official 404: W45N7@84347000 hole 84347001..84347100; "
    "W45N8@84347100 hole 84347101..84347200; "
    "first pass 33 of 35 official GETs 200, missing_chunks=2; "
    "confirm 05:03:09 game.time=84347242 still 404 both; retry2 05:04:52 game.time=84347264 still 404 both; "
    "just-published 84347200 first try 05:11:03 game.time=84347341 recovered 5/5, leftover two still official 404 "
    "(neighbors: W45N7@84346900/@84347100 both 200, db 0/0; "
    "W45N8@84347000/@84347200 both 200, db 0/0); "
    "final official_404_in_window=200"
)
leftover_txt = (
    "in-window official 404 still open: "
    "W45N7@84347000 (84347001..84347100), W45N8@84347100 (84347101..84347200) after confirm/retry2/just_published; "
    "aged leftover official 404 W45N8@84346100, W46N8@84346200, W47N8@84346200 were not retried this pass "
    "(already outside this 40-min window, along with older W45N7@84345800, W45N8@84344700, W47N8@84343800, W45N8@84343100, W47N8@84343400, W47N8@84343000, W45N7@84342300, W47N7@84342500, W45N8@84341100)."
)
confirm_summary = (
    "confirm 05:03:09 game.time=84347242 still official 404 W45N7@84347000,W45N8@84347100 inserted=0; "
    "retry2 05:04:52 game.time=84347264 still 404 both inserted=0; "
    "just-published 84347200 first try at 05:11:03 game.time=84347341 recovered 5/5 rooms inserted=2350 "
    "(after this window; W46N8/W47N8/W45N8/W45N7/W47N7 distinct=100, already_in_db=1197); "
    "leftover retry of the two in-window official 404s still official 404; "
    "in-window official 404 still open: W45N7@84347000, W45N8@84347100"
)
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} was over the 45s gate versus first-aligned rows "
    f"(delta first-robust -0.09932 s/tick, ~70.9s at tmin; "
    f"over45 later=5253 vs first=0, over15 later=16416 vs first=10833; "
    f"span_mean 4.77829 over45=5195 and prev_later 4.82867 over45=5755; lowest_over45 among sane was first); "
    f"applied corrective later-mean-robust realign of {NFIX_CORR} rows at game.time={GT_CORR}; "
    f"still_over_45s_vs_later=0; skipped_cross_chunk=0; "
    f"in-use later-mean-robust {TICK_S_IN_USE:.5f}; "
    f"subsequent just-published inserts used later-mean-robust {TICK_S_IN_USE:.5f} (ts_realigned=0)"
)
freeze_para = (
    "New box freeze this run 04:45:45-04:58:24 (749s); also earlier 03:45:22-04:05:50 (1228s), 03:10:01-03:17:13 (431s), 02:45:55-02:57:12 (671s), 02:16:19-02:17:47 (79s), 01:48:36-01:58:05 (564s) and 01:31:02-01:35:45 (283s). "
    "Listener last auto-restart 04:58:27 after that wake (run_listener.sh auto-restart, not this run; listener.py pid 733852 started 04:58:36; run_listener.sh pid 4035476). "
    "This run did not restart the listener; it was already up after that auto-restart and pulling segment-90 CPU/path buffers itself "
    "(pre-check 05:00:05 live.json age ~3.6s, stats.t=84347200, roomSlot W47N8 mid-rotation objects_n=0 / gameTime None just after reconnect; "
    "creep_cpu through 84347190 / path_arrivals through 84347182; "
    "by retry2 05:04:52 live.json gameTime still None / objects_n=0 but W47N8 creep_ticks were live through 84347267, stats.t=84347260, creep_cpu through 84347260 / path_arrivals through 84347258; "
    "by wrapup 05:11:50 gameTime had caught up at 84347350, roomSlot W46N8, objects_n=262). "
    "room_stats gap 84347021..84347189 (169) official-filled 169/169 in W46N8/W47N8/W47N7; "
    "W45N8 80/169 missing 89 because official 404 W45N8@84347100 covers 84347101..84347189 (84347021..84347100 official-filled); "
    "W45N7 89/169 missing 80 because official 404 W45N7@84347000 covers 84347021..84347100 (84347101..84347189 official-filled). "
    "This run did not restart the listener. "
    "Earlier room_stats gap 84346261..84346529 (269) remains official-filled 269/269 in W45N8/W45N7/W47N7; "
    "W46N8 229/269 missing 40 because official 404 W46N8@84346200 covers 84346261..84346300 (84346301..84346529 official-filled; this hole now aged out of this 40-min window); "
    "W47N8 231/269 missing 38 because official 404 W47N8@84346200 covers 84346263..84346300 (listener already had 84346261..84346262; 84346301..84346529 official-filled; this hole now aged out of this 40-min window). "
    "Earlier room_stats gap 84345811..84345919 (109) remains official-filled 109/109 in W46N8/W47N8/W45N8/W47N7; "
    "W45N7 19/109 missing 90 because official 404 W45N7@84345800 covers 84345811..84345900 (84345901..84345919 official-filled; this gap now aged out of this 40-min window). "
    "Aged official 404 W45N8@84346100, W46N8@84346200, W47N8@84346200 (and older W45N7@84345800, W45N8@84344700, W47N8@84343800, W45N8@84343100, W47N8@84343400, W47N8@84343000, W45N7@84342300, W47N7@84342500, W45N8@84341100) remain outside this window. "
    "live.json / stats.t were fresh at pre-check (age ~3.6s, tip stats.t=84347200); "
    "used stats.t to know 84347200 was publishable (waited until live stats.t>=84347340); single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84347190 / path_arrivals through 84347182 at pre-check); "
    "this run did not restart the listener."
)

ok_line = (
    f"ok_quiet=True coverage={recovered}/{expected} inserted_window={INSERTED_WINDOW} "
    f"inserted_total={INSERTED_TOTAL} tick_s_in_use={TICK_S_IN_USE:.5f} "
    "listener single_slot=True; no second listener; no war_cmd/pulse restart."
)
single = (not yield_present)
now_lines = [
    f"{finished_hkt} half-hour backfill OK (quiet)",
    f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
    f"  ({FIRST_PASS_LINE}; see history_backfill.txt)",
    f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST:.5f}; {tick_s_corr_txt}, in-use {TICK_S_IN_USE:.5f})",
    f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks={MISSING_CHUNKS}",
    f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
    f"per_room {PER_ROOM_LINE}",
    f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 +{INSERTED_RETRY2}, just_published +{INSERTED_JUST}, window {INSERTED_WINDOW}, run total {INSERTED_TOTAL})",
    f"ts_realigned_first={TS_REALIGNED_FIRST}; ts_realigned_corrective={NFIX_CORR} ({tick_s_corr_txt}; in-use {TICK_S_IN_USE:.5f})",
    "db_after",
    db_after_lines,
    f"coverage official_recovered={recovered}/{expected} unique_after={unique_after.get('unique_creep_tick_rows') or unique_after} empty_no_creep={empty_no_creep} official_404_in_window={official_404_missing}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    freeze_para,
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}",
    confirm_summary,
    ok_line,
]
now_text = "\n".join(now_lines) + "\n"

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
        "corrective_applied": tick_s.get("corrective_applied"),
        "later_mean_w46": tick_s.get("later_mean_w46"),
        "still_over_45s_vs_later": tick_s.get("still_over_45s_vs_later"),
        "reason": tick_s.get("reason"),
        "prev_later_over45_before_corrective": 5755,
        "prev_later_mean": 4.8286725,
        "note": "first-interval 4.69553 printed 4.696 was sane and already over45=0 vs first (lowest_over45=first); later-mean-robust 4.794848 was over the 45s gate versus first-aligned rows (over45=5253, delta -0.09932 s/tick ~70.9s at tmin); span_mean 4.77829 over45=5195 and prev_later 4.82867 over45=5755; applied corrective later-mean-robust realign of 5237 rows at game.time=84347233; still_over_45s_vs_later=0; in-use later-mean-robust 4.794848",
    },
    "just_published": {
        "base": 84347200,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "05:11:03",
        "recovered_game_time": 84347341,
        "inserted": INSERTED_JUST,
        "inserted_first_two": None,
        "inserted_remaining_three": None,
        "first_try_all_404": False,
        "first_try_at": "05:11:03",
        "first_try_game_time": 84347341,
        "first_try_recovered": ["W46N8", "W47N8", "W45N8", "W45N7", "W47N7"],
        "first_try_still_404": ["W45N7@84347000", "W45N8@84347100"],
        "retry_at": None,
        "retry_game_time": None,
        "retry_inserted": 0,
        "already_in_db": 1197,
        "ticks": "84347201..84347300",
        "all_five_official_200": True,
        "still_404": ["W45N7@84347000", "W45N8@84347100"],
        "in_window_still_404": ["W45N7@84347000", "W45N8@84347100"],
        "w45n7_empty_no_creep": [],
        "w47n7_empty_no_creep": [],
        "distinct": {"W46N8": 100, "W47N8": 100, "W45N8": 100, "W45N7": 100, "W47N7": 100},
    },
    "confirm": {
        "at": "05:03:09",
        "game_time": 84347242,
        "inserted": 0,
        "ssl_abort_first": None,
        "targets": 2,
        "recovered": [],
        "still_404": ["W45N7@84347000", "W45N8@84347100"],
        "note": "confirm still official 404 both at 05:03:09 game.time=84347242; neighbors all 200 (W45N7@84346900/@84347100, W45N8@84347000 and later just-published @84347200 also 200); db holes W45N7 0/0 84347001..84347100, W45N8 0/0 84347101..84347200",
    },
    "retry2": {"at": "05:04:52", "game_time": 84347264, "inserted": 0, "skipped": False, "still_404": ["W45N7@84347000", "W45N8@84347100"]},
    "in_window_404": {
        "W45N7@84347000": "84347001..84347100 still official 404 after confirm/retry2/just_published",
        "W45N8@84347100": "84347101..84347200 still official 404 after confirm/retry2/just_published",
    },
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 733852,
        "loop_pid": 4035476,
        "restart_at": "04:58:27",
        "listener_started": "04:58:36",
        "this_run_restarted": False,
        "waited_for_reconnect": True,
        "pre_cpu_path_after_wait": "creep_cpu through 84347190 / path_arrivals through 84347182 at pre-check 05:00:05; listener.py pid 733852 started 04:58:36 after run_listener.sh auto-restart 04:58:27",
    },
    "box_freeze": {
        "from": "2026-11-19 04:45:45",
        "to": "2026-11-19 04:58:24",
        "sec": 749,
        "restart_at": "04:58:27",
        "room_stats_gap": "84347021..84347189",
        "official_filled": "W46N8/W47N8/W47N7 169/169; W45N8 80/169 missing 89 due to official 404 W45N8@84347100 covering 84347101..84347189; W45N7 89/169 missing 80 due to official 404 W45N7@84347000 covering 84347021..84347100",
        "earlier_freeze": {
            "from": "2026-11-19 03:45:22",
            "to": "2026-11-19 04:05:50",
            "sec": 1228,
            "restart_at": "04:05:53",
            "room_stats_gap": "84346261..84346529",
            "official_filled": "W45N8/W45N7/W47N7 269/269; W46N8 229/269 missing 40 due to official 404 W46N8@84346200 covering 84346261..84346300 (aged out of this window); W47N8 231/269 missing 38 due to official 404 W47N8@84346200 covering 84346263..84346300 (aged out of this window)",
        },
        "earlier_freeze_2": {
            "from": "2026-11-19 03:10:01",
            "to": "2026-11-19 03:17:13",
            "sec": 431,
            "restart_at": "03:17:16",
            "room_stats_gap": "84345811..84345919",
            "official_filled": "W46N8/W47N8/W45N8/W47N7 109/109; W45N7 19/109 missing 90 due to official 404 W45N7@84345800 covering 84345811..84345900 (aged out of this window)",
        },
        "prior_in_window_gap": "84347021..84347189 official-filled 169/169 in W46N8/W47N8/W47N7, W45N8 80/169 missing 89 due to official 404 W45N8@84347100, W45N7 89/169 missing 80 due to official 404 W45N7@84347000; 84346261..84346529 official-filled 269/269 in W45N8/W45N7/W47N7, W46N8 229/269 missing 40 due to official 404 W46N8@84346200 (aged out), W47N8 231/269 missing 38 due to official 404 W47N8@84346200 (aged out); 84345811..84345919 official-filled 109/109 in W46N8/W47N8/W45N8/W47N7, W45N7 19/109 missing 90 due to official 404 W45N7@84345800 (aged out)",
        "new_freeze_this_run": True,
    },
    "ok_line": ok_line,
}

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
(DIR / "history_backfill_now.txt").write_text(now_text)
shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")
shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

verify = [
    f"{finished_hkt_sec} half-hour backfill verify",
    f"window {TMIN}..{TMAX} published_bases {PUB_BASES} game.time={GT_FIRST} inserted={INSERTED_TOTAL} coverage={recovered}/{expected}",
    f"missing_chunks={MISSING_CHUNKS} in_window_404=W45N7@84347000,W45N8@84347100; final official_404={official_404_missing} empty_no_creep={empty_no_creep}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    "just-published 84347200 first try 05:11:03 game.time=84347341 recovered 5/5 inserted=2350 (W46N8/W47N8/W45N8/W45N7/W47N7 distinct=100/100); leftover W45N7@84347000,W45N8@84347100 still official 404 after confirm/retry2/just_published.",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not restart the listener.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0500.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run_tee.txt").write_text(summary + now_text)
(DIR / "wrapup_run_stdout.txt").write_text(summary + f"now_text_bytes {len(now_text)}\n")
print(summary, end="")
print("now_text_bytes", len(now_text))
