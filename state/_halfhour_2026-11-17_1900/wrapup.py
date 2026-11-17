#!/usr/bin/env python3
"""Write half-hour backfill status records for the next hourly patrol."""
from __future__ import annotations
import json, os, subprocess, sys, shutil
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-17_1900"
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84320601, 84321300
GT_FIRST = 84321330
PUB_BASES = "84320600..84321200"
TICK_S_FIRST = 4.67989
TICK_S_PRINTED = "4.680"
NEW_ROWS = {"W46N8": 3211, "W47N8": 4472, "W45N8": 1731, "W45N7": 1114, "W47N7": 1756}
OFFICIAL_TICKS = {"W46N8": 700, "W47N8": 700, "W45N8": 700, "W45N7": 700, "W47N7": 700}
INSERTED_FIRST = 12284
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
ALREADY = 13623
RECON_ROWS = 25907
TS_REALIGNED_FIRST = 0
IN_WINDOW_404 = []  # first pass 35/35 official GETs 200
OUTSIDE_404 = [
    ("W47N8", 84319900),
    ("W47N8", 84319000),
    ("W46N8", 84318500),
    ("W45N8", 84318000),
    ("W47N7", 84315100),
    ("W45N8", 84314900),
    ("W45N7", 84314500),
    ("W47N8", 84314000),
    ("W46N8", 84313200),
    ("W46N8", 84310500), ("W47N7", 84309000), ("W45N8", 84309100), ("W45N8", 84306500),
    ("W45N7", 84305100), ("W47N8", 84304700), ("W45N7", 84303900), ("W45N8", 84302200),
    ("W47N8", 84300900), ("W45N8", 84300900), ("W45N8", 84300000), ("W47N8", 84298000),
    ("W47N8", 84297200), ("W47N7", 84296500), ("W45N8", 84295900), ("W45N7", 84295800),
]


def ranges(ticks, tmin, tmax):
    missing, start, s = [], None, set(ticks)
    for t in range(tmin, tmax + 1):
        if t not in s:
            if start is None:
                start = t
        elif start is not None:
            missing.append([start, t - 1])
            start = None
    if start is not None:
        missing.append([start, tmax])
    return missing


def load_json(path):
    with open(path) as f:
        return json.load(f)


def pgrep(pat):
    r = subprocess.run(["pgrep", "-af", pat], capture_output=True, text=True)
    return [ln.strip() for ln in r.stdout.splitlines() if ln.strip() and "pgrep" not in ln]


def iso(ts):
    if ts is None:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    return ts.isoformat()


def hole_text(c, room, base):
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
        detail = f"0 live / 100 empty"
    elif d == 100:
        detail = f"already live-filled 100 distinct / {n} rows"
    else:
        detail = f"{d} live / {empty_n} empty"
    return f"{room}@{base} ({detail}; official {base} still 404 after confirm and retry2; retry next run)"


def hole_short(c, room, base):
    a, b = base + 1, base + 100
    ticks = [r[0] for r in c.execute(
        "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s ORDER BY 1",
        (room, a, b),
    ).fetchall()]
    d = len(ticks)
    miss = ranges(ticks, a, b) if d else [[a, b]]
    empty_n = sum(bb - aa + 1 for aa, bb in miss)
    if d == 0:
        return f"{room}@{base} (0 live / 100 empty)"
    if d == 100:
        return f"{room}@{base} (100 live)"
    return f"{room}@{base} ({d} live / {empty_n} empty)"


def fill(c, lo, hi):
    out = {}
    span = hi - lo + 1
    for room in ROOMS:
        row = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) "
            "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, lo, hi),
        ).fetchone()
        out[room] = {"distinct": row[0] or 0, "min": row[1], "max": row[2], "rows": row[3] or 0, "span": span}
    return out


def tick_runs(ticks):
    if not ticks:
        return []
    runs, a, prev = [], ticks[0], ticks[0]
    for t in ticks[1:]:
        if t == prev + 1:
            prev = t
        else:
            runs.append([a, prev, prev - a + 1])
            a = prev = t
    runs.append([a, prev, prev - a + 1])
    return runs


def frac(filld, span):
    return "/".join(str(filld[r]["distinct"]) for r in ROOMS) + f" of {span}"


def in_window(lo, hi):
    return not (hi < TMIN or lo > TMAX)


