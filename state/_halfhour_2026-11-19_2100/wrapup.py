#!/usr/bin/env python3
"""Write local status records for the 21:00 half-hour official-history backfill."""
from __future__ import annotations
import json, shutil, time as _time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

HK = ZoneInfo("Asia/Hong_Kong")
ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-19_2100"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84358801, 84359500
PUB_BASES = "84358800..84359400"
GT_FIRST = 84359568
TICK_S_FIRST = 4.12026
TICK_S_PRINTED = "4.120"
TICK_S_IN_USE = 4.12026  # first-pass; later-mean-robust 4.10298 already inside 45s gate, no corrective
TICK_S_LATER = 4.10298
TS_REALIGNED_FIRST = 0
NFIX_CORR = 0
GT_CORR = None  # no corrective; tick_s_check at game.time=84359602, over45 later=0 and first=0
RECON_ROWS = 25875
ALREADY = 9679
INSERTED_FIRST = 16196
INSERTED_CONFIRM = 0  # skipped; missing_chunks=0
INSERTED_RETRY2 = 0  # skipped; missing_chunks=0
INSERTED_JUST = 0  # 84359500 not attempted (first-pass game.time=84359568 still in-progress)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
PER_ROOM_LINE = "W46N8:700t/4629new W47N8:700t/5332new W45N8:700t/2078new W45N7:700t/1766new W47N7:700t/2391new"
FIRST_PASS_LINE = (
    "first pass 35 of 35 official GETs 200, missing_chunks=0; "
    "20:30 half-hour already wrote through 84359000 (just-published 84359000 was not attempted then at gt=84359052, typically publishable around game.time>=84359140); "
    "(this pass already_in_db=9679 / inserted=16196; overlap 84358801..84359000 already present from the 20:30 half-hour plus live rotation after reconnect; "
    "this pass newly wrote previously unpublished 84359000..84359400 for all 5 rooms, completing official coverage of the new 20:42:14-21:03:05 freeze STATS gap official-covered part 84359231..84359500 270/270 in all 5 rooms; "
    "unpublished tail 84359501..84359549 of that 319-tick gap 84359231..84359549 remains in the still in-progress 84359500 chunk; "
    "prior 20:12:27-20:23:40 freeze STATS gap 84358791..84358969 now sits only as 84358801..84358969 inside this window start 84358801 and is official-filled in all 5 rooms (W47N8 169/169 of the remainder; the official 404 W47N8@84358700 hole 84358791..84358800 aged out of this window); "
    "prior 20:09:23 reconnect STATS gap 84358741..84358759, 19:45:09-19:59:19 freeze STATS gap 84358381..84358609, 19:32:54 reconnect STATS gap 84358181..84358209, 19:11:05-19:19:02 freeze STATS gap 84357911..84358009 and 18:40:00-18:58:21 freeze STATS gap 84357521..84357759 have now aged out of this window start 84358801); "
    "leftover official 404 W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out of this 40-min window and were not retried; "
    "no in-window official 404; confirm and retry2 skipped; "
    "just-published 84359500 not attempted (first-pass game.time=84359568 still inside the in-progress chunk)"
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
vs_first = tick_s.get("vs_first") or {}
vs_cand = tick_s.get("vs_candidates") or {}
live = json.loads((ROOT / "metrics" / "live.json").read_text())
rot = json.loads((ROOT / "metrics" / "listener_rot.json").read_text())
yield_present = (ROOT / "metrics" / "listener_yield_rooms").exists()

finished = datetime.now(HK)
finished_hkt = finished.strftime("%Y-%m-%d %H:%M Asia/Hong_Kong")
finished_hkt_sec = finished.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

db_lines = []
cpu_tip = path_tip = rs_tip = None
with db.connect() as c:
    for room in sorted(ROOMS):
        mn, mx, n, d = c.execute(
            "SELECT min(tick), max(tick), count(*), count(DISTINCT tick) "
            "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, TMIN, TMAX),
        ).fetchone()
        db_lines.append(f"  {room} ticks={mn}..{mx} rows={n} distinct={d}")
    cpu_tip = c.execute("SELECT max(tick) FROM creep_cpu").fetchone()[0]
    path_tip = c.execute("SELECT max(tick) FROM path_arrivals").fetchone()[0]
    rs_tip = c.execute("SELECT max(tick) FROM room_stats").fetchone()[0]
    # unpublished tail of the new freeze after wrapup
    tail = {}
    for room in ROOMS:
        d, n, mn, mx = c.execute(
            "SELECT count(DISTINCT tick), count(*), min(tick), max(tick) "
            "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, 84359501, 84359549),
        ).fetchone()
        tail[room] = {"distinct": d or 0, "rows": n or 0, "min": mn, "max": mx, "missing": 49 - (d or 0)}
db_after_lines = "\n".join(db_lines)

def empty_ranges(room):
    return (coverage.get(room) or {}).get("official_empty_no_creep_ranges") or []

inwin_txt = (
    "no in-window official 404 after first pass: all 35 of 35 official GETs 200, missing_chunks=0; "
    "confirm and retry2 skipped; final official_404_in_window=0"
)
leftover_txt = (
    "no in-window official 404 remains; "
    "aged leftover official 404 W45N7@84358500 (hole 84358501..84358600) and W47N8@84358700 (hole 84358701..84358800, including 10 ticks 84358791..84358800 of the 20:12:27-20:23:40 freeze gap and the entire 20:09:23 reconnect gap in W47N8) were not retried this pass "
    "(already outside this 40-min window, along with W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800, and older)."
)
confirm_summary = (
    "confirm and retry2 skipped (missing_chunks=0); "
    "just-published 84359500 not attempted (first-pass game.time=84359568 still inside the in-progress chunk; typically publishable around game.time>=84359640; next half-hour overlap will catch it); "
    "previously unpublished 84359000 (in-progress at the 20:30 half-hour / not attempted then at gt=84359052) plus 84359100..84359400 were written for all 5 rooms this pass"
)
vs_later_before = tick_s.get("still_over_45s_vs_later_before")
vs_first_over45 = vs_first.get("over45")
vs_later_over15_before = tick_s.get("still_over_15s_vs_later_before")
vs_first_over15 = vs_first.get("over15")
span_vs = (vs_cand.get("span_mean") or {})
prev_vs = (vs_cand.get("prev_later") or {})
later_vs = (vs_cand.get("later_robust") or vs_cand.get("later_raw") or {})
tick_s_corr_txt = (
    f"first-interval tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} was already inside the 45s gate versus first-pass-realigned rows "
    f"(delta first-robust 0.01953 s/tick, ~15.0s at tmin; "
    f"over45 later={vs_later_before} vs first={vs_first_over45}, over15 later={vs_later_over15_before} vs first={vs_first_over15}; "
    f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')} and prev_later {tick_s.get('prev_later_mean'):.5f} over45={prev_vs.get('over45')}; "
    f"lowest_over45 among sane was {tick_s.get('lowest_over45_sane')} (later_raw/later_robust mean_off closer to the live anchor than first, over15 {later_vs.get('over15')} vs first {vs_first_over15}); "
    f"no corrective later-mean-robust realign (later already inside the 45s gate); "
    f"first-pass realign moved {TS_REALIGNED_FIRST} rows; "
    f"still_over_45s_vs_later={tick_s.get('still_over_45s_vs_later')}; skipped_cross_chunk={tick_s.get('skipped_cross_chunk')}; "
    f"in-use first-pass {TICK_S_IN_USE:.5f}; "
    f"confirm and retry2 skipped; just-published 84359500 not attempted; previously unpublished 84359000..84359400 were written this pass"
)

w46_tail = tail["W46N8"]
freeze_para = (
    f"New recorded box freeze 20:42:14-21:03:05 Asia/Hong_Kong (1244s) caused run_listener.sh auto-restart 21:03:08 (listener.py pid 956956 started 21:03:18; not this run). "
    f"New room_stats gap 84359231..84359549 (319): official-covered 84359231..84359500 is official-filled 270/270 in all 5 rooms this pass; "
    f"unpublished tail 84359501..84359549 (49) still sits in the in-progress 84359500 chunk "
    f"(W46N8 live already has {w46_tail['distinct']}/49 ticks {w46_tail['min']}..{w46_tail['max'] if w46_tail['max'] else ''} after the 21:03:08 reconnect; W47N8/W45N8/W45N7/W47N7 0/49). "
    f"Prior 20:12:27-20:23:40 freeze STATS gap 84358791..84358969 now only has 84358801..84358969 inside this window and is official-filled there in all 5 rooms "
    f"(W47N8 169/169 of the remainder; official 404 W47N8@84358700 hole 84358791..84358800 aged out, not retried). "
    f"Prior 20:09:23 reconnect STATS gap 84358741..84358759 and 19:45:09-19:59:19 freeze STATS gap 84358381..84358609 have aged out of this window and official-filled from earlier passes as previously recorded, except the still-open official 404 holes W45N7@84358500 and W47N8@84358700 which remain outside this window. "
    f"Aged official 404 W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) remain outside this window. "
    f"live.json / stats.t were fresh at pre-check (age <2s, tip stats.t=84359560, roomSlot W46N8 objects_n=265) after the 21:03:08 auto-reconnect; CPU/path buffers were already flowing; "
    f"previously unpublished 84359000..84359400 were written for all 5 rooms this pass; just-published 84359500 was not yet publishable (game.time=84359568 at first pass); "
    f"single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84359550 / path_arrivals through 84359549 at pre-check; through {cpu_tip} / {path_tip} at wrapup); this run did not restart the listener."
)

stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
single = True
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
        "corrective_applied": bool(tick_s.get("corrective_applied")),
        "later_mean_w46": tick_s.get("later_mean_w46"),
        "still_over_45s_vs_later": tick_s.get("still_over_45s_vs_later"),
        "reason": tick_s.get("reason"),
        "prev_later_over45_before_corrective": (prev_vs or {}).get("over45"),
        "prev_later_mean": tick_s.get("prev_later_mean"),
        "note": tick_s_corr_txt,
    },
    "just_published": {
        "base": 84359500,
        "oom_killed_at": [],
        "oom_note": None,
        "recovered_at": None,
        "recovered_game_time": None,
        "inserted": 0,
        "note": "not attempted; first-pass game.time=84359568 was still inside the in-progress chunk (typically publishable around game.time>=84359640; next half-hour overlap will catch it)",
        "first_try_all_404": None,
        "first_try_at": None,
        "first_try_game_time": None,
        "first_try_recovered": [],
        "first_try_still_404": [],
        "retry_at": None,
        "retry_game_time": None,
        "retry_inserted": 0,
        "ticks": None,
        "all_five_official_200": None,
        "still_404": [],
        "in_window_still_404": [],
        "w45n7_empty_no_creep": empty_ranges("W45N7"),
        "w47n7_empty_no_creep": empty_ranges("W47N7"),
        "distinct": None,
        "skipped": True,
    },
    "confirm": {
        "at": None,
        "game_time": None,
        "inserted": 0,
        "ssl_abort_first": None,
        "targets": 0,
        "recovered": [],
        "still_404": [],
        "skipped": True,
        "note": "confirm skipped; missing_chunks=0 after first pass 35/35 official GETs 200",
    },
    "retry2": {
        "at": None,
        "game_time": None,
        "inserted": 0,
        "skipped": True,
        "still_404": [],
        "note": "retry2 skipped; missing_chunks=0",
    },
    "listener": {
        "single_slot": single,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": "present" if yield_present else "absent",
        "pid": 956956,
        "pid_at_precheck": 956956,
        "loop_pid": 4035476,
        "restart_at": "21:03:08",
        "listener_started": "21:03:18",
        "earlier_restart_this_hour": None,
        "wrapup_ws_timeout": None,
        "wrapup_autorestart": None,
        "wrapup_listener_started": None,
        "this_run_restarted": False,
        "waited_for_reconnect": True,
        "live_objects_empty_after_reconnect": False,
        "pre_cpu_path_after_wait": (
            f"creep_cpu through 84359550 / path_arrivals through 84359549 at pre-check 21:04:40; "
            f"live.json objects_n={len(live.get('objects') or {})} because roomSlot was {live.get('roomSlot')} (home-map); "
            f"by wrapup roomSlot {live.get('roomSlot')} objects_n={len(live.get('objects') or {})}, stats.t={stats.get('t')}, "
            f"creep_cpu through {cpu_tip} / path_arrivals through {path_tip}"
        ),
    },
    "box_freeze": {
        "from": "2026-11-19 20:42:14",
        "to": "2026-11-19 21:03:05",
        "sec": 1244,
        "restart_at": "21:03:08",
        "room_stats_gap": "84359231..84359549",
        "official_filled": (
            "official-filled 270/270 of published part 84359231..84359500 in all 5 rooms; "
            "unpublished tail 84359501..84359549 still in-progress "
            f"(W46N8 live {w46_tail['distinct']}/49 ticks {w46_tail['min']}..{w46_tail['max']}; other four rooms 0/49)"
        ),
        "earlier_restart_gap": None,
        "earlier_freeze": {
            "from": "2026-11-19 20:12:27",
            "to": "2026-11-19 20:23:40",
            "sec": 673,
            "restart_at": "20:23:43",
            "room_stats_gap": "84358791..84358969",
            "official_filled": (
                "remainder 84358801..84358969 still inside this window start 84358801 is official-filled in all 5 rooms "
                "(W47N8 169/169 of the remainder); official 404 W47N8@84358700 hole 84358791..84358800 aged out of this window"
            ),
        },
        "new_freeze_this_run": True,
        "missed_halfhours": None,
    },
}

