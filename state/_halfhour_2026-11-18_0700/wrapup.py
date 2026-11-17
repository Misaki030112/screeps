#!/usr/bin/env python3
"""Write half-hour backfill status records for the next hourly patrol."""
from __future__ import annotations
import json, os, subprocess, sys, shutil
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-18_0700"
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84329701, 84330400
GT_FIRST = 84330465
PUB_BASES = "84329700..84330300"
TICK_S_FIRST = 4.78412
TICK_S_PRINTED = "4.784"
NEW_ROWS = {"W46N8": 3959, "W47N8": 7152, "W45N8": 2199, "W45N7": 1548, "W47N7": 1489}
OFFICIAL_TICKS = {"W46N8": 700, "W47N8": 700, "W45N8": 700, "W45N7": 700, "W47N7": 600}
INSERTED_FIRST = 16347
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
INSERTED_RETRY2_UNIQUE_NET = 0
INSERTED_JUST_PUBLISHED = 2730
ALREADY = 7876
RECON_ROWS = 24223
TS_REALIGNED_FIRST = 0
IN_WINDOW_404 = [
    ("W47N7", 84330300),  # in-window official 404; confirm+retry2+just_published still 404; 0 live / 100 empty
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
    inserted_window = INSERTED_FIRST + INSERTED_CONFIRM + INSERTED_RETRY2_UNIQUE_NET
    inserted_total = inserted_window + INSERTED_JUST_PUBLISHED

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
        freeze_0637 = fill(c, 84330061, 84330439)
        freeze_0637_first = fill(c, 84330061, 84330400)
        freeze_0637_tail = fill(c, 84330401, 84330439)
        freeze_0637_hole = fill(c, 84330301, 84330400)
        freeze_0612 = fill(c, 84329761, 84329849)
        freeze_0612_early = fill(c, 84329761, 84329800)
        freeze_0612_tail = fill(c, 84329801, 84329849)
        freeze_0543 = fill(c, 84329391, 84329599)
        freeze_0513 = fill(c, 84329011, 84329179)
        freeze_0442 = fill(c, 84328611, 84328859)
        freeze_0442_pub = fill(c, 84328611, 84328800)
        freeze_0442_tail = fill(c, 84328801, 84328859)
        freeze_0411 = fill(c, 84328221, 84328349)
        freeze_0411_pub = fill(c, 84328221, 84328300)
        freeze_0411_tail = fill(c, 84328301, 84328349)
        freeze_0338 = fill(c, 84327811, 84328069)
        freeze_0315 = fill(c, 84327511, 84327599)
        rem_overlap = fill(c, 84329701, 84329900)
        rem_new = fill(c, 84329901, 84330400)
        rem_prev = fill(c, 84329701, 84329900)
        rem_prefill = fill(c, 84329701, 84329800)
        rem_just_window = fill(c, 84330301, 84330400)
        rem_just_published = fill(c, 84330401, 84330500)
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
        "in-window official 404 remains: "
        f"{hole_shorts['W47N7@84330300']} (100 empty 84330301..84330400); "
        "first pass 34 of 35 official GETs 200, missing_chunks=1; "
        "confirm and retry2 and the later just-published pass all still 404 at game.time>=84330520; "
        "leftover official 404 now outside window: "
        f"{hole_shorts['W45N8@84328100']} (84 empty 84328101..84328184); "
        f"{hole_shorts['W45N7@84328300']} (100 empty 84328301..84328400)"
    )
    first_pass_line = (
        "first pass 34 of 35 official GETs 200, missing_chunks=1 (404 W47N7@84330300); "
        "confirm recovered none inserted=0; leftover official 404s unchanged; "
        "retry2 at game.time=84330520 still 404 W47N7@84330300 and leftovers inserted=0; "
        "just-published pass then fetched base 84330400 (all five rooms 200) inserted=2730 "
        "and retried W47N7@84330300 still 404"
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
        f"ts_realigned={TS_REALIGNED_FIRST}. later-mean-robust {later:.5f} already inside the 45s gate "
        f"versus those already-live-aligned rows (vs_later over45={vs_later_after.get('over45')} "
        f"mean_off~{(vs_later_after.get('mean_off') or 0):.2f}s), so no corrective realign. "
        f"vs_first over45={vs_first.get('over45') if vs_first else 'n/a'} at the later live-anchor check "
        f"was not used to move rows. in-use first-pass {tick_s_in_use:.5f}."
    )
    game_time_note = (
        "New box freeze 06:37:05–07:05:46 (~1720s). Listener logged the freeze and "
        "run_listener restarted at 07:05:49, listener.py up at 07:05:59 (pid 183744). "
        "This run did not restart the listener, war_cmd, or pulse. live.json was fresh "
        f"after reconnect (stats.t live, gameTime field stayed empty at reconnect, roomSlot={live.get('roomSlot')}). "
        "Segment 90 buffers pulled after the 07:05 reconnect (creep_cpu and path_arrivals "
        "fresh through the tip). The 06:30 half-hour backfill had already official-backfilled "
        "84329201..84329900; leftover official 404s W45N8@84328100 and W45N7@84328300 remain outside this window. "
        "The 06:20 hourly patrol had already official-prefilled 84329601..84329800, so the 100-tick overlap "
        "84329701..84329800 in this window was already in the DB. "
        "room_stats gap 84330061..84330439 is the new 06:37 freeze: "
        "first pass official-published through 84330400 and filled 84330061..84330400 on four rooms "
        "(W47N7 only through 84330300 because W47N7@84330300 official 404); "
        "the former unpublished tail 84330401..84330439 sits in newly published base 84330400 and was official-filled on all five rooms in the later just-published pass; "
        "the only remaining freeze-gap hole is W47N7 84330301..84330400 (official 404, 0 live). "
        "Listener resumed writing room_stats/creep_ticks around 84330440 after the 07:05 reconnect. "
        "The prior 06:12 freeze 84329761..84329849 is now fully in this window and remains official-filled on all five rooms. "
        "The prior 05:43 freeze 84329391..84329599 is now before this window and remains official-filled on all five rooms. "
        "The prior 05:13 / 04:42 / 04:11 freezes remain before this window. "
        "The 200-tick overlap 84329701..84329900 with the 06:30 window was already in the DB (06:30 backfill)."
    )
    inserted_note = (
        f"This 07:00 first pass inserted {INSERTED_FIRST} new rows "
        f"(already_in_db={ALREADY}, reconstructed={RECON_ROWS}). "
        "The 200-tick overlap 84329701..84329900 with the 06:30 window was already present. "
        "The 06:20 hourly patrol had already official-prefilled 84329701..84329800 (subset of that overlap). "
        "Newly published ticks 84329901..84330400 (bases 84329900..84330300) were official 200 on four rooms on the first pass; "
        "W47N7@84330300 (84330301..84330400) official 404. "
        f"Confirm at {confirm_at} game.time={confirm_gt} recovered none inserted={INSERTED_CONFIRM}; "
        "leftover official 404s unchanged; in-window W47N7@84330300 still 404. "
        f"retry2 at {retry2_at} game.time={retry2_gt} still 404 on W47N7@84330300 and leftovers, inserted=0. "
        f"Just-published pass at game.time=84330527 fetched base 84330400 on all five rooms (200) and inserted {INSERTED_JUST_PUBLISHED} rows for 84330401..84330500 "
        "(including the 06:37 freeze tail 84330401..84330439); W47N7@84330300 still 404. "
        f"Coverage official_recovered={recovered}/{expected} including {empty_no_creep} official empty-no-creep "
        f"ticks; {official_404_missing} in-window official-404 ticks remain (W47N7@84330300)."
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
        "missing_chunks": 1,
        "missing_chunk_list": ["W47N7@84330300"],
        "missing_chunk_first_pass": ["W47N7@84330300"],
        "missing_chunk_note": (
            f"First pass (game.time={GT_FIRST}) published_bases {PUB_BASES}, reconstructed "
            f"{TMIN}..{TMAX} (700). 34 of 35 official GETs 200; missing_chunks=1 (404 W47N7@84330300). "
            f"Confirm at {confirm_at} game.time={confirm_gt} recovered none inserted={INSERTED_CONFIRM}; "
            "leftover official 404s still 404 "
            "(W45N8@84328100 and W45N7@84328300, outside this window). "
            f"retry2 at {retry2_at} game.time={retry2_gt} still 404 on W47N7@84330300 and leftovers, inserted=0. "
            "Just-published pass at game.time=84330527 filled base 84330400 on all five rooms; W47N7@84330300 still official 404."
        ),
        "creep_rows_reconstructed": RECON_ROWS,
        "already_in_db": ALREADY,
        "inserted": inserted_total,
        "inserted_first_pass": INSERTED_FIRST,
        "inserted_retry": INSERTED_CONFIRM,
        "inserted_retry2": INSERTED_RETRY2,
        "inserted_retry2_unique_net": INSERTED_RETRY2_UNIQUE_NET,
        "inserted_just_published": INSERTED_JUST_PUBLISHED,
        "inserted_window": inserted_window,
        "inserted_note": inserted_note,
        "ts_realigned": TS_REALIGNED_FIRST,
        "ts_realigned_corrective_later_mean": nfix_corr,
        "ts_realigned_confirm": 0,
        "ts_realigned_retry2": 0,
        "ts_realigned_just_published": 0,
        "ts_realigned_note": ts_realign_note,
        "ssl_first_attempt": False,
        "hourly_patrol_prefilled": True,
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
            "from": "2026-11-18 06:37:05",
            "to": "2026-11-18 07:05:46",
            "sec": 1720,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84330061, 84330439],
            "live_room_stats_gap_ticks": 379,
            "official_fill_full_gap": freeze_0637,
            "official_fill_first_pass_published_through_84330400": freeze_0637_first,
            "official_fill_just_published_tail_84330401_84330439": freeze_0637_tail,
            "official_fill_w47n7_404_hole_84330301_84330400": freeze_0637_hole,
            "official_fill_unpublished_tail": None,
            "published_part": [84330061, 84330400],
            "just_published_tail": [84330401, 84330439],
            "remaining_official_404": ["W47N7@84330300"],
            "note": (
                "new this run; room_stats gap 84330061..84330439 (379). Official first-pass published through 84330400. "
                f"Full-gap official-filled {frac(freeze_0637, 379)} of 379 "
                "(four rooms 379/379; W47N7 279/379, short on official 404 @84330300). "
                f"First-pass published part 84330061..84330400 (340) official-filled {frac(freeze_0637_first, 340)} of 340 "
                "(W47N7 short 100 ticks). "
                f"Just-published freeze tail 84330401..84330439 (39) official-filled {frac(freeze_0637_tail, 39)} of 39 on all five rooms. "
                "No unpublished tail remains in the freeze gap. "
                "Listener resumed around 84330440 after the 07:05 reconnect."
            ),
        },
        "prior_0612_box_freeze": {
            "from": "2026-11-18 06:12:53",
            "to": "2026-11-18 06:19:06",
            "sec": 372,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84329761, 84329849],
            "live_room_stats_gap_ticks": 89,
            "official_fill_full_gap": freeze_0612,
            "official_fill_already_published_through_84329800": freeze_0612_early,
            "official_fill_newly_published_84329801_84329849": freeze_0612_tail,
            "official_fill_unpublished_tail": None,
            "published_part": [84329761, 84329849],
            "unpublished_tail": None,
            "note": (
                "not new this run; now fully in this window (window starts 84329701). "
                f"Full-gap official-filled {frac(freeze_0612, 89)} of 89 on all five rooms "
                "(already official-filled by the 06:30 backfill / 06:20 patrol)."
            ),
        },
        "prior_0543_box_freeze": {
            "from": "2026-11-18 05:43:58",
            "to": "2026-11-18 05:59:00",
            "sec": 901,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84329391, 84329599],
            "live_room_stats_gap_ticks": 209,
            "official_fill_full_gap": freeze_0543,
            "published_part": [84329391, 84329599],
            "unpublished_tail": None,
            "note": (
                "not new this run; now before this window (window starts 84329701). "
                f"Full-gap official-filled {frac(freeze_0543, 209)} of 209 on all five rooms "
                "(already official-filled by the 06:00 backfill)."
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
            "note": (
                "not new this run; still before this window. "
                f"Full-gap official-filled {frac(freeze_0513, 169)} of 169 on all five rooms."
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
            "note": (
                "not new this run; still before this window. "
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
            "note": (
                "not new this run; still before this window. "
                f"official+live {frac(freeze_0411, 129)} of 129 "
                f"(published part 80t {frac(freeze_0411_pub, 80)} of 80; former unpublished tail 49t {frac(freeze_0411_tail, 49)} of 49, W45N7 still empty on leftover official 404 @84328300)."
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
                "not new this run; still before this window. "
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
                "not new this run; still before this window. "
                f"Full-gap official-filled {frac(freeze_0315, 89)} of 89 on all five rooms; no unpublished tail."
            ),
        },
        "remainder_overlap_84329701_84329900": rem_overlap,
        "remainder_new_84329901_84330400": rem_new,
        "remainder_prev_filled_84329701_84329900": rem_prev,
        "remainder_patrol_prefilled_84329701_84329800": rem_prefill,
        "remainder_window_last_chunk_84330301_84330400": rem_just_window,
        "remainder_just_published_84330401_84330500": rem_just_published,
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
        "just_published_at": "2026-11-18 07:13:24 Asia/Hong_Kong",
        "just_published_game_time": 84330527,
        "ok_quiet": True,
    }

    freeze_para = (
        f"New box freeze 06:37:05–07:05:46 (~1720s) room_stats gap 84330061..84330439; "
        f"full-gap official-filled {frac(freeze_0637, 379)} of 379 "
        f"(four rooms 379/379; W47N7 279/379 short on official 404 @84330300); "
        f"first-pass published part 84330061..84330400 {frac(freeze_0637_first, 340)} of 340; "
        f"just-published freeze tail 84330401..84330439 {frac(freeze_0637_tail, 39)} of 39 on all five rooms; "
        f"no unpublished tail remains in the freeze gap; listener resumed around 84330440 after the 07:05 reconnect. "
        f"Prior box freeze 06:12:53–06:19:06 (~372s) room_stats gap 84329761..84329849 now fully in this window; "
        f"official-filled {frac(freeze_0612, 89)} of 89 on all five rooms. "
        f"Prior box freeze 05:43:58–05:59:00 (~901s) room_stats gap 84329391..84329599 now before this window; "
        f"official-filled {frac(freeze_0543, 209)} of 209 on all five rooms. "
        f"Prior box freeze 05:13:36–05:25:59 (~743s) room_stats gap 84329011..84329179 still before this window; "
        f"official-filled {frac(freeze_0513, 169)} of 169 on all five rooms. "
        f"Prior box freeze 04:42:19–05:00:55 (~1108s) room_stats gap 84328611..84328859 still before this window; "
        f"official-filled {frac(freeze_0442, 249)} of 249 on all five rooms. "
        f"Prior box freeze 04:11:18–04:20:01 (~522s) room_stats gap 84328221..84328349 still before this window; "
        f"official+live {frac(freeze_0411, 129)} of 129 "
        f"(published part 80t {frac(freeze_0411_pub, 80)} of 80; former unpublished tail 49t {frac(freeze_0411_tail, 49)} of 49, W45N7 still empty on leftover official 404 @84328300). "
        f"Prior box freeze 03:38:35–03:58:00 (~1156s) room_stats gap 84327811..84328069 still before this window; official-filled {frac(freeze_0338, 259)} of 259 on all five rooms. "
        f"Prior box freeze 03:15:10–03:21:01 (~350s) room_stats gap 84327511..84327599 still before this window; official-filled {frac(freeze_0315, 89)} of 89 on all five rooms. "
        f"Overlap 84329701..84329900 with the 06:30 window official-filled {frac(rem_overlap, 200)} of 200 on all five rooms. "
        f"Rest of window 84329901..84330400 official-filled {frac(rem_new, 500)} of 500 "
        f"(W47N7 short 100 ticks on official 404 @84330300; patrol-prefilled 84329701..84329800 {frac(rem_prefill, 100)} of 100 is in the overlap). "
        f"Just-published 84330401..84330500 official-filled {frac(rem_just_published, 100)} of 100 on all five rooms (outside the formal 40-min window, fills the 06:37 freeze tail). "
        f"In-window official 404 remains: {hole_shorts['W47N7@84330300']}. "
        "W45N8@84328100 (16 live / 84 empty) and W45N7@84328300 (0 live / 100 empty) remain outside this window and still official 404. "
        "W45N8@84326300 (0 live / 100 empty) and W45N8@84326500 (22 live / 78 empty) remain outside this window and still official 404. "
        "W45N8@84326100 remains outside this window and still official 404 (0 live / 100 empty). "
        "W45N7@84324900 remains outside this window and still official 404. "
        "W47N8@84324300 / W47N8@84323200 / W47N8@84322100 / W47N8@84321300 / W45N7@84321600 / W47N8@84319900 and older leftovers remain outside this window and official 404."
    )
    ok_line = (
        f"ok=true (quiet); first-pass missing_chunks=1 (34 of 35 official GETs 200, 404 W47N7@84330300); "
        f"confirm recovered none inserted=0; leftover official 404s unchanged; "
        f"retry2 still 404 W47N7@84330300 and leftovers inserted=0; just-published base 84330400 inserted=2730, W47N7@84330300 still 404; {inwin_txt}; "
        f"{tick_s_corr_txt}, tick_s_in_use={tick_s_in_use:.5f} (first-pass realign {TICK_S_FIRST} committed {TS_REALIGNED_FIRST}); "
        f"new 06:37 freeze gap 84330061..84330439 official-filled {frac(freeze_0637, 379)} of 379 "
        f"(four rooms 379/379; W47N7 279/379 short on official 404 @84330300), no unpublished tail; "
        f"prior 06:12 freeze gap 84329761..84329849 now fully in this window official-filled {frac(freeze_0612, 89)} of 89; "
        f"prior 05:43 freeze gap 84329391..84329599 now before this window official-filled {frac(freeze_0543, 209)} of 209; "
        f"prior 05:13 freeze gap 84329011..84329179 still before this window official-filled {frac(freeze_0513, 169)} of 169; "
        f"prior 04:42 freeze gap 84328611..84328859 still before this window official-filled {frac(freeze_0442, 249)} of 249; "
        f"prior 04:11 freeze gap 84328221..84328349 still before this window official+live {frac(freeze_0411, 129)} of 129 (W45N7 short on official 404 @84328300); "
        f"prior 03:38 freeze gap 84327811..84328069 official-filled {frac(freeze_0338, 259)} of 259 still before this window; "
        f"prior 03:15 freeze gap 84327511..84327599 official-filled {frac(freeze_0315, 89)} of 89 still before this window; "
        f"{inwin_txt}; W47N7 official empty-no-creep 0 ranges []; {leftover_txt}"
    )

    now_lines = [
        f"{finished_hkt} half-hour backfill OK (quiet)",
        f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={','.join(ROOMS)} dry=False",
        f"  ({first_pass_line}; see history_backfill.txt)",
        (
            f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST}; {tick_s_corr_txt}, in-use {tick_s_in_use:.5f})"
        ),
        f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks=1 (first pass 1; 1 remains: W47N7@84330300)",
        f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
        f"per_room {per_room_line}",
        f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 +{INSERTED_RETRY2_UNIQUE_NET}, just_published +{INSERTED_JUST_PUBLISHED}, window {inserted_window}, run total {inserted_total})",
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
            f"confirm recovered none inserted=0 leftover official 404s unchanged; retry2 still 404 W47N7@84330300 and leftovers inserted=0; just-published base 84330400 inserted=2730 W47N7@84330300 still 404; {inwin_txt}; "
            f"W45N8 official empty-no-creep 0 ranges {w45n8_empty}; W45N7 official empty-no-creep 0 ranges {w45n7_empty}; "
            f"W47N7 official empty-no-creep {empty_no_creep} ranges {w47n7_empty}; {leftover_txt}"
        ),
        freeze_para,
        (
            f"listener single_slot={len(lis) <= 1 and not yield_present} roomSlot={live.get('roomSlot')} rot={rot} "
            f"yield={'present' if yield_present else 'absent'}"
        ),
        "confirm recovered none inserted=0 leftover official 404s unchanged; retry2 still 404 W47N7@84330300 and leftovers inserted=0; just-published 84330400 inserted=2730",
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
        f"missing_chunks=1 in_window_404=1 (W47N7@84330300) empty_no_creep={empty_no_creep}",
        (
            f"tick_s first={TICK_S_FIRST} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; "
            f"first-pass realign committed {TS_REALIGNED_FIRST}; in-use {tick_s_in_use:.5f}; later over45={vs_later_after.get('over45')}."
        ),
        (
            f"confirm recovered none inserted=0 leftover official 404s unchanged; retry2 still 404 W47N7@84330300 and leftovers inserted=0; just-published base 84330400 inserted=2730 W47N7@84330300 still 404; {inwin_txt}; "
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
        shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_0700.txt")

    summary = (
        f"{finished_hkt} wrapup ok\n"
        f"wrote history_backfill.json history_backfill_now.txt verify.txt\n"
        f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2_UNIQUE_NET}+just{INSERTED_JUST_PUBLISHED} coverage={recovered}/{expected} tick_s_in_use={tick_s_in_use:.5f} later_mean_reverted={later_reverted}\n"
    )
    (DIR / "wrapup_run.txt").write_text(summary)
    (DIR / "wrapup_run_tee.txt").write_text(summary + now_text)
    print(summary)
    print(now_text)


if __name__ == "__main__":
    main()
