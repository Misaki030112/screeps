#!/usr/bin/env python3
"""Write local status records for the 04:00 half-hour official-history backfill."""
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
DIR = ROOT / "state" / "_halfhour_2026-11-20_0400"
assert "_halfhour_2026-11-20_0400" in str(DIR), DIR
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84365001, 84365700
PUB_BASES = "84365000..84365600"
GT_FIRST = 84365799
TICK_S_FIRST = 4.06851
TICK_S_PRINTED = "4.069"
TICK_S_IN_USE = 4.07385  # later_raw; first 4.06851 also over45=0 but later has lower over15 (2611 vs 8539)
TICK_S_LATER = 4.07385
TS_REALIGNED_FIRST = 0
NFIX_CORR = 0
GT_CORR = None
RECON_ROWS = 24572
ALREADY = 12243
INSERTED_FIRST = 12329
INSERTED_CONFIRM = 0  # confirm still 404 W45N7@84365200
INSERTED_RETRY2 = 0
PER_ROOM_LINE = "W46N8:700t/3927new W47N8:700t/3679new W45N8:700t/2026new W45N7:600t/1134new W47N7:700t/1563new"
FIRST_PASS_CORE = (
    "first pass 34 of 35 official GETs 200, missing_chunks=1 W45N7@84365200; "
    "03:40 half-hour already wrote through 84365100 / reconstructed through 84365200 (just-published 84365200 was attempted then at 03:38:45 gt=84365342 and recovered W46N8/W47N8/W45N8/W47N7, W45N7@84365200 stayed official 404 after retry at 03:39:59 gt=84365360, ticks 84365201..84365300); "
    "no concurrent 1h patrol this hour (last delivered 03:32); "
    "(this pass already_in_db=12243 / inserted=12329; overlap 84365001..84365700 already partly present from the 03:40 half-hour official fill, just-published 84365200 for four rooms, and live rotation; "
    "this pass inserted 12329 additional rows: W46N8 3927, W47N8 3679, W45N8 2026, W45N7 1134, W47N7 1563; "
    "NEW 03:46:06-04:06:15 freeze STATS gap 84365441..84365749 (309): official-filled 309/309 in W46N8/W47N8/W45N8/W47N7 after just-published 84365700; W45N7 236/309 official empty_no_creep 84365441..84365507 and 84365512..84365517 (official GETs 200); "
    "prior 03:18:44-03:22:57 freeze STATS gap 84365001..84365119 remains official-filled 119/119 in four rooms, W45N7 evac empty_no_creep 42/119 (already told by the 03:32 1h patrol); "
    "prior 02:52:31-03:03:13 freeze STATS gap 84364661..84364829 has aged out of this window start 84365001 and remains official-filled 169/169 in all 5 (already told by the 03:32 1h patrol); "
    "prior 02:21:37-02:25:12, 01:47:00-02:03:02, 01:30:52-01:33:08 and 01:14:19-01:18:28 freezes have aged out of this window start 84365001 (already told); "
    "leftover official 404 W47N8@84363900 aged out of this 40-min window and was not retried (hole 84363901..84363950 still unfilled, db live-only 84363951..84364000; already told by the 02:34 1h patrol); "
    "leftover official 404 W46N8@84362700, W47N8@84361700, W46N8@84360600, W45N7@84360200, W47N8@84359900, W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 already aged out and were not retried; "
    "in-window official 404: W45N7@84365200 (hole 84365201..84365300, confirm 04:11:44 gt=84365825 and retry2 04:12:59 gt=84365843 both stayed official 404; not yet told by a 1h patrol — first seen by the 03:40 half-hour quiet run); "
    "W45N7 official empty_no_creep 84365042, 84365044..84365200, 84365414..84365507 and 84365512..84365517 (258 ticks, official GETs 200; evac then later empty stretches)"
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
vs_first = tick_s.get("vs_first") or {}
vs_cand = tick_s.get("vs_candidates") or {}
live = json.loads((ROOT / "metrics" / "live.json").read_text())
rot = json.loads((ROOT / "metrics" / "listener_rot.json").read_text())
yield_present = (ROOT / "metrics" / "listener_yield_rooms").exists()
just_pub_path = DIR / "just_published_84365700.json"
just_pub_payload = json.loads(just_pub_path.read_text()) if just_pub_path.exists() else {}
confirm_payload = {}
try:
    confirm_payload = json.loads((DIR / "backfill_confirm_gets.json").read_text())
except Exception:
    confirm_payload = {}

finished = datetime.now(HK)
finished_hkt = finished.strftime("%Y-%m-%d %H:%M Asia/Hong_Kong")
finished_hkt_sec = finished.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")

def rng(c, room, t0, t1, expected_n):
    d, n, mn, mx = c.execute(
        "SELECT count(DISTINCT tick), count(*), min(tick), max(tick) "
        "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, t0, t1),
    ).fetchone()
    return {"distinct": d or 0, "rows": n or 0, "min": mn, "max": mx, "missing": expected_n - (d or 0)}

INSERTED_JUST = int(just_pub_payload.get("inserted") or 0)
just_recovered = just_pub_payload.get("recovered") or []
just_still_404 = just_pub_payload.get("still_404") or []
just_gt = just_pub_payload.get("game_time")
just_at = just_pub_payload.get("at")
all_five = (len(just_recovered) == 5 and not just_still_404)
INSERTED_WINDOW = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2
retry_note = just_pub_payload.get("retry_note") or ""
just_note = (
    f"just-published 84365700 attempted at {just_at} game.time={just_gt} "
    f"(typically publishable around game.time>=84365840) and was "
    + ("200 for all 5 rooms" if all_five else f"not fully published (recovered={just_recovered or []} still_404={just_still_404 or []})")
    + f" (inserted={INSERTED_JUST}); ticks 84365701..84365800 sit just after this reconstructed window"
    + (f"; {retry_note}" if retry_note else "")
)
INSERTED_TOTAL = INSERTED_WINDOW + INSERTED_JUST
FIRST_PASS_LINE = FIRST_PASS_CORE + "; " + just_note

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
    freeze0346 = {room: rng(c, room, 84365441, 84365749, 309) for room in ROOMS}
    freeze0318 = {room: rng(c, room, 84365001, 84365119, 119) for room in ROOMS}
    freeze0252 = {room: rng(c, room, 84364661, 84364829, 169) for room in ROOMS}
    freeze0221 = {room: rng(c, room, 84364201, 84364269, 69) for room in ROOMS}
    freeze0147 = {room: rng(c, room, 84363701, 84363949, 249) for room in ROOMS}
    freeze0130 = {room: rng(c, room, 84363461, 84363509, 49) for room in ROOMS}
    hole_w46n8_62700 = rng(c, "W46N8", 84362701, 84362800, 100)
    hole_w47n8_61700 = rng(c, "W47N8", 84361701, 84361800, 100)
    hole_w46n8_60600 = rng(c, "W46N8", 84360601, 84360700, 100)
    aged_w45n7_60200 = rng(c, "W45N7", 84360201, 84360300, 100)
    aged_w47n8_59900 = rng(c, "W47N8", 84359901, 84360000, 100)
    hole_w47n8_63900 = rng(c, "W47N8", 84363901, 84364000, 100)
    hole_w45n7_65200 = rng(c, "W45N7", 84365201, 84365300, 100)
    just_pub = {room: rng(c, room, 84365701, 84365800, 100) for room in ROOMS}
    w45n7_empty = rng(c, "W45N7", 84365042, 84365200, 159)
db_after_lines = "\n".join(db_lines)

inwin_txt = (
    "in-window official 404 after first pass: 34 of 35 official GETs 200, missing_chunks=1 W45N7@84365200; "
    "confirm at 04:11:44 gt=84365825 still 404; retry2 at 04:12:59 gt=84365843 still 404; "
    f"final official_404_in_window=1 (W45N7@84365200 hole 84365201..84365300 still db {hole_w45n7_65200['distinct']}/100)"
)
leftover_txt = (
    f"In-window official 404 W45N7@84365200 (hole 84365201..84365300 still db {hole_w45n7_65200['distinct']}/100, no rows; first seen by the 03:40 half-hour quiet run; confirm 04:11:44 gt=84365825 and retry2 04:12:59 gt=84365843 both stayed official 404) is still unfilled and has not yet been told by a 1h patrol. "
    f"Leftover official 404 W47N8@84363900 (hole 84363901..84364000 still db {hole_w47n8_63900['distinct']}/100 live-only 84363951..84364000, missing 84363901..84363950; already told by the 02:34 1h patrol) aged out of this window start 84365001 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W46N8@84362700 (hole 84362701..84362800 still db {hole_w46n8_62700['distinct']}/100, no live rows; already told by the 01:26 1h patrol) aged out of this window start 84365001 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W47N8@84361700 (hole 84361701..84361800 still db {hole_w47n8_61700['distinct']}/100 live-only; already told) aged out of this window start 84365001 and was not retried this pass (still unfilled). "
    f"Aged leftover official 404 W46N8@84360600 (hole 84360601..84360700 still db {hole_w46n8_60600['distinct']}/100 live-only; already told) aged out and was not retried (still unfilled). "
    f"Aged leftover official 404 W45N7@84360200 (hole 84360201..84360300 still db {aged_w45n7_60200['distinct']}/100; already told) and W47N8@84359900 (hole 84359901..84360000 still db {aged_w47n8_59900['distinct']}/100; already told) also sit outside this window and were not retried (still unfilled). "
    "Aged leftover official 404 W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300, W47N8@84352400, W47N7@84350700, W46N8@84346200, W47N8@84346200, W45N7@84347000, W45N8@84347100, W47N8@84347800 (and older) were not retried this pass "
    "(already outside this 40-min window). "
    "This window has empty_no_creep=258 in W45N7 (official 200; 84365042, 84365044..84365200 evac, plus later empty 84365414..84365507 and 84365512..84365517)."
)
confirm_summary = (
    "confirm 04:11:44 gt=84365825 and retry2 04:12:59 gt=84365843 both left W45N7@84365200 official 404 (inserted 0+0); "
    + just_note
    + "; this pass inserted 12329 additional rows in the reconstructed window (W46N8 3927 / W47N8 3679 / W45N8 2026 / W45N7 1134 / W47N7 1563) on top of the 03:40 half-hour official fill and just-published 84365200 for four rooms"
)

vs_first_over45 = (vs_cand.get("first") or vs_first or {}).get("over45")
vs_first_over15 = (vs_cand.get("first") or vs_first or {}).get("over15")
span_vs = (vs_cand.get("span_mean") or {})
prev_vs = (vs_cand.get("prev_later") or {})
later_vs = (vs_cand.get("later_raw") or vs_cand.get("later_robust") or {})
first_vs = (vs_cand.get("first") or vs_first or {})
all_vs = (vs_cand.get("all_mean") or {})
tick_s_corr_txt = (
    f"script {TICK_S_FIRST:.5f} printed {TICK_S_PRINTED} is in the sane 3-6s band; "
    f"later-mean-robust {TICK_S_LATER:.5f} (raw later-mean also {TICK_S_LATER:.5f}) is the live-anchor-best "
    f"(delta first-robust {TICK_S_FIRST-TICK_S_LATER:.5f} s/tick, ~{(GT_FIRST-TMIN)*abs(TICK_S_FIRST-TICK_S_LATER):.1f}s at tmin; "
    f"over45 later={later_vs.get('over45')} vs first={vs_first_over45} vs all_mean={all_vs.get('over45')} vs prev_later={prev_vs.get('over45')}, "
    f"over15 later={later_vs.get('over15')} vs first={vs_first_over15} vs all_mean={all_vs.get('over15')} vs prev_later={prev_vs.get('over15')}; "
    f"span_mean {tick_s.get('span_mean'):.5f} over45={span_vs.get('over45')}; "
    f"lowest_over45 among sane was {tick_s.get('lowest_over45_sane')} {TICK_S_IN_USE:.5f} "
    f"(mean_off later {later_vs.get('mean_off')} closer to the live anchor than first {first_vs.get('mean_off')}, all_mean {all_vs.get('mean_off')} or prev_later {prev_vs.get('mean_off')}); "
    f"first-pass realign moved {TS_REALIGNED_FIRST} rows with first {TICK_S_FIRST:.5f}; "
    f"tick_s_check applied no corrective realign (live-anchor-best later_raw {TICK_S_IN_USE:.5f} already inside 45s gate, over45=0; first also over45=0); "
    f"still_over_45s_vs_later={tick_s.get('still_over_45s_vs_later')}; skipped_cross_chunk={tick_s.get('skipped_cross_chunk')}; "
    f"in-use later_raw {TICK_S_IN_USE:.5f}; "
    f"in-window official 404: W45N7@84365200; {just_note}"
)

stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
f0346 = ", ".join(f"{r} {freeze0346[r]['distinct']}/309" for r in ROOMS)
f0318 = ", ".join(f"{r} {freeze0318[r]['distinct']}/119" for r in ROOMS)
f0252 = ", ".join(f"{r} {freeze0252[r]['distinct']}/169" for r in ROOMS)
f0221 = ", ".join(f"{r} {freeze0221[r]['distinct']}/69" for r in ROOMS)
f0147 = ", ".join(f"{r} {freeze0147[r]['distinct']}/249" for r in ROOMS)
f0130 = ", ".join(f"{r} {freeze0130[r]['distinct']}/49" for r in ROOMS)
objs = live.get("objects") or {}
objects_n = len(objs) if isinstance(objs, (list, dict)) else 0
freeze0318_four = all(freeze0318[r]["missing"] == 0 for r in ROOMS if r != "W45N7")
freeze0252_all = all(freeze0252[r]["missing"] == 0 for r in ROOMS)
freeze0318_fill = (
    f"official-filled {f0318}" if all(freeze0318[r]["missing"] == 0 for r in ROOMS)
    else f"official-filled 119/119 in four rooms; W45N7 {freeze0318['W45N7']['distinct']}/119 official empty_no_creep after evac (counts {f0318})"
)
freeze0346_fill = (
    f"official-filled {f0346}" if all(freeze0346[r]["missing"] == 0 for r in ROOMS)
    else f"official-filled 309/309 in four rooms; W45N7 {freeze0346['W45N7']['distinct']}/309 official empty_no_creep 84365441..84365507 and 84365512..84365517 (counts {f0346})"
)
freeze_para = (
    f"NEW box freeze 03:46:06-04:06:15 Asia/Hong_Kong (1201s) caused run_listener.sh auto-restart 04:06:18 (listener.py pid 1112279 started 04:06:28; this run found the listener after reconnect and did not itself restart it). "
    f"room_stats gap 84365441..84365749 (309): {freeze0346_fill}. "
    f"This new freeze has not yet been told by a delivered 1h patrol (last delivered 1h patrol was 03:32). "
    f"Prior box freeze 03:18:44-03:22:57 Asia/Hong_Kong (247s; run_listener.sh auto-restarts 03:18:23 and 03:23:00; already told by the 03:32 1h patrol) "
    f"room_stats gap 84365001..84365119 (119) remains official-filled 119/119 in four rooms, W45N7 evac empty_no_creep (counts {f0318}). "
    f"Prior box freeze 02:52:31-03:03:13 Asia/Hong_Kong (636s; run_listener.sh auto-restart 03:03:16; already told by the 03:32 1h patrol) "
    f"room_stats gap 84364661..84364829 (169) has aged out of this window start 84365001 and remains official-filled 169/169 in all 5 (counts {f0252}). "
    f"Prior box freeze 02:21:37-02:25:12 Asia/Hong_Kong (214s; already told by the 02:34 1h patrol) "
    f"room_stats gap 84364201..84364269 (69) has aged out of this window start 84365001 and remains official-filled 69/69 in all 5 (counts {f0221}). "
    f"Prior box freeze 01:47:00-02:03:02 Asia/Hong_Kong (961s; already told by the 02:34 1h patrol) "
    f"room_stats gap 84363701..84363949 (249) has aged out of this window start 84365001 and remains official-filled 249/249 in four rooms and 200/249 in W47N8 missing 84363901..84363949 because W47N8@84363900 stayed official 404 (counts {f0147}). "
    f"Prior box freeze 01:30:52-01:33:08 Asia/Hong_Kong (131s; already told by the 02:34 1h patrol) "
    f"room_stats gap 84363461..84363509 (49) has aged out of this window start 84365001 and remains official-filled 49/49 in all 5 (counts {f0130}). "
    f"Prior box freeze 01:14:19-01:18:28 Asia/Hong_Kong (248s; already told by the 01:26 1h patrol) and earlier freezes 00:45:20-01:01:07, 00:31:21-00:32:40, 00:13:42-00:18:42, 23:47:48-23:55:08, 23:20:04-23:24:46 and 22:55:09-23:02:20 have aged out of this window start 84365001. "
    f"In-window official 404 W45N7@84365200 (hole 84365201..84365300 still db {hole_w45n7_65200['distinct']}/100; confirm+retry2 stayed official 404; not yet told by a 1h patrol) remains unfilled. "
    f"Leftover official 404 W47N8@84363900 (hole 84363901..84363950 still db {hole_w47n8_63900['distinct']}/100 live-only 84363951..84364000; already told by the 02:34 1h patrol) aged out of this window and was not retried. "
    f"Aged official 404 W46N8@84362700, W47N8@84361700, W46N8@84360600, W45N7@84360200, W47N8@84359900, W47N8@84359500, W45N7@84358500, W47N8@84358700, W46N8@84354300, W47N7@84354300 (and older) remain outside this window. "
    f"This window empty_no_creep=258 in W45N7 (official 200; 84365042, 84365044..84365200 evac, plus 84365414..84365507 and 84365512..84365517). "
    f"live.json / stats.t were fresh at pre-check 04:09:35 (age ~3.7s, tip stats.t=84365790, roomSlot W45N7 objects_n=0 / gameTime=None mid-remote-slot after the 04:06:18 auto-reconnect, but live ingest already had W45N7 ticks 84365789..84365795 and CPU/path were flowing); "
    f"this pass inserted 12329 additional rows in 84365001..84365700, and {just_note}; "
    f"single_slot held, creep_cpu and path_arrivals flowing (creep_cpu through 84365790 / path_arrivals through 84365780 at pre-check; through {cpu_tip} / {path_tip} at wrapup); this run did not restart the listener."
)

listener_line = (
    f"listener single_slot={not yield_present} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; "
    "no second listener started; no war_cmd/pulse restart."
)
ok_line = (
    f"ok_quiet=True coverage={recovered}/{expected} inserted_window={INSERTED_WINDOW} inserted_total={INSERTED_TOTAL} "
    f"tick_s_in_use={TICK_S_IN_USE} listener single_slot={not yield_present}; no second listener; no war_cmd/pulse restart."
)

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
    listener_line,
    confirm_summary,
    ok_line,
]) + "\n"

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
    "later_mean_applied_then_reverted": False,
    "later_mean_applied_nfix": 0,
    "later_mean_reverted_nfix": 0,
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
    "tick_s_realign": tick_s,
    "just_published": just_pub_payload,
    "confirm": confirm_payload,
    "retry2": (confirm_payload.get("retry2") or {"skipped": False, "still_404": ["W45N7@84365200"]}),
    "listener": {
        "single_slot": not yield_present,
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "yield": yield_present,
        "pid": 1112279,
    },
    "box_freeze": {
        "from": "2026-11-20 03:46:06",
        "to": "2026-11-20 04:06:15",
        "sec": 1201,
        "restart_at": ["2026-11-20 04:06:18"],
        "listener_pid": 1112279,
        "listener_started": "2026-11-20 04:06:28",
        "room_stats_gap": [84365441, 84365749, 309],
        "official_fill": {r: freeze0346[r] for r in ROOMS},
        "prior_0318": {"gap": [84365001, 84365119, 119], "fill": {r: freeze0318[r] for r in ROOMS}, "told_by": "03:32 1h patrol"},
        "prior_0252": {"gap": [84364661, 84364829, 169], "fill": {r: freeze0252[r] for r in ROOMS}, "told_by": "03:32 1h patrol"},
    },
    "new_official_404_not_yet_told": ["W45N7@84365200"],
    "already_told_still_unfilled": [
        "W47N8@84363900",
        "W46N8@84362700",
        "W47N8@84361700",
        "W46N8@84360600",
        "W45N7@84360200",
        "W47N8@84359900",
    ],
    "inwin_txt": inwin_txt,
    "leftover_txt": leftover_txt,
    "freeze_para": freeze_para,
    "confirm_summary": confirm_summary,
    "listener_line": listener_line,
    "ok_line": ok_line,
    "wrapup_cpu_tip": cpu_tip,
    "wrapup_path_tip": path_tip,
    "wrapup_rs_tip": rs_tip,
    "just_pub_db": just_pub,
    "w45n7_empty_window": w45n7_empty,
}

(DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
(DIR / "history_backfill_now.txt").write_text(now_text)
shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")
shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

verify = [
    f"{finished_hkt_sec} verify 04:00 half-hour official-history backfill",
    f"window ticks {TMIN}..{TMAX} published_bases {PUB_BASES} game.time_first={GT_FIRST}",
    f"inserted_first={INSERTED_FIRST} confirm={INSERTED_CONFIRM} retry2={INSERTED_RETRY2} just_published={INSERTED_JUST} total={INSERTED_TOTAL}",
    f"coverage {recovered}/{expected} empty_no_creep={empty_no_creep} official_404={official_404_missing}",
    f"tick_s_in_use={TICK_S_IN_USE:.5f} ts_realigned_first={TS_REALIGNED_FIRST} ts_realigned_corrective={NFIX_CORR}",
    f"{inwin_txt}",
    f"{leftover_txt}",
    freeze_para,
    listener_line,
    "This run did not itself restart the listener. Last run_listener.sh auto-restart was 04:06:18 (listener.py pid 1112279 started 04:06:28) after the new box freeze 03:46:06-04:06:15 (1201s, room_stats gap 84365441..84365749). Earlier: 03:23:00 and 03:18:23 after 03:18:44-03:22:57; 03:03:16 after 02:52:31-03:03:13; 02:25:15 after 02:21:37-02:25:12; 02:03:05 after 01:47:00-02:03:02; 01:33:11 after 01:30:52-01:33:08; 01:18:31 after 01:14:19-01:18:28. This run found the listener after the auto-reconnect; by pre-check 04:09:35 live.json was fresh (stats.t=84365790, roomSlot W45N7, objects_n=0 / gameTime=None mid-remote-slot) and CPU/path buffers were flowing (creep_cpu through 84365790 / path_arrivals through 84365780); by wrapup the listener was on W46N8 with gameTime and objects; single_slot held.",
]
verify_text = "\n".join(verify) + "\n"
(DIR / "verify.txt").write_text(verify_text)
(ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
retry2_src = DIR / "backfill_retry2.txt"
if retry2_src.exists():
    shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0400.txt")
summary = (
    f"{finished_hkt} wrapup ok\n"
    "wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2}+just{INSERTED_JUST} coverage={recovered}/{expected} tick_s_in_use={TICK_S_IN_USE:.5f}\n"
)
(DIR / "wrapup_run.txt").write_text(summary)
print(summary, end="")
print("ok_line", ok_line)
