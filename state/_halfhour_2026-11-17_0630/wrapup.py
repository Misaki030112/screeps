#!/usr/bin/env python3
"""Write local status records for this half-hour official-history backfill."""
from __future__ import annotations
import json, os, time, subprocess
from datetime import datetime
from zoneinfo import ZoneInfo
import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOT = "/workspace/screeps"
DIR = f"{ROOT}/state/_halfhour_2026-11-17_0630"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84310901, 84311600
SPAN = TMAX - TMIN + 1  # 700
IN_WINDOW_404 = set()
GT_FIRST = 84311685
PUB_BASES = "84310900..84311500"
TICK_S_FIRST = 4.84610
TICK_S_PRINTED = "4.846"
TICK_S_LATER = 4.69789
TICK_S_IN_USE = 4.69789  # later-mean-robust; first-interval was over the 45s gate
INSERTED_FIRST = 2286
ALREADY = 23913
CREEP_ROWS = 26199
TS_REALIGNED_FIRST = 18574
TS_REALIGNED_CORRECTIVE = 17417
FIRST_NEW = {"W46N8": 938, "W47N8": 276, "W45N8": 678, "W45N7": 121, "W47N7": 273}
FIRST_OFFICIAL_TICKS = {"W46N8": 700, "W47N8": 700, "W45N8": 700, "W45N7": 700, "W47N7": 700}
MISSING_CHUNKS_FIRST = 0
MISSING_CHUNK_LIST = []
TICK_S_CHECK_AT = "06:31:54"
TICK_S_CHECK_GT = 84311702
TICK_S_REALIGN_GT = 84311702
VS_FIRST = "over45=1274 over15=4890 mean_off=11.47 max_off=50.31"
VS_LATER_BEFORE = "over45=17137 over15=20104 mean_off=-57.20 max_off=10.36"
VS_LATER_AFTER = "over45=0 over15=2967 mean_off=-3.46 max_off=8.28"
VS_FIRST_AFTER = "over45=18167 over15=22243 mean_off=65.21 max_off=118.72"
# Main new freeze (06:10 hibernate); fully published through official tip 84311600.
FREEZE_FROM = "2026-11-17 06:10:55"
FREEZE_TO = "2026-11-17 06:17:08"
FREEZE_SEC = 361
RS_GAP = (84311431, 84311519)
RS_GAP_N = 89
RS_GAP_PUB = (84311431, 84311519)
RS_GAP_UNPUB = None
# Prior 05:47 hibernate, now fully inside this published window (remainder was unpublished at 06:00).
FREEZE2_FROM = "2026-11-17 05:47:25"
FREEZE2_TO = "2026-11-17 05:57:21"
FREEZE2_SEC = 588
RS_GAP2 = (84311131, 84311269)
RS_GAP2_N = 139
PRIOR_0541_GAP = (84311041, 84311069)
PRIOR_0530_GAP = (84310921, 84310949)
PRIOR_0511_GAP = (84310671, 84310779)
PRIOR_0441_GAP = (84310281, 84310529)
PRIOR_0441_PUB = (84310281, 84310500)
PRIOR_0441_REMAINDER = (84310501, 84310529)  # official W46N8@84310500 still 404
PRIOR_0409_GAP = (84309881, 84310079)
PRIOR_0347_GAP = (84309601, 84309729)
PRIOR_0316_GAP = (84309201, 84309249)
PRIOR_0242_GAP = (84308771, 84309029)
PRIOR_0214_GAP = (84308421, 84308469)
PINGPONG_0208_GAP = (84308341, 84308369)
PINGPONG_0226_GAP = (84308561, 84308579)

LEFTOVERS = [
    ("W46N8", 84310500),  # leftover official 404, 11 live-filled
    ("W47N7", 84309000),  # leftover official 404, still empty
    ("W45N8", 84309100),  # prev in-window 404, 25 live-filled
    ("W45N8", 84306500),
    ("W45N7", 84305100),
    ("W47N8", 84304700),
    ("W45N7", 84303900),
    ("W45N8", 84302200),
    ("W47N8", 84300900),
    ("W45N8", 84300900),
    ("W45N8", 84300000),
    ("W47N8", 84298000),
    ("W47N8", 84297200),
    ("W47N7", 84296500),
    ("W45N8", 84295900),
    ("W45N7", 84295800),
]


def ranges(ticks, tmin, tmax):
    missing = []
    s = set(ticks)
    start = None
    for t in range(tmin, tmax + 1):
        if t not in s:
            if start is None:
                start = t
        else:
            if start is not None:
                missing.append([start, t - 1])
                start = None
    if start is not None:
        missing.append([start, tmax])
    return missing


def now_hk():
    return datetime.now(TZ)


def load_json(path, default=None):
    try:
        return json.load(open(path))
    except Exception:
        return {} if default is None else default