ok_line = (
    f"ok_quiet=True coverage={recovered}/{expected} inserted_window={INSERTED_WINDOW} "
    f"inserted_total={INSERTED_TOTAL} tick_s_in_use={TICK_S_IN_USE:.5f} "
    f"listener single_slot=True; no second listener; no war_cmd/pulse restart."
)
payload["ok_line"] = ok_line

now_text = "\n".join([
    f"{finished_hkt} half-hour backfill OK (quiet)",
    f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
    f"  ({FIRST_PASS_LINE}; see history_backfill.txt)",
    f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST:.5f}; {tick_s_corr_txt})",
    f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks={MISSING_CHUNKS}",
    f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
    f"per_room {PER_ROOM_LINE}",
    f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 +{INSERTED_RETRY2}, just_published +{INSERTED_JUST}, window {INSERTED_WINDOW}, run total {INSERTED_TOTAL})",
    f"ts_realigned_first={TS_REALIGNED_FIRST} ts_realigned_corrective={NFIX_CORR} tick_s_in_use={TICK_S_IN_USE:.5f}",
    "db_after",
    db_after_lines,
    f"coverage official_recovered={recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing} unique_room_ticks={unique_after.get('distinct_room_ticks')}",
    f"{inwin_txt}",
    f"{leftover_txt}",
    freeze_para,
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}",
    confirm_summary,
    ok_line,
]) + "\n"

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
(DIR / "history_backfill_now.txt").write_text(now_text)
shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")
shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

