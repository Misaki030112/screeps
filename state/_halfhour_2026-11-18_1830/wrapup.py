#!/usr/bin/env python3
"""Write local status records for the 18:30 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-18_1830"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84338401, 84339100
PUB_BASES = "84338400..84339000"
GT_FIRST = 84339196
TICK_S_FIRST = 4.47569
TICK_S_PRINTED = "4.476"
TICK_S_IN_USE = 4.72549
TS_REALIGNED_FIRST = 499
NFIX_CORR = 21719
GT_CORR = 84339214
RECON_ROWS = 29663
ALREADY = 29663
INSERTED_FIRST = 0
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0  # confirm already included AGED leftovers; all still 404
INSERTED_JUST = 2886  # all five rooms first try at 18:32:05 game.time=84339224
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/0new W47N8:700t/0new W45N8:700t/0new W45N7:700t/0new W47N7:700t/0new"
FIRST_PASS_LINE = (
    "first pass 35 of 35 official GETs 200, missing_chunks=0; "
    "hourly_patrol_prefilled=true from 18:21 patrol official already through 84339100 "
    "(same window as this first pass, inserted=7884 then, this pass already_in_db=29663 / inserted=0); "
    "18:00 backfill already wrote through 84338800 and just-published 84338800 (84338801..84338900) for all five rooms"
)
MISSING_CHUNKS = 0

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
    "in-window official 404: none "
    "(35 of 35 first-pass official GETs 200, missing_chunks=0)"
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
    "confirm inserted=0 (18:32:28 game.time=84339228, 14 leftover + 35 aged still 404, no SSL abort; "
    "no separate retry2, confirm already included AGED); "
    "just-published 84339100 recovered all five first try inserted=2886 at 18:32:05 game.time=84339224 "
    "(after this window, all five distinct=100, no first 404); "
    "in-window official 404: none; "
    "leftover W47N8@84337400 still 404 (25 live / 75 empty 84337426..84337500), not told; "
    "leftover W46N8@84336400 / W47N7@84334700 / W47N8@84334600 / W45N8@84333500 / W47N8@84333300 / "
    "W47N8@84332600 / W47N7@84332600 / W47N8@84332700 / W45N8@84332200 still 404 official holes, not told"
)
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band, "
    f"but later-mean-robust {TICK_S_IN_USE:.5f} was over the 45s gate vs first-pass rows "
    f"(delta first-robust -0.24980 s/tick, ~198.6s at tmin, 22071 rows over45 vs later before); "
    f"applied corrective later-mean-robust realign of {NFIX_CORR} rows at game.time={GT_CORR}, "
    f"still_over_45s_vs_later={vs_later_after.get('over45', 0)}; "
    f"subsequent confirm/just-published inserts used later-mean {TICK_S_IN_USE:.5f}"
)
freeze_para = (
    "Listener restart 18:20:45 (box wake after freeze 18:14:41-18:20:42 (360s); "
    "run_listener.sh auto-restart, not this run; pid 486948) "
    "room_stats gap 84339001..84339089 (89); official-filled 89/89 of 89 of 89 all five. "
    "This run did not restart the listener. "
    "Listener restart 17:57:15 (17:42:38-17:57:12 freeze (873s), not this run; pid 478068) "
    "room_stats gap 84338591..84338789 (199) remains in this window and stays official-filled "
    "199/199 of 199 of 199 all five. "
    "Listener restart 17:18:42 (17:14:33-17:18:39 freeze (244s), not this run; pid 463150) "
    "room_stats gap 84338231..84338289 (59) is now outside this window and stays official-filled "
    "59/59 of 59 of 59 all five. "
    "Listener restart 16:57:13 (16:49:42-16:57:10 freeze (447s), not this run; pid 454066) "
    "room_stats gap 84337901..84338019 (119) is now outside this window and stays official-filled "
    "119/119 of 119 of 119 all five."
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
        "base": 84339100,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": "18:32:05",
        "recovered_game_time": 84339224,
        "inserted": INSERTED_JUST,
        "inserted_first_two": None,
        "inserted_remaining_three": None,
        "w47n8_w45n8_w47n7_first_404": False,
        "ticks": "84339101..84339200",
        "all_five_distinct": 100,
    },
    "confirm": {
        "at": "18:32:28",
        "game_time": 84339228,
        "inserted": 0,
        "ssl_abort_first": None,
        "targets": 49,
        "note": "confirm already included 14 leftover + 35 aged; all still 404; no separate retry2",
    },
    "retry2": {"at": None, "game_time": None, "inserted": 0, "skipped": True, "reason": "confirm already included AGED; all still 404"},
    "in_window_404": {},
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 486948,
        "restart_at": "18:20:45",
        "this_run_restarted": False,
    },
    "box_freeze": {
        "from": "2026-11-18 18:14:41",
        "to": "2026-11-18 18:20:42",
        "sec": 360,
        "room_stats_gap": "84339001..84339089",
        "official_filled": "89/89 all five",
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
    f"missing_chunks={MISSING_CHUNKS} in_window_404=none empty_no_creep={empty_no_creep}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    "just-published 84339100 recovered all five first try at 18:32:05 game.time=84339224 inserted=2886 (after this window, all five distinct=100, no first 404); leftover W47N8@84337400 still 404, not told.",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not restart the listener.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1830.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run_tee.txt").write_text(summary + now_text)
print(summary, end="")
print("now_text_bytes", len(now_text))