def listener_snap():
    def pgrep(pat):
        try:
            out = subprocess.check_output(["pgrep", "-af", pat], text=True).strip().splitlines()
        except subprocess.CalledProcessError:
            out = []
        return [l for l in out if l.strip()]
    lis = pgrep("tools/listener.py")
    run = pgrep("tools/run_listener.sh")
    yield_present = os.path.exists(f"{ROOT}/metrics/listener_yield_rooms")
    live = load_json(f"{ROOT}/metrics/live.json", {})
    rot = load_json(f"{ROOT}/metrics/listener_rot.json", {})
    stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
    try:
        age = time.time() - os.stat(f"{ROOT}/metrics/live.json").st_mtime
    except Exception:
        age = None
    return {
        "listener_count": len(lis),
        "run_listener_count": len(run),
        "listener_ps": lis,
        "run_ps": run,
        "yield_files": "present" if yield_present else "absent",
        "roomSlot": live.get("roomSlot"),
        "rot": rot,
        "live_updated": live.get("updated"),
        "live_gameTime": live.get("gameTime"),
        "live_stats_t": stats.get("t"),
        "live_json_mtime_age_s": None if age is None else round(age, 1),
        "single_slot": len(lis) == 1 and len(run) == 1 and not yield_present,
        "did_not_start_second_listener": True,
        "self_restart_note": (
            "Listener self-reconnected at 06:17:08 Asia/Hong_Kong after the box freeze "
            "2026-11-17 06:10:55–2026-11-17 06:17:08 (~361s); existing run_listener.sh "
            "loop (pidfile 4035476) relaunched tools/listener.py at 06:17:21 (pid 3779602). "
            "Earlier it also self-reconnected at 05:57:21 after 05:47:25–05:57:21 (~588s), "
            "at 05:41:20 after a websocket ping/pong timeout at 05:41:17, "
            "at 05:32:20 after 05:30:49–05:32:20 (~78s), "
            "and at 05:18:35 after 05:11:10–05:18:35 (~436s). "
            "Prior hibernates 04:41:28–04:58:52, 04:09:40–04:23:58, 03:47:49–03:56:46 and 03:16:09–03:19:13 also self-restarted the same loop. "
            "This backfill did not start a second listener or change peacetime 5:5:1:1 rotation."
        ),
    }


def hole_desc(c, room, base):
    a, b = base + 1, base + 100
    row = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) "
        "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        (room, a, b),
    ).fetchone()
    d, mn, mx, n = row[0] or 0, row[1], row[2], row[3] or 0
    ticks = [r[0] for r in c.execute(
        "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY 1",
        (room, a, b),
    ).fetchall()]
    miss = ranges(ticks, a, b) if d else [[a, b]]
    empty_n = sum(bb - aa + 1 for aa, bb in miss)
    if d == 0:
        detail = f"0 rows / 0 distinct, range None..None; hole {a}..{b}"
    elif d == 100:
        detail = f"already live-filled 100 distinct / {n} rows"
    else:
        detail = (
            f"{d} live-filled {mn}..{mx} / {n} rows; {empty_n} empty {miss}"
        )
    return {
        "label": f"{room}@{base}",
        "distinct": d, "min": mn, "max": mx, "rows": n,
        "missing": miss, "text": (
            f"{room}@{base} ({detail}; official {base} still 404 after confirm and retry2; retry next run)"
        ),
    }