verify = [
    f"{finished_hkt_sec} verify 21:00 half-hour official-history backfill",
    f"window ticks {TMIN}..{TMAX} published_bases {PUB_BASES} game.time_first={GT_FIRST}",
    f"inserted_first={INSERTED_FIRST} confirm={INSERTED_CONFIRM} retry2={INSERTED_RETRY2} just_published={INSERTED_JUST} total={INSERTED_TOTAL}",
    f"coverage {recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}",
    f"tick_s_first={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} in_use={TICK_S_IN_USE:.5f} later_mean_robust={TICK_S_LATER:.5f} corrective={tick_s.get('corrective_applied')} nfix={NFIX_CORR}",
    f"{inwin_txt}",
    f"{leftover_txt}",
    freeze_para,
    f"listener single_slot={single} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 21:03:08 (listener.py pid 956956 started 21:03:18) after the new recorded box freeze 20:42:14-21:03:05 (1244s, room_stats gap 84359231..84359549). There was no earlier auto-restart this hour. The 21:03:08 reconnect had already recovered stats/CPU/path by pre-check 21:04:40 (live.json fresh, stats.t advancing, roomSlot W46N8 objects_n=265; single_slot held).",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_note = DIR / "backfill_retry2.txt"
if not retry2_note.exists():
    retry2_note.write_text("retry2 skipped; missing_chunks=0 after first pass 35/35 official GETs 200\n")
shutil.copyfile(retry2_note, ROOT / "state" / "_halfhour_backfill_retry2_2100.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
(DIR / "wrapup_run_tee.txt").write_text(summary + now_text)
(DIR / "wrapup_run_stdout.txt").write_text(summary + f"now_text_bytes {len(now_text)}\n")
print(summary, end="")
print("wrote", DIR / "history_backfill.json")
