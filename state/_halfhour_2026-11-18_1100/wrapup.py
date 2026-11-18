#!/usr/bin/env python3
"""Write half-hour backfill status records for the next hourly patrol."""
from __future__ import annotations
import json, os, subprocess, sys, shutil
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-18_1100"
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84332601, 84333300
GT_FIRST = 84333399
PUB_BASES = "84332600..84333200"
TICK_S_FIRST = 4.60572
TICK_S_PRINTED = "4.606"
NEW_ROWS = {"W46N8": 1484, "W47N8": 1337, "W45N8": 987, "W45N7": 744, "W47N7": 517}
OFFICIAL_TICKS = {"W46N8": 700, "W47N8": 500, "W45N8": 700, "W45N7": 700, "W47N7": 600}
INSERTED_FIRST = 5069
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
INSERTED_RETRY2_UNIQUE_NET = 0
INSERTED_JUST_PUBLISHED = 2150  # W46N8/W45N8/W45N7/W47N7 @84333300; W47N8@84333300 still 404 after 3 retries
ALREADY = 16470
RECON_ROWS = 21539
TS_REALIGNED_FIRST = 0
IN_WINDOW_404 = [
    ("W47N8", 84332600),  # genuine official hole this window; 0 live / 100 empty; still 404 after 84333000 published
    ("W47N7", 84332600),  # genuine official hole this window; 0 live / 100 empty
    ("W47N8", 84332700),  # genuine official hole this window; 17 live / 83 empty (84332701..84332783)
]
OUTSIDE_404 = [
    ("W45N8", 84332200),  # leftover official 404 now outside window; 0 live / 100 empty
    ("W47N7", 84331000),  # leftover official 404 now outside window; 0 live / 100 empty
    ("W47N7", 84330300),  # leftover official 404 now outside window; 0 live / 100 empty
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
        freeze_0718 = fill(c, 84330581, 84330609)
        freeze_0732 = fill(c, 84330761, 84330789)
        freeze_0742 = fill(c, 84330881, 84330909)
        freeze_0742_pub = fill(c, 84330881, 84330900)
        freeze_0742_tail = fill(c, 84330901, 84330909)
        freeze_0749 = fill(c, 84330981, 84331089)
        freeze_0749_pub = fill(c, 84330981, 84331000)
        freeze_0749_hole = fill(c, 84331001, 84331089)
        freeze_0804 = fill(c, 84331171, 84331199)
        freeze_0804_pub = fill(c, 84331171, 84331200)
        freeze_0812 = fill(c, 84331271, 84331329)
        freeze_w47n7_empty = fill(c, 84331194, 84331311)
        freeze_0839 = fill(c, 84331601, 84331929)
        freeze_0839_pub = fill(c, 84331601, 84331900)
        freeze_0839_tail = fill(c, 84331901, 84331929)
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
        rem_overlap = fill(c, 84332601, 84333100)
        rem_new = fill(c, 84333101, 84333300)
        rem_prev = fill(c, 84332601, 84333100)
        rem_prefill = fill(c, 84332101, 84332800)
        rem_just_window = fill(c, 84333201, 84333300)
        rem_just_published = fill(c, 84333301, 84333400)
        rem_prev_just = fill(c, 84333001, 84333100)
        rem_hole = fill(c, 84332601, 84332783)
        rem_hole_w47n8 = fill(c, 84332601, 84332783)
        rem_hole_w47n7 = fill(c, 84332601, 84332700)
        rem_hole_w45n8 = fill(c, 84332201, 84332300)
        rem_prefill_hour = fill(c, 84332501, 84333200)
        freeze_1015 = fill(c, 84332831, 84332879)
        freeze_1031 = fill(c, 84333031, 84333059)
        freeze_1047 = fill(c, 84333241, 84333339)
        freeze_1047_win = fill(c, 84333241, 84333300)
        freeze_1047_tail = fill(c, 84333301, 84333339)
        freeze_0916 = fill(c, 84332071, 84332189)
        freeze_0947 = fill(c, 84332471, 84332679)
        freeze_0947_pub = fill(c, 84332471, 84332600)
        freeze_0947_tail = fill(c, 84332601, 84332679)
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
        "W45N8@84332200",
        "W47N7@84331000",
        "W47N7@84330300",
        "W45N8@84328100", "W45N7@84328300",
        "W45N8@84326300", "W45N8@84326500", "W45N8@84326100", "W45N7@84324900",
        "W47N8@84324300", "W47N8@84323200", "W47N8@84322100", "W47N8@84321300",
        "W45N7@84321600", "W47N8@84319900", "W47N8@84319000", "W46N8@84318500",
        "W45N8@84318000", "W47N7@84315100", "W45N8@84314900", "W45N7@84314500",
        "W47N8@84314000", "W46N8@84313200",
    ]
    leftover_bits = [f"leftover official 404 {hole_shorts[k]} still outside window" for k in leftover_order if k in hole_shorts]
    leftover_txt = "; ".join(leftover_bits) + "; older leftovers unchanged."
    inwin_txt = (
        "in-window official 404 remains: W47N8@84332600 (0 live / 100 empty 84332601..84332700), "
        "W47N7@84332600 (0 live / 100 empty 84332601..84332700), "
        "W47N8@84332700 (17 live / 83 empty 84332701..84332783; combined W47N8 hole 84332601..84332783); "
        "first pass 32 of 35 official GETs 200, missing_chunks=3; "
        f"confirm at game.time={confirm_gt} recovered none leftover official 404s unchanged inserted=0; "
        f"retry2 at game.time={retry2_gt} still 404 leftovers and the three in-window holes inserted=0; "
        "just-published at 11:02:33 game.time=84333444 base 84333300 recovered W46N8/W45N8/W45N7/W47N7 inserted=2150 (after this window); "
        "W47N8@84333300 first 404, still 404 after retries at 11:04:25 game.time=84333468, 11:06:21 game.time=84333493, and 11:07:39 game.time=84333510 (unpublished-tail lag / possible new official hole after this window, not told); "
        "the three in-window 404s still 404 after 84333200 and 84333300 (four rooms) published (genuine official holes, not unpublished-tail lag, not a systemic history outage); "
        "leftover official 404 now outside window: "
        f"{hole_shorts['W45N8@84332200']} (100 empty 84332201..84332300); "
        f"{hole_shorts['W47N7@84331000']} (100 empty 84331001..84331100); "
        f"{hole_shorts['W47N7@84330300']} (100 empty 84330301..84330400); "
        f"{hole_shorts['W45N8@84328100']} (84 empty 84328101..84328184); "
        f"{hole_shorts['W45N7@84328300']} (100 empty 84328301..84328400)"
    )
    first_pass_line = (
        "first pass 32 of 35 official GETs 200, missing_chunks=3 404 W47N8@84332600, W47N7@84332600, W47N8@84332700; "
        "hourly_patrol_prefilled=true from 10:18 patrol 84332101..84332800 (overlap); 10:30 backfill already wrote through 84333100; "
        "confirm recovered none leftover official 404s unchanged; "
        f"retry2 at game.time={retry2_gt} still 404 leftovers and the three in-window holes inserted=0; "
        "just-published at 11:02:33 game.time=84333444 recovered W46N8/W45N8/W45N7/W47N7 @84333300 inserted=2150; "
        "W47N8@84333300 still 404 after 3 retries through game.time=84333510 (after this window, not told); "
        "W47N8@84332600 / W47N7@84332600 / W47N8@84332700 still 404 treated as leftover official holes (0/0/17 live), not told; "
        "W45N8@84332200 still 404 treated as a leftover official hole (0 live), not told"
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
        f"SUCCEEDED, ts_realigned_first={TS_REALIGNED_FIRST}. "
        f"later-mean-robust {later:.5f} (delta first-robust -0.03549 s/tick, ~28.3s at tmin); "
        f"later-mean-robust already inside 45s gate, no corrective realign, nfix={nfix_corr}; "
        f"vs_later over45={vs_later_after.get('over45')} "
        f"mean_off~{(vs_later_after.get('mean_off') or 0):.2f}s; skipped_cross_chunk=0. "
        f"in-use first-pass {tick_s_in_use:.5f} (corrective_applied=False; first-pass rows already inside the 45s gate)."
    )
    game_time_note = (
        "Listener self-healed the new 10:47:39–10:53:38 (~358s) box freeze "
        "(restart 10:53:41, pid 279589 under run_listener.sh 4035476) before this run, "
        "and earlier the 10:31:48 restart plus the 10:15:24–10:18:21 (~169s) and 09:47:23–10:02:45 (~918s) freezes. "
        "This run did not restart the listener, war_cmd, or pulse. live.json was fresh at pre-check "
        f"(stats.t flowing, roomSlot={live.get('roomSlot')}; ingest healthy; live gameTime field was None but stats.t was current). "
        "Segment 90 buffers already pulled after the 10:53 reconnect (creep_cpu and path_arrivals fresh through the tip). "
        "The 10:30 half-hour backfill had already official-backfilled 84332301..84333000 "
        "(just-published then recovered all five @84333000), "
        "and the 10:18 hourly patrol official-backfilled 84332101..84332800. "
        "Leftover official 404s W45N8@84332200, W47N7@84331000, W47N7@84330300, W45N8@84328100 and W45N7@84328300 remain outside this window. "
        "Prior freeze 09:47 (room_stats 84332471..84332679, 209) is official-filled through 84332600 on all five rooms; "
        "tail 84332601..84332679 remains a confirmed official 404 on W47N8/W47N7 @84332600. "
        "Prior freeze 10:15 (room_stats 84332831..84332879, 49) stays official-filled on all five rooms. "
        "Prior 10:31 room_stats gap 84333031..84333059 (29) stays official-filled on all five rooms (10:30 just-published 84333000). "
        "New freeze 10:47 (room_stats 84333241..84333339, 99) is official-filled through 84333300 on all five rooms; "
        "just-published tail 84333301..84333339 recovered on W46N8/W45N8/W45N7/W47N7, W47N8@84333300 still 404 after this window. "
        "In-window official holes: W47N8@84332600, W47N7@84332600, W47N8@84332700 (combined W47N8 84332601..84332783). "
        "Listener is on the peacetime single-slot rotation."
    )
    inserted_note = (
        f"This 11:00 first pass inserted {INSERTED_FIRST} new rows "
        f"(already_in_db={ALREADY}, reconstructed={RECON_ROWS}). "
        "hourly_patrol_prefilled=true from 10:18 patrol 84332101..84332800 (overlap); 10:30 backfill already wrote through 84333100. "
        "The overlap 84332601..84333100 with the 10:30 window / just-published 84333000 was already present except the W47 official holes. "
        "Newly published ticks 84333101..84333300 were official 200 on all five rooms. "
        f"Confirm at {confirm_at} game.time={confirm_gt} recovered none, inserted={INSERTED_CONFIRM}; "
        "outside-window leftover official 404s unchanged; in-window W47N8@84332600 / W47N7@84332600 / W47N8@84332700 still 404. "
        f"retry2 at {retry2_at} game.time={retry2_gt} still 404 on leftovers and the three in-window holes, inserted={INSERTED_RETRY2}. "
        "Just-published at 11:02:33 game.time=84333444 base 84333300 recovered W46N8/W45N8/W45N7/W47N7 inserted=2150 (after this window); "
        "W47N8@84333300 first 404, still 404 after 3 retries through game.time=84333510 (after this window, not told); "
        "the three in-window 404s still 404 after later chunks published (genuine official holes). "
        f"Coverage official_recovered={recovered}/{expected} including {empty_no_creep} official empty-no-creep "
        f"ticks; {official_404_missing} in-window official-404 ticks remain (W47N8 84332601..84332783 and W47N7 84332601..84332700)."
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
        "missing_chunks": 3,
        "missing_chunk_list": ["W47N8@84332600", "W47N7@84332600", "W47N8@84332700"],
        "missing_chunk_first_pass": ["W47N8@84332600", "W47N7@84332600", "W47N8@84332700"],
        "missing_chunk_note": (
            f"First pass (game.time={GT_FIRST}) published_bases {PUB_BASES}, reconstructed "
            f"{TMIN}..{TMAX} (700). 32 of 35 official GETs 200; missing_chunks=3 "
            "(W47N8@84332600, W47N7@84332600, W47N8@84332700). "
            f"Confirm at {confirm_at} game.time={confirm_gt} recovered none inserted={INSERTED_CONFIRM}; "
            "leftover official 404s still 404 "
            "(W45N8@84332200, W47N7@84331000, W47N7@84330300, W45N8@84328100 and W45N7@84328300, all outside this window); "
            "in-window three holes still 404. "
            f"retry2 at {retry2_at} game.time={retry2_gt} still 404 on leftovers and the three in-window holes, inserted={INSERTED_RETRY2}. "
            "Just-published at 11:02:33 game.time=84333444 base 84333300 recovered W46N8/W45N8/W45N7/W47N7 inserted=2150; "
            "W47N8@84333300 still 404 after 3 retries through game.time=84333510 (after this window, not told); "
            "the three in-window 404s still 404 after 84333200 and 84333300 (four rooms) published (genuine official holes)."
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
        "hourly_patrol_prefilled": True,  # 10:18 patrol 84332101..84332800 overlap; 10:30 backfill through 84333100
        "hourly_patrol_prefill_ticks": [84332101, 84332800],
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
                "not new this run; room_stats gap 84330061..84330439 (379) overlaps the start of this window (window starts 84330101). Official already published through 84330400 as of the 07:00 / 07:20 passes. "
                f"Full-gap official-filled {frac(freeze_0637, 379)} of 379 "
                "(four rooms 379/379; W47N7 279/379, short on official 404 @84330300). "
                f"First-pass published part 84330061..84330400 (340) official-filled {frac(freeze_0637_first, 340)} of 340 "
                "(W47N7 short 100 ticks). "
                f"Just-published freeze tail 84330401..84330439 (39) official-filled {frac(freeze_0637_tail, 39)} of 39 on all five rooms. "
                "No unpublished tail remains in the freeze gap. "
                "Listener resumed around 84330440 after the 07:05 reconnect."
            ),
        },
        "new_0718_box_freeze": {
            "from": "2026-11-18 07:18:12",
            "to": "2026-11-18 07:19:32",
            "sec": 79,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84330581, 84330609],
            "live_room_stats_gap_ticks": 29,
            "official_fill_full_gap": freeze_0718,
            "note": (
                "not new this run; fully in this window. "
                f"Full-gap official-filled {frac(freeze_0718, 29)} of 29 on all five rooms."
            ),
        },
        "new_0732_box_freeze": {
            "from": "2026-11-18 07:32:23",
            "to": "2026-11-18 07:34:00",
            "sec": 94,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84330761, 84330789],
            "live_room_stats_gap_ticks": 29,
            "official_fill_full_gap": freeze_0732,
            "note": (
                "not new this run; fully in this window. "
                f"Full-gap official-filled {frac(freeze_0732, 29)} of 29 on all five rooms."
            ),
        },
        "new_0742_box_freeze": {
            "from": "2026-11-18 07:42:09",
            "to": "2026-11-18 07:43:21",
            "sec": 69,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84330881, 84330909],
            "live_room_stats_gap_ticks": 29,
            "official_fill_full_gap": freeze_0742,
            "official_fill_just_published_84330881_84330900": freeze_0742_pub,
            "official_fill_unpublished_tail_84330901_84330909": freeze_0742_tail,
            "published_part": [84330881, 84330900],
            "unpublished_tail": [84330901, 84330909],
            "remaining_official_404": [],
            "note": (
                "not new this run; now fully inside this window and official-filled on all five rooms "
                f"{frac(freeze_0742, 29)} of 29 (W47N7@84330800 recovered 200 on this first pass). "
                "No unpublished tail remains."
            ),
        },
        "new_0749_box_freeze": {
            "from": "2026-11-18 07:49:40",
            "to": "2026-11-18 07:57:23",
            "sec": 459,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84330981, 84331089],
            "live_room_stats_gap_ticks": 109,
            "official_fill_full_gap": freeze_0749,
            "official_fill_published_through_84331000": freeze_0749_pub,
            "official_fill_w47n7_404_hole_84331001_84331089": freeze_0749_hole,
            "published_part": [84330981, 84331000],
            "remaining_official_404": ["W47N7@84331000"],
            "note": (
                "new this run and fully in this window. "
                f"Full-gap official-filled {frac(freeze_0749, 109)} of 109 "
                "(four rooms 109/109; W47N7 20/109, only 84330981..84331000, short on official 404 @84331000). "
                f"Published part 84330981..84331000 (20) official-filled {frac(freeze_0749_pub, 20)} of 20 on all five rooms. "
                f"W47N7 official-404 hole 84331001..84331089 (89) official-filled {frac(freeze_0749_hole, 89)} of 89 "
                "(four rooms 89/89; W47N7 0/89). "
                "Listener resumed around 84331090 after the 07:57 reconnect."
            ),
        },
        "new_0804_box_freeze": {
            "from": "2026-11-18 08:04:42",
            "to": "2026-11-18 08:06:29",
            "sec": 103,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84331171, 84331199],
            "live_room_stats_gap_ticks": 29,
            "official_fill_full_gap": freeze_0804,
            "official_fill_just_published_through_84331200": freeze_0804_pub,
            "remaining_official_404": ["W47N8@84331100", "W45N8@84331100", "W47N7@84331100"],
            "note": (
                "new this run; sits after the formal 40-min window (ends 84331100), inside just-published base 84331100. "
                f"Full-gap official+live {frac(freeze_0804, 29)} of 29. "
                "W46N8 and W45N7 official 200 on 84331100; W47N8/W45N8/W47N7 still official 404 @84331100. "
                "Listener resumed around 84331200 after the 08:06 reconnect."
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
                "not new this run; now before this window (window starts 84330101). "
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
                "not new this run; still before this window (window starts 84330101). "
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
        "remainder_overlap_84332601_84333100": rem_overlap,
        "remainder_new_84333101_84333300": rem_new,
        "remainder_prev_filled_84332601_84333100": rem_prev,
        "remainder_prev_backfill_prefilled_84332101_84332800": rem_prefill,
        "remainder_window_last_chunk_84333201_84333300": rem_just_window,
        "remainder_just_published_84333301_84333400": rem_just_published,
        "remainder_prev_just_published_84333001_84333100": rem_prev_just,
        "remainder_in_window_hole_w47n8_84332601_84332783": rem_hole_w47n8,
        "remainder_in_window_hole_w47n7_84332601_84332700": rem_hole_w47n7,
        "remainder_outside_hole_w45n8_84332201_84332300": rem_hole_w45n8,
        "remainder_hour_window_84332501_84333200": rem_prefill_hour,
        "freeze_1031_fill": freeze_1031,
        "freeze_1047_fill": freeze_1047,
        "freeze_1047_win": freeze_1047_win,
        "freeze_1047_tail": freeze_1047_tail,
        "new_1031_room_stats_gap": {
            "live_room_stats_gap": [84333031, 84333059],
            "live_room_stats_gap_ticks": 29,
            "official_fill_full_gap": freeze_1031,
            "note": (
                "not new as a box-pause record this run (appeared after the 10:31:48 listener restart); fully in this window. "
                f"Full-gap official-filled {frac(freeze_1031, 29)} of 29 on all five rooms (10:30 just-published 84333000)."
            ),
        },
        "new_1047_box_freeze": {
            "from": "2026-11-18 10:47:39",
            "to": "2026-11-18 10:53:38",
            "sec": 358,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84333241, 84333339],
            "live_room_stats_gap_ticks": 99,
            "official_fill_full_gap": freeze_1047,
            "official_fill_window_84333241_84333300": freeze_1047_win,
            "official_fill_just_published_tail_84333301_84333339": freeze_1047_tail,
            "published_part": [84333241, 84333300],
            "unpublished_tail": [84333301, 84333339],
            "remaining_official_404": ["W47N8@84333300"],
            "note": (
                "new this run. "
                f"Full-gap official+just-published {frac(freeze_1047, 99)} of 99. "
                f"Window part 84333241..84333300 (60) official-filled {frac(freeze_1047_win, 60)} of 60 on all five rooms. "
                f"Just-published tail 84333301..84333339 (39) official-filled {frac(freeze_1047_tail, 39)} of 39 "
                "(W46N8/W45N8/W45N7/W47N7 39/39; W47N8 still official 404 @84333300 after 3 retries through game.time=84333510, treated as unpublished-tail lag after this window, not told). "
                "Listener resumed around 84333340 after the 10:53:41 restart (this run did not restart it)."
            ),
        },
        "freeze_1015_fill": freeze_1015,
        "freeze_0839_fill": freeze_0839,
        "freeze_0839_pub": freeze_0839_pub,
        "freeze_0839_tail": freeze_0839_tail,
        "freeze_0916_fill": freeze_0916,
        "freeze_0947_fill": freeze_0947,
        "freeze_0947_pub": freeze_0947_pub,
        "freeze_0947_tail": freeze_0947_tail,
        "new_0947_box_freeze": {
            "from": "2026-11-18 09:47:23",
            "to": "2026-11-18 10:02:45",
            "sec": 918,
            "kind": "box_hibernate",
            "live_room_stats_gap": [84332471, 84332679],
            "live_room_stats_gap_ticks": 209,
            "official_fill_full_gap": freeze_0947,
            "official_fill_published_through_84332600": freeze_0947_pub,
            "official_fill_just_published_tail_84332601_84332679": freeze_0947_tail,
            "published_part": [84332471, 84332600],
            "unpublished_tail": [84332601, 84332679],
            "remaining_official_404": ["W47N8@84332600", "W47N7@84332600"],  # now confirmed leftover official holes, not unpublished-tail
            "note": (
                "new this run. "
                f"Full-gap official+just-published {frac(freeze_0947, 209)} of 209. "
                f"Published part 84332471..84332600 (130) official-filled {frac(freeze_0947_pub, 130)} of 130 on all five rooms. "
                f"Just-published / unpublished tail 84332601..84332679 (79) official-filled {frac(freeze_0947_tail, 79)} of 79 "
                "(W46N8/W45N8/W45N7 79/79 via official 200 @84332600 plus live on W46N8; W47N8/W47N7 0/79 still official 404 @84332600, now a confirmed leftover official hole after later chunks published, not told). "
                "Listener resumed around 84332680 after the 10:02:49 restart (this run did not restart it). New 10:15 freeze 84332831..84332879 is official-filled on all five rooms."
            ),
        },
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
        "just_published_at": "2026-11-18 11:02:33 Asia/Hong_Kong",
        "just_published_game_time": 84333444,
        "just_published_retry_at": "2026-11-18 11:07:39 Asia/Hong_Kong",
        "just_published_retry_game_time": 84333510,
        "just_published_skipped": False,
        "just_published_skip_reason": None,
        "just_published_recovered": ["W46N8@84333300", "W45N8@84333300", "W45N7@84333300", "W47N7@84333300"],
        "just_published_still_404": ["W47N8@84332600", "W47N7@84332600", "W47N8@84332700", "W45N8@84332200", "W47N7@84331000", "W47N7@84330300", "W45N8@84328100", "W45N7@84328300"],
        "just_published_unpublished_tail_404": ["W47N8@84333300"],
        "freeze_0812_fill": freeze_0812,
        "w47n7_empty_no_creep_fill": freeze_w47n7_empty,
        "ok_quiet": True,
    }

    freeze_para = (
        f"Prior box freeze 06:37:05–07:05:46 (~1720s) room_stats gap 84330061..84330439 still before this window (window starts 84332601); "
        f"full-gap official-filled {frac(freeze_0637, 379)} of 379 "
        f"(four rooms 379/379; W47N7 279/379 short on leftover official 404 @84330300); "
        f"no unpublished tail remains in that freeze gap. "
        f"Prior box freeze 07:18:12–07:19:32 (~79s) room_stats gap 84330581..84330609; official-filled {frac(freeze_0718, 29)} of 29 on all five rooms. "
        f"Prior box freeze 07:32:23–07:34:00 (~94s) room_stats gap 84330761..84330789; official-filled {frac(freeze_0732, 29)} of 29 on all five rooms. "
        f"Prior box freeze 07:42:09–07:43:21 (~69s) room_stats gap 84330881..84330909; official-filled {frac(freeze_0742, 29)} of 29 on all five rooms (W47N7@84330800 recovered this run). "
        f"Prior box freeze 07:49:40–07:57:23 (~459s) room_stats gap 84330981..84331089; official-filled {frac(freeze_0749, 109)} of 109 "
        f"(four rooms 109/109; W47N7 20/109 short on official 404 @84331000); listener resumed around 84331090 after the 07:57 reconnect (this run did not restart it). "
        f"Prior box freeze 08:04:42–08:06:29 (~103s) room_stats gap 84331171..84331199 is now fully in the formal window; official-filled {frac(freeze_0804, 29)} of 29 "
        f"on the four occupied rooms (W47N7 official empty-no-creep from 84331194 in this 29); listener resumed around 84331200 after the 08:06 reconnect (this run did not restart it). "
        f"Prior box freeze 08:12:49–08:16:17 (~204s) room_stats gap 84331271..84331329; official-filled {frac(freeze_0812, 59)} of 59 "
        f"on the four occupied rooms (W47N7 official empty-no-creep 84331194..84331311); listener resumed after the 08:16:20 restart (pid 215341, this run did not restart it). "
        f"Prior box freeze 06:12:53–06:19:06 (~372s) room_stats gap 84329761..84329849 still before this window; "
        f"official-filled {frac(freeze_0612, 89)} of 89 on all five rooms. "
        f"Prior box freeze 05:43:58–05:59:00 (~901s) room_stats gap 84329391..84329599 still before this window; "
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
        f"Prior box freeze 08:39:15–09:04:10 (~1490s) room_stats gap 84331601..84331929; still official-filled {frac(freeze_0839, 329)} of 329 on all five rooms. "
        f"Prior box freeze 09:16:55–09:24:40 (~460s) room_stats gap 84332071..84332189; official-filled {frac(freeze_0916, 119)} of 119 on all five rooms. "
        f"Prior box freeze 09:47:23–10:02:45 (~918s) room_stats gap 84332471..84332679; official-filled {frac(freeze_0947, 209)} of 209 "
        f"(published part 84332471..84332600 {frac(freeze_0947_pub, 130)} of 130 on all five rooms; "
        f"tail 84332601..84332679 {frac(freeze_0947_tail, 79)} of 79, W47N8/W47N7 still official 404 @84332600 now a confirmed leftover official hole, not told); "
        "listener resumed after the 10:02:49 restart (this run did not restart it). "
        f"Prior box freeze 10:15:24–10:18:21 (~169s) room_stats gap 84332831..84332879; official-filled {frac(freeze_1015, 49)} of 49 on all five rooms; "
        "listener resumed after the 10:18:25 restart (pid 263038, this run did not restart it). "
        f"Prior 10:31 room_stats gap 84333031..84333059 official-filled {frac(freeze_1031, 29)} of 29 on all five rooms (filled by the 10:30 just-published 84333000). "
        f"New box freeze 10:47:39–10:53:38 (~358s) room_stats gap 84333241..84333339; official-filled {frac(freeze_1047, 99)} of 99 "
        f"(window 84333241..84333300 all five {frac(freeze_1047_win, 60)} of 60; just-published tail 84333301..84333339 {frac(freeze_1047_tail, 39)} of 39, W47N8@84333300 still 404 after this window, not told); "
        "listener resumed after the 10:53:41 restart (pid 279589, this run did not restart it). "
        f"Overlap 84332601..84333100 with the 10:30 window / just-published 84333000 official-filled {frac(rem_overlap, 500)} of 500 "
        f"(W46N8/W45N8/W45N7 500/500; W47N8 317/500 short on official 404 84332601..84332783; W47N7 400/500 short on official 404 84332601..84332700). "
        f"Rest of formal window 84333101..84333300 official-filled {frac(rem_new, 200)} of 200 on all five rooms. "
        f"Last official chunk in-window 84333201..84333300 official-filled {frac(rem_just_window, 100)} of 100 on all five rooms. "
        f"Just-published 84333301..84333400 official-filled {frac(rem_just_published, 100)} of 100 "
        f"(W46N8/W45N8/W45N7/W47N7 recovered; W47N8@84333300 still 404 after 3 retries through game.time=84333510, not told). "
        "In-window official 404 remains: W47N8@84332600 (0 live / 100 empty), W47N7@84332600 (0 live / 100 empty), W47N8@84332700 (17 live / 83 empty; combined W47N8 84332601..84332783), genuine official holes after later chunks published. "
        "W45N8@84332200 (0 live / 100 empty), W47N7@84331000 (0 live / 100 empty), W47N7@84330300 (0 live / 100 empty), W45N8@84328100 (16 live / 84 empty) and W45N7@84328300 (0 live / 100 empty) remain outside this window and still official 404. "
        "W45N8@84326300 (0 live / 100 empty) and W45N8@84326500 (22 live / 78 empty) remain outside this window and still official 404. "
        "W45N8@84326100 remains outside this window and still official 404 (0 live / 100 empty). "
        "W45N7@84324900 remains outside this window and still official 404. "
        "W47N8@84324300 / W47N8@84323200 / W47N8@84322100 / W47N8@84321300 / W45N7@84321600 / W47N8@84319900 and older leftovers remain outside this window and official 404."
    )
    ok_line = (
        f"ok=true (quiet); first-pass missing_chunks=3 (32 of 35 official GETs 200, 404 W47N8@84332600, W47N7@84332600, W47N8@84332700); "
        f"hourly_patrol_prefilled=true from 10:18 patrol 84332101..84332800 (overlap); 10:30 backfill already wrote through 84333100; "
        f"confirm recovered none leftover official 404s unchanged inserted=0; "
        f"retry2 still 404 leftovers and the three in-window holes inserted=0; just-published 84333300 recovered W46N8/W45N8/W45N7/W47N7 inserted=2150; W47N8@84333300 still 404 after 3 retries, not told; in-window W47 holes and leftover W45N8@84332200 still 404 official holes, not told; {inwin_txt}; "
        f"{tick_s_corr_txt}, tick_s_in_use={tick_s_in_use:.5f} (first-pass realign SUCCEEDED, ts_realigned_first={TS_REALIGNED_FIRST}); "
        f"prior 06:37 freeze gap 84330061..84330439 official-filled {frac(freeze_0637, 379)} of 379 "
        f"(four rooms 379/379; W47N7 279/379 short on leftover official 404 @84330300), no unpublished tail; "
        f"prior 07:18 freeze gap 84330581..84330609 official-filled {frac(freeze_0718, 29)} of 29 on all five rooms; "
        f"prior 07:32 freeze gap 84330761..84330789 official-filled {frac(freeze_0732, 29)} of 29 on all five rooms; "
        f"prior 07:42 freeze gap 84330881..84330909 official-filled {frac(freeze_0742, 29)} of 29 on all five rooms; "
        f"prior 07:49 freeze gap 84330981..84331089 official-filled {frac(freeze_0749, 109)} of 109 (four rooms 109/109; W47N7 20/109 short on official 404 @84331000); "
        f"prior 08:04 freeze gap 84331171..84331199 now in-window official-filled {frac(freeze_0804, 29)} of 29 (W47N7 empty-no-creep from 84331194); "
        f"prior 08:12 freeze gap 84331271..84331329 official-filled {frac(freeze_0812, 59)} of 59 (W47N7 official empty-no-creep 84331194..84331311); "
        f"prior 08:39 freeze gap 84331601..84331929 official-filled {frac(freeze_0839, 329)} of 329 on all five rooms; "
        f"prior 09:16 freeze gap 84332071..84332189 official-filled {frac(freeze_0916, 119)} of 119 on all five rooms; "
        f"prior 09:47 freeze gap 84332471..84332679 official-filled {frac(freeze_0947, 209)} of 209 (pub 130/130 all five; tail short on W47 official 404 @84332600, now confirmed leftover hole, not told); "
        f"prior 10:15 freeze gap 84332831..84332879 official-filled {frac(freeze_1015, 49)} of 49 on all five rooms; "
        f"prior 10:31 room_stats gap 84333031..84333059 official-filled {frac(freeze_1031, 29)} of 29 on all five rooms (filled by the 10:30 just-published 84333000); "
        f"new 10:47 freeze gap 84333241..84333339 official-filled {frac(freeze_1047, 99)} of 99 (window 84333241..84333300 all five {frac(freeze_1047_win, 60)} of 60; just-published tail 84333301..84333339 {frac(freeze_1047_tail, 39)} of 39, W47N8@84333300 still 404 after this window, not told); "
        f"prior 06:12 freeze gap 84329761..84329849 now before this window official-filled {frac(freeze_0612, 89)} of 89; "
        f"prior 05:43 freeze gap 84329391..84329599 still before this window official-filled {frac(freeze_0543, 209)} of 209; "
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
        f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks=3 (first pass 3; in-window official 404 W47N8@84332600, W47N7@84332600, W47N8@84332700)",
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
            f"first-pass realign SUCCEEDED ts_realigned_first={TS_REALIGNED_FIRST}; in-use {tick_s_in_use:.5f}; later over45={vs_later_after.get('over45')}."
        ),
        (
            f"confirm recovered none leftover official 404s unchanged inserted=0; retry2 still 404 leftovers inserted=0; just-published 84333300 recovered W46N8/W45N8/W45N7/W47N7 inserted=2150; W47N8@84333300 still 404 after 3 retries, not told; in-window W47N8@84332600 / W47N7@84332600 / W47N8@84332700 still 404 leftover official holes (0/0/17 live), not told; W45N8@84332200 still 404 leftover official hole (0 live), not told; {inwin_txt}; "
            f"W45N8 official empty-no-creep 0 ranges {w45n8_empty}; W45N7 official empty-no-creep 0 ranges {w45n7_empty}; "
            f"W47N7 official empty-no-creep {empty_no_creep} ranges {w47n7_empty}; {leftover_txt}"
        ),
        freeze_para,
        (
            f"listener single_slot={len(lis) <= 1 and not yield_present} roomSlot={live.get('roomSlot')} rot={rot} "
            f"yield={'present' if yield_present else 'absent'}"
        ),
        "confirm recovered none leftover official 404s unchanged inserted=0; retry2 still 404 leftovers inserted=0; just-published 84333300 recovered W46N8/W45N8/W45N7/W47N7 inserted=2150; W47N8@84333300 still 404 after 3 retries, not told; in-window W47N8@84332600 / W47N7@84332600 / W47N8@84332700 still 404 leftover official holes (0/0/17 live), not told; W45N8@84332200 still 404 leftover official hole (0 live), not told",
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
        f"missing_chunks=3 in_window_404=3 empty_no_creep={empty_no_creep}",
        (
            f"tick_s first={TICK_S_FIRST} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; "
            f"first-pass realign SUCCEEDED ts_realigned_first={TS_REALIGNED_FIRST}; in-use {tick_s_in_use:.5f}; later over45={vs_later_after.get('over45')}."
        ),
        (
            f"confirm recovered none leftover official 404s unchanged inserted=0; retry2 still 404 leftovers inserted=0; just-published 84333300 recovered W46N8/W45N8/W45N7/W47N7 inserted=2150; W47N8@84333300 still 404 after 3 retries, not told; in-window W47N8@84332600 / W47N7@84332600 / W47N8@84332700 still 404 leftover official holes (0/0/17 live), not told; W45N8@84332200 still 404 leftover official hole (0 live), not told; {inwin_txt}; "
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
        shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1100.txt")

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
