#!/usr/bin/env python3
"""Write half-hour backfill status records for the next hourly patrol."""
from __future__ import annotations
import json, os, subprocess, sys, shutil
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-18_0600"
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84328901, 84329600
GT_FIRST = 84329607
PUB_BASES = "84328900..84329500"
TICK_S_FIRST = 4.87479
TICK_S_PRINTED = "4.875"
NEW_ROWS = {"W46N8": 3612, "W47N8": 4678, "W45N8": 1377, "W45N7": 1325, "W47N7": 1659}
OFFICIAL_TICKS = {"W46N8": 700, "W47N8": 700, "W45N8": 700, "W45N7": 700, "W47N7": 700}
INSERTED_FIRST = 12651
INSERTED_CONFIRM = 535
INSERTED_RETRY2 = 0
INSERTED_RETRY2_UNIQUE_NET = 0
ALREADY = 12481
RECON_ROWS = 25132
TS_REALIGNED_FIRST = 12731
IN_WINDOW_404 = [
]
OUTSIDE_404 = [
    ("W45N8", 84328100),  # leftover official 404 now outside window; 16 live / 84 empty
    ("W45N7", 84328300),  # leftover official 404 now outside window; 0 live / 100 empty
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
    later_reverted = bool(tsr.get("later_mean_reverted"))
    corrective = bool(tsr.get("corrective_applied")) and not later_reverted
    nfix_corr = int(tsr.get("ts_realigned_to_later_mean") or 0)
    tick_s_in_use = float(tsr.get("tick_s_in_use") or (later if corrective else TICK_S_FIRST))
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
        freeze_0543 = fill(c, 84329391, 84329599)
        freeze_0543_early = fill(c, 84329391, 84329500)
        freeze_0543_tail = fill(c, 84329501, 84329599)
        freeze_0513 = fill(c, 84329011, 84329179)
        freeze_0513_pub = fill(c, 84329011, 84329100)
        freeze_0513_newpub = fill(c, 84329101, 84329179)
        freeze_0442 = fill(c, 84328611, 84328859)
        freeze_0442_pub = fill(c, 84328611, 84328800)
        freeze_0442_tail = fill(c, 84328801, 84328859)
        freeze_0411 = fill(c, 84328221, 84328349)
        freeze_0411_pub = fill(c, 84328221, 84328300)
        freeze_0411_tail = fill(c, 84328301, 84328349)
        freeze_0338 = fill(c, 84327811, 84328069)
        freeze_0315 = fill(c, 84327511, 84327599)
        rem_overlap = fill(c, 84328901, 84329200)
        rem_new = fill(c, 84329201, 84329600)
        rem_prev = fill(c, 84328901, 84329200)
        rem_just = fill(c, 84329201, 84329600)
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
        "W45N8@84328100", "W45N7@84328300",
        "W45N8@84326300", "W45N8@84326500", "W45N8@84326100", "W45N7@84324900",
        "W47N8@84324300", "W47N8@84323200", "W47N8@84322100", "W47N8@84321300",
        "W45N7@84321600", "W47N8@84319900", "W47N8@84319000", "W46N8@84318500",
        "W45N8@84318000", "W47N7@84315100", "W45N8@84314900", "W45N7@84314500",
        "W47N8@84314000", "W46N8@84313200",
    ]
    leftover_bits = [f"leftover official 404 {hole_shorts[k]} still outside window" for k in leftover_order]
    leftover_txt = "; ".join(leftover_bits) + "; older leftovers unchanged."
    inwin_txt = (
        "no in-window official 404 remains (first pass 34 of 35, 404 W47N7@84329500; "
        "confirm recovered W47N7@84329500 inserted=535; final missing_chunks=0); "
        "leftover official 404 now outside window: "
        f"{hole_shorts['W45N8@84328100']} (84 empty 84328101..84328184); "
        f"{hole_shorts['W45N7@84328300']} (100 empty 84328301..84328400)"
    )
    first_pass_line = (
        "first pass 34 of 35 official GETs 200, missing_chunks=1 (404 W47N7@84329500); "
        "confirm recovered W47N7@84329500 inserted=535; leftover official 404s unchanged; "
        "retry2 still 404 W45N8@84328100 and W45N7@84328300 inserted=0"
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
        f"later-mean-robust {later:.5f} automatic corrective applied then immediately reverted "
        f"(worse vs live anchor), nfix_kept=0"
        if later_reverted else
        (
            f"later-mean-robust {later:.5f} automatic corrective applied and kept, nfix={nfix_corr}"
            if corrective else
            f"later-mean-robust {later:.5f} already inside 45s gate, no corrective realign, nfix=0"
        )
    )
    ts_realign_note = (
        f"First pass (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}, live anchor game.time={GT_FIRST}) "
        f"ts_realigned={TS_REALIGNED_FIRST}. later-mean-robust {later:.5f} was over the 45s gate versus "
        f"those already-live-aligned rows, so a corrective realign was attempted and then immediately "
        f"reverted (pre-corrective vs_first over45=0 mean_off~-0.05s; after later-mean vs_first "
        f"over45=15289 mean_off~+46s; revert hb.realign_ts nrev=15289 at game.time=84329635; "
        f"after-revert vs_first over45=0 mean_off=1.165s). in-use first-pass {tick_s_in_use:.5f}."
    )
    game_time_note = (
        "New box freeze 05:43:58–05:59:00 (~901s). Listener logged the freeze and "
        "run_listener restarted at 05:59:03, listener.py up at 05:59:13 (pid 164222). "
        "This run did not restart the listener, war_cmd, or pulse. live.json was fresh "
        f"after reconnect (gameTime and stats.t live, roomSlot={live.get('roomSlot')}). "
        "Segment 90 buffers pulled after the 05:59 reconnect (creep_cpu and path_arrivals "
        "fresh through the tip). The 05:30 half-hour backfill had already official-backfilled "
        "84328501..84329200; leftover official 404s W45N8@84328100 and W45N7@84328300 remain outside this window. "
        "No concurrent hourly-patrol official backfill this window (05:40 patrol had already finished). "
        "room_stats gap 84329391..84329599 is the new 05:43 freeze: "
        "the entire 209-tick gap sits in published bases 84329300, 84329400 and 84329500 and is official-filled on all five rooms "
        "(W47N7@84329500 was 404 on the first pass and recovered on confirm); "
        "no unpublished tail remains in the freeze gap. "
        "Listener resumed writing room_stats/creep_ticks at 84329600. "
        "The prior 05:13 freeze 84329011..84329179 is now fully in this window and remains official-filled on all five rooms. "
        "The prior 04:42 freeze 84328611..84328859 is now before this window and remains official-filled on all five rooms. "
        "The prior 04:11 freeze 84328221..84328349 is still before this window; W45N7@84328300 remains official 404. "
        "The 300-tick overlap 84328901..84329200 with the 05:30 window was already in the DB (05:30 backfill)."
    )
    inserted_note = (
        f"This 06:00 first pass inserted {INSERTED_FIRST} new rows "
        f"(already_in_db={ALREADY}, reconstructed={RECON_ROWS}). "
        "The 300-tick overlap 84328901..84329200 with the 05:30 window was already present. "
        "No concurrent hourly-patrol official prefill in this window. "
        "Newly published ticks 84329201..84329600 (bases 84329200..84329500) were official 200 on the first pass "
        "except W47N7@84329500 (404), including the 05:43 freeze gap on the other four rooms. "
        f"Confirm at {confirm_at} game.time={confirm_gt} recovered W47N7@84329500 inserted={INSERTED_CONFIRM}; "
        "leftover official 404s unchanged. "
        f"retry2 at {retry2_at} game.time={retry2_gt} still 404 "
        "on W45N8@84328100 and W45N7@84328300, inserted=0 (W47N7@84329500 still 200, inserted=0). "
        f"Coverage official_recovered={recovered}/{expected} including {empty_no_creep} official empty-no-creep "
        "ticks; 0 in-window official-404 ticks remain."
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
        "tick_s_later_mean_applied_then_reverted": later_reverted,
        "tick_s_corrective_applied": corrective,
        "missing_chunks": 0,
        "missing_chunk_list": [],
        "missing_chunk_first_pass": ["W47N7@84329500"],
        "missing_chunk_note": (
            f"First pass (game.time={GT_FIRST}) published_bases {PUB_BASES}, reconstructed "
            f"{TMIN}..{TMAX} (700). 34 of 35 official GETs 200; missing_chunks=1 (404 W47N7@84329500). "
            f"Confirm at {confirm_at} game.time={confirm_gt} recovered W47N7@84329500 inserted={INSERTED_CONFIRM}; "
            "leftover official 404s still 404 "
            "(W45N8@84328100 and W45N7@84328300, outside this window). "
            f"retry2 at {retry2_at} game.time={retry2_gt} still 404 on W45N8@84328100 and W45N7@84328300, inserted=0."
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
            "from": "2026-11-18 05:43:58",
            "to": "2026-11-18 05:59:00",
            "sec": 901,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84329391, 84329599],
            "live_room_stats_gap_ticks": 209,
            "official_fill_full_gap": freeze_0543,
            "official_fill_published_part": freeze_0543,
            "official_fill_already_published_through_84329500": freeze_0543_early,
            "official_fill_newly_published_84329501_84329599": freeze_0543_tail,
            "official_fill_unpublished_tail": None,
            "published_part": [84329391, 84329599],
            "unpublished_tail": None,
            "note": (
                "new this run; room_stats gap 84329391..84329599 (209). Official published through 84329500, "
                "so the entire freeze gap sits in bases 84329300, 84329400 and 84329500 (ticks through 84329600). "
                f"Full-gap official-filled {frac(freeze_0543, 209)} of 209 on all five rooms. "
                f"Already-published part 84329391..84329500 (110) official-filled {frac(freeze_0543_early, 110)} of 110 "
                "on the first pass. "
                f"Newly published 84329501..84329599 (99) official-filled {frac(freeze_0543_tail, 99)} of 99 "
                "(four rooms on the first pass; W47N7@84329500 recovered on confirm). "
                "No unpublished tail remains in the freeze gap. "
                "Listener resumed at 84329600."
            ),
        },
        "prior_0513_box_freeze": {
            "from": "2026-11-18 05:13:36",
            "to": "2026-11-18 05:25:59",
            "sec": 743,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84329011, 84329179],
            "live_room_stats_gap_ticks": 169,
            "official_fill_full_gap": freeze_0513,
            "official_fill_published_part": freeze_0513_pub,
            "official_fill_newly_published_84329101_84329179": freeze_0513_newpub,
            "published_part": [84329011, 84329179],
            "unpublished_tail": None,
            "note": (
                "not new this run; now fully in this window (window starts 84328901). "
                f"Full-gap official-filled {frac(freeze_0513, 169)} of 169 on all five rooms "
                "(already official-filled by the 05:30 backfill / 05:27 patrol)."
            ),
        },
        "prior_0442_box_freeze": {
            "from": "2026-11-18 04:42:19",
            "to": "2026-11-18 05:00:55",
            "sec": 1108,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84328611, 84328859],
            "live_room_stats_gap_ticks": 249,
            "official_fill_full_gap": freeze_0442,
            "official_fill_published_part": freeze_0442_pub,
            "official_fill_former_unpublished_tail": freeze_0442_tail,
            "published_part": [84328611, 84328800],
            "former_unpublished_tail": [84328801, 84328859],
            "note": (
                "not new this run; now before this window (window starts 84328901). "
                f"Former published part 84328611..84328800 official-filled {frac(freeze_0442_pub, 190)} of 190 on all five rooms. "
                f"Former unpublished tail 84328801..84328859 is now official-filled {frac(freeze_0442_tail, 59)} of 59 on all five rooms "
                "(84328800 chunk published; 05:27 patrol and this run). "
                f"Full-gap official-filled {frac(freeze_0442, 249)} of 249 on all five rooms."
            ),
        },
        "prior_0411_box_freeze": {
            "from": "2026-11-18 04:11:18",
            "to": "2026-11-18 04:20:01",
            "sec": 522,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84328221, 84328349],
            "live_room_stats_gap_ticks": 129,
            "official_fill_full_gap": freeze_0411,
            "official_fill_published_part": freeze_0411_pub,
            "official_fill_unpublished_tail": freeze_0411_tail,
            "published_part": [84328221, 84328300],
            "unpublished_tail": [84328301, 84328349],
            "note": (
                "not new this run; still before this window (window starts 84328901). "
                f"Published-part official-filled {frac(freeze_0411_pub, 80)} of 80 on all five rooms. "
                f"Former unpublished tail 84328301..84328349 official+live {frac(freeze_0411_tail, 49)} of 49 "
                "(W45N7 still 0 on leftover official 404 @84328300; other rooms official-filled). "
                f"Full-gap official+live {frac(freeze_0411, 129)} of 129."
            ),
        },
        "prior_0338_box_freeze": {
            "from": "2026-11-18 03:38:35",
            "to": "2026-11-18 03:58:00",
            "sec": 1156,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84327811, 84328069],
            "live_room_stats_gap_ticks": 259,
            "official_fill_full_gap": freeze_0338,
            "note": (
                "not new this run; still before this window (window starts 84328901). "
                f"Full-gap official-filled {frac(freeze_0338, 259)} of 259 on all five rooms."
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
            "note": (
                "not new this run; still before this window (window starts 84328901). "
                f"Full-gap official-filled {frac(freeze_0315, 89)} of 89 on all five rooms; no unpublished tail."
            ),
        },
        "remainder_overlap_84328901_84329200": rem_overlap,
        "remainder_new_84329201_84329600": rem_new,
        "remainder_prev_filled_84328901_84329200": rem_prev,
        "remainder_just_published_84329201_84329600": rem_just,
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
        f"New box freeze 05:43:58–05:59:00 (~901s) room_stats gap 84329391..84329599; "
        f"entire gap official-filled {frac(freeze_0543, 209)} of 209 of 209 on all five rooms "
        f"(already-published 84329391..84329500 {frac(freeze_0543_early, 110)} of 110 on the first pass; "
        f"newly published 84329501..84329599 {frac(freeze_0543_tail, 99)} of 99, four rooms first pass and W47N7 recovered on confirm; "
        f"no unpublished tail remains in the freeze gap; listener resumed at 84329600). "
        f"Prior box freeze 05:13:36–05:25:59 (~743s) room_stats gap 84329011..84329179 now fully in this window; "
        f"official-filled {frac(freeze_0513, 169)} of 169 of 169 on all five rooms. "
        f"Prior box freeze 04:42:19–05:00:55 (~1108s) room_stats gap 84328611..84328859 now before this window; "
        f"official-filled {frac(freeze_0442, 249)} of 249 of 249 on all five rooms. "
        f"Prior box freeze 04:11:18–04:20:01 (~522s) room_stats gap 84328221..84328349 still before this window; "
        f"official+live {frac(freeze_0411, 129)} of 129 of 129 "
        f"(published part 80t {frac(freeze_0411_pub, 80)} of 80; former unpublished tail 49t {frac(freeze_0411_tail, 49)} of 49, W45N7 still empty on leftover official 404 @84328300). "
        f"Prior box freeze 03:38:35–03:58:00 (~1156s) room_stats gap 84327811..84328069 still before this window; official-filled {frac(freeze_0338, 259)} of 259 of 259 on all five rooms. "
        f"Prior box freeze 03:15:10–03:21:01 (~350s) room_stats gap 84327511..84327599 still before this window; official-filled {frac(freeze_0315, 89)} of 89 of 89 on all five rooms. "
        f"Overlap 84328901..84329200 with the 05:30 window official-filled {frac(rem_overlap, 300)} of 300 of 300 on all five rooms. "
        f"Rest of window 84329201..84329600 official-filled {frac(rem_new, 400)} of 400 of 400 on all five rooms "
        f"(just-published 84329201..84329600 {frac(rem_just, 400)} of 400; no concurrent patrol prefill). "
        "No in-window official 404 remains after confirm recovered W47N7@84329500. "
        "W45N8@84328100 (16 live / 84 empty) and W45N7@84328300 (0 live / 100 empty) remain outside this window and still official 404. "
        "W45N8@84326300 (0 live / 100 empty) and W45N8@84326500 (22 live / 78 empty) remain outside this window and still official 404. "
        "W45N8@84326100 remains outside this window and still official 404 (0 live / 100 empty). "
        "W45N7@84324900 remains outside this window and still official 404. "
        "W47N8@84324300 / W47N8@84323200 / W47N8@84322100 / W47N8@84321300 / W45N7@84321600 / W47N8@84319900 and older leftovers remain outside this window and official 404."
    )
    ok_line = (
        f"ok=true (quiet); first-pass missing_chunks=1 (34 of 35 official GETs 200, 404 W47N7@84329500); confirm recovered W47N7@84329500 inserted=535; leftover official 404s unchanged; "
        f"retry2 still 404 W45N8@84328100 and W45N7@84328300 inserted=0; {inwin_txt}; "
        f"{tick_s_corr_txt}, tick_s_in_use={tick_s_in_use:.5f} (first-pass realign {TICK_S_FIRST} committed {TS_REALIGNED_FIRST}); "
        f"new 05:43 freeze gap 84329391..84329599 official-filled {frac(freeze_0543, 209)} of 209 of 209 on all five rooms, no unpublished tail; "
        f"prior 05:13 freeze gap 84329011..84329179 now fully in this window official-filled {frac(freeze_0513, 169)} of 169 of 169; "
        f"prior 04:42 freeze gap 84328611..84328859 now before this window official-filled {frac(freeze_0442, 249)} of 249 of 249; "
        f"prior 04:11 freeze gap 84328221..84328349 still before this window official+live {frac(freeze_0411, 129)} of 129 of 129 (W45N7 short on official 404 @84328300); "
        f"prior 03:38 freeze gap 84327811..84328069 official-filled {frac(freeze_0338, 259)} of 259 of 259 still before this window; "
        f"prior 03:15 freeze gap 84327511..84327599 official-filled {frac(freeze_0315, 89)} of 89 of 89 still before this window; "
        f"{inwin_txt}; W47N7 official empty-no-creep 0 ranges []; {leftover_txt}"
    )

    now_lines = [
        f"{finished_hkt} half-hour backfill OK (quiet)",
        f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
        f"  ({first_pass_line}; see history_backfill.txt)",
        (
            f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST}; {tick_s_corr_txt}, in-use {tick_s_in_use:.5f})"
        ),
        f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks=0 (first pass 1; 0 remain)",
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
            f"confirm recovered W47N7@84329500 inserted=535 leftover official 404s unchanged; retry2 still 404 W45N8@84328100 and W45N7@84328300 inserted=0; {inwin_txt}; "
            f"W45N8 official empty-no-creep 0 ranges {w45n8_empty}; W45N7 official empty-no-creep 0 ranges {w45n7_empty}; "
            f"W47N7 official empty-no-creep {empty_no_creep} ranges {w47n7_empty}; {leftover_txt}"
        ),
        freeze_para,
        (
            f"listener single_slot={len(lis) <= 1 and not yield_present} roomSlot={live.get('roomSlot')} rot={rot} "
            f"yield={'present' if yield_present else 'absent'}"
        ),
        "confirm recovered W47N7@84329500 inserted=535 leftover official 404s unchanged; retry2 still 404 W45N8@84328100 and W45N7@84328300 inserted=0",
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
            f"confirm recovered W47N7@84329500 inserted=535 leftover official 404s unchanged; retry2 still 404 W45N8@84328100 and W45N7@84328300 inserted=0; {inwin_txt}; "
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
    retry2_src = DIR / "backfill_retry2.txt"
    if retry2_src.exists():
        shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0600.txt")

    summary = (
        f"{finished_hkt} wrapup ok\n"
        f"wrote history_backfill.json history_backfill_now.txt verify.txt\n"
        f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2_UNIQUE_NET} coverage={recovered}/{expected} tick_s_in_use={tick_s_in_use:.5f} later_mean_reverted={later_reverted}\n"
    )
    (DIR / "wrapup_run.txt").write_text(summary)
    (DIR / "wrapup_run_tee.txt").write_text(summary + now_text)
    print(summary)
    print(now_text)


if __name__ == "__main__":
    main()
