#!/usr/bin/env python3
"""Write local status records for the 21:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-18_2100"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84340501, 84341200
PUB_BASES = "84340500..84341100"
GT_FIRST = 84341202
TICK_S_FIRST = 4.66417
TICK_S_PRINTED = "4.664"
TICK_S_IN_USE = 4.66417
TICK_S_LATER = 4.63436
TS_REALIGNED_FIRST = 47
NFIX_CORR = 0
GT_CORR = None
RECON_ROWS = 21423
ALREADY = 10874
INSERTED_FIRST = 10549
INSERTED_CONFIRM = 1889  # recovered W47N8@84341100 (1283) and W47N7@84341100 (606) at 21:08:30 game.time=84341231
INSERTED_RETRY2 = 0  # focused W45N8@84341100 still 404 at 21:10:16 game.time=84341252
INSERTED_JUST = 2649  # first try all 404 at 21:14:07 game.time=84341303; retry all five recovered 2649 at 21:17:51 game.time=84341350
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/4229new W47N8:600t/2341new W45N8:600t/1048new W45N7:700t/1543new W47N7:600t/1388new"
FIRST_PASS_LINE = (
    "first pass 32 of 35 official GETs 200, missing_chunks=3 (W47N8@84341100, W45N8@84341100, W47N7@84341100); "
    "hourly_patrol_prefilled=true from 20:17 patrol official already through 84340500 "
    "(overlap of this window); 20:30 half-hour already wrote through 84340700 and just-published 84340700 "
    "(84340701..84340800) for all five rooms (this pass already_in_db=10874 / inserted=10549); "
    "confirm later recovered W47N8@84341100 and W47N7@84341100"
)
MISSING_CHUNKS = 3

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
    "first pass 32 of 35 official GETs 200, missing_chunks=3; confirm recovered W47N8@84341100 and W47N7@84341100, "
    "W45N8@84341100 still 404 after confirm 21:08:39 and focused retry2 21:10:16"
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
    "confirm inserted=1889 (21:08:30 game.time=84341231, recovered W47N8@84341100 inserted=1283 and "
    "W47N7@84341100 inserted=606; W45N8@84341100 + 14 leftover + 35 aged still 404, no SSL abort; "
    "confirm already included AGED; focused retry2 W45N8@84341100 still 404 at 21:10:16 game.time=84341252); "
    "just-published 84341200 first try all 404 at 21:14:07 game.time=84341303; "
    "retry all five recovered inserted=2649 at 21:17:51 game.time=84341350 "
    "(after this window; W46N8/W47N8/W45N8/W47N7 distinct=100, W45N7 official empty-no-creep 84341201..84341300 0 rows, "
    "already_in_db=928 mostly W46N8 live); "
    "in-window official 404: W45N8@84341100 still 404 (20 live / 80 empty 84341101..84341180), not told; "
    "leftover W47N8@84337400 still 404 (25 live / 75 empty 84337426..84337500), not told; "
    "leftover W46N8@84336400 / W47N7@84334700 / W47N8@84334600 / W45N8@84333500 / W47N8@84333300 / "
    "W47N8@84332600 / W47N7@84332600 / W47N8@84332700 / W45N8@84332200 still 404 official holes, not told"
)
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} already inside the 45s gate vs first-pass rows "
    f"(delta first-robust 0.02981 s/tick, ~20.9s at tmin, over45 vs later=0, over15 later=4251 vs first=72); "
    f"no corrective realign; first-interval was lowest-over45 among sane; "
    f"still_over_45s_vs_later=0; "
    f"subsequent confirm/just-published inserts used first-interval {TICK_S_IN_USE:.5f}"
)
freeze_para = (
    "Listener restart 21:03:43 (box wake after freeze 20:46:34-21:03:40 (1024s); "
    "run_listener.sh auto-restart, not this run; pid 551487) "
    "room_stats gap 84340941..84341179 (239); official-filled W46N8/W47N8/W45N7/W47N7 239/239, "
    "W45N8 160/239 (missing 84341101..84341179 because W45N8@84341100 official 404 after confirm and retry2; "
    "20 live ticks 84341181..84341200 after reconnect). "
    "This run did not restart the listener. "
    "Listener restart 20:17:41 (20:15:01-20:17:38 freeze (157s), not this run; pid 531610) "
    "room_stats gap 84340531..84340579 (49) remains in this window and stays official-filled "
    "49/49 all five. "
    "Listener restart 19:59:58 (19:45:50-19:59:55 freeze (838s), not this run; pid 522451) "
    "room_stats gap 84340161..84340359 (199) is now outside this window and stays official-filled "
    "199/199 all five. "
    "Listener restart 19:18:10 (19:11:47-19:18:07 freeze (377s), not this run; pid 505651) "
    "room_stats gap 84339731..84339819 (89) is now outside this window and stays official-filled "
    "89/89 all five."
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
        "base": 84341200,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "21:17:51",
        "recovered_game_time": 84341350,
        "inserted": INSERTED_JUST,
        "inserted_first_two": None,
        "inserted_remaining_three": None,
        "first_try_all_404": True,
        "first_try_at": "21:14:07",
        "first_try_game_time": 84341303,
        "retry_at": "21:17:51",
        "retry_game_time": 84341350,
        "retry_inserted": 2649,
        "already_in_db": 928,
        "ticks": "84341201..84341300",
        "all_five_official_200": True,
        "w45n7_empty_no_creep": "84341201..84341300",
        "distinct": {"W46N8": 100, "W47N8": 100, "W45N8": 100, "W45N7": 0, "W47N7": 100},
    },
    "confirm": {
        "at": "21:08:30",
        "game_time": 84341231,
        "inserted": 1889,
        "ssl_abort_first": None,
        "targets": 52,
        "recovered": ["W47N8@84341100", "W47N7@84341100"],
        "note": "confirm already included 3 in-window + 14 leftover + 35 aged; focused retry2 only for leftover in-window W45N8@84341100",
    },
    "retry2": {"at": "21:10:16", "game_time": 84341252, "inserted": 0, "skipped": False, "reason": "focused W45N8@84341100 still official 404"},
    "in_window_404": {"W45N8@84341100": {"ticks": "84341101..84341180", "live": "84341181..84341200", "distinct_live": 20}},
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 551487,
        "restart_at": "21:03:43",
        "this_run_restarted": False,
    },
    "box_freeze": {
        "from": "2026-11-18 20:46:34",
        "to": "2026-11-18 21:03:40",
        "sec": 1024,
        "room_stats_gap": "84340941..84341179",
        "official_filled": "W46N8/W47N8/W45N7/W47N7 239/239; W45N8 160/239 (W45N8@84341100 official 404 for 84341101..84341179)",
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
    "just-published 84341200 first try all 404 at 21:14:07 game.time=84341303; retry all five recovered inserted=2649 at 21:17:51 game.time=84341350 (after this window; W45N7 official empty-no-creep 84341201..84341300); in-window W45N8@84341100 still 404, not told; leftover W47N8@84337400 still 404, not told.",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not restart the listener.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_2100.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run_tee.txt").write_text(summary + now_text)
print(summary, end="")
print("now_text_bytes", len(now_text))
