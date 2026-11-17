#!/usr/bin/env python3
"""Write half-hour backfill status records for the next hourly patrol."""
from __future__ import annotations
import json, os, subprocess, sys, shutil
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-17_1730"
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84319401, 84320100
GT_FIRST = 84320146
PUB_BASES = "84319400..84320000"
TICK_S_FIRST = 4.61603
TICK_S_PRINTED = "4.616"
NEW_ROWS = {"W46N8": 399, "W47N8": 1570, "W45N8": 447, "W45N7": 259, "W47N7": 536}
OFFICIAL_TICKS = {"W46N8": 700, "W47N8": 600, "W45N8": 700, "W45N7": 700, "W47N7": 700}
INSERTED_FIRST = 3211
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
ALREADY = 20809
RECON_ROWS = 24020
TS_REALIGNED_FIRST = 15291
IN_WINDOW_404 = [("W47N8", 84319900)]  # first-pass official 404 still after confirm/retry2 (0 live / 100 empty 84319901..84320000)
OUTSIDE_404 = [
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
        detail = f"0 rows / 0 distinct, range None..None; hole {a}..{b}"
    elif d == 100:
        detail = f"already live-filled 100 distinct / {n} rows"
    else:
        detail = f"{d} live-filled {mn}..{mx} / {n} rows; {empty_n} empty {miss}"
    return f"{room}@{base} ({detail}; official {base} still 404 after confirm and retry2; retry next run)"


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
    return "/".join(str((filld[r]["distinct"])) for r in ROOMS) + f" of {span}"


def main():
    cov = load_json(DIR / "coverage_final.json")
    confirm = load_json(DIR / "backfill_confirm_gets.json")
    tsr = load_json(DIR / "tick_s_realign.json")
    coverage = cov.get("coverage") or {}
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
        freeze_1348_pub = fill(c, 84317271, 84317400)
        freeze_1412 = fill(c, 84317571, 84317679)
        freeze_1449 = fill(c, 84318051, 84318239)
        freeze_1449_win = fill(c, 84318051, 84318200)
        freeze_1449_unpub = fill(c, 84318201, 84318239)
        freeze_1516 = fill(c, 84318391, 84318459)
        freeze_1544 = fill(c, 84318741, 84318979)
        freeze_1544_pub = fill(c, 84318741, 84318900)
        freeze_1544_unpub = fill(c, 84318901, 84318979)
        freeze_1619 = fill(c, 84319201, 84319279)
        freeze_1648 = fill(c, 84319571, 84319749)
        freeze_1648_pub = fill(c, 84319571, 84319700)
        freeze_1648_unpub = fill(c, 84319701, 84319749)
        freeze_1714 = fill(c, 84319901, 84320019)
        freeze_1714_404 = fill(c, 84319901, 84320000)
        freeze_1714_tail = fill(c, 84320001, 84320019)
        rem_overlap = fill(c, 84319401, 84319700)
        rem_new = fill(c, 84319701, 84320100)
        hole_w47_19900 = hole_text(c, "W47N8", 84319900)
        hole_w47_19000 = hole_text(c, "W47N8", 84319000)
        hole_w45_18000 = hole_text(c, "W45N8", 84318000)
        hole_w46_18500 = hole_text(c, "W46N8", 84318500)
        hole_w47_15100 = hole_text(c, "W47N7", 84315100)
        hole_w45_14900 = hole_text(c, "W45N8", 84314900)
        hole_w45_14500 = hole_text(c, "W45N7", 84314500)
        hole_w47_14000 = hole_text(c, "W47N8", 84314000)
        hole_w46_13200 = hole_text(c, "W46N8", 84313200)
        cpu = c.execute(
            "SELECT min(tick), max(tick), count(*), min(ts), max(ts) "
            "FROM creep_cpu WHERE ts >= '2026-11-17 17:23:14+08'"
        ).fetchone()
        path = c.execute(
            "SELECT min(tick), max(tick), count(*), min(ts), max(ts) "
            "FROM path_arrivals WHERE ts >= '2026-11-17 17:23:14+08'"
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

    per_room = {}
    for room in ROOMS:
        cvr = coverage[room]
        per_room[room] = {
            "official_ticks_first_pass": OFFICIAL_TICKS[room],
            "new_rows_first_pass": NEW_ROWS[room],
            "distinct": cvr["distinct"],
            "rows": cvr["rows"],
            "range": cvr["range"],
            "missing_n": cvr["missing_n"],
            "missing_ranges": cvr["missing_ranges"],
            "official_404_missing": cvr["official_404_missing"],
            "official_404_missing_ranges": cvr.get("official_404_missing_ranges") or [],
            "official_empty_no_creep": cvr.get("official_empty_no_creep") or 0,
            "official_empty_no_creep_ranges": cvr.get("official_empty_no_creep_ranges") or [],
        }

    w45n7_empty = (coverage.get("W45N7") or {}).get("official_empty_no_creep_ranges") or []
    empty_n = cov.get("empty_no_creep") or 0
    official_404_n = cov.get("official_404_missing") or 0
    recovered = cov.get("official_recovered")
    expected = cov.get("expected")

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
        f"missing_chunks=1 of 35 official GETs (34 of 35 200, first-pass official 404 W47N8@84319900 only). "
        f"No RemoteDisconnected this run. "
        f"The previous 17:00 half-hour run official-backfilled 84319001..84319700 (inserted=9397+0+0 already_in_db=15906 "
        f"at game.time=84319773, published_bases 84319000..84319600, first-pass missing_chunks=1 404 W47N8@84319000, "
        f"confirm/retry2 inserted=0, leftover official 404 W47N8@84319000 after confirm/retry2, "
        f"tick_s=4.61928 printed 4.619, ts_realigned_first=3383, "
        f"later-mean-robust 4.68701 corrective nfix=1991, after over45=0, in-use 4.68701). "
        f"The concurrent 17:23 hourly patrol had already official-backfilled 84319301..84320000 (inserted=7173 already_in_db=16839 "
        f"at game.time=84320032, published_bases 84319300..84319900, first-pass missing_chunks=1 404 W47N8@84319900). "
        f"This run overlapped 84319401..84319700 (official-filled on all five rooms; prior leftover W47N8@84319000 is now outside this window) "
        f"and newly covered the previously unpublished remainder 84319701..84320100, including the just-published 84319700..84320000 chunks "
        f"and the full 17:14 freeze gap 84319901..84320019, except official 404 W47N8@84319900 (0 live / 100 empty 84319901..84320000; 84320001..84320019 official-filled). "
        f"The prior 16:48 freeze gap 84319571..84319749 is now fully inside this window, including the previously unpublished tail 84319701..84319749. "
        f"The prior 16:19 freeze gap 84319201..84319279 and earlier freeze bands are now before this window. "
        f"Confirm at {confirm_at} game.time={confirm_gt} recovered none inserted={INSERTED_CONFIRM}; "
        f"retry2 at {retry2_at} game.time={retry2_gt} inserted={INSERTED_RETRY2}; "
        f"final in-window official 404=1 (W47N8@84319900, 0 live / 100 empty 84319901..84320000). "
        f"W47N8@84319000 is now outside this window (48 live 84319001..84319048, 52 empty 84319049..84319100). "
        f"W46N8@84318500 is now outside this window (32 live 84318569..84318600, 68 empty 84318501..84318568). "
        f"W45N8@84318000 is now outside this window (0 live, 100 empty 84318001..84318100). "
        f"W47N7@84315100 is outside this window (0 live, 100 empty 84315101..84315200). "
        f"W45N8@84314900 is outside this window (0 live, 100 empty 84314901..84315000). "
        f"W45N7 official empty-no-creep {empty_n} ticks {w45n7_empty}."
    )
    inserted_note = (
        f"This 17:30 first pass inserted {INSERTED_FIRST} new rows "
        f"(already_in_db={ALREADY}, reconstructed={RECON_ROWS}) "
        f"because the overlap 84319401..84319700 was already official-backfilled by the 17:00 half-hour run, "
        f"and the concurrent 17:23 hourly patrol had already official-backfilled 84319301..84320000 except W47N8@84319900. "
        f"This pass official-filled the just-published 84320000 chunk (84320001..84320100) and any remaining holes in 84319701..84320000, except first-pass 404 on W47N8@84319900. "
        f"Confirm recovered none inserted={INSERTED_CONFIRM}; retry2 inserted={INSERTED_RETRY2}; W47N8@84319900 still 404. "
        f"inserted_total={INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2}. "
        f"First-pass realign committed ts_realigned_first={TS_REALIGNED_FIRST} (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}). "
        + corr_txt
    )
    live_note = (
        f"One new box freeze since the 17:00 run: 17:14:55–17:23:14 Asia/Hong_Kong (~488s) "
        f"(room_stats gap 84319901..84320019, 119 ticks; fully inside this official window 84319401..84320100; no unpublished tail). "
        f"Listener self-reconnected at 17:23:14 after the freeze (relaunch 17:23:17, current tools/listener.py pid 4060050 started 17:23:27; pidfile 4035476); the 17:23 hourly patrol had already done that reconnect. "
        f"This run did not restart the listener. After the 17:23:14 reconnect the listener itself has kept pulling recent CPU / path buffers "
        f"(creep_cpu {cpu[0]}..{cpu[1]}, {cpu[2]} rows, first ts {iso(cpu[3])}; "
        f"path_arrivals {path[0]}..{path[1]}, {path[2]} rows, first ts {iso(path[3])}). "
        f"Peacetime single-slot rotation holds (roomSlot={live.get('roomSlot')}, rot={rot}, yield_files={'present' if yield_present else 'absent'}). "
        f"This run did not start a second listener or change the 5:5:1:1 poll. Official history HTTP does not use a room slot. "
        f"The previous 17:00 half-hour run had already official-backfilled 84319001..84319700; the concurrent 17:23 hourly patrol had already official-backfilled 84319301..84320000 except W47N8@84319900."
    )
    hourly_note = (
        f"The previous 17:00 half-hour run official-backfilled 84319001..84319700 (inserted=9397+0+0 already_in_db=15906 "
        f"at game.time=84319773, published_bases 84319000..84319600, first-pass missing_chunks=1 404 W47N8@84319000, "
        f"confirm/retry2 inserted=0, leftover official 404 W47N8@84319000 after confirm/retry2, "
        f"tick_s=4.61928 printed 4.619, ts_realigned_first=3383, "
        f"later-mean-robust 4.68701 corrective nfix=1991, after over45=0, in-use 4.68701). "
        f"The concurrent 17:23 hourly patrol official-backfilled 84319301..84320000 (inserted=7173 already_in_db=16839 "
        f"at game.time=84320032, published_bases 84319300..84319900, first-pass missing_chunks=1 404 W47N8@84319900) before this run's first pass. "
        f"The prior 16:48 freeze band 84319571..84319749 is now fully inside this window, including the previously unpublished tail. "
        f"The prior 16:19 freeze and earlier freeze bands are now before this window. "
        f"This half-hour backfill is the official-history catch-up for {TMIN}..{TMAX} "
        f"(inserted={INSERTED_FIRST} first pass, already_in_db={ALREADY}, first-pass missing_chunks=1, "
        f"confirm/retry2 inserted=0, final in-window official 404=1 W47N8@84319900)."
    )

    payload = {
        "ok": True,
        "routine": "Screeps 半小时轨迹补数",
        "finished_at": now.isoformat(),
        "finished_at_hkt": now.strftime("%Y-%m-%d %H:%M Asia/Hong_Kong"),
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
        "tick_s_first_pass_outlier": False,
        "tick_s_later_mean_applied_then_reverted": False,
        "tick_s_corrective_applied": corrective,
        "missing_chunks": 1,
        "missing_chunk_list": ["W47N8@84319900"],
        "missing_chunk_first_pass": ["W47N8@84319900"],
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
        "ssl_first_attempt": (
            f"first official-history pass 34 of 35 official GETs 200, missing_chunks=1 (404 W47N8@84319900 only); "
            f"no RemoteDisconnected this run; first-pass realign committed ts_realigned={TS_REALIGNED_FIRST}; "
            f"later-mean-robust {later:.5f} was over the 45s gate before corrective "
            f"(still_over_45s_vs_later_before={tsr.get('still_over_45s_vs_later_before')}); "
            f"corrective nfix={nfix_corr}, after over45={vs_later['over45']}; "
            f"in-use later-mean-robust {tick_s_in_use:.5f}. "
            f"Confirm/retry2 recovered none; W47N8@84319900 still 404 (inserted={INSERTED_CONFIRM}+{INSERTED_RETRY2})."
        ),
        "hourly_patrol_prefilled": hourly_note,
        "per_room": per_room,
        "known_official_404s_outside_window": holes,
        "known_official_404s_in_window": [hole_w47_19900],
        "w45n7_empty_no_creep_in_window": bool(w45n7_empty),
        "w45n7_empty_no_creep_ranges": w45n7_empty,
        "empty_no_creep_in_window": bool(empty_n),
        "empty_no_creep_ranges": {"W45N7": w45n7_empty},
        "empty_no_creep_ticks": empty_n,
        "official_room_ticks_fetched": recovered,
        "official_room_ticks_with_creeps": cov.get("official_with_creeps"),
        "official_recovered": recovered,
        "official_expected": expected,
        "new_box_freeze": {
            "from": "2026-11-17 17:14:55",
            "to": "2026-11-17 17:23:14",
            "sec": 488,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84319901, 84320019],
            "live_room_stats_gap_ticks": 119,
            "official_fill_full_gap": freeze_1714,
            "official_fill_404_chunk": freeze_1714_404,
            "official_fill_after_404": freeze_1714_tail,
            "published_part": [84319901, 84320019],
            "unpublished_tail": [],
            "note": "new this run; full live gap 84319901..84320019 is inside official window 84319401..84320100. Four rooms official-filled 119/119; W47N8 missing 84319901..84320000 due to official 404 @84319900, official-filled 84320001..84320019 (19 ticks). No unpublished tail.",
        },
        "prior_1648_box_freeze": {
            "from": "2026-11-17 16:48:24",
            "to": "2026-11-17 17:01:37",
            "sec": 782,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84319571, 84319749],
            "live_room_stats_gap_ticks": 179,
            "official_fill_full_gap": freeze_1648,
            "official_fill_published_part": freeze_1648_pub,
            "official_fill_unpublished_tail": freeze_1648_unpub,
            "published_part": [84319571, 84319700],
            "unpublished_tail": [84319701, 84319749],
            "note": "not new this run; full live gap 84319571..84319749 is now inside official window 84319401..84320100, including the previously unpublished tail 84319701..84319749; official-filled on all five rooms",
        },
        "prior_1619_box_freeze": {
            "from": "2026-11-17 16:19:45",
            "to": "2026-11-17 16:24:50",
            "sec": 296,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84319201, 84319279],
            "live_room_stats_gap_ticks": 79,
            "official_fill_full_gap": freeze_1619,
            "published_part": [84319201, 84319279],
            "unpublished_tail": [],
            "note": "not new this run; full live gap 84319201..84319279 is now before this window start (window starts 84319401) and already official-filled on all five rooms; no unpublished tail",
        },
        "prior_1544_box_freeze": {
            "from": "2026-11-17 15:44:05",
            "to": "2026-11-17 16:01:24",
            "sec": 1039,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84318741, 84318979],
            "live_room_stats_gap_ticks": 239,
            "official_fill_full_gap": freeze_1544,
            "official_fill_published_part": freeze_1544_pub,
            "official_fill_unpublished_tail": freeze_1544_unpub,
            "published_part": [84318741, 84318900],
            "unpublished_tail": [84318901, 84318979],
            "note": "not new this run; full live gap 84318741..84318979 is now before this window start (window starts 84319401) and already official-filled on all five rooms, including the previously unpublished tail 84318901..84318979",
        },
        "prior_1516_box_freeze": {
            "from": "2026-11-17 15:16:17",
            "to": "2026-11-17 15:20:45",
            "sec": 257,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84318391, 84318459],
            "live_room_stats_gap_ticks": 69,
            "official_fill_full_gap": freeze_1516,
            "published_part": [84318391, 84318459],
            "unpublished_tail": [],
            "note": "not new this run; full live gap 84318391..84318459 is now before this window start (window starts 84318701) and already official-filled on all five rooms",
        },
        "prior_1449_box_freeze": {
            "from": "2026-11-17 14:49:29",
            "to": "2026-11-17 15:03:38",
            "sec": 848,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84318051, 84318239],
            "live_room_stats_gap_ticks": 189,
            "official_fill_full_gap": freeze_1449,
            "official_fill_published_part": freeze_1449_win,
            "official_fill_unpublished_tail": freeze_1449_unpub,
            "published_part": [84318051, 84318200],
            "unpublished_tail": [84318201, 84318239],
            "note": "not new this run; tail 84318201..84318239 remains in the overlap and is official-filled on all five rooms; the front 84318051..84318200 and the W45N8@84318000 hole are now before this window start (window starts 84318201)",
        },
        "prior_1412_box_freeze": {
            "from": "2026-11-17 14:12:36",
            "to": "2026-11-17 14:19:51",
            "sec": 435,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84317571, 84317679],
            "live_room_stats_gap_ticks": 109,
            "official_fill_full_gap": freeze_1412,
            "published_part": [84317571, 84317679],
            "unpublished_tail": [],
            "note": "not new this run; full live gap 84317571..84317679 is now before this window start (window starts 84318201) and already official-filled on all five rooms",
        },
        "prior_1348_box_freeze": {
            "from": "2026-11-17 13:48:54",
            "to": "2026-11-17 13:59:17",
            "sec": 623,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84317271, 84317419],
            "live_room_stats_gap_ticks": 149,
            "official_fill_full_gap": freeze_1348,
            "official_fill_published_part": freeze_1348_pub,
            "published_part": [84317271, 84317400],
            "unpublished_tail_now_in_window": [84317401, 84317419],
            "note": "not new this run; full live gap 84317271..84317419 is now before this window start (window starts 84318201) and already official-filled",
        },
        "prior_1318_box_freeze": {
            "from": "2026-11-17 13:18:38",
            "to": "2026-11-17 13:26:04",
            "sec": 436,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84316901, 84316999],
            "live_room_stats_gap_ticks": 99,
            "official_fill_full_gap": freeze_1318,
            "note": "not new this run; now fully before this window start (window starts 84318201); already official-filled",
        },
        "prior_1252_box_freeze": {
            "from": "2026-11-17 12:52:46",
            "to": "2026-11-17 12:54:44",
            "sec": 110,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84316561, 84316599],
            "live_room_stats_gap_ticks": 39,
            "official_fill_full_gap": freeze_1252,
            "note": "not new this run; now fully before this window start (window starts 84318201); already official-filled by the 13:00/13:30 runs",
        },
        "prior_1257_box_freeze": {
            "from": "2026-11-17 12:57:07",
            "to": "2026-11-17 13:00:29",
            "sec": 190,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84316621, 84316679],
            "live_room_stats_gap_ticks": 59,
            "official_fill_full_gap": freeze_1257,
            "note": "not new this run; now fully before this window start (window starts 84318201); already official-filled by the 13:00/13:30 runs",
        },
        "prior_1148_box_freeze": {
            "from": "2026-11-17 11:48:38",
            "to": "2026-11-17 11:51:05",
            "sec": 137,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84315741, 84315789],
            "live_room_stats_gap_ticks": 49,
            "official_fill_full_gap": freeze_1148,
            "note": "not new this run; fully before this window start (window starts 84318201); official-filled on all five rooms",
        },
        "prior_1111_box_freeze": {
            "from": "2026-11-17 11:11:00",
            "to": "2026-11-17 11:25:57",
            "sec": 888,
            "room_stats_gap": [84315261, 84315469],
            "span": 209,
            "official_fill_full_gap": freeze_1111,
            "note": "not new this run; fully before this window start (window starts 84318201); four rooms 209/209, W45N7 empty-no-creep in parts",
        },
        "prior_1054_freeze": {
            "from": "2026-11-17 10:54:19",
            "to": "2026-11-17 10:58:41",
            "sec": 262,
            "live_room_stats_gap": [84315041, 84315119],
            "official_fill_full_gap": freeze_1054,
            "note": "prior 10:54 freeze; now fully before this window start. W47N7 missing 84315101..84315119 due to official 404 @84315100; W45N7 official empty-no-creep in that band",
        },
        "prior_1044_freeze_outside_or_edge": {
            "from": "2026-11-17 10:44:25",
            "to": "2026-11-17 10:46:18",
            "sec": 100,
            "live_room_stats_gap": [84314921, 84314959],
            "official_fill_full_gap": freeze_1044,
            "note": "fully before this window start (window starts 84318201). W45N8 still missing due to official 404 @84314900; W45N7 official empty-no-creep",
        },
        "prior_1011_freeze_outside_window": {
            "from": "2026-11-17 10:11:26",
            "to": "2026-11-17 10:21:56",
            "sec": 624,
            "live_room_stats_gap": [84314501, 84314639],
            "official_fill_full_gap": freeze_1011,
            "official_fill_404_part": freeze_1011_404,
            "note": "not new this run; already official-filled by earlier runs; fully before this window. Four rooms 139/139; W45N7 still missing 84314501..84314600 due to official 404 @84314500",
        },
        "prior_0943_freeze_outside_window": {
            "from": "2026-11-17 09:43:21",
            "to": "2026-11-17 09:58:12",
            "sec": 883,
            "live_room_stats_gap": [84314141, 84314339],
            "official_fill": freeze_0943,
            "note": "not new this run; already official-filled 199/199; fully before this window",
        },
        "prior_0917_freeze_outside_window": {
            "from": "2026-11-17 09:17:21",
            "to": "2026-11-17 09:25:37",
            "sec": 489,
            "live_room_stats_gap": [84313811, 84313929],
            "official_fill": freeze_0917,
            "note": "not new this run; already official-filled 119/119; fully before this window",
        },
        "prior_0743_freeze_outside_window": {
            "from": "2026-11-17 07:43:34",
            "to": "2026-11-17 08:04:17",
            "sec": 1232,
            "live_room_stats_gap": [84312611, 84312889],
            "official_fill": freeze_0743,
            "note": "not new this run; already official-filled 279/279; fully before this window",
        },
        "prior_0713_freeze_outside_window": {
            "live_room_stats_gap": [84312221, 84312399],
            "official_fill": freeze_0713,
            "note": "already official-filled 179/179; fully before this window",
        },
        "remainder_overlap_84319401_84319700": rem_overlap,
        "remainder_new_84319701_84320100": rem_new,
        "unique_after": cov.get("unique_after"),
        "db_tips": tips,
        "db_after": db_after,
        "live_after_official_tip": live_after,
        "segment90_after_172314_reconnect": segment90,
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
    freeze_1714_txt = (
        f"New box freeze 17:14:55–17:23:14 (~488s) room_stats gap 84319901..84320019; "
        f"official-filled {frac(freeze_1714, 119)} of 84319901..84320019 (in this window; W47N8 missing 84319901..84320000 due to official 404 @84319900, 84320001..84320019 official-filled; no unpublished tail)."
    )
    freeze_1648_txt = (
        f"Prior box freeze 16:48:24–17:01:37 (~782s) room_stats gap 84319571..84319749; "
        f"official-filled {frac(freeze_1648, 179)} (previously unpublished tail 84319701..84319749 already official-filled; now fully in this window)."
    )
    freeze_1619_txt = (
        f"Prior box freeze 16:19:45–16:24:50 (~296s) room_stats gap 84319201..84319279; "
        f"official-filled {frac(freeze_1619, 79)} (fully published, now before this window; no unpublished tail)."
    )
    freeze_1544_txt = (
        f"Prior box freeze 15:44:05–16:01:24 (~1039s) room_stats gap 84318741..84318979; "
        f"official-filled {frac(freeze_1544, 239)} (previously unpublished tail 84318901..84318979 already official-filled; now before this window)."
    )
    freeze_1516_txt = (
        f"Prior box freeze 15:16:17–15:20:45 (~257s) room_stats gap 84318391..84318459; "
        f"official-filled {frac(freeze_1516, 69)} (fully published, now before this window)."
    )
    freeze_1449_txt = (
        f"Prior box freeze 14:49:29–15:03:38 (~848s) room_stats gap 84318051..84318239; "
        f"official-filled {frac(freeze_1449, 189)} (now before this window)."
    )
    freeze_1412_txt = (
        f"Prior box freeze 14:12:36–14:19:51 (~435s) room_stats gap 84317571..84317679; "
        f"official-filled {frac(freeze_1412, 109)} (fully published, now before this window)."
    )
    freeze_1348_txt = (
        f"Prior box freeze 13:48:54–13:59:17 (~623s) room_stats gap 84317271..84317419; "
        f"official-filled {frac(freeze_1348, 149)} (now before this window)."
    )
    freeze_1318_txt = (
        f"Prior box freeze 13:18:38–13:26:04 (~436s) room_stats gap 84316901..84316999; "
        f"official-filled {frac(freeze_1318, 99)} (now before this window)."
    )
    freeze_1252_txt = (
        f"Prior box freeze 12:52:46–12:54:44 (~110s) room_stats gap 84316561..84316599; "
        f"official-filled {frac(freeze_1252, 39)} (now before this window)."
    )
    freeze_1257_txt = (
        f"Prior box freeze 12:57:07–13:00:29 (~190s) room_stats gap 84316621..84316679; "
        f"official-filled {frac(freeze_1257, 59)} (now before this window)."
    )
    freeze_1148_txt = (
        f"Prior box freeze 11:48:38–11:51:05 (~137s) room_stats gap 84315741..84315789; "
        f"official-filled {frac(freeze_1148, 49)} (now before this window)."
    )
    freeze_1111_txt = (
        f"Prior box freeze 11:11:00–11:25:57 (~888s) room_stats gap 84315261..84315469 still official-filled "
        f"{frac(freeze_1111, 209)} (W45N7 empty-no-creep in parts of this band; still before this window)."
    )
    corr_short = (
        f"later-mean-robust {later:.5f} corrective nfix={nfix_corr} (after over45={vs_later['over45']}), in-use {tick_s_in_use:.5f}"
        if corrective else
        f"later-mean-robust {later:.5f} no corrective nfix={nfix_corr} (after over45={vs_later['over45']}), in-use {tick_s_in_use:.5f}"
    )
    now_text = (
        f"{now.strftime('%Y-%m-%d %H:%M:%S')} Asia/Hong_Kong half-hour backfill OK (quiet)\n"
        f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False\n"
        f"  (first-pass 34 of 35 official GETs 200, missing_chunks=1 404 W47N8@84319900; confirm/retry2 inserted=0, W47N8@84319900 still 404; see history_backfill.txt)\n"
        f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST}; {corr_short})\n"
        f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks=1 (first pass)\n"
        f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}\n"
        f"per_room {per_txt}\n"
        f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 +{INSERTED_RETRY2}, total {INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2})\n"
        f"ts_realigned_first={TS_REALIGNED_FIRST}; ts_realigned_corrective={nfix_corr} "
        f"(later-mean-robust {later:.5f} {'corrective' if corrective else 'no corrective'}, after over45={vs_later['over45']})\n"
        f"db_after\n{db_after_txt}\n"
        f"coverage official_recovered={recovered}/{expected} unique_after={cov.get('unique_after')} "
        f"empty_no_creep={empty_n} official_404_in_window={official_404_n}\n"
        f"tick_s_check later-mean-robust {later:.5f} {'corrective' if corrective else 'no corrective'} nfix={nfix_corr} "
        f"(later over45={vs_later['over45']} over15={vs_later['over15']} "
        f"mean_off={vs_later['mean_off']:.2f} max_off={vs_later['max_off']:.2f}); "
        f"in-use tick_s={tick_s_in_use:.5f}\n"
        f"confirm recovered=none inserted={INSERTED_CONFIRM}; retry2 inserted={INSERTED_RETRY2}; "
        f"final in-window official 404 W47N8@84319900 (0 live, 100 empty 84319901..84320000); leftover official 404 W47N8@84319000 now outside this window (48 live 84319001..84319048, 52 empty 84319049..84319100); leftover official 404 W46N8@84318500 now outside this window (32 live 84318569..84318600, 68 empty 84318501..84318568); leftover official 404 W45N8@84318000 now outside this window (0 live, 100 empty 84318001..84318100); leftover official 404 W47N7@84315100 still outside this window (0 live, 100 empty 84315101..84315200); "
        f"W45N7 official empty-no-creep {empty_n} ticks {w45n7_empty}; "
        f"leftover official 404 W45N8@84314900 still outside this window (0 live, 100 empty 84314901..84315000); "
        f"leftover official 404 W45N7@84314500 still outside this window (0 live, 100 empty 84314501..84314600); "
        f"leftover official 404 W47N8@84314000 still outside this window (49 live 84314052..84314100, 51 empty 84314001..84314051); "
        f"leftover official 404 W46N8@84313200 still outside this window (96 live 84313205..84313300, 4 empty 84313201..84313204); "
        f"older leftovers unchanged (W46N8@84310500 11 live, W47N7@84309000 empty, W45N8@84309100 25 live, and older leftovers still 404).\n"
        f"{freeze_1714_txt} {freeze_1648_txt} {freeze_1619_txt} {freeze_1544_txt} {freeze_1516_txt} {freeze_1449_txt} {freeze_1412_txt} {freeze_1348_txt} {freeze_1318_txt} {freeze_1252_txt} {freeze_1257_txt} {freeze_1148_txt} {freeze_1111_txt} "
        f"Prior 10:54 freeze gap 84315041..84315119 still official-filled on three rooms, W47N7 missing 84315101..84315119 due to official 404 @84315100, W45N7 empty-no-creep. "
        f"Prior 10:44 freeze gap 84314921..84314959 now fully before this window; W45N8 missing due to official 404 @84314900. "
        f"Prior 10:11 freeze gap 84314501..84314639 still official-filled 139/139 on four rooms, W45N7 missing 84314501..84314600 due to official 404 @84314500 (still before window). "
        f"Prior 09:43 / 09:17 / 07:43 freeze gaps still official-filled (199/199, 119/119, 279/279) and still before this window. "
        f"Previously unpublished 84319401..84319700 official-filled on all five rooms, including just-published 84319400..84319600 and the published part of the new 16:48 freeze gap 84319571..84319700. "
        f"Overlap 84319001..84319400 stays official-filled on four rooms fully and W47N8 except official 404 @84319000. W47N8@84319000 remains in this window; W46N8@84318500 and W45N8@84318000 stay outside this window.\n"
        f"listener single_slot={len(lis)<=1 and not yield_present} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}\n"
        f"confirm recovered=none inserted={INSERTED_CONFIRM} retry2 inserted={INSERTED_RETRY2}\n"
        f"ok=true (quiet); first-pass missing_chunks=1 (34 of 35 official GETs 200, 404 W47N8@84319900 still 404 after confirm and retry2); "
        f"later-mean-robust {later:.5f} {'corrective' if corrective else 'no corrective'} nfix={nfix_corr}, tick_s_in_use={tick_s_in_use:.5f} "
        f"(first-pass realign {TICK_S_FIRST} committed {TS_REALIGNED_FIRST}); "
        f"new 16:48 freeze gap 84319571..84319749 published part 84319571..84319700 official-filled {frac(freeze_1648_pub, 130)} in this window, unpublished tail 84319701..84319749; "
        f"prior 16:19 freeze gap 84319201..84319279 official-filled {frac(freeze_1619, 79)} in this window, no unpublished tail; "
        f"prior 15:44 freeze gap 84318741..84318979 official-filled {frac(freeze_1544, 239)} now before this window; "
        f"prior 15:16 freeze gap 84318391..84318459 official-filled {frac(freeze_1516, 69)} now before this window; "
        f"prior 14:49 freeze gap 84318051..84318239 official-filled {frac(freeze_1449, 189)} now before this window; "
        f"prior 14:12 freeze gap 84317571..84317679 official-filled {frac(freeze_1412, 109)} now before this window; "
        f"prior 13:48 freeze gap 84317271..84317419 official-filled {frac(freeze_1348, 149)} now before this window; "
        f"prior 13:18 freeze gap 84316901..84316999 official-filled {frac(freeze_1318, 99)} now before this window; "
        f"prior 12:52 freeze gap 84316561..84316599 official-filled {frac(freeze_1252, 39)} now before this window; "
        f"prior 12:57 freeze gap 84316621..84316679 official-filled {frac(freeze_1257, 59)} now before this window; "
        f"prior 11:48 freeze gap 84315741..84315789 still official-filled {frac(freeze_1148, 49)}, still before this window; "
        f"prior 11:11 freeze gap 84315261..84315469 still official-filled {frac(freeze_1111, 209)}, still before this window; "
        f"leftover official 404 W46N8@84318500 now outside window; leftover official 404 W45N8@84318000 still outside window; leftover official 404 W47N7@84315100 still outside window; leftover official 404 W45N8@84314900 still outside window; "
        f"other leftover official 404s unchanged.\n"
    )
    (DIR / "history_backfill_now.txt").write_text(now_text)
    (ROOT / "state" / "_halfhour_backfill_now.txt").write_text(now_text)

    verify = [
        f"window {TMIN}..{TMAX} (700)",
    ]
    for room in ROOMS:
        cvr = coverage[room]
        verify.append(
            f"{room} distinct={cvr['distinct']} rows={cvr['rows']} range={cvr['range']} "
            f"missing_n={cvr['missing_n']} {cvr['missing_ranges']} "
            f"empty_no_creep={cvr.get('official_empty_no_creep')} {cvr.get('official_empty_no_creep_ranges')} "
            f"official_404={cvr.get('official_404_missing')} {cvr.get('official_404_missing_ranges')}"
        )
    verify.append(f"unique_after {cov.get('unique_after')}")
    verify.append(
        f"official_with_creeps={cov.get('official_with_creeps')} empty_no_creep={empty_n} "
        f"official_404_missing={official_404_n} official_recovered={recovered} expected={expected} "
        f"in_window_404={cov.get('in_window_official_404')}"
    )
    verify.append(f"live_ticks_after_official_tip {json.dumps(live_after, default=str)}")
    verify.append(f"db_tips {json.dumps(tips, default=str)}")
    verify.append(
        f"New 16:48 freeze 84319571..84319749 published part 84319571..84319700 official-filled {frac(freeze_1648_pub, 130)} in this window; unpublished tail 84319701..84319749. "
        f"Prior 16:19 freeze 84319201..84319279 official-filled {frac(freeze_1619, 79)} in this window; no unpublished tail. "
        f"Prior 15:44 freeze 84318741..84318979 official-filled {frac(freeze_1544, 239)} now before this window (previously unpublished tail already official-filled). "
        f"Prior 15:16 freeze 84318391..84318459 official-filled {frac(freeze_1516, 69)} now before this window. "
        f"Prior 14:49 freeze 84318051..84318239 official-filled {frac(freeze_1449, 189)}, now before this window. "
        f"Prior 14:12 freeze 84317571..84317679 official-filled {frac(freeze_1412, 109)}, now before this window. "
        f"Prior 13:48 freeze 84317271..84317419 official-filled {frac(freeze_1348, 149)}, now before this window. "
        f"Prior 13:18 freeze 84316901..84316999 official-filled {frac(freeze_1318, 99)}, now before this window. "
        f"Prior 12:52 freeze 84316561..84316599 official-filled {frac(freeze_1252, 39)}, now before this window. "
        f"Prior 12:57 freeze 84316621..84316679 official-filled {frac(freeze_1257, 59)}, now before this window. "
        f"Prior 11:48 freeze 84315741..84315789 official-filled {frac(freeze_1148, 49)}, still before this window. "
        f"Prior 11:11 freeze 84315261..84315469 official-filled {frac(freeze_1111, 209)}, still before this window. "
        f"Prior 10:54 freeze 84315041..84315119 still missing W47N7 84315101..84315119 due to official 404 @84315100, still before this window. "
        f"Prior 10:44 / 10:11 / 09:43 / 09:17 / 07:43 freeze bands unchanged and still before this window start."
    )
    verify.append(
        f"previously unpublished 84319401..84319700 official-filled on all five rooms; "
        f"includes just-published 84319400..84319600 and the published part of the new 16:48 freeze gap 84319571..84319700. "
        f"Overlap 84319001..84319400 official-filled on four rooms fully and W47N8 except official 404 @84319000 (48 live / 52 empty). "
        f"Prior 16:19 freeze now fully in this window and official-filled; prior 15:44 / 15:16 / 14:49 / 14:12 / 13:48 / 13:18 / 12:52 / 12:57 freeze gaps still official-filled and now before this window."
    )
    verify.append(
        f"tick_s first={TICK_S_FIRST} printed {TICK_S_PRINTED}; later-mean-robust {later:.5f} {'corrective' if corrective else 'no corrective'} nfix={nfix_corr}; "
        f"first-pass realign committed {TS_REALIGNED_FIRST}; in-use {tick_s_in_use:.5f}; later over45={vs_later['over45']}."
    )
    verify.append(
        f"confirm recovered none inserted={INSERTED_CONFIRM}; retry2 inserted={INSERTED_RETRY2}; final in-window official 404 W47N8@84319900 (0 live / 100 empty); leftover official 404 W47N8@84319000 now outside window (48 live / 52 empty); leftover official 404 W46N8@84318500 now outside window (32 live / 68 empty); leftover official 404 W45N8@84318000 now outside window (0 live / 100 empty); leftover official 404 W47N7@84315100 still outside window (0 live / 100 empty); "
        f"leftover official 404 W45N8@84314900 still outside window (0 live / 100 empty); "
        f"leftover official 404 W45N7@84314500 still outside window (0 live / 100 empty); "
        f"leftover official 404 W47N8@84314000 still outside window (49 live / 51 empty); "
        f"leftover official 404 W46N8@84313200 still outside window (96 live / 4 empty); older leftovers unchanged."
    )
    verify.append(
        f"listener single_slot={len(lis)<=1 and not yield_present} roomSlot={live.get('roomSlot')} rot={rot} "
        f"yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart."
    )
    verify.append("This run did not restart the listener.")
    verify_text = "\n".join(verify) + "\n"
    (DIR / "verify.txt").write_text(verify_text)
    (ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)

    summary = (
        f"{now.strftime('%Y-%m-%d %H:%M:%S')} HKT wrapup ok quiet\n"
        f"window {TMIN}..{TMAX} inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2} missing_chunks=1 first-pass, final in-window 404 W47N8@84319900 tick_s_in_use={tick_s_in_use:.5f} corrective_nfix={nfix_corr}\n"
        f"wrote history_backfill.json history_backfill_now.txt verify.txt\n"
    )
    (DIR / "wrapup_run.txt").write_text(summary)
    print(summary, end="")
    print("in-window official 404 W47N8@84319900:", hole_w47_19900)
    print("outside official 404 W47N8@84319000:", hole_w47_19000)
    print("outside official 404 W46N8@84318500:", hole_w46_18500)
    print("outside official 404 W45N8@84318000:", hole_w45_18000)
    print("outside official 404 W47N7@84315100:", hole_w47_15100)
    print("outside official 404 W45N8@84314900:", hole_w45_14900)
    print("outside official 404 W45N7@84314500:", hole_w45_14500)
    print("outside official 404 W47N8@84314000:", hole_w47_14000)
    print("outside official 404 W46N8@84313200:", hole_w46_13200)
    print("freeze_fill_1148", json.dumps(freeze_1148, default=str))
    print("freeze_fill_1111", json.dumps(freeze_1111, default=str))
    print("freeze_fill_1054", json.dumps(freeze_1054, default=str))
    print("freeze_fill_1044", json.dumps(freeze_1044, default=str))
    print("remainder_overlap", json.dumps(rem_overlap, default=str))
    print("remainder_new", json.dumps(rem_new, default=str))
    print("freeze_fill_1252", json.dumps(freeze_1252, default=str))
    print("freeze_fill_1257", json.dumps(freeze_1257, default=str))
    print("freeze_fill_1318", json.dumps(freeze_1318, default=str))
    print("freeze_fill_1619", json.dumps(freeze_1619, default=str))
    print("freeze_fill_1544", json.dumps(freeze_1544, default=str))
    print("freeze_fill_1544_pub", json.dumps(freeze_1544_pub, default=str))
    print("freeze_fill_1544_unpub", json.dumps(freeze_1544_unpub, default=str))
    print("freeze_fill_1516", json.dumps(freeze_1516, default=str))
    print("freeze_fill_1449", json.dumps(freeze_1449, default=str))
    print("freeze_fill_1449_win", json.dumps(freeze_1449_win, default=str))
    print("freeze_fill_1449_unpub", json.dumps(freeze_1449_unpub, default=str))
    print("freeze_fill_1412", json.dumps(freeze_1412, default=str))
    print("freeze_fill_1348", json.dumps(freeze_1348, default=str))
    print("freeze_fill_1348_pub", json.dumps(freeze_1348_pub, default=str))
    print("listener", lis, runl, live.get("roomSlot"), rot)
    print("ok")


if __name__ == "__main__":
    main()
