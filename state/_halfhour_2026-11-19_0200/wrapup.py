#!/usr/bin/env python3
"""Write local status records for the 02:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-19_0200"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84344201, 84344900
PUB_BASES = "84344200..84344800"
GT_FIRST = 84344934
TICK_S_FIRST = 4.76286
TICK_S_PRINTED = "4.763"
TICK_S_IN_USE = 4.76498
TICK_S_LATER = 4.76498
TS_REALIGNED_FIRST = 39
NFIX_CORR = 653
GT_CORR = 84344955  # corrective later-mean-robust realign nfix=653
RECON_ROWS = 27604
ALREADY = 20614
INSERTED_FIRST = 6990
INSERTED_CONFIRM = 0  # confirm 02:01:40 gt=84344957 still official 404 W45N8@84344700
INSERTED_RETRY2 = 0  # retry2 02:02:17 gt=84344965 still official 404 W45N8@84344700
INSERTED_JUST = 2677  # first try 02:08:26 game.time=84345042 recovered 5/5 just-base; leftover W45N8@84344700 still 404
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/1369new W47N8:700t/3836new W45N8:600t/673new W45N7:700t/453new W47N7:700t/659new"
FIRST_PASS_LINE = (
    "first pass 34 of 35 official GETs 200, missing_chunks=1 W45N8@84344700; "
    "hourly_patrol_prefilled=true from 00:19 patrol official already through 84343500 "
    "/ reconstructed through 84343600 and just-published 84343600 (84343601..84343700) for all 5 rooms; "
    "01:00 half-hour already wrote through 84344200 and just-published 84344200 (84344201..84344300); "
    "01:17 hourly patrol analyzed live tip ~84344450 but did not write a new official-history fill; "
    "01:30 half-hour already wrote through 84344600 and just-published 84344600 (84344601..84344700) for all 5 rooms "
    "(overlap of this window; this pass already_in_db=20614 / inserted=6990); "
    "W47N8@84343800 already aged out of this 40-min window"
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
    "in-window official 404: W45N8@84344700 hole 84344701..84344800; "
    "first pass 34 of 35 official GETs 200, missing_chunks=1; "
    "confirm 02:01:40 game.time=84344957 still 404; retry2 02:02:17 game.time=84344965 still 404; "
    "just-published 84344900 first try 02:08:26 game.time=84345042 recovered 5/5, leftover W45N8@84344700 still official 404 (neighbors @84344600/@84344800 both 200, db 0/0); "
    "final official_404_in_window=100"
)
leftover_txt = (
    "in-window official 404 still open: W45N8@84344700 (84344701..84344800) after confirm/retry2/just_published; "
    "aged leftover official 404 W47N8@84343800 was not retried this pass "
    "(already outside this 40-min window, along with older W45N8@84343100, W47N8@84343400, W47N8@84343000, W45N7@84342300, W47N7@84342500, W45N8@84341100)."
)
confirm_summary = (
    "confirm 02:01:40 game.time=84344957 still official 404 W45N8@84344700 inserted=0; "
    "retry2 02:02:17 game.time=84344965 still 404 inserted=0; "
    "just-published 84344900 first try at 02:08:26 game.time=84345042 recovered 5/5 rooms inserted=2677 "
    "(after this window; W46N8/W47N8/W45N8/W45N7 distinct=100, W47N7 distinct=40 from 84344917 official empty-no-creep 84344901..84344916, already_in_db=1220); "
    "leftover retry W45N8@84344700 still official 404; in-window official 404 still open: W45N8@84344700"
)
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} was over the 45s gate before corrective "
    f"(delta first-robust -0.00212 s/tick, ~1.6s at tmin, over45 later=1637 vs first=1109, over15 later=10187 vs first=9545; first was lowest-over45 among sane before corrective); "
    f"applied corrective later-mean-robust realign of {NFIX_CORR} rows at game.time={GT_CORR}; "
    f"after over45 later=0, over15 later=7241; in-use later-mean-robust {TICK_S_IN_USE:.5f}; "
    f"subsequent just-published inserts used later-mean-robust {TICK_S_IN_USE:.5f} (ts_realigned=0)"
)
freeze_para = (
    "Listener restart 01:58:08 (box wake after freeze 01:48:36-01:58:05 (564s); also earlier restart 01:35:48 after freeze 01:31:02-01:35:45 (283s); "
    "run_listener.sh auto-restart, not this run; pid 662251). "
    "New room_stats gap 84344781..84344919 (139); official-filled 139/139 in W46N8/W47N8/W45N7; "
    "W45N8 119/139 missing 20 because official 404 W45N8@84344700 covers 84344781..84344800 (the rest 84344801..84344919 filled via this window + just-published 84344900); "
    "W47N7 26/139 because official empty-no-creep covers 84344804..84344842, 84344844..84344878, 84344880..84344900 in-window and continues 84344901..84344916 after the window (just-published W47N7 starts 84344917). "
    "This run did not restart the listener. "
    "Earlier room_stats gap 84344561..84344639 (79, from the 01:31-01:35 freeze) remains official-filled 79/79 all five. "
    "Earlier room_stats gap 84344021..84344229 (209, from the 00:47-01:02 freeze) remains official-filled 209/209 in W46N8/W47N8/W45N8/W47N7; "
    "W45N7 0/209 because official empty-no-creep continues 84343972..84344239 (covers this gap; this window still has W45N7 empty 84344201..84344239). "
    "Earlier room_stats gap 84343821..84343859 (39, from the 00:31-00:34 freeze) is official-filled 39/39 in W46N8/W45N8/W45N7/W47N7; "
    "W47N8 0/39 missing all 39 because W47N8@84343800 stayed official 404 (still outside this window). "
    "Earlier room_stats gap 84343611..84343669 (59) remains official-filled 59/59 all five. "
    "Aged official 404 W47N8@84343800 (and older W45N8@84343100, W47N8@84343400, W47N8@84343000, W45N7@84342300, W47N7@84342500, W45N8@84341100) remain outside this window. "
    "live.json / stats.t were fresh at pre-check (age ~1.6s, tip 84344920, roomSlot W46N8 with objects_n=264); "
    "used stats.t to know 84344900 was publishable; single_slot held, creep_cpu and path_arrivals flowing after reconnect (creep_cpu through 84344920 / path_arrivals through 84344900 at pre-check); "
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
        "prev_later_over45_before_corrective": 3631,
        "prev_later_mean": 4.79049,
        "note": "prev_later 4.79049 had over45=3631 before corrective (worst of the candidates); first was lowest-over45 among sane (1109 vs later 1637); established check still applied later-mean-robust because later was over the 45s gate; after over45 later=0 (and first also 0)",
    },
    "just_published": {
        "base": 84344900,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "02:08:26",
        "recovered_game_time": 84345042,
        "inserted": INSERTED_JUST,
        "inserted_first_two": None,
        "inserted_remaining_three": None,
        "first_try_all_404": False,
        "first_try_at": "02:08:26",
        "first_try_game_time": 84345042,
        "first_try_recovered": ["W46N8", "W47N8", "W45N8", "W45N7", "W47N7"],
        "first_try_still_404": ["W45N8@84344700"],
        "retry_at": None,
        "retry_game_time": None,
        "retry_inserted": 0,
        "already_in_db": 1220,
        "ticks": "84344901..84345000",
        "all_five_official_200": True,
        "still_404": ["W45N8@84344700"],
        "in_window_still_404": ["W45N8@84344700"],
        "w45n7_empty_no_creep": [],
        "w47n7_empty_no_creep": [[84344901, 84344916]],
        "distinct": {"W46N8": 100, "W47N8": 100, "W45N8": 100, "W45N7": 100, "W47N7": 40},
    },
    "confirm": {
        "at": "02:01:40",
        "game_time": 84344957,
        "inserted": 0,
        "ssl_abort_first": None,
        "targets": 1,
        "recovered": [],
        "still_404": ["W45N8@84344700"],
        "note": "confirm still official 404 W45N8@84344700 at 02:01:40 game.time=84344957; neighbors @84344600/@84344800 both 200; db 0/0",
    },
    "retry2": {"at": "02:02:17", "game_time": 84344965, "inserted": 0, "skipped": False, "still_404": ["W45N8@84344700"]},
    "in_window_404": {"W45N8@84344700": "84344701..84344800 still official 404 after confirm/retry2/just_published"},
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 662251,
        "restart_at": "01:58:08",
        "this_run_restarted": False,
    },
    "box_freeze": {
        "from": "2026-11-19 01:48:36",
        "to": "2026-11-19 01:58:05",
        "sec": 564,
        "earlier_freeze": {
            "from": "2026-11-19 01:31:02",
            "to": "2026-11-19 01:35:45",
            "sec": 283,
            "restart_at": "01:35:48",
            "room_stats_gap": "84344561..84344639",
            "official_filled": "all five 79/79",
        },
        "room_stats_gap": "84344781..84344919",
        "official_filled": "W46N8/W47N8/W45N7 139/139; W45N8 119/139 missing 20 due to official 404 W45N8@84344700 (84344781..84344800); W47N7 26/139 official empty-no-creep 84344804..84344916 with two isolated present ticks in-window plus 84344917..84344919",
        "prior_in_window_gap": "84344561..84344639 official-filled 79/79 all five; 84343821..84343859 official-filled 39/39 in W46N8/W45N8/W45N7/W47N7; W47N8 0/39 missing all 39 due to official 404 W47N8@84343800 (still aged out)",
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
    f"missing_chunks={MISSING_CHUNKS} in_window_404=W45N8@84344700; final official_404={official_404_missing} empty_no_creep={empty_no_creep}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    "just-published 84344900 first try 02:08:26 game.time=84345042 recovered 5/5 inserted=2677 (W46N8/W47N8/W45N8/W45N7 distinct=100/100, W47N7 40/100 official empty-no-creep 84344901..84344916); leftover W45N8@84344700 still official 404 after confirm/retry2/just_published (db 0/0).",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not restart the listener.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0200.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run_tee.txt").write_text(summary + now_text)
print(summary, end="")
print("now_text_bytes", len(now_text))