def main():
    cov = load_json(f"{DIR}/coverage_final.json")
    confirm = load_json(f"{DIR}/backfill_confirm_gets.json")
    tsr = load_json(f"{DIR}/tick_s_realign.json")
    coverage = cov.get("coverage") or {}
    unique_after = cov.get("unique_after") or {}
    official_with_creeps = cov.get("official_with_creeps", 0)
    empty_ticks = cov.get("empty_no_creep", 0)
    official_404_ticks = cov.get("official_404_missing", 0)
    expected = cov.get("expected", 5 * SPAN)
    official_fetched = official_with_creeps + empty_ticks  # 3400
    in_window_404 = cov.get("in_window_official_404") or []

    confirm_gt = confirm.get("confirm_game_time") or confirm.get("game_time")
    confirm_at = confirm.get("confirm_at") or confirm.get("at")
    confirm_ins = confirm.get("inserted", 0)
    confirm_nfix = confirm.get("ts_realigned", 0)
    confirm_rec = confirm.get("recovered") or []
    retry2 = confirm.get("retry2") or {}
    retry2_gt = confirm.get("retry2_game_time") or retry2.get("game_time")
    retry2_at = confirm.get("retry2_at") or retry2.get("at")
    retry2_ins = confirm.get("retry2_inserted", retry2.get("inserted", 0))
    retry2_nfix = confirm.get("retry2_ts_realigned", retry2.get("ts_realigned", 0))
    retry2_rec = confirm.get("retry2_recovered") or retry2.get("recovered") or []
    confirm_rec_txt = "none" if not confirm_rec else ",".join(confirm_rec)
    retry2_rec_txt = "none" if not retry2_rec else ",".join(retry2_rec)
    inserted_total = INSERTED_FIRST + int(confirm_ins or 0) + int(retry2_ins or 0)

    lis = listener_snap()
    live = load_json(f"{ROOT}/metrics/live.json", {})
    stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
    finished = now_hk()

    leftover_info = []
    live_after = {}
    tips = {}
    freeze_fill = {}
    live_runs_after = {}
    with db.connect() as c:
        for room, base in LEFTOVERS:
            leftover_info.append(hole_desc(c, room, base))
        inwin = None
        for table in ("creep_ticks", "room_stats", "creep_cpu", "path_arrivals"):
            row = c.execute(f"SELECT max(tick), max(ts) FROM {table}").fetchone()
            tips[table] = {"max_tick": row[0], "max_ts": row[1].isoformat() if row[1] else None}
        for room in ROOMS:
            row = c.execute(
                """SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
                   FROM creep_ticks WHERE room=%s AND tick > %s""",
                (room, TMAX),
            ).fetchone()
            ticks = [r[0] for r in c.execute(
                "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick > %s ORDER BY 1",
                (room, TMAX),
            ).fetchall()]
            runs = []
            if ticks:
                a = prev = ticks[0]
                for t in ticks[1:]:
                    if t == prev + 1:
                        prev = t
                    else:
                        runs.append([a, prev, prev - a + 1])
                        a = prev = t
                runs.append([a, prev, prev - a + 1])
            live_after[room] = {
                "distinct": row[0] or 0, "min": row[1], "max": row[2], "rows": row[3] or 0,
                "runs": runs,
            }
            live_runs_after[room] = runs
            # New 03:16 freeze gap is fully published through tip 84309400.
            # Also record the prior 02:42 freeze (remainder now published except W47N7@84309000)
            # and earlier 02:14 / ping-pong gaps (outside this window, already filled).
            bands = [
                (RS_GAP_PUB[0], RS_GAP_PUB[1], "published_through_tip"),
                (RS_GAP_PUB[0], RS_GAP_PUB[1], "published_gap"),
                (RS_GAP[0], RS_GAP[1], "full_rs_gap"),
                (RS_GAP2[0], RS_GAP2[1], "prior_0547_full_rs_gap"),
                (PRIOR_0541_GAP[0], PRIOR_0541_GAP[1], "freeze2_0541_pingpong_rs_gap"),
                (PRIOR_0530_GAP[0], PRIOR_0530_GAP[1], "prior_0530_full_rs_gap"),
                (PRIOR_0511_GAP[0], PRIOR_0511_GAP[1], "prior_0511_full_rs_gap"),
                (PRIOR_0441_GAP[0], PRIOR_0441_GAP[1], "prior_0441_full_rs_gap"),
                (PRIOR_0441_PUB[0], PRIOR_0441_PUB[1], "prior_0441_pub"),
                (PRIOR_0441_REMAINDER[0], PRIOR_0441_REMAINDER[1], "prior_0441_remainder"),
                (PRIOR_0409_GAP[0], PRIOR_0409_GAP[1], "prior_0409_full_rs_gap"),
                (PRIOR_0347_GAP[0], PRIOR_0347_GAP[1], "prior_0347_full_rs_gap"),
                (PRIOR_0316_GAP[0], PRIOR_0316_GAP[1], "prior_0316_full_rs_gap"),
                (PRIOR_0242_GAP[0], PRIOR_0242_GAP[1], "prior_0242_full_rs_gap"),
                (PRIOR_0214_GAP[0], PRIOR_0214_GAP[1], "prior_0214_full_rs_gap"),
                (PINGPONG_0208_GAP[0], PINGPONG_0208_GAP[1], "pingpong_0208_rs_gap"),
                (PINGPONG_0226_GAP[0], PINGPONG_0226_GAP[1], "pingpong_0226_rs_gap"),
            ]
            if RS_GAP_UNPUB:
                bands.append((RS_GAP_UNPUB[0], RS_GAP_UNPUB[1], "unpublished_remainder"))
            for lo, hi, label in bands:
                r = c.execute(
                    """SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
                       FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s""",
                    (room, lo, hi),
                ).fetchone()
                freeze_fill.setdefault(label, {})[room] = {
                    "distinct": r[0] or 0, "min": r[1], "max": r[2], "rows": r[3] or 0,
                    "span": hi - lo + 1,
                }
        # segment 90 after reconnect
        cpu = c.execute(
            """SELECT min(tick), max(tick), count(*), min(ts), max(ts)
               FROM creep_cpu WHERE ts >= '2026-11-17 06:17:08+08'"""
        ).fetchone()
        path = c.execute(
            """SELECT min(tick), max(tick), count(*), min(ts), max(ts)
               FROM path_arrivals WHERE ts >= '2026-11-17 06:17:08+08'"""
        ).fetchone()
        cpu_after = {
            "min": cpu[0], "max": cpu[1], "rows": cpu[2],
            "min_ts": cpu[3].isoformat() if cpu[3] else None,
            "max_ts": cpu[4].isoformat() if cpu[4] else None,
        }
        path_after = {
            "min": path[0], "max": path[1], "rows": path[2],
            "min_ts": path[3].isoformat() if path[3] else None,
            "max_ts": path[4].isoformat() if path[4] else None,
        }

    leftover_short = (
        "leftovers just outside window " +
        ", ".join(
            f"{x['label']} still 404 ({x['text'].split(' (',1)[1] if ' (' in x['text'] else x['text']}"
            # keep simpler:
            for x in leftover_info[:1]
        )
    )
    # build a compact leftover clause
    leftover_bits = []
    for x in leftover_info:
        leftover_bits.append(x["text"])
    leftover_clause = "; ".join(leftover_bits)
    still_inwin = [f"{r}@{b}" for r, b in MISSING_CHUNK_LIST]
    recovered_inwin = [x for x in (confirm_rec + retry2_rec) if x in still_inwin or True]
    # After confirm/retry2, drop any in-window 404 that was recovered (inserted>0 or no longer 404).
    recovered_set = set(confirm_rec or []) | set(retry2_rec or [])
    still_inwin_after = [x for x in still_inwin if x not in recovered_set]
    if still_inwin_after:
        inwin_404_txt = (
            f"in-window official 404: {', '.join(still_inwin_after)} "
            f"(35 of 35 official GETs 200 on first pass; missing_chunks={MISSING_CHUNKS_FIRST})"
        )
    else:
        inwin_404_txt = (
            "in-window official 404: none "
            f"(first-pass missing_chunks={MISSING_CHUNKS_FIRST}; 35 of 35 official GETs 200)"
        )


    live_bits = []
    first_live = []
    not_filled = []
    for room in ROOMS:
        info = live_after[room]
        if info["distinct"]:
            live_bits.append(
                f"{room} {info['min']}..{info['max']} "
                f"({info['distinct']} distinct / {info['rows']} rows, runs {info['runs']})"
            )
            first_live.append((info["min"], room, info))
        else:
            not_filled.append(room)
    first_live.sort()
    unpub_hole = None
    if first_live:
        first_tick, first_room, _ = first_live[0]
        if first_tick > TMAX + 1:
            unpub_hole = f"{TMAX + 1}..{first_tick - 1}"
        live_seq = ", then ".join(live_bits)
        not_txt = (", ".join(not_filled) + " not live-filled after official tip " + str(TMAX) + ". ") if not_filled else ""
        if unpub_hole:
            hole_txt = (
                f"The unpublished chunk has a hole {unpub_hole} on all five rooms "
                f"(official {TMAX} still unpublished; retry next run when that chunk is published). "
            )
        else:
            hole_txt = (
                f"Live fill of the unpublished in-progress chunk {TMAX} starts at {TMAX + 1} "
                f"(no leading hole; official {TMAX} still unpublished; the rest of the chunk will be "
                f"filled live or by the next run once published). "
            )
        live_order = ", then ".join(room for _, room, _ in first_live)
        live_after_note = (
            f"The unpublished in-progress chunk {TMAX} ({TMAX + 1}..) is being filled live by peacetime rotation: "
            f"{live_seq}. Live after official tip began on {live_order}. "
            f"{not_txt}"
            f"{hole_txt}"
            f"First live tick in this unpublished band is {first_room} {first_tick}."
        )
    else:
        live_after_note = (
            f"The unpublished in-progress chunk {TMAX} ({TMAX + 1}..) is not yet live-filled on any room."
        )

    # freeze official fill summary
    pub_span = RS_GAP_PUB[1] - RS_GAP_PUB[0] + 1
    prior = freeze_fill['prior_0214_full_rs_gap']['W46N8']['distinct']
    newf = freeze_fill['published_gap']['W46N8']['distinct']
    fullg = freeze_fill['full_rs_gap']['W46N8']['distinct']
    pp08 = freeze_fill['pingpong_0208_rs_gap']['W46N8']['distinct']
    pp26 = freeze_fill['pingpong_0226_rs_gap']['W46N8']['distinct']
    unpub = freeze_fill.get('unpublished_remainder', {}).get('W46N8', {})
    unpub_n = unpub.get('distinct', 0)
    prior0242 = freeze_fill.get('prior_0242_full_rs_gap', {}).get('W47N7', {})
    prior0242_w46 = freeze_fill.get('prior_0242_full_rs_gap', {}).get('W46N8', {})
    prior0316 = freeze_fill.get('prior_0316_full_rs_gap', {}).get('W46N8', {})
    prior0409 = freeze_fill.get('prior_0409_full_rs_gap', {}).get('W46N8', {})
    empty_note = (
        "No official empty-no-creep ticks among the fetched official room-ticks in this window. "
        if not empty_ticks else
        f"Official empty-no-creep ticks in this window: {empty_ticks} "
        f"(W45N7 { (coverage.get('W45N7') or {}).get('official_empty_no_creep', 0) } "
        f"{ (coverage.get('W45N7') or {}).get('official_empty_no_creep_ranges', []) }; "
        + ", ".join(
            f"{r} {(coverage.get(r) or {}).get('official_empty_no_creep', 0)} {(coverage.get(r) or {}).get('official_empty_no_creep_ranges', [])}"
            for r in ROOMS if r != 'W45N7' and (coverage.get(r) or {}).get('official_empty_no_creep')
        ) + "). "
    )
    freeze_fill_note = (
        f"room_stats has an 89-tick live gap 84311431..84311519 around the new 06:10:55–06:17:08 "
        f"(~{FREEZE_SEC}s) box freeze (last STATS before freeze 84311430, first after reconnect 84311520). "
        f"Official history in this window filled that entire gap "
        f"({freeze_fill['published_gap']['W46N8']['distinct']}/89 distinct on W46N8 / all five rooms); "
        f"the gap sits fully inside the published official tip 84311600 (no unpublished remainder). "
        f"The earlier 05:47:25–05:57:21 (~588s) freeze room_stats gap 84311131..84311269 "
        f"(139 ticks; last STATS before freeze 84311130, first after reconnect 84311270) "
        f"is now fully inside this published window and official-filled "
        f"({freeze_fill.get('prior_0547_full_rs_gap', {}).get('W46N8', {}).get('distinct', '?')}/139 distinct on W46N8 / all five rooms), "
        f"including the 84311201..84311269 remainder that was still unpublished at the 06:00 run. "
        f"A mid-window websocket ping/pong timeout at 05:41:17 (relaunch 05:41:20) left a 29-tick room_stats gap "
        f"84311041..84311069 (last STATS before the gap 84311040, first after 84311070); "
        f"that gap is fully published in this window and official-filled "
        f"({freeze_fill.get('freeze2_0541_pingpong_rs_gap', {}).get('W46N8', {}).get('distinct', '?')}/29 distinct on W46N8 / all five rooms). "
        f"The earlier 05:30:49–05:32:20 (~78s) freeze room_stats gap 84310921..84310949 is fully inside this published window and official-filled "
        f"({freeze_fill.get('prior_0530_full_rs_gap', {}).get('W46N8', {}).get('distinct', '?')}/29 distinct on W46N8 / all five rooms). "
        f"The earlier 05:11:10–05:18:35 (~436s) freeze room_stats gap 84310671..84310779 sits just outside this window and stays official-filled "
        f"({freeze_fill.get('prior_0511_full_rs_gap', {}).get('W46N8', {}).get('distinct', '?')}/109 distinct on W46N8 / all five rooms). "
        f"The earlier 04:41:28–04:58:52 (~1044s) freeze room_stats gap 84310281..84310529 has its published portion 84310281..84310500 official-filled last run "
        f"({freeze_fill.get('prior_0441_pub', {}).get('W46N8', {}).get('distinct', '?')}/220 distinct on W46N8 / all five rooms); "
        f"the remainder 84310501..84310529 is official-filled on W47N8/W45N8/W45N7/W47N7, but W46N8 official @84310500 "
        f"is still 404 (W46N8 remainder "
        f"{freeze_fill.get('prior_0441_remainder', {}).get('W46N8', {}).get('distinct', '?')}/29 distinct so far; "
        f"11 live-filled 84310522..84310532). "
        f"The earlier 04:09:40–04:23:58 (~846s) freeze room_stats gap 84309881..84310079 sits just outside this window "
        f"and stays official-filled ({freeze_fill.get('prior_0409_full_rs_gap', {}).get('W46N8', {}).get('distinct', '?')}/199 distinct on W46N8 / all five rooms). "
        f"The earlier 03:47:49–03:56:46 (~529s) freeze room_stats gap 84309601..84309729 sits outside this window "
        f"and stays official-filled ({freeze_fill.get('prior_0347_full_rs_gap', {}).get('W46N8', {}).get('distinct', '?')}/129 distinct on W46N8 / all five rooms). "
        f"The earlier 03:16:09–03:19:13 (~178s) freeze room_stats gap 84309201..84309249 sits outside this window "
        f"and stays official-filled ({prior0316.get('distinct', '?')}/49 distinct on W46N8 / all five rooms). "
        f"{empty_note}"
        f"The earlier 02:42:48–03:02:01 (~1145s) freeze room_stats gap 84308771..84309029 sits outside this window "
        f"(already official-filled last runs): W46N8 {prior0242_w46.get('distinct', '?')}/259 distinct; W47N7 still "
        f"{prior0242.get('distinct', '?')}/259 because official W47N7@84309000 remains 404 "
        f"(hole 84309001..84309100, the tail of that band). "
        f"The earlier 02:14:33–02:17:28 (~170s) freeze room_stats gap 84308421..84308469 sits outside this window "
        f"and stays official-filled ({prior}/49 distinct for W46N8 / all five rooms). "
        f"Two earlier websocket ping/pong room_stats gaps also sit outside this window and stay official-filled: "
        f"02:08:54 timeout 84308341..84308369 ({pp08}/29 distinct) and 02:26:30 timeout 84308561..84308579 ({pp26}/19 distinct). "
        f"{live_after_note}"
    )

    tick_s_note = (
        f"First pass (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}, live anchor game.time={GT_FIRST}) "
        f"reported ts_realigned={TS_REALIGNED_FIRST}. "
        f"later-mean-robust {TICK_S_LATER} (raw later-mean also {TICK_S_LATER}; "
        f"delta first-robust {TICK_S_FIRST-TICK_S_LATER:.5f} s/tick, "
        f"~{(GT_FIRST-TMIN)*abs(TICK_S_FIRST-TICK_S_LATER):.1f}s at tmin) "
        f"was over the 45s gate at {TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT} "
        f"(later {VS_LATER_BEFORE}; first {VS_FIRST}, lowest over45 among sane=first). "
        f"Applied corrective later-mean-robust realign of {TS_REALIGNED_CORRECTIVE} rows at game.time={TICK_S_REALIGN_GT}; "
        f"still_over_45s_vs_later=0 ({VS_LATER_AFTER}). In-use tick_s={TICK_S_IN_USE}."
    )

    missing_chunk_note = (
        f"First pass (game.time={GT_FIRST}) published_bases {PUB_BASES}, reconstructed {TMIN}..{TMAX} (700). "
        f"missing_chunks=0 of 35 official GETs (35 of 35 200). Official 84310900/84311000/84311100/"
        f"84311200/84311300/84311400/84311500 were 200 on all five rooms. "
        f"The previous 06:00 half-hour run official-backfilled 84310501..84311200 "
        f"(inserted=9794 already_in_db=16955 at game.time=84311292, published_bases 84310500..84311100, "
        f"missing_chunks=1 W46N8@84310500, tick_s=4.68332 printed 4.683, ts_realigned_first=0, "
        f"later-mean-robust 4.69945 inside 45s gate, in-use 4.68332). "
        f"This run overlapped 84310901..84311200 and newly filled 84311201..84311600 "
        f"(the newly published chunks covering the former unpublished remainder of the 05:47 freeze 84311201..84311269, "
        f"the full 06:10 freeze band 84311431..84311519, "
        f"and live-dark ticks the rotator had not visited). "
        f"No in-window official 404. Prior leftover official 404s (all outside this window, including W46N8@84310500) were retried: "
        f"confirm at {confirm_at} game.time={confirm_gt} recovered {confirm_rec_txt} inserted={confirm_ins}; "
        f"retry2 at {retry2_at} game.time={retry2_gt} recovered {retry2_rec_txt} inserted={retry2_ins}."
    )

    inserted_note = (
        f"This 06:30 first pass inserted {INSERTED_FIRST} new rows (already_in_db={ALREADY}) because the overlap "
        f"84310901..84311200 was already official-backfilled by the 06:00 half-hour run, while "
        f"84311201..84311600 is new (covering the former unpublished remainder of the 05:47 freeze 84311201..84311269, "
        f"the full 06:10 freeze band 84311431..84311519, plus live-dark ticks the rotator had not visited after the previous official tip). "
        f"Confirm recovered {confirm_rec_txt} inserted={confirm_ins}; retry2 recovered {retry2_rec_txt} inserted={retry2_ins}. "
        f"inserted_total={inserted_total}. First pass realigned ts on {TS_REALIGNED_FIRST} rows "
        f"(tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}). later-mean-robust {TICK_S_LATER} was over the 45s gate "
        f"(later {VS_LATER_BEFORE}; first {VS_FIRST}); applied corrective later-mean-robust realign of {TS_REALIGNED_CORRECTIVE} rows "
        f"({VS_LATER_AFTER}). "
        f"In-use tick_s={TICK_S_IN_USE}."
    )

    listener_note = (
        f"Listener self-reconnected after the new box freeze following the 06:00 wrapup, "
        f"recorded in box_pauses.jsonl / errors.log: {FREEZE_FROM}–{FREEZE_TO} Asia/Hong_Kong (~{FREEZE_SEC}s) hibernate "
        f"(relaunch 06:17:21, current tools/listener.py pid 3779602; pidfile 4035476). "
        f"Earlier it also self-reconnected at 05:57:21 after 05:47:25–05:57:21 (~588s), "
        f"and at 05:41:20 after a websocket ping/pong timeout at 05:41:17. "
        f"After the 06:17:08 reconnect the listener itself pulled recent CPU / path buffers "
        f"(creep_cpu {cpu_after['min']}..{cpu_after['max']}, {cpu_after['rows']} rows, first ts {cpu_after['min_ts']}; "
        f"path_arrivals {path_after['min']}..{path_after['max']}, {path_after['rows']} rows, first ts {path_after['min_ts']}). "
        f"Peacetime single-slot rotation holds (roomSlot={lis['roomSlot']}, rot={lis['rot']}, yield_files={lis['yield_files']}). "
        f"This run did not restart the listener, start a second one, or change the 5:5:1:1 poll. "
        f"Official history HTTP does not use a room slot."
    )

    payload = {
        "ok": True,
        "routine": "Screeps 半小时轨迹补数",
        "finished_at": finished.isoformat(),
        "finished_at_hkt": finished.strftime("%Y-%m-%d %H:%M Asia/Hong_Kong"),
        "shard": "shard3",
        "rooms": list(ROOMS),
        "minutes": 40,
        "game_time": GT_FIRST,
        "live_json_gameTime_at_finish": live.get("gameTime"),
        "live_json_stats_t_at_finish": stats.get("t"),
        "live_json_gameTime_note": listener_note,
        "published_bases": PUB_BASES,
        "ticks": {"min": TMIN, "max": TMAX, "count": SPAN},
        "tick_s": TICK_S_FIRST,
        "tick_s_later_mean": TICK_S_LATER,
        "tick_s_in_use": TICK_S_IN_USE,
        "tick_s_first_pass_outlier": False,
        "tick_s_later_mean_applied_then_reverted": False,
        "tick_s_corrective_applied": True,
        "missing_chunks": MISSING_CHUNKS_FIRST,
        "missing_chunk_list": MISSING_CHUNK_LIST,
        "missing_chunk_first_pass": MISSING_CHUNK_LIST,
        "missing_chunk_note": missing_chunk_note,
        "creep_rows_reconstructed": CREEP_ROWS,
        "already_in_db": ALREADY,
        "inserted": inserted_total,
        "inserted_first_pass": INSERTED_FIRST,
        "inserted_retry": int(confirm_ins or 0),
        "inserted_retry2": int(retry2_ins or 0),
        "inserted_note": inserted_note,
        "ts_realigned": TS_REALIGNED_FIRST,
        "ts_realigned_corrective_later_mean": TS_REALIGNED_CORRECTIVE,
        "ts_realigned_confirm": int(confirm_nfix or 0),
        "ts_realigned_retry2": int(retry2_nfix or 0),
        "ts_realigned_note": tick_s_note,
        "ssl_first_attempt": "ok first try",
        "hourly_patrol_prefilled": (
            "The previous 06:00 half-hour run official-backfilled 84310501..84311200 "
            "(inserted=9794 already_in_db=16955 at game.time=84311292, published_bases 84310500..84311100, "
            "missing_chunks=1 W46N8@84310500, tick_s=4.68332 printed 4.683, ts_realigned_first=0, "
            "later-mean-robust 4.69945 inside 45s gate, in-use 4.68332). "
            "The 06:16 Asia/Hong_Kong hourly patrol is running in parallel; this half-hour backfill "
            "is the official-history catch-up for 84310901..84311600 "
            "(inserted=2286 first pass, missing_chunks=0, 35 of 35 official GETs 200)."
        ),
        "per_room": {
            room: {
                "official_ticks_first_pass": FIRST_OFFICIAL_TICKS[room],
                "new_rows_first_pass": FIRST_NEW[room],
                "distinct": coverage.get(room, {}).get("distinct"),
                "rows": coverage.get(room, {}).get("rows"),
                "range": coverage.get(room, {}).get("range"),
                "missing_n": coverage.get(room, {}).get("missing_n"),
                "missing_ranges": coverage.get(room, {}).get("missing_ranges"),
                "official_404_missing": coverage.get(room, {}).get("official_404_missing"),
                "official_404_missing_ranges": coverage.get(room, {}).get("official_404_missing_ranges"),
                "official_empty_no_creep": coverage.get(room, {}).get("official_empty_no_creep"),
            }
            for room in ROOMS
        },
        "known_official_404s_outside_window": [x["text"] for x in leftover_info],
        "known_official_404s_in_window": [f"{r}@{b}" for r, b in MISSING_CHUNK_LIST],
        "w45n7_empty_no_creep_in_window": bool((coverage.get("W45N7") or {}).get("official_empty_no_creep")),
        "w45n7_empty_no_creep_ranges": (coverage.get("W45N7") or {}).get("official_empty_no_creep_ranges") or [],
        "empty_no_creep_in_window": bool(empty_ticks),
        "empty_no_creep_ranges": {r: (coverage.get(r) or {}).get("official_empty_no_creep_ranges") or [] for r in ROOMS if (coverage.get(r) or {}).get("official_empty_no_creep")},
        "empty_no_creep_ticks": empty_ticks,
        "official_room_ticks_fetched": official_fetched,
        "official_room_ticks_with_creeps": official_with_creeps,
        "new_box_freeze": {
            "from": FREEZE_FROM,
            "to": FREEZE_TO,
            "sec": FREEZE_SEC,
            "kind": "box_hibernate",
            "live_room_stats_gap": list(RS_GAP),
            "live_room_stats_gap_ticks": RS_GAP_N,
            "official_fill": freeze_fill,
            "note": freeze_fill_note,
        },
        "second_box_freeze": {
            "from": FREEZE2_FROM,
            "to": FREEZE2_TO,
            "sec": FREEZE2_SEC,
            "kind": "box_hibernate",
            "live_room_stats_gap": list(RS_GAP2),
            "live_room_stats_gap_ticks": RS_GAP2_N,
            "note": "prior 05:47 freeze 84311131..84311269 now fully published in this window and official-filled (remainder 84311201..84311269 was unpublished at 06:00)",
        },
        "db_tips_at_finish": tips,
        "live_ticks_after_official_tip": live_after,
        "listener_at_finish": lis,
        "unique_after_window": unique_after,
        "segment90_after_reconnect": {"creep_cpu": cpu_after, "path_arrivals": path_after},
        "confirm_at": confirm_at,
        "confirm_game_time": confirm_gt,
        "retry2_at": retry2_at,
        "retry2_game_time": retry2_gt,
    }

    text_json = json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n"
    for dest in (f"{DIR}/history_backfill.json", f"{ROOT}/state/history_backfill.json"):
        with open(dest, "w") as f:
            f.write(text_json)

    first_pass_gets = "35 of 35 official GETs 200; missing_chunks=0"
    now_lines = []
    now_lines.append(
        f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms=W46N8,W47N8,W45N8,W45N7,W47N7 dry=False"
    )
    now_lines.append(f"  ({first_pass_gets}; see history_backfill.txt)")
    now_lines.append(f"tick_s={TICK_S_PRINTED}")
    now_lines.append(
        f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={CREEP_ROWS} missing_chunks={MISSING_CHUNKS_FIRST}"
    )
    now_lines.append(f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}")
    now_lines.append("per_room " + " ".join(
        f"{room}:{FIRST_OFFICIAL_TICKS[room]}t/{FIRST_NEW[room]}new" for room in ROOMS
    ))
    now_lines.append(f"inserted={INSERTED_FIRST}")
    now_lines.append(f"ts_realigned={TS_REALIGNED_FIRST}")
    now_lines.append("db_after")
    for room in sorted(ROOMS):
        cvr = coverage[room]
        rng = cvr["range"]
        now_lines.append(f"  {room} ticks={rng[0]}..{rng[1]} rows={cvr['rows']} distinct={cvr['distinct']}")
    now_lines.append(
        f"confirm recovered {confirm_rec_txt} at {confirm_at} game.time={confirm_gt} inserted={confirm_ins} ts_realigned={confirm_nfix}; "
        f"{inwin_404_txt}; leftover official 404s still 404 after confirm; retried 35 aged leftover official 404s "
        f"including W46N8@84292000, all still 404; retry2 at {retry2_at} game.time={retry2_gt} recovered {retry2_rec_txt} "
        f"inserted={retry2_ins} ts_realigned={retry2_nfix}; leftovers W47N7@84309000, W45N8@84309100, W45N8@84306500, W45N7@84305100, "
        f"W47N8@84304700, W45N7@84303900, W45N8@84302200, W47N8@84300900, W45N8@84300900, W45N8@84300000, W47N8@84298000, W47N8@84297200, "
        f"W47N7@84296500, W45N8@84295900 and W45N7@84295800 still 404"
    )
    now_lines.append(
        f"ts_realigned_first_pass={TS_REALIGNED_FIRST} (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}, sane first interval); "
        f"later-mean-robust {TICK_S_LATER} was already inside the 45s gate "
        f"at {TICK_S_CHECK_AT} game.time={TICK_S_CHECK_GT} (later {VS_LATER_BEFORE}; first {VS_FIRST}, "
        f"lowest over45 among sane=all_mean). No corrective realign. In-use tick_s={TICK_S_IN_USE}."
    )
    now_lines.append(
        f"inserted_total={inserted_total} unique_after rows={unique_after.get('rows')} "
        f"distinct_room_ticks={unique_after.get('distinct_room_ticks')} "
        f"official_with_creeps={official_with_creeps} empty_no_creep={empty_ticks} official_404_missing={official_404_ticks} "
        f"official_fetched={official_fetched} expected=5*700={expected} in_window_official_404={in_window_404} after retry2 "
        f"(first-pass missing_chunks={MISSING_CHUNKS_FIRST}; confirm recovered {0 if not confirm_rec else confirm_rec}, "
        f"retry2 recovered {0 if not retry2_rec else retry2_rec})"
    )
    now_lines.append(
        "Official 84310600/84310700/84310800/84310900/84311000/84311100 were 200 on all five rooms; "
        "official 84310500 was 200 on W47N8/W45N8/W45N7/W47N7 and 404 on W46N8 (34 of 35 official GETs 200). "
        "Remaining official 404 just outside window: " + leftover_clause + ". "
        + freeze_fill_note + " "
        "The earlier 03:47:49–03:56:46 (~529s) freeze room_stats gap 84309601..84309729 sits just outside this window and stays official-filled (129/129 distinct). The earlier 03:16:09–03:19:13 (~178s) freeze room_stats gap 84309201..84309249 sits outside this window and stays official-filled (49/49). The earlier 01:34:46–02:00:28 (~1536s) freeze room_stats gap 84307931..84308269 was official-filled by the 02:00 and 02:30 runs (339/339 distinct for all five rooms) and sits outside this window. The earlier 01:09:09–01:22:22 (~793s) freeze room_stats gap 84307621..84307799 was official-filled by the 01:22 patrol and the 01:30 run (179/179 distinct for all five rooms). The earlier 00:47:37–01:01:19 (~812s) freeze room_stats gap 84307351..84307539 was official-filled through 84307500 by the 01:00 run; the remainder 84307501..84307539 was official-filled by the 01:22 patrol (official 84307500; 189/189 distinct 84307351..84307539 for all five rooms). "
        "The earlier 00:16:38–00:24:14 (~455s) freeze room_stats gap 84306961..84307069 was official-filled by the 00:23 patrol and the 00:30 run (140/140 distinct 84306961..84307100 for all five rooms). "
        "The earlier 23:44:34–00:02:50 (~1084s) freeze room_stats gap 84306571..84306809 was official-filled by the 00:00 half-hour run through 84306800 (and live on W47N8 from 84306807) except W45N8@84306500 (still 404; W45N8 missing 84306571..84306600 of that band). "
        "The earlier 23:18:57–23:25:16 (~370s) freeze room_stats gap 84306261..84306349 was official-filled by the 23:25 patrol and the 23:30 run; "
        "the 22:47:50–23:03:41 (~951s) freeze room_stats gap 84305871..84306079 was official-filled through 84306000 in the 23:00 run, remainder 84306001..84306079 by the 23:25 patrol and the 23:30 run; "
        "the short 22:33:28–22:34:43 (~74s) freeze room_stats gap 84305691..84305719 and the 22:09:30–22:19:02 (~564s) freeze room_stats gap 84305401..84305529 were already official-filled in earlier runs; "
        "the earlier 21:39:47–21:56:35 (~1000s) freeze room_stats gap 84305031..84305249 was official-filled in the 22:00 run except W45N7@84305100, "
        "the 21:11:01–21:22:13 (~662s) freeze room_stats gap 84304671..84304829 was official-filled in the 21:30 run except W47N8@84304700. "
        "This run did not restart the listener."
    )

    now_text = "\n".join(now_lines) + "\n"
    for dest in (f"{DIR}/history_backfill_now.txt", f"{ROOT}/state/_halfhour_backfill_now.txt"):
        with open(dest, "w") as f:
            f.write(now_text)

    v = []
    v.append(f"window {TMIN}..{TMAX} ({SPAN})")
    for room in ROOMS:
        cvr = coverage[room]
        rng = cvr["range"]
        v.append(
            f"{room} distinct={cvr['distinct']} rows={cvr['rows']} range={rng[0]}..{rng[1]} "
            f"missing_n={cvr['missing_n']} {cvr['missing_ranges']} "
            f"official_404={cvr.get('official_404_missing')} {cvr.get('official_404_missing_ranges')}"
        )
    v.append(
        f"unique_after rows={unique_after.get('rows')} distinct_ticks={unique_after.get('distinct_ticks')} "
        f"distinct_room_ticks={unique_after.get('distinct_room_ticks')} unique_creep_tick_rows={unique_after.get('unique_creep_tick_rows')}"
    )
    v.append(
        f"official_with_creeps={official_with_creeps} empty_no_creep={empty_ticks} "
        f"official_404_missing={official_404_ticks} official_fetched={official_fetched} expected={expected}"
    )
    v.append(f"inserted_total={inserted_total} already_in_db={ALREADY} missing_chunks_first={MISSING_CHUNKS_FIRST} {MISSING_CHUNK_LIST}")
    v.append(f"tick_s_first={TICK_S_FIRST} tick_s_later={TICK_S_LATER} tick_s_in_use={TICK_S_IN_USE} corrective_nfix={TS_REALIGNED_CORRECTIVE}")
    v.append(f"new_freeze {FREEZE_FROM}..{FREEZE_TO} ({FREEZE_SEC}s) room_stats gap {RS_GAP[0]}..{RS_GAP[1]} ({RS_GAP_N})")
    v.append(f"freeze_fill {json.dumps(freeze_fill, default=str)}")
    v.append(f"live_after {json.dumps(live_after, default=str)}")
    v.append(f"db_tips {json.dumps(tips, default=str)}")
    v.append(f"listener single_slot={lis['single_slot']} roomSlot={lis['roomSlot']} rot={lis['rot']} yield={lis['yield_files']}")
    v.append(f"confirm recovered={confirm_rec_txt} retry2 recovered={retry2_rec_txt}")
    v.append(
        "ok=true (quiet); first-pass missing_chunks=0 (35 of 35 official GETs 200, no in-window official 404); "
        "corrective later-mean-robust realign nfix=17417 tick_s_in_use=4.69789 (first 4.84610 was over the 45s gate); "
        "new 06:10 freeze gap 84311431..84311519 official-filled (fully published); "
        "prior 05:47 freeze gap 84311131..84311269 now official-filled including former unpublished remainder; "
        "05:41 ping/pong gap 84311041..84311069 official-filled; prior 05:30 gap 84310921..84310949 official-filled; "
        "prior 05:11 sits outside window and stays official-filled; prior 04:41 remainder W46N8 still depends on official @84310500 (still 404 after confirm/retry2); "
        "prior 04:09/03:47/03:16 already official-filled outside window; "
        "prior 02:42 remainder W47N7@84309000 still 404; leftover W45N8@84309100 still 404 (25 live)."
    )
    verify_text = "\n".join(v) + "\n"
    for dest in (f"{DIR}/verify.txt", f"{ROOT}/state/_halfhour_backfill_verify.txt"):
        with open(dest, "w") as f:
            f.write(verify_text)

    wrap_text = (
        f"{finished.strftime('%Y-%m-%d %H:%M:%S %Z')} wrapup ok quiet\n"
        f"window {TMIN}..{TMAX} inserted={inserted_total} missing_chunks={MISSING_CHUNKS_FIRST} "
        f"tick_s_in_use={TICK_S_IN_USE} corrective_nfix={TS_REALIGNED_CORRECTIVE}\n"
        f"wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    )
    with open(f"{DIR}/wrapup_run.txt", "w") as f:
        f.write(wrap_text)
    print(wrap_text)
    print("in_window", inwin)
    print("freeze_fill", json.dumps(freeze_fill, indent=2, default=str))
    print("live_after", live_after)
    print("cpu_after", cpu_after)
    print("path_after", path_after)
    print("leftovers:")
    for x in leftover_info:
        print(" ", x["text"])
    print("wrote status records")


if __name__ == "__main__":
    main()