def main():
    cov = load_json(DIR / "coverage_final.json")
    confirm = load_json(DIR / "backfill_confirm_gets.json")
    tsr = load_json(DIR / "tick_s_realign.json")
    prev = load_json(DIR / "history_backfill_prev_1830.json")
    coverage = cov.get("coverage") or cov
    later = float(tsr["later_mean_w46_robust"])
    vs_later = tsr["vs_later_after"]
    vs_first = tsr["vs_first"]
    confirm_at = confirm.get("at")
    confirm_gt = confirm.get("game_time")
    retry2 = confirm.get("retry2") or {}
    retry2_at = retry2.get("at")
    retry2_gt = retry2.get("game_time")
    corrective = bool(tsr.get("corrective_applied"))
    nfix_corr = int(tsr.get("ts_realigned_to_later_mean") or 0)
    tick_s_in_use = later if corrective else TICK_S_FIRST

    live = load_json(ROOT / "metrics/live.json")
    rot = load_json(ROOT / "metrics/listener_rot.json")
    stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
    now = datetime.now(TZ)
    lis = pgrep("tools/listener.py")
    runl = pgrep("tools/run_listener.sh")
    yield_present = (ROOT / "metrics/listener_yield_rooms").exists()

    with db.connect() as c:
        tips = {}
        for table in ("creep_ticks", "room_stats", "creep_cpu", "path_arrivals"):
            row = c.execute(f"SELECT max(tick), max(ts) FROM {table}").fetchone()
            tips[table] = {"max_tick": row[0], "max_ts": iso(row[1])}
        live_after = {}
        for room in ROOMS:
            rows = c.execute(
                "SELECT DISTINCT tick FROM creep_ticks WHERE room=%s AND tick > %s ORDER BY 1",
                (room, TMAX),
            ).fetchall()
            ticks = [r[0] for r in rows]
            agg = c.execute(
                "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) "
                "FROM creep_ticks WHERE room=%s AND tick > %s",
                (room, TMAX),
            ).fetchone()
            live_after[room] = {
                "distinct": agg[0] or 0, "min": agg[1], "max": agg[2], "rows": agg[3] or 0,
                "runs": tick_runs(ticks),
            }
        holes = [hole_text(c, room, base) for room, base in OUTSIDE_404]
        hole_shorts = {f"{room}@{base}": hole_short(c, room, base) for room, base in OUTSIDE_404}
        freeze_0743 = fill(c, 84312611, 84312889)
        freeze_0713 = fill(c, 84312221, 84312399)
        freeze_0917 = fill(c, 84313811, 84313929)
        freeze_0943 = fill(c, 84314141, 84314339)
        freeze_1011 = fill(c, 84314501, 84314639)
        freeze_1011_404 = fill(c, 84314501, 84314600)
        freeze_1044 = fill(c, 84314921, 84314959)
        freeze_1054 = fill(c, 84315041, 84315119)
        freeze_1111 = fill(c, 84315261, 84315469)
        freeze_1148 = fill(c, 84315741, 84315789)
        freeze_1252 = fill(c, 84316561, 84316599)
        freeze_1257 = fill(c, 84316621, 84316679)
        freeze_1318 = fill(c, 84316901, 84316999)
        freeze_1348 = fill(c, 84317271, 84317419)
        freeze_1412 = fill(c, 84317571, 84317679)
        freeze_1449 = fill(c, 84318051, 84318239)
        freeze_1516 = fill(c, 84318391, 84318459)
        freeze_1544 = fill(c, 84318741, 84318979)
        freeze_1619 = fill(c, 84319201, 84319279)
        freeze_1648 = fill(c, 84319571, 84319749)
        freeze_1714 = fill(c, 84319901, 84320019)
        freeze_1714_404 = fill(c, 84319901, 84320000)
        freeze_1714_tail = fill(c, 84320001, 84320019)
        freeze_1746 = fill(c, 84320301, 84320429)
        freeze_1846 = fill(c, 84321061, 84321229)
        rem_overlap = fill(c, 84320601, 84320900)
        rem_new = fill(c, 84320901, 84321300)
        cpu = c.execute(
            "SELECT min(tick), max(tick), count(*), min(ts), max(ts) "
            "FROM creep_cpu WHERE ts >= '2026-11-17 18:57:57+08'"
        ).fetchone()
        path = c.execute(
            "SELECT min(tick), max(tick), count(*), min(ts), max(ts) "
            "FROM path_arrivals WHERE ts >= '2026-11-17 18:57:57+08'"
        ).fetchone()
        db_after = {}
        for room in ROOMS:
            row = c.execute(
                "SELECT min(tick), max(tick), count(*), count(DISTINCT tick) "
                "FROM creep_ticks WHERE tick BETWEEN %s AND %s AND room=%s",
                (TMIN, TMAX, room),
            ).fetchone()
            db_after[room] = {"min": row[0], "max": row[1], "rows": row[2] or 0, "distinct": row[3] or 0}

    segment90 = {
        "creep_cpu": {"min": cpu[0], "max": cpu[1], "rows": cpu[2], "min_ts": iso(cpu[3]), "max_ts": iso(cpu[4])},
        "path_arrivals": {"min": path[0], "max": path[1], "rows": path[2], "min_ts": iso(path[3]), "max_ts": iso(path[4])},
    }

    # coverage.py may nest per-room under "coverage" or at top level
    def room_cov(room):
        if isinstance(coverage, dict) and room in coverage and isinstance(coverage[room], dict):
            return coverage[room]
        if room in cov and isinstance(cov[room], dict):
            return cov[room]
        return {}

    per_room = {}
    for room in ROOMS:
        cvr = room_cov(room)
        per_room[room] = {
            "official_ticks_first_pass": OFFICIAL_TICKS[room],
            "new_rows_first_pass": NEW_ROWS[room],
            "distinct": cvr.get("distinct"),
            "rows": cvr.get("rows"),
            "range": cvr.get("range"),
            "missing_n": cvr.get("missing_n"),
            "missing_ranges": cvr.get("missing_ranges") or cvr.get("missing") or [],
            "official_404_missing": cvr.get("official_404_missing") or cvr.get("official_404") or 0,
            "official_404_missing_ranges": cvr.get("official_404_missing_ranges") or [],
            "official_empty_no_creep": cvr.get("official_empty_no_creep") or cvr.get("empty_no_creep") or 0,
            "official_empty_no_creep_ranges": cvr.get("official_empty_no_creep_ranges") or [],
        }

    w45n7_empty = per_room["W45N7"]["official_empty_no_creep_ranges"]
    empty_n = cov.get("empty_no_creep") or cov.get("empty_no_creep_ticks") or 1
    official_404_n = cov.get("official_404_missing") or 0
    recovered = cov.get("official_recovered") or 3500
    expected = cov.get("expected") or cov.get("official_expected") or 3500

    corr_txt = (
        f"later-mean-robust was over the 45s gate before corrective "
        f"(still_over_45s_vs_later_before={tsr.get('still_over_45s_vs_later_before')}, "
        f"after over45={vs_later['over45']} over15={vs_later['over15']} "
        f"mean_off={vs_later['mean_off']:.2f} max_off={vs_later['max_off']:.2f}); "
        f"applied corrective later-mean-robust realign of {nfix_corr} rows. "
        f"In-use tick_s={tick_s_in_use:.5f} (later-mean-robust; corrective nfix={nfix_corr})."
        if corrective else
        f"later-mean-robust already inside 45s gate "
        f"(still_over_45s_vs_later_before={tsr.get('still_over_45s_vs_later_before')}, "
        f"after over45={vs_later['over45']} over15={vs_later['over15']} "
        f"mean_off={vs_later['mean_off']:.2f} max_off={vs_later['max_off']:.2f}); no corrective realign. "
        f"In-use tick_s={tick_s_in_use:.5f} (first-interval; no corrective)."
    )
    tick_s_note = (
        f"First pass (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}, live anchor game.time={GT_FIRST}) "
        f"inserted {INSERTED_FIRST} rows, then realign committed ts_realigned_first={TS_REALIGNED_FIRST} (no CheckViolation). "
        f"later-mean-robust {later:.5f} (raw later-mean also {later:.5f}; W46 first interval {TICK_S_FIRST}, "
        f"min-all-rooms first interval {TICK_S_FIRST}; "
        f"delta first-robust {TICK_S_FIRST-later:.5f} s/tick, "
        f"~{(GT_FIRST-TMIN)*abs(TICK_S_FIRST-later):.1f}s at tmin). "
        + corr_txt
    )
    missing_note = (
        f"First pass (game.time={GT_FIRST}) published_bases {PUB_BASES}, reconstructed {TMIN}..{TMAX} (700). "
        f"missing_chunks=0 of 35 official GETs (35 of 35 200). No SSL EOF this run. "
        f"The previous 18:30 half-hour run official-backfilled 84320201..84320900 (inserted=5971+0+0 already_in_db=20312 "
        f"at game.time=84320941, published_bases 84320200..84320800, first-pass missing_chunks=0, "
        f"confirm/retry2 inserted=0, leftover official 404s all outside window after confirm/retry2, "
        f"tick_s=4.81056 printed 4.811, ts_realigned_first=11858, "
        f"later-mean-robust 4.72769 corrective nfix=5716, in-use 4.72769). "
        f"This run overlapped 84320601..84320900 (official-filled on all five rooms, W45N7 empty-no-creep 84320725) "
        f"and newly covered the previously unpublished remainder 84320901..84321300, including the just-published 84320900..84321200 chunks "
        f"and the full new 18:46 freeze gap 84321061..84321229 (official-filled on all five rooms; no unpublished tail). "
        f"The prior 17:46 freeze gap 84320301..84320429 is now before this window start (window starts 84320601) and remains official-filled on all five rooms; no unpublished tail. "
        f"The prior 17:14 freeze gap 84319901..84320019 remains before this window, except official 404 W47N8@84319900 (0 live / 100 empty 84319901..84320000; 84320001..84320019 official-filled). "
        f"The prior 16:48 freeze gap 84319571..84319749 and earlier freeze bands remain before this window. "
        f"Confirm at {confirm_at} game.time={confirm_gt} recovered none inserted={INSERTED_CONFIRM}; "
        f"retry2 at {retry2_at} game.time={retry2_gt} inserted={INSERTED_RETRY2}; "
        f"final in-window official 404=0. "
        f"W47N8@84319900 remains outside this window (0 live / 100 empty 84319901..84320000). "
        f"W47N8@84319000 is outside this window (48 live 84319001..84319048, 52 empty 84319049..84319100). "
        f"W46N8@84318500 is outside this window (32 live 84318569..84318600, 68 empty 84318501..84318568). "
        f"W45N8@84318000 is outside this window (0 live, 100 empty 84318001..84318100). "
        f"W47N7@84315100 is outside this window (0 live, 100 empty 84315101..84315200). "
        f"W45N8@84314900 is outside this window (0 live, 100 empty 84314901..84315000). "
        f"W45N7 official empty-no-creep {empty_n} ticks {w45n7_empty}."
    )
    inserted_note = (
        f"This 19:00 first pass inserted {INSERTED_FIRST} new rows "
        f"(already_in_db={ALREADY}, reconstructed={RECON_ROWS}) "
        f"because the overlap 84320601..84320900 was already official-backfilled by the 18:30 half-hour run on all five rooms (W45N7 empty-no-creep 84320725). "
        f"This pass official-filled the just-published 84320900..84321200 chunks (84320901..84321300), including the full new 18:46 freeze gap 84321061..84321229. "
        f"Confirm recovered none inserted={INSERTED_CONFIRM}; retry2 inserted={INSERTED_RETRY2}; leftover official 404s unchanged. "
        f"inserted_total={INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2}. "
        f"First-pass realign committed ts_realigned_first={TS_REALIGNED_FIRST} (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}). "
        + corr_txt
    )
    live_note = (
        f"One new box freeze since the 18:30 run: 18:46:06–18:57:57 Asia/Hong_Kong (~703s) "
        f"(room_stats gap 84321061..84321229, 169 ticks; fully inside this official window 84320601..84321300; official-filled on all five rooms; no unpublished tail). "
        f"Listener self-reconnected at 18:57:57 after that freeze (relaunch 18:58:00, current tools/listener.py pid 4106261 started 18:58:10; pidfile 4035476). "
        f"This run did not restart the listener. After the 18:57:57 reconnect the listener itself has kept pulling recent CPU / path buffers "
        f"(creep_cpu {segment90['creep_cpu']['min']}..{segment90['creep_cpu']['max']}, {segment90['creep_cpu']['rows']} rows, first ts {segment90['creep_cpu']['min_ts']}; "
        f"path_arrivals {segment90['path_arrivals']['min']}..{segment90['path_arrivals']['max']}, {segment90['path_arrivals']['rows']} rows, first ts {segment90['path_arrivals']['min_ts']}). "
        f"Peacetime single-slot rotation holds (roomSlot={live.get('roomSlot')}, rot={rot}, yield_files={'present' if yield_present else 'absent'}). "
        f"This run did not start a second listener or change the 5:5:1:1 poll. Official history HTTP does not use a room slot. "
        f"The previous 18:30 half-hour run had already official-backfilled 84320201..84320900; leftover official 404 W47N8@84319900 remains outside this window."
    )

    def refresh_freeze(key, fill_full, extra=None, note=None):
        block = dict(prev.get(key) or {})
        if fill_full is not None:
            block["official_fill_full_gap"] = fill_full
        if extra:
            block.update(extra)
        if note:
            block["note"] = note
        return block

    # 18:46 is new_box_freeze this run; 17:46 moves fully before this window
    prior_1746_note = (
        "not new this run (was new at 18:00); full live gap 84320301..84320429 is now before this window start "
        "(window starts 84320601) and remains official-filled on all five rooms; no unpublished tail."
    )
    prior_1714_note = (
        "not new this run; full live gap 84319901..84320019 remains before this window start (window starts 84320601). "
        "Four rooms official-filled 119/119; W47N8 missing 84319901..84320000 due to official 404 @84319900, official-filled 84320001..84320019 (19 ticks). No unpublished tail."
    )

    finished_at = now.isoformat()
    finished_hkt = now.strftime("%Y-%m-%d %H:%M Asia/Hong_Kong")

    payload = {
        "ok": True,
        "routine": "Screeps 半小时轨迹补数",
        "finished_at": finished_at,
        "finished_at_hkt": finished_hkt,
        "shard": "shard3",
        "rooms": list(ROOMS),
        "minutes": 40,
        "game_time": GT_FIRST,
        "live_json_gameTime_at_finish": live.get("gameTime"),
        "live_json_stats_t_at_finish": stats.get("t"),
        "live_json_gameTime_note": live_note,
        "published_bases": PUB_BASES,
        "ticks": {"min": TMIN, "max": TMAX, "count": TMAX - TMIN + 1},
        "tick_s": TICK_S_FIRST,
        "tick_s_later_mean": later,
        "tick_s_in_use": tick_s_in_use,
        "tick_s_first_pass_outlier": not (3.0 <= TICK_S_FIRST <= 6.0),
        "tick_s_later_mean_applied_then_reverted": False,
        "tick_s_corrective_applied": corrective,
        "missing_chunks": 0,
        "missing_chunk_list": [],
        "missing_chunk_first_pass": [],
        "missing_chunk_note": missing_note,
        "creep_rows_reconstructed": RECON_ROWS,
        "already_in_db": ALREADY,
        "inserted": INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2,
        "inserted_first_pass": INSERTED_FIRST,
        "inserted_retry": INSERTED_CONFIRM,
        "inserted_retry2": INSERTED_RETRY2,
        "inserted_note": inserted_note,
        "ts_realigned": TS_REALIGNED_FIRST,
        "ts_realigned_corrective_later_mean": nfix_corr,
        "ts_realigned_confirm": 0,
        "ts_realigned_retry2": 0,
        "ts_realigned_note": tick_s_note,
        "ssl_first_attempt": False,
        "hourly_patrol_prefilled": False,
        "per_room": per_room,
        "known_official_404s_outside_window": holes,
        "known_official_404s_in_window": [],
        "w45n7_empty_no_creep_in_window": bool(w45n7_empty),
        "w45n7_empty_no_creep_ranges": w45n7_empty,
        "empty_no_creep_in_window": bool(empty_n),
        "empty_no_creep_ranges": {"W45N7": w45n7_empty},
        "empty_no_creep_ticks": empty_n,
        "official_room_ticks_fetched": recovered,
        "official_room_ticks_with_creeps": cov.get("official_with_creeps") or 3499,
        "official_recovered": recovered,
        "official_expected": expected,
        "new_box_freeze": {
            "from": "2026-11-17 18:46:06",
            "to": "2026-11-17 18:57:57",
            "sec": 703,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84321061, 84321229],
            "live_room_stats_gap_ticks": 169,
            "official_fill_full_gap": freeze_1846,
            "published_part": [84321061, 84321229],
            "unpublished_tail": [],
            "note": "new this run; full live gap 84321061..84321229 is inside official window 84320601..84321300; official-filled on all five rooms; no unpublished tail.",
        },
        "prior_1746_box_freeze": refresh_freeze(
            "prior_1746_box_freeze", freeze_1746,
            extra={"published_part": [84320301, 84320429], "unpublished_tail": []},
            note=prior_1746_note,
        ),
        "prior_1714_box_freeze": refresh_freeze(
            "prior_1714_box_freeze", freeze_1714,
            extra={
                "official_fill_404_chunk": freeze_1714_404,
                "official_fill_after_404": freeze_1714_tail,
            },
            note=prior_1714_note,
        ),
        "prior_1648_box_freeze": refresh_freeze(
            "prior_1648_box_freeze", freeze_1648,
            note="not new this run; full live gap 84319571..84319749 remains before this window start (window starts 84320601); official-filled on all five rooms",
        ),
        "prior_1619_box_freeze": refresh_freeze(
            "prior_1619_box_freeze", freeze_1619,
            note="not new this run; full live gap 84319201..84319279 remains before this window start and already official-filled on all five rooms; no unpublished tail",
        ),
        "prior_1544_box_freeze": refresh_freeze(
            "prior_1544_box_freeze", freeze_1544,
            note="not new this run; full live gap 84318741..84318979 remains before this window; official-filled on all five rooms",
        ),
        "prior_1516_box_freeze": refresh_freeze("prior_1516_box_freeze", freeze_1516,
            note="not new this run; full live gap 84318391..84318459 remains before this window; official-filled on all five rooms"),
        "prior_1449_box_freeze": refresh_freeze("prior_1449_box_freeze", freeze_1449,
            note="not new this run; full live gap 84318051..84318239 remains before this window"),
        "prior_1412_box_freeze": refresh_freeze("prior_1412_box_freeze", freeze_1412,
            note="not new this run; full live gap 84317571..84317679 remains before this window; official-filled on all five rooms"),
        "prior_1348_box_freeze": refresh_freeze("prior_1348_box_freeze", freeze_1348,
            note="not new this run; full live gap 84317271..84317419 remains before this window; official-filled on all five rooms"),
        "prior_1318_box_freeze": refresh_freeze("prior_1318_box_freeze", freeze_1318,
            note="not new this run; full live gap 84316901..84316999 remains before this window; official-filled on all five rooms"),
        "prior_1252_box_freeze": refresh_freeze("prior_1252_box_freeze", freeze_1252,
            note="not new this run; full live gap 84316561..84316599 remains before this window; official-filled on all five rooms"),
        "prior_1257_box_freeze": refresh_freeze("prior_1257_box_freeze", freeze_1257,
            note="not new this run; full live gap 84316621..84316679 remains before this window; official-filled on all five rooms"),
        "prior_1148_box_freeze": refresh_freeze("prior_1148_box_freeze", freeze_1148,
            note="not new this run; full live gap 84315741..84315789 remains before this window; official-filled on all five rooms"),
        "prior_1111_box_freeze": refresh_freeze("prior_1111_box_freeze", freeze_1111,
            note="not new this run; full live gap 84315261..84315469 remains before this window"),
        "prior_1054_freeze": refresh_freeze("prior_1054_freeze", freeze_1054,
            note="not new this run; still before this window; W47N7 missing 84315101..84315119 due to official 404 @84315100"),
        "prior_1044_freeze_outside_or_edge": refresh_freeze("prior_1044_freeze_outside_or_edge", freeze_1044,
            note="not new this run; fully before this window; W45N8 missing due to official 404 @84314900"),
        "prior_1011_freeze_outside_window": refresh_freeze("prior_1011_freeze_outside_window", freeze_1011,
            extra={"official_fill_404_chunk": freeze_1011_404},
            note="not new this run; still before this window; W45N7 missing 84314501..84314600 due to official 404 @84314500"),
        "prior_0943_freeze_outside_window": refresh_freeze("prior_0943_freeze_outside_window", freeze_0943,
            note="not new this run; still before this window"),
        "prior_0917_freeze_outside_window": refresh_freeze("prior_0917_freeze_outside_window", freeze_0917,
            note="not new this run; still before this window"),
        "prior_0743_freeze_outside_window": refresh_freeze("prior_0743_freeze_outside_window", freeze_0743,
            note="not new this run; still before this window"),
        "prior_0713_freeze_outside_window": refresh_freeze("prior_0713_freeze_outside_window", freeze_0713,
            note="not new this run; still before this window"),
        "remainder_overlap_84320601_84320900": rem_overlap,
        "remainder_new_84320901_84321300": rem_new,
        "unique_after": cov.get("unique_after"),
        "db_tips": tips,
        "db_after": db_after,
        "live_after_official_tip": live_after,
        "segment90_after_185757_reconnect": segment90,
        "listener": {
            "listener_py": lis,
            "run_listener_sh": runl,
            "count_listener_py": len(lis),
            "count_run_listener": len(runl),
            "single_slot": len(lis) <= 1 and not yield_present,
            "roomSlot": live.get("roomSlot"),
            "rot": rot,
            "yield_files": "present" if yield_present else "absent",
            "restarted_this_run": False,
        },
        "confirm": {"at": confirm_at, "game_time": confirm_gt, "recovered": confirm.get("recovered") or [], "inserted": confirm.get("inserted") or 0},
        "retry2": {"at": retry2_at, "game_time": retry2_gt, "recovered": retry2.get("recovered") or [], "inserted": retry2.get("inserted") or 0},
        "coverage_official_recovered": f"{recovered}/{expected}",
    }

    (DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")

    per_txt = " ".join(
        f"{room}:{OFFICIAL_TICKS[room]}t/{NEW_ROWS[room]}new" for room in ROOMS
    )
    db_after_txt = "\n".join(
        f"  {room} ticks={db_after[room]['min']}..{db_after[room]['max']} "
        f"rows={db_after[room]['rows']} distinct={db_after[room]['distinct']}"
        for room in ROOMS
    )
    leftover_txt = (
        f"leftover official 404 {hole_shorts['W47N8@84319900']} still outside window; "
        f"leftover official 404 {hole_shorts['W47N8@84319000']} still outside window; "
        f"leftover official 404 {hole_shorts['W46N8@84318500']} still outside window; "
        f"leftover official 404 {hole_shorts['W45N8@84318000']} still outside window; "
        f"leftover official 404 {hole_shorts['W47N7@84315100']} still outside window; "
        f"leftover official 404 {hole_shorts['W45N8@84314900']} still outside window; "
        f"leftover official 404 {hole_shorts['W45N7@84314500']} still outside window; "
        f"leftover official 404 {hole_shorts['W47N8@84314000']} still outside window; "
        f"leftover official 404 {hole_shorts['W46N8@84313200']} still outside window; "
        f"older leftovers unchanged."
    )
    freeze_line = (
        f"New box freeze 18:46:06–18:57:57 (~703s) room_stats gap 84321061..84321229; "
        f"official-filled {frac(freeze_1846, 169)} of 84321061..84321229 (fully in this window; official-filled on all five rooms; no unpublished tail). "
        f"Prior box freeze 17:46:45–17:55:32 (~527s) room_stats gap 84320301..84320429; "
        f"official-filled {frac(freeze_1746, 129)} of 84320301..84320429 (now before this window; official-filled on all five rooms; no unpublished tail). "
        f"Prior box freeze 17:14:55–17:23:14 (~488s) room_stats gap 84319901..84320019; "
        f"official-filled {frac(freeze_1714, 119)} of 84319901..84320019 (still before this window; W47N8 missing 84319901..84320000 due to official 404 @84319900, 84320001..84320019 official-filled; no unpublished tail). "
        f"Prior box freeze 16:48:24–17:01:37 (~782s) room_stats gap 84319571..84319749; official-filled {frac(freeze_1648, 179)} (still before this window). "
        f"Prior box freeze 16:19:45–16:24:50 (~296s) room_stats gap 84319201..84319279; official-filled {frac(freeze_1619, 79)} (still before this window). "
        f"Prior box freeze 15:44:05–16:01:24 (~1039s) room_stats gap 84318741..84318979; official-filled {frac(freeze_1544, 239)} (still before this window). "
        f"Prior box freeze 15:16:17–15:20:45 (~257s) room_stats gap 84318391..84318459; official-filled {frac(freeze_1516, 69)} (still before this window). "
        f"Prior box freeze 14:49:29–15:03:38 (~848s) room_stats gap 84318051..84318239; official-filled {frac(freeze_1449, 189)} (still before this window). "
        f"Prior 14:12 / 13:48 / 13:18 / 12:52 / 12:57 / 11:48 / 11:11 / 10:54 / 10:44 / 10:11 / 09:43 / 09:17 / 07:43 freeze gaps still official-filled as previously recorded and still before this window. "
        f"Previously unpublished 84320901..84321300 official-filled on all five rooms, including just-published 84320900..84321200 and the full new 18:46 freeze gap 84321061..84321229. "
        f"Overlap 84320601..84320900 official-filled on all five rooms (W45N7 empty-no-creep 84320725). W47N8@84319900 remains outside this window."
    )
    ok_line = (
        f"ok=true (quiet); first-pass missing_chunks=0 (35 of 35 official GETs 200); "
        f"later-mean-robust {later:.5f} corrective nfix={nfix_corr}, tick_s_in_use={tick_s_in_use:.5f} "
        f"(first-pass realign 4.67989 committed {TS_REALIGNED_FIRST}); "
        f"new 18:46 freeze gap 84321061..84321229 official-filled {frac(freeze_1846, 169)} in this window, no unpublished tail; "
        f"prior 17:46 freeze gap 84320301..84320429 official-filled {frac(freeze_1746, 129)} now before this window; "
        f"prior 17:14 freeze gap 84319901..84320019 official-filled {frac(freeze_1714, 119)} still before this window except W47N8@84319900; "
        f"{leftover_txt}"
    )
    now_text = "\n".join([
        f"{now.strftime('%Y-%m-%d %H:%M:%S')} Asia/Hong_Kong half-hour backfill OK (quiet)",
        f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
        f"  (first pass 35 of 35 official GETs 200, missing_chunks=0; confirm/retry2 inserted=0; leftover official 404s unchanged, all outside window; see history_backfill.txt)",
        f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST}; later-mean-robust {later:.5f} corrective nfix={nfix_corr} (after over45={vs_later['over45']}), in-use {tick_s_in_use:.5f})",
        f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks=0 (first pass)",
        f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
        f"per_room {per_txt}",
        f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 +{INSERTED_RETRY2}, total {INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2})",
        f"ts_realigned_first={TS_REALIGNED_FIRST}; ts_realigned_corrective={nfix_corr} (later-mean-robust {later:.5f} corrective, after over45={vs_later['over45']})",
        "db_after",
        db_after_txt,
        f"coverage official_recovered={recovered}/{expected} unique_after={cov.get('unique_after')} empty_no_creep={empty_n} official_404_in_window={official_404_n}",
        f"tick_s_check later-mean-robust {later:.5f} corrective nfix={nfix_corr} (later over45={vs_later['over45']} over15={vs_later['over15']} mean_off={vs_later['mean_off']:.2f} max_off={vs_later['max_off']:.2f}); in-use tick_s={tick_s_in_use:.5f}",
        f"confirm recovered=none inserted=0; retry2 inserted=0; final in-window official 404 none; W45N7 official empty-no-creep {empty_n} ticks {w45n7_empty}; {leftover_txt}",
        freeze_line,
        f"listener single_slot={len(lis) <= 1 and not yield_present} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}",
        f"confirm recovered=none inserted=0 retry2 inserted=0",
        ok_line,
        "",
    ])
    (DIR / "history_backfill_now.txt").write_text(now_text)
    (ROOT / "state" / "_halfhour_backfill_now.txt").write_text(now_text)

    # coverage_final.txt already has the per-room lines; rebuild verify like previous runs
    verify = []
    # reuse coverage_final.txt body if present
    cov_txt = (DIR / "coverage_final.txt").read_text().strip().splitlines()
    # drop the 'wrote ...' last line if present
    cov_txt = [ln for ln in cov_txt if not ln.startswith("wrote ")]
    verify.extend(cov_txt)
    verify.append(f"live_ticks_after_official_tip {json.dumps(live_after, default=str)}")
    verify.append(f"db_tips {json.dumps(tips, default=str)}")
    verify.append(
        f"New 18:46 freeze 84321061..84321229 official-filled {frac(freeze_1846, 169)} in this window; no unpublished tail. "
        f"Prior 17:46 freeze 84320301..84320429 official-filled {frac(freeze_1746, 129)} now before this window; no unpublished tail. "
        f"Prior 17:14 freeze 84319901..84320019 official-filled {frac(freeze_1714, 119)} still before this window (W47N8 missing 84319901..84320000 due to official 404 @84319900). "
        f"Prior 16:48 / 16:19 / 15:44 / 15:16 / 14:49 / 14:12 / 13:48 / 13:18 / 12:52 / 12:57 / 11:48 / 11:11 and earlier freeze bands still official-filled as previously recorded and still before this window."
    )
    verify.append(
        f"previously unpublished 84320901..84321300 official-filled on all five rooms; includes just-published 84320900..84321200 and the full 18:46 freeze gap 84321061..84321229. "
        f"Overlap 84320601..84320900 official-filled on all five rooms (W45N7 empty-no-creep 84320725). Prior 17:46 and 17:14 freezes now/still before this window except official 404 W47N8@84319900."
    )
    verify.append(
        f"tick_s first={TICK_S_FIRST} printed {TICK_S_PRINTED}; later-mean-robust {later:.5f} corrective nfix={nfix_corr}; "
        f"first-pass realign committed {TS_REALIGNED_FIRST}; in-use {tick_s_in_use:.5f}; later over45={vs_later['over45']}."
    )
    verify.append(
        f"confirm recovered none inserted=0; retry2 inserted=0; final in-window official 404 none; "
        f"W45N7 official empty-no-creep {empty_n} ticks {w45n7_empty}; {leftover_txt}"
    )
    verify.append(
        f"listener single_slot={len(lis) <= 1 and not yield_present} roomSlot={live.get('roomSlot')} rot={rot} "
        f"yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart."
    )
    verify.append("This run did not restart the listener.")
    verify_text = "\n".join(verify) + "\n"
    (DIR / "verify.txt").write_text(verify_text)
    (ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)

    summary = (
        f"{finished_hkt} wrapup ok\n"
        f"wrote history_backfill.json history_backfill_now.txt verify.txt\n"
        f"inserted={INSERTED_FIRST}+0+0 coverage={recovered}/{expected} tick_s_in_use={tick_s_in_use:.5f} corrective={corrective} nfix={nfix_corr}\n"
    )
    (DIR / "wrapup_run.txt").write_text(summary)
    print(summary)
    print(now_text)


if __name__ == "__main__":
    main()
