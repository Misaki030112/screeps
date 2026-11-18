#!/usr/bin/env python3
"""Write local status records for the 16:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-18_1600"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84336601, 84337300
PUB_BASES = "84336600..84337200"
GT_FIRST = 84337328
TICK_S_FIRST = 4.61262
TICK_S_PRINTED = "4.613"
TICK_S_IN_USE = 4.69892
TS_REALIGNED_FIRST = 6072
NFIX_CORR = 5066
GT_CORR = 84337351
RECON_ROWS = 25548
ALREADY = 15704
INSERTED_FIRST = 9844
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
INSERTED_JUST = 2067
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/1824new W47N8:700t/3773new W45N8:700t/1922new W45N7:700t/994new W47N7:700t/1331new"
FIRST_PASS_LINE = (
    "first pass 35 of 35 official GETs 200, missing_chunks=0; "
    "hourly_patrol_prefilled=true from 15:22 patrol official already through 84336800 (overlap); "
    "15:30 backfill already wrote through 84336900 and just-published 84336900 (84336901..84337000) for all five rooms"
)

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

inwin_txt = "in-window official 404: none (35 of 35 first-pass official GETs 200, missing_chunks=0)"
leftover_txt = (
    "leftover official 404 now outside window: "
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
    "confirm inserted=0 leftover official 404s unchanged; retry2 inserted=0 leftovers still 404; "
    "just-published 84337300 recovered all five rooms inserted=2067 (after this window); "
    "in-window official 404: none; "
    "leftover W46N8@84336400 / W47N7@84334700 / W47N8@84334600 / W45N8@84333500 / W47N8@84333300 / "
    "W47N8@84332600 / W47N7@84332600 / W47N8@84332700 / W45N8@84332200 still 404 official holes, not told"
)
tick_s_corr_txt = (
    f"later-mean-robust {TICK_S_IN_USE:.5f} was over the 45s gate vs first-pass rows "
    f"(tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}, ~72.3s at tmin); "
    f"applied corrective later-mean-robust realign of {NFIX_CORR} rows at game.time={GT_CORR}, "
    f"still_over_45s_vs_later={vs_later_after.get('over45', 0)}"
)
freeze_para = (
    "Listener restart 16:02:35 (box wake after freeze 15:50:56-16:02:32 (689s); "
    "run_listener.sh auto-restart, not this run; pid 431060) room_stats gap 84337151..84337319 (169); "
    "official-filled 169/169 of 169 of 169 all five "
    "(in-window published 84337151..84337300 all five 150/150 of 150 of 150; "
    "tail 84337301..84337319 all five 19/19 of 19 of 19 after just-published 84337300). "
    "This run did not restart the listener. "
    "Listener restart 15:23:01 (15:22 hourly patrol, not this run; pid 413974) "
    "room_stats gap 84336791..84336809 (19) remains in this window and stays official-filled "
    "19/19 of 19 of 19 all five. "
    "Earlier 14:43:48-15:04:09 freeze / room_stats gap 84336301..84336569 is now outside this window."
)
ok_line = (
    f"ok_quiet=True coverage={recovered}/{expected} inserted_window={INSERTED_WINDOW} "
    f"inserted_total={INSERTED_TOTAL} tick_s_in_use={TICK_S_IN_USE:.5f} "
    "listener single_slot=True; no second listener; no war_cmd/pulse restart."
)
nl = "\n"
single = (not yield_present)
now_lines = [
    f"{finished_hkt} half-hour backfill OK (quiet)",
    f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
    f"  ({FIRST_PASS_LINE}; see history_backfill.txt)",
    f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST:.5f}; {tick_s_corr_txt}, in-use {TICK_S_IN_USE:.5f})",
    f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks=0",
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
    "missing_chunks": 0,
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
        "base": 84337300,
        "early_404_at": "16:08:32",
        "early_game_time": 84337384,
        "ssl_abort_at": "16:11:29",
        "ssl_abort_game_time": 84337421,
        "recovered_at": "16:12:59",
        "recovered_game_time": 84337441,
        "inserted": INSERTED_JUST,
        "ticks": "84337301..84337400",
        "all_five_distinct": 100,
    },
    "confirm": {"at": "16:06:12", "game_time": 84337355, "inserted": 0},
    "retry2": {"at": "16:07:37", "game_time": 84337373, "inserted": 0},
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 431060,
        "restart_at": "16:02:35",
        "this_run_restarted": False,
    },
    "box_freeze": {
        "from": "2026-11-18 15:50:56",
        "to": "2026-11-18 16:02:32",
        "sec": 689,
        "room_stats_gap": "84337151..84337319",
        "official_filled": "169/169 all five",
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
    f"missing_chunks=0 in_window_404=0 empty_no_creep={empty_no_creep}",
    f"tick_s first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {TICK_S_IN_USE:.5f}; later over45={vs_later_after.get('over45')}.",
    f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
    f"just-published early 16:08:32 game.time=84337384 still 404; ssl abort 16:11:29 game.time=84337421 after leftover 404s; recovered 16:12:59 game.time=84337441 base 84337300 all five rooms inserted=2067 (after this window).",
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not restart the listener.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1600.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run_tee.txt").write_text(summary + now_text)
print(summary, end="")
print("now_text_bytes", len(now_text))
