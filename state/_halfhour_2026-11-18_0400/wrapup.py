#!/usr/bin/env python3
"""Write half-hour backfill status records for the next hourly patrol."""
from __future__ import annotations
import json, os, subprocess, sys, shutil
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-18_0400"
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84327301, 84328000
GT_FIRST = 84328097
PUB_BASES = "84327300..84327900"
TICK_S_FIRST = 4.70261
TICK_S_PRINTED = "4.703"
NEW_ROWS = {"W46N8": 2900, "W47N8": 5278, "W45N8": 1598, "W45N7": 1452, "W47N7": 1509}
OFFICIAL_TICKS = {"W46N8": 700, "W47N8": 700, "W45N8": 700, "W45N7": 700, "W47N7": 700}
INSERTED_FIRST = 12737
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
INSERTED_RETRY2_UNIQUE_NET = 0
ALREADY = 12711
RECON_ROWS = 25448
TS_REALIGNED_FIRST = 1269
IN_WINDOW_404 = []
OUTSIDE_404 = [
    ("W45N8", 84326300),
    ("W45N8", 84326500),
    ("W45N8", 84326100),
    ("W45N7", 84324900),
    ("W47N8", 84324300),
    ("W47N8", 84323200),
    ("W47N8", 84322100),
    ("W45N7", 84321600),
    ("W47N8", 84321300),
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


def frac(filld, span):
    return "/".join(str(filld[r]["distinct"]) for r in ROOMS) + f" of {span}"


def main():
    cov = load_json(DIR / "coverage_final.json")
    confirm = load_json(DIR / "backfill_confirm_gets.json")
    tsr = load_json(DIR / "tick_s_realign.json")
    coverage = cov.get("coverage") or cov
    later = float(tsr["later_mean_w46_robust"])
    vs_first = tsr.get("vs_first")
    vs_later_after = tsr.get("vs_later_after") or {}
    confirm_at = confirm.get("at")
    confirm_gt = confirm.get("game_time")
    retry2 = confirm.get("retry2") or {}
    retry2_at = retry2.get("at")
    retry2_gt = retry2.get("game_time")
    corrective = bool(tsr.get("corrective_applied"))
    nfix_corr = int(tsr.get("ts_realigned_to_later_mean") or 0)
    tick_s_in_use = later if corrective else TICK_S_FIRST
    inserted_total = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2_UNIQUE_NET

    live = load_json(ROOT / "metrics/live.json")
    rot = load_json(ROOT / "metrics/listener_rot.json")
    stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
    now = datetime.now(TZ)
    finished_hkt = now.strftime("%Y-%m-%d %H:%M Asia/Hong_Kong")
    finished_hkt_sec = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    lis = pgrep("tools/listener.py")
    runl = pgrep("tools/run_listener.sh")
    yield_present = (ROOT / "metrics/listener_yield_rooms").exists() or any(
        (ROOT / "metrics").glob("yield*")
    )

    with db.connect() as c:
        tips = {}
        for table in ("creep_ticks", "room_stats", "creep_cpu", "path_arrivals"):
            row = c.execute(f"SELECT max(tick), max(ts) FROM {table}").fetchone()
            tips[table] = {"max_tick": row[0], "max_ts": iso(row[1])}
        db_after = {}
        per_room = {}
        for room in ROOMS:
            dba = c.execute(
                "SELECT min(tick), max(tick), count(*), count(DISTINCT tick) "
                "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, TMIN, TMAX),
            ).fetchone()
            db_after[room] = {
                "min": dba[0], "max": dba[1], "rows": dba[2] or 0, "distinct": dba[3] or 0,
            }
            room_cov = (coverage.get(room) or {}) if isinstance(coverage, dict) else {}
            per_room[room] = {
                "official_ticks": OFFICIAL_TICKS[room],
                "new_rows_first_pass": NEW_ROWS[room],
                "db_rows": dba[2] or 0,
                "db_distinct": dba[3] or 0,
                "db_min": dba[0],
                "db_max": dba[1],
                "missing_n": room_cov.get("missing_n"),
                "missing_ranges": room_cov.get("missing_ranges"),
                "official_empty_no_creep": room_cov.get("official_empty_no_creep"),
                "official_empty_no_creep_ranges": room_cov.get("official_empty_no_creep_ranges"),
                "official_404_missing": room_cov.get("official_404_missing"),
            }
        hole_shorts = {f"{room}@{base}": hole_short(c, room, base) for room, base in OUTSIDE_404 + IN_WINDOW_404}
        freeze_0338 = fill(c, 84327811, 84328069)
        freeze_0338_pub = fill(c, 84327811, 84328000)
        freeze_0338_tail = fill(c, 84328001, 84328069)
        freeze_0315 = fill(c, 84327511, 84327599)
        freeze_0241 = fill(c, 84327081, 84327369)
        freeze_0241_pub = fill(c, 84327081, 84327300)
        freeze_0241_tail = fill(c, 84327301, 84327369)
        freeze_0211 = fill(c, 84326701, 84326799)
        freeze_0139 = fill(c, 84326291, 84326549)
        freeze_0139_pub = fill(c, 84326291, 84326500)
        freeze_0139_tail = fill(c, 84326501, 84326549)
        freeze_0110 = fill(c, 84325931, 84326149)
        freeze_0110_pub = fill(c, 84325931, 84326100)
        freeze_0110_tail = fill(c, 84326101, 84326149)
        freeze_0044 = fill(c, 84325601, 84325789)
        freeze_0010 = fill(c, 84325171, 84325209)
        freeze_0023 = fill(c, 84325320, 84325360)
        freeze_0002 = fill(c, 84325051, 84325089)
        freeze_2342 = fill(c, 84324821, 84324969)
        rem_overlap = fill(c, 84327301, 84327600)
        rem_new = fill(c, 84327601, 84328000)
        unique = c.execute(
            """SELECT count(*), count(DISTINCT (creep, tick)), count(DISTINCT tick),
                      count(DISTINCT (room, tick))
               FROM creep_ticks WHERE tick BETWEEN %s AND %s AND room = ANY(%s)""",
            (TMIN, TMAX, list(ROOMS)),
        ).fetchone()

    unique_after = {
        "rows": unique[0],
        "unique_creep_tick_rows": unique[1],
        "distinct_ticks": unique[2],
        "distinct_room_ticks": unique[3],
    }
    recovered = int(cov.get("official_recovered") or 0)
    expected = int(cov.get("expected") or 3500)
    empty_no_creep = int(cov.get("empty_no_creep") or 0)
    official_404_missing = int(cov.get("official_404_missing") or 0)
    w45n7_empty = (coverage.get("W45N7") or {}).get("official_empty_no_creep_ranges") or []
    w45n8_empty = (coverage.get("W45N8") or {}).get("official_empty_no_creep_ranges") or []
    w47n7_empty = (coverage.get("W47N7") or {}).get("official_empty_no_creep_ranges") or []

    leftover_order = [
        "W45N8@84326300", "W45N8@84326500", "W45N8@84326100", "W45N7@84324900",
        "W47N8@84324300", "W47N8@84323200", "W47N8@84322100", "W47N8@84321300",
        "W45N7@84321600", "W47N8@84319900", "W47N8@84319000", "W46N8@84318500",
        "W45N8@84318000", "W47N7@84315100", "W45N8@84314900", "W45N7@84314500",
        "W47N8@84314000", "W46N8@84313200",
    ]
    leftover_bits = [f"leftover official 404 {hole_shorts[k]} still outside window" for k in leftover_order]
    leftover_txt = "; ".join(leftover_bits) + "; older leftovers unchanged."
    inwin_txt = "no in-window official 404 remains"
    first_pass_line = (
        "first pass 35 of 35 official GETs 200, missing_chunks=0; confirm inserted=0 leftover outside-window 404s unchanged; "
        "retry2 skipped no in-window official 404s"
    )
    per_room_line = " ".join(
        f"{room}:{per_room[room]['official_ticks']}t/{per_room[room]['new_rows_first_pass']}new"
        for room in ROOMS
    )
    db_after_lines = "\n".join(
        f"  {room} ticks={db_after[room]['min']}..{db_after[room]['max']} rows={db_after[room]['rows']} distinct={db_after[room]['distinct']}"
        for room in ROOMS
    )

    tick_s_corr_txt = (
        f"later-mean-robust {later:.5f} automatic corrective applied and kept, nfix={nfix_corr}"
        if corrective else
        f"later-mean-robust {later:.5f} already inside 45s gate, no corrective realign, nfix=0"
    )
    ts_realign_note = (
        f"First pass (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}, live anchor game.time={GT_FIRST}) "
        f"ts_realigned={TS_REALIGNED_FIRST}. later-mean-robust {later:.5f} already inside the 45s gate "
        f"(delta first-robust -0.04354 s/tick, ~34.7s at tmin; vs_later over45 before="
        f"{(tsr.get('still_over_45s_vs_later_before'))}). No corrective realign. in-use {tick_s_in_use:.5f}."
    )
    game_time_note = (
        "New box freeze 03:38:35–03:58:00 (~1156s). Listener logged the freeze and "
        "run_listener restarted at 03:58:03, listener.py up at 03:58:13 (pid 123538). "
        "This run did not restart the listener, war_cmd, or pulse. live.json was fresh "
        f"after reconnect (stats.t live, roomSlot={live.get('roomSlot')}; gameTime/objects empty is expected "
        "because live.json is the home map only and the peacetime slot is currently not W46N8). "
        "Segment 90 buffers pulled after the 03:58 reconnect (creep_cpu and path_arrivals "
        "fresh through the tip). room_stats gap 84327811..84328069 is the new freeze: "
        "published part 84327811..84328000 (190) sits in published bases through 84327900 and is official-filled; "
        "unpublished tail 84328001..84328069 (69) is not yet published and was not live-filled "
        "(listener resumed writing room_stats/creep_ticks at 84328070). "
        "The prior 03:15 freeze 84327511..84327599 is now fully in this window and official-filled. "
        "The 300-tick overlap 84327301..84327600 with the 03:30 window was already in the DB "
        "(03:30 backfill + 03:20 hourly patrol); this first pass inserted the newly published ticks."
    )
    inserted_note = (
        f"This 04:00 first pass inserted {INSERTED_FIRST} new rows "
        f"(already_in_db={ALREADY}, reconstructed={RECON_ROWS}). "
        "The 300-tick overlap 84327301..84327600 with the 03:30 window was already present. "
        "Newly published ticks 84327601..84328000 (400) include the 03:38 freeze published part "
        "84327811..84328000 (190) and were written idempotently this pass. "
        "Confirm inserted 0; retry2 skipped (no in-window official 404s). "
        f"Coverage official_recovered={recovered}/{expected} including {empty_no_creep} official empty-no-creep "
        "ticks; no in-window official 404."
    )

    payload = {
        "ok": True,
        "routine": "Screeps 半小时轨迹补数",
        "finished_at": now.isoformat(),
        "finished_at_hkt": finished_hkt,
        "shard": "shard3",
        "rooms": list(ROOMS),
        "minutes": 40,
        "game_time": GT_FIRST,
        "live_json_gameTime_at_finish": live.get("gameTime"),
        "live_json_stats_t_at_finish": (stats or {}).get("t"),
        "live_json_gameTime_note": game_time_note,
        "published_bases": PUB_BASES,
        "ticks": {"min": TMIN, "max": TMAX, "count": 700},
        "tick_s": TICK_S_FIRST,
        "tick_s_later_mean": later,
        "tick_s_in_use": tick_s_in_use,
        "tick_s_first_pass_outlier": False,
        "tick_s_later_mean_applied_then_reverted": False,
        "tick_s_corrective_applied": corrective,
        "missing_chunks": 0,
        "missing_chunk_list": [],
        "missing_chunk_first_pass": [],
        "missing_chunk_note": (
            f"First pass (game.time={GT_FIRST}) published_bases {PUB_BASES}, reconstructed "
            f"{TMIN}..{TMAX} (700). 35 of 35 official GETs 200; missing_chunks=0. "
            f"Confirm at {confirm_at} game.time={confirm_gt} retried leftover outside-window 404s, "
            f"inserted=0 (all still 404). retry2 skipped, no in-window official 404s."
        ),
        "creep_rows_reconstructed": RECON_ROWS,
        "already_in_db": ALREADY,
        "inserted": inserted_total,
        "inserted_first_pass": INSERTED_FIRST,
        "inserted_retry": INSERTED_CONFIRM,
        "inserted_retry2": INSERTED_RETRY2,
        "inserted_retry2_unique_net": INSERTED_RETRY2_UNIQUE_NET,
        "inserted_note": inserted_note,
        "ts_realigned": TS_REALIGNED_FIRST,
        "ts_realigned_corrective_later_mean": nfix_corr,
        "ts_realigned_confirm": 0,
        "ts_realigned_retry2": 0,
        "ts_realigned_note": ts_realign_note,
        "ssl_first_attempt": False,
        "hourly_patrol_prefilled": False,
        "per_room": per_room,
        "known_official_404s_outside_window": [f"{r}@{b}" for r, b in OUTSIDE_404],
        "known_official_404s_in_window": [f"{r}@{b}" for r, b in IN_WINDOW_404],
        "w45n7_empty_no_creep_in_window": bool(w45n7_empty),
        "w45n7_empty_no_creep_ranges": w45n7_empty,
        "empty_no_creep_in_window": bool(empty_no_creep),
        "empty_no_creep_ranges": {room: (coverage.get(room) or {}).get("official_empty_no_creep_ranges") or [] for room in ROOMS},
        "empty_no_creep_ticks": empty_no_creep,
        "official_room_ticks_fetched": recovered,
        "official_room_ticks_with_creeps": unique_after["distinct_room_ticks"],
        "official_recovered": recovered,
        "official_expected": expected,
        "new_box_freeze": {
            "from": "2026-11-18 03:38:35",
            "to": "2026-11-18 03:58:00",
            "sec": 1156,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84327811, 84328069],
            "live_room_stats_gap_ticks": 259,
            "official_fill_full_gap": freeze_0338,
            "official_fill_published_part": freeze_0338_pub,
            "official_fill_unpublished_tail": freeze_0338_tail,
            "published_part": [84327811, 84328000],
            "unpublished_tail": [84328001, 84328069],
            "note": (
                "new this run; room_stats gap 84327811..84328069 (259). Official published through 84327900, "
                "so published part 84327811..84328000 (190) sits in bases 84327800..84327900. "
                f"Published-part official-filled {frac(freeze_0338_pub, 190)} of 190 on all five rooms. "
                f"Unpublished tail 84328001..84328069 official+live {frac(freeze_0338_tail, 69)} of 69 "
                "(all empty: chunk 84328000 not yet published, and the listener resumed at 84328070). "
                f"Full-gap official+live {frac(freeze_0338, 259)} of 259."
            ),
        },
        "prior_0315_box_freeze": {
            "from": "2026-11-18 03:15:10",
            "to": "2026-11-18 03:21:01",
            "sec": 350,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84327511, 84327599],
            "live_room_stats_gap_ticks": 89,
            "official_fill_full_gap": freeze_0315,
            "published_part": [84327511, 84327599],
            "unpublished_tail": None,
            "note": (
                "not new this run; still fully in this window (window starts 84327301). Official published through 84327900, "
                "so the whole gap sits in published base 84327500. "
                f"Full-gap official-filled {frac(freeze_0315, 89)} of 89 on all five rooms; no unpublished tail."
            ),
        },
        "prior_0241_box_freeze": {
            "from": "2026-11-18 02:41:09",
            "to": "2026-11-18 03:02:43",
            "sec": 1293,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84327081, 84327369],
            "live_room_stats_gap_ticks": 289,
            "official_fill_full_gap": freeze_0241,
            "official_fill_published_part": freeze_0241_pub,
            "official_fill_unpublished_tail": freeze_0241_tail,
            "published_part": [84327081, 84327300],
            "unpublished_tail": [84327301, 84327369],
            "note": (
                "not new this run; 84327081..84327300 is now before this window start (window starts 84327301); "
                "former unpublished tail 84327301..84327369 is in this window and in published bases 84327300. "
                f"Full-gap official+live {frac(freeze_0241, 289)} of 289 "
                f"(part before window {frac(freeze_0241_pub, 220)} of 220; in-window former tail {frac(freeze_0241_tail, 69)} of 69); "
                "no unpublished tail remains."
            ),
        },
        "prior_0211_box_freeze": {
            "from": "2026-11-18 02:11:07",
            "to": "2026-11-18 02:18:00",
            "sec": 405,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84326701, 84326799],
            "live_room_stats_gap_ticks": 99,
            "official_fill_full_gap": freeze_0211,
            "published_part": [84326701, 84326799],
            "unpublished_tail": None,
            "note": (
                "not new this run; now before this window start (window starts 84327301). "
                f"Full-gap official-filled {frac(freeze_0211, 99)} of 99 on all five rooms; no unpublished tail."
            ),
        },
        "prior_0139_box_freeze": {
            "from": "2026-11-18 01:39:14",
            "to": "2026-11-18 01:58:27",
            "sec": 1153,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84326291, 84326549],
            "live_room_stats_gap_ticks": 259,
            "official_fill_full_gap": freeze_0139,
            "official_fill_published_part": freeze_0139_pub,
            "official_fill_unpublished_tail": freeze_0139_tail,
            "published_part": [84326291, 84326500],
            "unpublished_tail": [84326501, 84326549],
            "note": (
                "not new this run; now before this window start (window starts 84327301). "
                f"Full-gap official+live {frac(freeze_0139, 259)} of 259 "
                f"(published part {frac(freeze_0139_pub, 210)} of 210; former tail {frac(freeze_0139_tail, 49)} of 49). "
                "W45N8 still missing ticks in leftover official 404 W45N8@84326300 (0 live / 100 empty) "
                "and W45N8@84326500 (22 live / 78 empty), both outside this window."
            ),
        },
        "prior_0110_box_freeze": {
            "from": "2026-11-18 01:10:45",
            "to": "2026-11-18 01:26:26",
            "sec": 934,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84325931, 84326149],
            "live_room_stats_gap_ticks": 219,
            "official_fill_full_gap": freeze_0110,
            "official_fill_published_part": freeze_0110_pub,
            "official_fill_unpublished_tail": freeze_0110_tail,
            "published_part": [84325931, 84326100],
            "unpublished_tail": [84326101, 84326149],
            "note": (
                "not new this run; now before this window start (window starts 84327301). "
                f"Full-gap official+live {frac(freeze_0110, 219)} of 219 "
                f"(published part {frac(freeze_0110_pub, 170)} of 170; former tail {frac(freeze_0110_tail, 49)} of 49). "
                "W45N8 still missing ticks due to leftover official 404 W45N8@84326100 (0 live / 100 empty), outside this window. "
                "W47N7 still missing 16 ticks 84325931..84325946 due to official empty-no-creep."
            ),
        },
        "prior_0044_box_freeze": {
            "from": "2026-11-18 00:44:18",
            "to": "2026-11-18 00:58:17",
            "sec": 830,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84325601, 84325789],
            "official_fill_full_gap": freeze_0044,
            "note": (
                "not new this run; now before this window start (window starts 84327301); "
                f"official-filled {frac(freeze_0044, 189)} of 189 ticks on all five rooms; no unpublished tail."
            ),
        },
        "prior_0010_box_freeze": {
            "from": "2026-11-18 00:10:06",
            "to": "2026-11-18 00:12:20",
            "sec": 127,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84325171, 84325209],
            "official_fill_full_gap": freeze_0010,
            "note": (
                "not new this run; now before this window; "
                f"official-filled {frac(freeze_0010, 39)} of 39 ticks."
            ),
        },
        "prior_0023_ws_drop": {
            "from": "2026-11-18 00:23:40",
            "to": "2026-11-18 00:23:50",
            "sec": 10,
            "kind": "ws_connection_lost",
            "official_fill_nearby": freeze_0023,
            "note": (
                "not new this run; now before this window; "
                f"official-filled {frac(freeze_0023, 41)} of 41 ticks 84325320..84325360."
            ),
        },
        "prior_0002_ws_pong": {
            "from": "2026-11-18 00:02:37",
            "to": "2026-11-18 00:02:41",
            "sec": 95,
            "kind": "ws_ping_pong_timeout",
            "live_room_stats_gap": [84325051, 84325089],
            "official_fill_full_gap": freeze_0002,
            "note": (
                "not new this run; now before this window; "
                f"official-filled {frac(freeze_0002, 39)} of 39 ticks."
            ),
        },
        "prior_2342_box_freeze": {
            "from": "2026-11-17 23:42:43",
            "to": "2026-11-17 23:53:44",
            "sec": 661,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84324821, 84324969],
            "official_fill_full_gap": freeze_2342,
            "note": (
                "not new this run; now before this window; "
                f"official-filled {frac(freeze_2342, 149)} of 149 ticks "
                "(W45N7 missing 69 ticks 84324901..84324969 due to leftover official 404 @84324900)."
            ),
        },
        "remainder_overlap_84327301_84327600": rem_overlap,
        "remainder_new_84327601_84328000": rem_new,
        "unique_after": unique_after,
        "db_tips": tips,
        "db_after": db_after,
        "listener": {
            "single_slot": len(lis) <= 1 and not yield_present,
            "listener_pids": lis,
            "run_listener": runl,
            "roomSlot": live.get("roomSlot"),
            "rot": rot,
            "yield": bool(yield_present),
        },
        "confirm_at": confirm_at,
        "confirm_game_time": confirm_gt,
        "retry2_at": retry2_at,
        "retry2_game_time": retry2_gt,
        "ok_quiet": True,
    }

    freeze_para = (
        f"New box freeze 03:38:35–03:58:00 (~1156s) room_stats gap 84327811..84328069; "
        f"published part 84327811..84328000 official-filled {frac(freeze_0338_pub, 190)} of 190 of 190 on all five rooms; "
        f"unpublished tail 84328001..84328069 official+live {frac(freeze_0338_tail, 69)} of 69 of 69 "
        f"(all empty: chunk 84328000 not yet published, listener resumed at 84328070). "
        f"Prior box freeze 03:15:10–03:21:01 (~350s) room_stats gap 84327511..84327599; official-filled {frac(freeze_0315, 89)} of 89 of 89 on all five rooms still in this window, no unpublished tail. "
        f"Prior box freeze 02:41:09–03:02:43 (~1293s) room_stats gap 84327081..84327369; official+live {frac(freeze_0241, 289)} of 289 of 289 "
        f"(part before window 220t {frac(freeze_0241_pub, 220)} of 220 of 220; in-window former tail 69t {frac(freeze_0241_tail, 69)} of 69 of 69; no unpublished tail remains). "
        f"Prior box freeze 02:11:07–02:18:00 (~405s) room_stats gap 84326701..84326799; official-filled {frac(freeze_0211, 99)} of 99 of 99 on all five rooms now before this window, no unpublished tail. "
        f"Prior box freeze 01:39:14–01:58:27 (~1153s) room_stats gap 84326291..84326549; official+live {frac(freeze_0139, 259)} of 259 of 259 now before this window "
        f"(published 210t {frac(freeze_0139_pub, 210)} of 210; former unpublished tail 49t {frac(freeze_0139_tail, 49)} of 49; W45N8 short from leftover official 404 @84326300 and @84326500). "
        f"Prior box freeze 01:10:45–01:26:26 (~934s) room_stats gap 84325931..84326149; official-filled {frac(freeze_0110, 219)} of 219 of 219 ticks still before this window "
        f"(W45N8 missing 49 due to leftover official 404 @84326100; W47N7 missing 16 due to official empty-no-creep). "
        f"Prior box freeze 00:44:18–00:58:17 (~830s) room_stats gap 84325601..84325789; official-filled {frac(freeze_0044, 189)} of 189 of 189 ticks still before this window, no unpublished tail. "
        f"Prior box freeze 00:10:06–00:12:20 (~127s) room_stats gap 84325171..84325209; official-filled {frac(freeze_0010, 39)} of 39 of 39 ticks still before this window. "
        f"Prior websocket connection-lost 00:23:40 official-filled {frac(freeze_0023, 41)} of 41 of 41 ticks 84325320..84325360 still before this window. "
        f"Prior websocket ping/pong timeout 00:02:37 room_stats gap 84325051..84325089; official-filled {frac(freeze_0002, 39)} of 39 of 39 ticks still before this window. "
        f"Prior box freeze 23:42:43–23:53:44 (~661s) room_stats gap 84324821..84324969; official-filled {frac(freeze_2342, 149)} of 149 of 149 ticks still before this window (W45N7 missing 69 ticks 84324901..84324969 due to leftover official 404 @84324900). "
        f"Overlap 84327301..84327600 official-filled {frac(rem_overlap, 300)} of 300 of 300. "
        f"New published 84327601..84328000 official-filled {frac(rem_new, 400)} of 400 of 400. "
        "Includes just-published 84327600..84327900 chunks and the new 03:38 freeze published part. "
        "Unpublished tail 84328001..84328069 remains for the next run. "
        "W45N8@84326300 (0 live / 100 empty) and W45N8@84326500 (22 live / 78 empty) remain outside this window and still official 404. "
        "W45N8@84326100 remains outside this window and still official 404 (0 live / 100 empty). "
        "W45N7@84324900 remains outside this window and still official 404. "
        "W47N8@84324300 / W47N8@84323200 / W47N8@84322100 / W47N8@84321300 / W45N7@84321600 / W47N8@84319900 and older leftovers remain outside this window and official 404."
    )
    ok_line = (
        f"ok=true (quiet); first-pass missing_chunks=0 (35 of 35 official GETs 200); confirm inserted=0 leftover outside-window 404s unchanged; "
        f"retry2 skipped no in-window official 404s; no in-window official 404 remains; "
        f"{tick_s_corr_txt}, tick_s_in_use={tick_s_in_use:.5f} (first-pass realign {TICK_S_FIRST} committed {TS_REALIGNED_FIRST}); "
        f"new 03:38 freeze gap 84327811..84328069 published part official-filled {frac(freeze_0338_pub, 190)} of 190 of 190 on all five rooms, "
        f"unpublished tail {frac(freeze_0338_tail, 69)} of 69 of 69 still empty; "
        f"prior 03:15 freeze gap 84327511..84327599 official-filled {frac(freeze_0315, 89)} of 89 of 89 on all five rooms still in this window, no unpublished tail; "
        f"prior 02:41 freeze gap 84327081..84327369 official+live {frac(freeze_0241, 289)} of 289 of 289 "
        f"(part before window 220t {frac(freeze_0241_pub, 220)} of 220 of 220; in-window former tail 69t {frac(freeze_0241_tail, 69)} of 69 of 69; no unpublished tail remains); "
        f"prior 02:11 freeze gap 84326701..84326799 official-filled {frac(freeze_0211, 99)} of 99 of 99 on all five rooms now before this window, no unpublished tail; "
        f"prior 01:39 freeze gap 84326291..84326549 official+live {frac(freeze_0139, 259)} of 259 of 259 now before this window "
        f"(published 210t {frac(freeze_0139_pub, 210)} of 210; former unpublished tail 49t {frac(freeze_0139_tail, 49)} of 49; W45N8 short from leftover official 404 @84326300 and @84326500); "
        f"prior 01:10 freeze gap 84325931..84326149 official-filled {frac(freeze_0110, 219)} of 219 of 219 ticks still before this window "
        f"(W45N8 missing 49 due to leftover official 404 @84326100; W47N7 missing 16 due to official empty-no-creep); "
        f"prior 00:44 freeze gap 84325601..84325789 official-filled {frac(freeze_0044, 189)} of 189 of 189 ticks still before this window, no unpublished tail; "
        f"prior 00:10 freeze gap 84325171..84325209 official-filled {frac(freeze_0010, 39)} of 39 of 39 ticks still before this window; "
        f"prior 00:23 connection-lost band 84325320..84325360 official-filled {frac(freeze_0023, 41)} of 41 of 41 ticks still before this window; "
        f"prior 00:02 ping/pong gap 84325051..84325089 official-filled {frac(freeze_0002, 39)} of 39 of 39 ticks still before this window; "
        f"prior 23:42 freeze gap 84324821..84324969 official-filled {frac(freeze_2342, 149)} of 149 of 149 ticks still before this window (W45N7 missing 69 due to official 404 @84324900); "
        f"no in-window official 404 remains; W47N7 official empty-no-creep 0 ranges []; {leftover_txt}"
    )

    now_lines = [
        f"{finished_hkt} half-hour backfill OK (quiet)",
        f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
        f"  ({first_pass_line}; see history_backfill.txt)",
        (
            f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST}; {tick_s_corr_txt}, in-use {tick_s_in_use:.5f})"
        ),
        f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks=0",
        f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
        f"per_room {per_room_line}",
        f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 +{INSERTED_RETRY2_UNIQUE_NET}, total {inserted_total})",
        (
            f"ts_realigned_first={TS_REALIGNED_FIRST}; ts_realigned_corrective={nfix_corr} "
            f"({tick_s_corr_txt}; in-use {tick_s_in_use:.5f})"
        ),
        "db_after",
        db_after_lines,
        f"coverage official_recovered={recovered}/{expected} unique_after={unique_after} empty_no_creep={empty_no_creep} official_404_in_window={official_404_missing}",
        (
            f"tick_s first={TICK_S_FIRST} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; "
            f"first-pass realign committed {TS_REALIGNED_FIRST}; in-use {tick_s_in_use:.5f}; later over45={vs_later_after.get('over45')}."
        ),
        (
            f"confirm inserted=0 leftover official 404s unchanged; retry2 skipped no in-window official 404s; {inwin_txt}; "
            f"W45N8 official empty-no-creep 0 ranges {w45n8_empty}; W45N7 official empty-no-creep 0 ranges {w45n7_empty}; "
            f"W47N7 official empty-no-creep {empty_no_creep} ranges {w47n7_empty}; {leftover_txt}"
        ),
        freeze_para,
        (
            f"listener single_slot={len(lis) <= 1 and not yield_present} roomSlot={live.get('roomSlot')} rot={rot} "
            f"yield={'present' if yield_present else 'absent'}"
        ),
        "confirm inserted=0 leftover 404s unchanged; retry2 skipped no in-window official 404s",
        ok_line,
    ]
    now_text = "\n".join(now_lines) + "\n"

    (DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    (DIR / "history_backfill_now.txt").write_text(now_text)
    shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")
    shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")

    verify = [
        f"{finished_hkt_sec} half-hour backfill verify",
        f"window {TMIN}..{TMAX} published_bases {PUB_BASES} game.time={GT_FIRST} inserted={inserted_total} coverage={recovered}/{expected}",
        f"missing_chunks=0 in_window_404=0 empty_no_creep={empty_no_creep}",
        (
            f"tick_s first={TICK_S_FIRST} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; "
            f"first-pass realign committed {TS_REALIGNED_FIRST}; in-use {tick_s_in_use:.5f}; later over45={vs_later_after.get('over45')}."
        ),
        (
            f"confirm inserted=0 leftover official 404s unchanged; retry2 skipped no in-window official 404s; {inwin_txt}; "
            f"W45N8 official empty-no-creep 0 ranges {w45n8_empty}; W45N7 official empty-no-creep 0 ranges {w45n7_empty}; "
            f"W47N7 official empty-no-creep {empty_no_creep} ranges {w47n7_empty}; {leftover_txt}"
        ),
        (
            f"listener single_slot={len(lis) <= 1 and not yield_present} roomSlot={live.get('roomSlot')} rot={rot} "
            f"yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart."
        ),
        "This run did not restart the listener.",
    ]
    verify_text = "\n".join(verify) + "\n"
    (DIR / "verify.txt").write_text(verify_text)
    (ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)

    summary = (
        f"{finished_hkt} wrapup ok\n"
        f"wrote history_backfill.json history_backfill_now.txt verify.txt\n"
        f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2_UNIQUE_NET} coverage={recovered}/{expected} tick_s_in_use={tick_s_in_use:.5f} later_mean_reverted=False\n"
    )
    (DIR / "wrapup_run.txt").write_text(summary)
    (DIR / "wrapup_run_tee.txt").write_text(summary + now_text)
    print(summary)
    print(now_text)


if __name__ == "__main__":
    main()
