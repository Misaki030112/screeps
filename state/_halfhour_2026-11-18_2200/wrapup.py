#!/usr/bin/env python3
"""Write local status records for the 22:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-18_2200"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84341101, 84341800
PUB_BASES = "84341100..84341700"
GT_FIRST = 84341872
TICK_S_FIRST = 4.68290
TICK_S_PRINTED = "4.683"
TICK_S_IN_USE = 4.67304
TICK_S_LATER = 4.67304
TS_REALIGNED_FIRST = 75
NFIX_CORR = 0
GT_CORR = None
RECON_ROWS = 23179
ALREADY = 17300
INSERTED_FIRST = 5879
INSERTED_CONFIRM = 0  # W45N8@84341100 + leftovers + aged still 404 at 22:00:01 game.time=84341891
INSERTED_RETRY2 = 0  # focused W45N8@84341100 still 404 at 22:01:23 game.time=84341908
INSERTED_JUST = 2847  # first try all five recovered 2847 at 22:03:27 game.time=84341934
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/980new W47N8:700t/2637new W45N8:600t/935new W45N7:700t/727new W47N7:700t/600new"
FIRST_PASS_LINE = (
    "first pass 34 of 35 official GETs 200, missing_chunks=1 (W45N8@84341100); "
    "hourly_patrol_prefilled=true from 21:24 patrol official already through 84341300 "
    "(overlap of this window); 21:30 half-hour already wrote through 84341500 and just-published 84341500 "
    "(84341501..84341600) for all five rooms (this pass already_in_db=17300 / inserted=5879); "
    "W45N8@84341100 still official 404 after confirm and retry2"
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
    "in-window official 404: W45N8@84341100 (80 ticks 84341101..84341180; 20 live 84341181..84341200); "
    "first pass 34 of 35 official GETs 200, missing_chunks=1; "
    "W45N8@84341100 still 404 after confirm 22:00:01 and focused retry2 22:01:23"
)
leftover_txt = (
    "leftover official 404 now outside window: "
    "W47N8@84337400 (25 live / 75 empty) (75 empty 84337426..84337500); "
    "W46N8@84336400 (0 live / 100 empty) (100 empty 84336401..84336500); "
    "W47N7@84334700 (0 live / 100 empty) (100 empty 84334701..84334800; later chunk 84334800 already 200); "
    "W47N8@84334600 (29 live / 71 empty) (71 empty 84334630..84334700; later chunks 84334700/84334800 already 200); "
    "W45N8@84333500 (0 live / 100 empty) (100 empty 84333501..84333600); "
    "W47N8@84333300 (16 live / 84 empty) (84 empty 84333301..84333333 and 84333350..84333400); "
    "W47N8@84332600 (0 live / 100 empty) (100 empty 84332601..84332700); "
    "W47N7@84332600 (0 live / 100 empty) (100 empty 84332601..84332700); "
    "W47N8@84332700 (17 live / 83 empty) (83 empty 84332701..84332783; combined leftover W47N8 hole 84332601..84332783); "
    "W45N8@84332200 (0 live / 100 empty) (100 empty 84332201..84332300); "
    "W47N7@84331000 (0 live / 100 empty) (100 empty 84331001..84331100); "
    "W47N7@84330300 (0 live / 100 empty) (100 empty 84330301..84330400); "
    "W45N8@84328100 (16 live / 84 empty) (84 empty 84328101..84328184); "
    "W45N7@84328300 (0 live / 100 empty) (100 empty 84328301..84328400); "
    "older leftovers unchanged."
)
confirm_summary = (
    "confirm inserted=0 (22:00:01 game.time=84341891, W45N8@84341100 + 14 leftover + 35 aged still 404, no SSL abort; "
    "confirm already included AGED; focused retry2 W45N8@84341100 still 404 at 22:01:23 game.time=84341908); "
    "just-published 84341800 first try all five recovered inserted=2847 at 22:03:27 game.time=84341934 "
    "(after this window; all five distinct=100, already_in_db=544); "
    "in-window official 404: W45N8@84341100 still 404 (20 live / 80 empty 84341101..84341180), not told; "
    "leftover W47N8@84337400 still 404 (25 live / 75 empty 84337426..84337500), not told; "
    "leftover W46N8@84336400 / W47N7@84334700 / W47N8@84334600 / W45N8@84333500 / W47N8@84333300 / "
    "W47N8@84332600 / W47N7@84332600 / W47N8@84332700 / W45N8@84332200 still 404 official holes, not told"
)
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} already inside the 45s gate vs first-pass rows "
    f"(delta first-robust 0.00986 s/tick, ~7.6s at tmin, over45 vs later=0, over15 later=111 vs first=628); "
    f"no corrective realign; "
    f"subsequent confirm/just-published inserts used later-mean-robust {TICK_S_IN_USE:.5f}"
)
freeze_para = (
    "Listener restart 21:56:58 (box wake after freeze 21:43:29-21:56:55 (801s); "
    "run_listener.sh auto-restart, not this run; pid 571655) "
    "room_stats gap 84341671..84341859 (189); official-filled 189/189 all five. "
    "This run did not restart the listener. "
    "Listener restart 21:24:35 (21:22:04-21:24:32 freeze (141s), not this run; pid 560436) "
    "room_stats gap 84341401..84341439 (39) remains in this window and stays official-filled 39/39 all five. "
    "Listener restart 21:03:43 (20:46:34-21:03:40 freeze (1024s), not this run; pid 551487) "
    "room_stats gap 84340941..84341179 (239) remains in this window and stays official-filled "
    "W46N8/W47N8/W45N7/W47N7 239/239, W45N8 160/239 (missing 84341101..84341179 because W45N8@84341100 official 404 after confirm and retry2; "
    "20 live ticks 84341181..84341200). "
    "Listener restart 20:17:41 (20:15:01-20:17:38 freeze (157s), not this run; pid 531610) "
    "room_stats gap 84340531..84340579 (49) is now outside this window and stays official-filled "
    "49/49 all five. "
    "After the post-restart rotate onto W47N8, live.json objects were still 0 and gameTime remained 84341874 "
    "at wrapup (live.json mtime fresh, stats.t/cpu/path buffers flowing, single_slot held); "
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
    },
    "just_published": {
        "base": 84341800,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "22:03:27",
        "recovered_game_time": 84341934,
        "inserted": INSERTED_JUST,
        "inserted_first_two": None,
        "inserted_remaining_three": None,
        "first_try_all_404": False,
        "first_try_at": "22:03:27",
        "first_try_game_time": 84341934,
        "retry_at": None,
        "retry_game_time": None,
        "retry_inserted": 0,
        "already_in_db": 544,
        "ticks": "84341801..84341900",
        "all_five_official_200": True,
        "w45n7_empty_no_creep": None,
        "distinct": {"W46N8": 100, "W47N8": 100, "W45N8": 100, "W45N7": 100, "W47N7": 100},
    },
    "confirm": {
        "at": "22:00:01",
        "game_time": 84341891,
        "inserted": 0,
        "ssl_abort_first": None,
        "targets": 50,
        "recovered": [],
        "note": "confirm already included 1 in-window + 14 leftover + 35 aged; all still 404; focused retry2 only for leftover in-window W45N8@84341100",
    },
    "retry2": {"at": "22:01:23", "game_time": 84341908, "inserted": 0, "skipped": False, "reason": "focused W45N8@84341100 still official 404"},
    "in_window_404": {"W45N8@84341100": {"ticks": "84341101..84341180", "live": "84341181..84341200", "distinct_live": 20}},
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 571655,
        "restart_at": "21:56:58",
        "this_run_restarted": False,
    },
    "box_freeze": {
        "from": "2026-11-18 21:43:29",
        "to": "2026-11-18 21:56:55",
        "sec": 801,
        "room_stats_gap": "84341671..84341859",
        "official_filled": "all five 189/189",
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
    f"missing_chunks={MISSING_CHUNKS} in_window_404=W45N8@84341100 (80t 84341101..84341180) empty_no_creep={empty_no_creep}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    "just-published 84341800 first try all five recovered inserted=2847 at 22:03:27 game.time=84341934 (after this window; all five distinct=100); in-window W45N8@84341100 still 404, not told; leftover W47N8@84337400 still 404, not told.",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not restart the listener.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_2200.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run_tee.txt").write_text(summary + now_text)
print(summary, end="")
print("now_text_bytes", len(now_text))
