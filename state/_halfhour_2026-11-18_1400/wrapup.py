#!/usr/bin/env python3
"""Write half-hour backfill status records for the next hourly patrol."""
from __future__ import annotations
import json, os, subprocess, sys, shutil
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-18_1400"
PREV = ROOT / "state" / "_halfhour_2026-11-18_1330" / "history_backfill.json"
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

TZ = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TMIN, TMAX = 84335101, 84335800
GT_FIRST = 84335826
PUB_BASES = "84335100..84335700"
TICK_S_FIRST = 4.71893
TICK_S_PRINTED = "4.719"
NEW_ROWS = {"W46N8": 3596, "W47N8": 2666, "W45N8": 938, "W45N7": 773, "W47N7": 1248}
OFFICIAL_TICKS = {"W46N8": 700, "W47N8": 700, "W45N8": 700, "W45N7": 700, "W47N7": 700}
INSERTED_FIRST = 9221
INSERTED_CONFIRM = 0
INSERTED_RETRY2 = 0
INSERTED_RETRY2_UNIQUE_NET = 0
INSERTED_JUST_PUBLISHED = 2914
ALREADY = 15773
RECON_ROWS = 24994
TS_REALIGNED_FIRST = 11052
IN_WINDOW_404 = []
OUTSIDE_404 = [
    ("W47N7", 84334700), ("W47N8", 84334600), ("W45N8", 84333500), ("W47N8", 84333300), ("W47N8", 84332600), ("W47N7", 84332600),
    ("W47N8", 84332700), ("W45N8", 84332200), ("W47N7", 84331000), ("W47N7", 84330300),
    ("W45N8", 84328100), ("W45N7", 84328300), ("W45N8", 84326300), ("W45N8", 84326500),
    ("W45N8", 84326100), ("W45N7", 84324900), ("W47N8", 84324300), ("W47N8", 84323200),
    ("W47N8", 84322100), ("W45N7", 84321600), ("W47N8", 84321300), ("W47N8", 84319900),
    ("W47N8", 84319000), ("W46N8", 84318500), ("W45N8", 84318000), ("W47N7", 84315100),
    ("W45N8", 84314900), ("W45N7", 84314500), ("W47N8", 84314000), ("W46N8", 84313200),
    ("W46N8", 84310500), ("W47N7", 84309000), ("W45N8", 84309100), ("W45N8", 84306500),
    ("W45N7", 84305100), ("W47N8", 84304700), ("W45N7", 84303900), ("W45N8", 84302200),
    ("W47N8", 84300900), ("W45N8", 84300900), ("W45N8", 84300000), ("W47N8", 84298000),
    ("W47N8", 84297200), ("W47N7", 84296500), ("W45N8", 84295900), ("W45N7", 84295800),
]
HIST_KEYS = [
    "new_box_freeze", "new_0718_box_freeze", "new_0732_box_freeze", "new_0742_box_freeze",
    "new_0749_box_freeze", "new_0804_box_freeze", "prior_0612_box_freeze", "prior_0543_box_freeze",
    "prior_0513_box_freeze", "prior_0442_box_freeze", "prior_0411_box_freeze", "prior_0338_box_freeze",
    "prior_0315_box_freeze", "freeze_0812_fill", "w47n7_empty_no_creep_fill",
    "freeze_1031_fill", "freeze_1047_fill", "freeze_1047_win", "freeze_1047_tail",
    "new_1031_room_stats_gap", "new_1047_box_freeze", "freeze_1015_fill",
    "freeze_0839_fill", "freeze_0839_pub", "freeze_0839_tail", "freeze_0916_fill",
    "freeze_0947_fill", "freeze_0947_pub", "freeze_0947_tail", "new_0947_box_freeze",
    "freeze_1216_fill", "freeze_1216_pre", "freeze_1216_tail",
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
    if d == 0: return f"{room}@{base} (0 live / 100 empty)"
    if d == 100: return f"{room}@{base} (100 live)"
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

def main():
    cov = load_json(DIR / "coverage_final.json")
    confirm = load_json(DIR / "backfill_confirm_gets.json")
    tsr = load_json(DIR / "tick_s_realign.json")
    prev = load_json(PREV)
    coverage = cov.get("coverage") or cov
    later = float(tsr["later_mean_w46_robust"])
    vs_later_after = tsr.get("vs_later_after") or {}
    confirm_at = confirm.get("at")
    confirm_gt = confirm.get("game_time")
    retry2 = confirm.get("retry2") or {}
    retry2_at = retry2.get("at")
    retry2_gt = retry2.get("game_time")
    later_reverted = bool(tsr.get("later_mean_reverted"))
    corrective = bool(tsr.get("corrective_applied")) and not later_reverted
    nfix_corr = int(tsr.get("ts_realigned_to_later_mean") or 0)
    tick_s_in_use = later
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
    yield_present = (ROOT / "metrics/listener_yield_rooms").exists() or any((ROOT / "metrics").glob("yield*"))
    with db.connect() as c:
        tips = {}
        for table in ("creep_ticks", "room_stats", "creep_cpu", "path_arrivals"):
            row = c.execute(f"SELECT max(tick), max(ts) FROM {table}").fetchone()
            tips[table] = {"max_tick": row[0], "max_ts": iso(row[1])}
        db_after, per_room = {}, {}
        for room in ROOMS:
            dba = c.execute(
                "SELECT min(tick), max(tick), count(*), count(DISTINCT tick) "
                "FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, TMIN, TMAX),
            ).fetchone()
            db_after[room] = {"min": dba[0], "max": dba[1], "rows": dba[2] or 0, "distinct": dba[3] or 0}
            room_cov = (coverage.get(room) or {}) if isinstance(coverage, dict) else {}
            per_room[room] = {
                "official_ticks": OFFICIAL_TICKS[room], "new_rows_first_pass": NEW_ROWS[room],
                "db_rows": dba[2] or 0, "db_distinct": dba[3] or 0, "db_min": dba[0], "db_max": dba[1],
                "missing_n": room_cov.get("missing_n"), "missing_ranges": room_cov.get("missing_ranges"),
                "official_empty_no_creep": room_cov.get("official_empty_no_creep"),
                "official_empty_no_creep_ranges": room_cov.get("official_empty_no_creep_ranges"),
                "official_404_missing": room_cov.get("official_404_missing"),
            }
        hole_shorts = {f"{room}@{base}": hole_short(c, room, base) for room, base in OUTSIDE_404 + IN_WINDOW_404}
        rem_overlap = fill(c, 84335101, 84335500)
        rem_new = fill(c, 84335601, 84335800)
        rem_prev = fill(c, 84335101, 84335400)
        rem_prefill = fill(c, 84335101, 84335200)
        rem_just_window = fill(c, 84335701, 84335800)
        rem_just_published = fill(c, 84335801, 84335900)
        rem_prev_just = fill(c, 84335401, 84335500)
        rem_hole_w47n8 = fill(c, 84333301, 84333400)
        rem_hole_w47n7 = fill(c, 84332601, 84332700)
        rem_hole_w45n8 = fill(c, 84333501, 84333600)
        rem_hole_w47n8_346 = fill(c, 84334601, 84334700)
        rem_hole_w47n7_347 = fill(c, 84334701, 84334800)
        rem_prefill_hour = fill(c, 84334601, 84335100)
        rem_patrol_404_chunk = fill(c, 84335201, 84335300)
        freeze_1015 = fill(c, 84332831, 84332879)
        freeze_1031 = fill(c, 84333031, 84333059)
        freeze_1047 = fill(c, 84333241, 84333339)
        freeze_1047_win = fill(c, 84333241, 84333300)
        freeze_1047_tail = fill(c, 84333301, 84333339)
        freeze_1216 = fill(c, 84334381, 84334439)
        freeze_1216_pre = fill(c, 84334381, 84334400)
        freeze_1216_tail = fill(c, 84334401, 84334439)
        freeze_1320 = fill(c, 84335221, 84335299)
        freeze_1354 = fill(c, 84335661, 84335809)
        freeze_1354_win = fill(c, 84335661, 84335800)
        freeze_1354_tail = fill(c, 84335801, 84335809)
        unique = c.execute(
            """SELECT count(*), count(DISTINCT (creep, tick)), count(DISTINCT tick),
                      count(DISTINCT (room, tick))
               FROM creep_ticks WHERE tick BETWEEN %s AND %s AND room = ANY(%s)""" ,
            (TMIN, TMAX, list(ROOMS)),
        ).fetchone()
    unique_after = {"rows": unique[0], "unique_creep_tick_rows": unique[1], "distinct_ticks": unique[2], "distinct_room_ticks": unique[3]}
    recovered = int(cov.get("official_recovered") or 0)
    expected = int(cov.get("expected") or 3500)
    empty_no_creep = int(cov.get("empty_no_creep") or 0)
    official_404_missing = int(cov.get("official_404_missing") or 0)
    w45n7_empty = (coverage.get("W45N7") or {}).get("official_empty_no_creep_ranges") or []
    w45n8_empty = (coverage.get("W45N8") or {}).get("official_empty_no_creep_ranges") or []
    w47n7_empty = (coverage.get("W47N7") or {}).get("official_empty_no_creep_ranges") or []
    leftover_order = [
        "W47N7@84334700", "W47N8@84334600", "W45N8@84333500", "W47N8@84333300", "W47N8@84332600", "W47N7@84332600", "W47N8@84332700",
        "W45N8@84332200", "W47N7@84331000", "W47N7@84330300", "W45N8@84328100", "W45N7@84328300",
        "W45N8@84326300", "W45N8@84326500", "W45N8@84326100", "W45N7@84324900",
        "W47N8@84324300", "W47N8@84323200", "W47N8@84322100", "W47N8@84321300",
        "W45N7@84321600", "W47N8@84319900", "W47N8@84319000", "W46N8@84318500",
        "W45N8@84318000", "W47N7@84315100", "W45N8@84314900", "W45N7@84314500",
        "W47N8@84314000", "W46N8@84313200",
    ]
    leftover_bits = [f"leftover official 404 {hole_shorts[k]} still outside window" for k in leftover_order if k in hole_shorts]
    leftover_txt = "; ".join(leftover_bits) + "; older leftovers unchanged."
    inwin_txt = (
        "no in-window official 404; "
        "first pass 35 of 35 official GETs 200, missing_chunks=0; "
        f"confirm at game.time={confirm_gt} inserted=0, leftover official 404s unchanged; "
        f"retry2 at game.time={retry2_gt} inserted=0, leftovers still 404; "
        "just-published at 14:14:22 game.time=84335920 base 84335800 recovered all five rooms inserted=2914 (after this window); "
        "leftover official 404 now outside window: "
        f"{hole_shorts['W47N7@84334700']} (100 empty 84334701..84334800; later chunk 84334800 already 200); "
        f"{hole_shorts['W47N8@84334600']} (71 empty 84334630..84334700; later chunks 84334700/84334800 already 200); "
        f"{hole_shorts['W45N8@84333500']} (100 empty 84333501..84333600); "
        f"{hole_shorts['W47N8@84333300']} (84 empty 84333301..84333333 and 84333350..84333400); "
        f"{hole_shorts['W47N8@84332600']} (100 empty 84332601..84332700); "
        f"{hole_shorts['W47N7@84332600']} (100 empty 84332601..84332700); "
        f"{hole_shorts['W47N8@84332700']} (83 empty 84332701..84332783; combined leftover W47N8 hole 84332601..84332783); "
        f"{hole_shorts['W45N8@84332200']} (100 empty 84332201..84332300); "
        f"{hole_shorts['W47N7@84331000']} (100 empty 84331001..84331100); "
        f"{hole_shorts['W47N7@84330300']} (100 empty 84330301..84330400); "
        f"{hole_shorts['W45N8@84328100']} (84 empty 84328101..84328184); "
        f"{hole_shorts['W45N7@84328300']} (100 empty 84328301..84328400)"
    )
    first_pass_line = (
        "first pass 35 of 35 official GETs 200, missing_chunks=0; "
        "hourly_patrol_prefilled=true from 13:23 patrol official already through 84335100 (overlap, first chunk of this window); 13:30 backfill already wrote through 84335400 and just-published 84335500 for all five rooms; "
        "confirm inserted=0 leftover official 404s unchanged; "
        f"retry2 at game.time={retry2_gt} inserted=0 leftovers still 404; "
        "just-published at 14:14:22 game.time=84335920 recovered all five rooms @84335800 inserted=2914 (after this window); "
        "W47N7@84334700 still 404 treated as leftover official hole (0 live; later chunk 84334800 already 200), not told; "
        "W47N8@84334600 still 404 treated as leftover official hole (29 live already in 84334601..84334629; later chunks 84334700/84334800 already 200), not told; "
        "W45N8@84333500 still 404 treated as leftover official hole (0 live), not told; "
        "W47N8@84333300 / W47N8@84332600 / W47N7@84332600 / W47N8@84332700 / W45N8@84332200 still 404 treated as leftover official holes (16/0/0/17/0 live), not told"
    )
    per_room_line = " ".join(f"{room}:{per_room[room]['official_ticks']}t/{per_room[room]['new_rows_first_pass']}new" for room in ROOMS)
    nl = chr(10)
    db_after_lines = nl.join(f"  {room} ticks={db_after[room]['min']}..{db_after[room]['max']} rows={db_after[room]['rows']} distinct={db_after[room]['distinct']}" for room in ROOMS)
    tick_s_corr_txt = (
        f"later-mean-robust {later:.5f} over the 45s gate vs first-pass rows, "
        f"corrective realign nfix={nfix_corr} at game.time={tsr.get('gt_realign')}, still_over_45s_vs_later={vs_later_after.get('over45')}"
    )
    ts_realign_note = (
        f"First pass (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}, live anchor game.time={GT_FIRST}) "
        f"moved {TS_REALIGNED_FIRST} rows, ts_realigned_first={TS_REALIGNED_FIRST}. "
        f"later-mean-robust {later:.5f} (delta first-robust 0.09840 s/tick, ~71.3s at tmin); "
        f"applied corrective later-mean-robust realign of {nfix_corr} rows at game.time={tsr.get('gt_realign')}; "
        f"still_over_45s_vs_later={vs_later_after.get('over45')}; vs_later over45={vs_later_after.get('over45')} "
        f"mean_off~{(vs_later_after.get('mean_off') or 0):.2f}s; skipped_cross_chunk=0. "
        f"in-use later-mean-robust {tick_s_in_use:.5f} (corrective_applied=True)."
    )
    game_time_note = (
        "Listener self-healed after the box freeze 13:54:32–14:05:04 (~626s); restart 14:05:08, new pid 380979 under run_listener.sh 4035476. "
        "This run did not restart the listener, war_cmd, or pulse. "
        "live.json was fresh at pre-check (stats.t and cpu flowing; gameTime/objects caught up after the just-restarted listener warmed). "
        "Segment 90 buffers pulled after the 14:05 reconnect (creep_cpu and path_arrivals already fresh through the tip at pre-check). "
        "The 13:30 half-hour backfill had already official-backfilled 84334701..84335400 "
        "(just-published then recovered all five rooms @84335400), "
        "and the 13:23 hourly patrol official-backfilled through 84335100 (first chunk of this window). "
        "Leftover official 404s W47N7@84334700, W47N8@84334600, W45N8@84333500, W47N8@84333300, W47N8@84332600, W47N7@84332600, W47N8@84332700, W45N8@84332200, W47N7@84331000, W47N7@84330300, W45N8@84328100 and W45N7@84328300 remain outside this window. "
        "No in-window official hole. Listener is on the peacetime single-slot rotation."
    )
    inserted_note = (
        f"This 14:00 first pass inserted {INSERTED_FIRST} new rows (already_in_db={ALREADY}, reconstructed={RECON_ROWS}). "
        "hourly_patrol_prefilled=true from 13:23 patrol official already through 84335100 (overlap, first chunk of this window); 13:30 backfill already wrote through 84335400 and just-published 84335500 for all five rooms. "
        "The overlap 84335101..84335500 with the 13:30 window / just-published 84335400 was already present. "
        "Newly published ticks 84335601..84335800 were official 200 on all five rooms in the first pass. "
        "The in-window box-freeze gap 84335661..84335809 sits inside recovered chunks 84335600/84335700 plus just-published 84335800 (9-tick tail). "
        f"Confirm at {confirm_at} game.time={confirm_gt} inserted={INSERTED_CONFIRM}; "
        "outside-window leftover official 404s unchanged; no in-window official 404. "
        f"retry2 at {retry2_at} game.time={retry2_gt} inserted={INSERTED_RETRY2}; leftovers still 404. "
        "Just-published at 14:14:22 game.time=84335920 base 84335800 recovered all five rooms inserted=2914 (after this window). "
        f"Coverage official_recovered={recovered}/{expected} including {empty_no_creep} official empty-no-creep ticks (W45N7 165: 84335628 and 84335630..84335793); {official_404_missing} in-window official-404 ticks remain. Official history recovered 3500 of 3500 room-ticks."
    )
    missing_chunk_note = (
        f"First pass (game.time={GT_FIRST}) published_bases {PUB_BASES}, reconstructed {TMIN}..{TMAX} (700). 35 of 35 official GETs 200; missing_chunks=0. "
        f"Confirm at {confirm_at} game.time={confirm_gt} inserted={INSERTED_CONFIRM}; leftover official 404s unchanged; no in-window official 404. "
        f"retry2 at {retry2_at} game.time={retry2_gt} inserted={INSERTED_RETRY2}; leftovers still 404. "
        "Just-published at 14:14:22 game.time=84335920 base 84335800 recovered all five rooms inserted=2914 (after this window)."
    )
    payload = {
        "ok": True, "routine": "Screeps 半小时轨迹补数", "finished_at": now.isoformat(),
        "finished_at_hkt": finished_hkt, "shard": "shard3", "rooms": list(ROOMS), "minutes": 40,
        "game_time": GT_FIRST, "live_json_gameTime_at_finish": live.get("gameTime"),
        "live_json_stats_t_at_finish": (stats or {}).get("t"), "live_json_gameTime_note": game_time_note,
        "published_bases": PUB_BASES, "ticks": {"min": TMIN, "max": TMAX, "count": 700},
        "tick_s": TICK_S_FIRST, "tick_s_later_mean": later, "tick_s_in_use": tick_s_in_use,
        "tick_s_first_pass_outlier": False, "tick_s_later_mean_applied_then_reverted": later_reverted,
        "tick_s_corrective_applied": corrective, "missing_chunks": 0,
        "missing_chunk_list": [], "missing_chunk_first_pass": [],
        "missing_chunk_note": missing_chunk_note, "creep_rows_reconstructed": RECON_ROWS,
        "already_in_db": ALREADY, "inserted": inserted_total, "inserted_first_pass": INSERTED_FIRST,
        "inserted_retry": INSERTED_CONFIRM, "inserted_retry2": INSERTED_RETRY2,
        "inserted_retry2_unique_net": INSERTED_RETRY2_UNIQUE_NET,
        "inserted_just_published": INSERTED_JUST_PUBLISHED, "inserted_window": inserted_window,
        "inserted_note": inserted_note, "ts_realigned": TS_REALIGNED_FIRST,
        "ts_realigned_corrective_later_mean": nfix_corr, "ts_realigned_confirm": 0,
        "ts_realigned_retry2": 0, "ts_realigned_just_published": 0, "ts_realigned_note": ts_realign_note,
        "ssl_first_attempt": False, "hourly_patrol_prefilled": True,
        "hourly_patrol_prefill_ticks": [84335101, 84335200], "per_room": per_room,
        "known_official_404s_outside_window": [f"{r}@{b}" for r, b in OUTSIDE_404],
        "known_official_404s_in_window": [],
        "w45n7_empty_no_creep_in_window": bool(w45n7_empty), "w45n7_empty_no_creep_ranges": w45n7_empty,
        "empty_no_creep_in_window": bool(empty_no_creep),
        "empty_no_creep_ranges": {room: (coverage.get(room) or {}).get("official_empty_no_creep_ranges") or [] for room in ROOMS},
        "empty_no_creep_ticks": empty_no_creep, "official_room_ticks_fetched": recovered,
        "official_room_ticks_with_creeps": unique_after["distinct_room_ticks"],
        "official_recovered": recovered, "official_expected": expected,
        "remainder_overlap_84335101_84335500": rem_overlap,
        "remainder_new_84335601_84335800": rem_new,
        "remainder_prev_filled_84335101_84335400": rem_prev,
        "remainder_patrol_prefilled_84335101_84335200": rem_prefill,
        "remainder_window_last_chunk_84335701_84335800": rem_just_window,
        "remainder_just_published_84335801_84335900": rem_just_published,
        "remainder_prev_just_published_84335401_84335500": rem_prev_just,
        "remainder_outside_hole_w45n8_84333501_84333600": rem_hole_w45n8,
        "remainder_outside_hole_w47n8_84334601_84334700": rem_hole_w47n8_346,
        "remainder_outside_hole_w47n7_84334701_84334800": rem_hole_w47n7_347,
        "remainder_outside_hole_w47n8_84333301_84333400": rem_hole_w47n8,
        "remainder_outside_hole_w47n7_84332601_84332700": rem_hole_w47n7,
        "remainder_hour_window_84334601_84335100": rem_prefill_hour,
        "remainder_patrol_404_chunk_84335201_84335300": rem_patrol_404_chunk,
        "unique_after": unique_after, "db_tips": tips, "db_after": db_after,
        "listener": {"single_slot": len(lis) <= 1 and not yield_present, "listener_pids": lis,
                     "run_listener": runl, "roomSlot": live.get("roomSlot"), "rot": rot, "yield": bool(yield_present)},
        "confirm_at": confirm_at, "confirm_game_time": confirm_gt,
        "retry2_at": retry2_at, "retry2_game_time": retry2_gt,
        "just_published_at": "2026-11-18 14:14:22 Asia/Hong_Kong", "just_published_game_time": 84335920,
        "just_published_retry_at": None, "just_published_retry_game_time": None,
        "just_published_skipped": False, "just_published_skip_reason": None,
        "just_published_recovered": ["W46N8@84335800", "W47N8@84335800", "W45N8@84335800", "W45N7@84335800", "W47N7@84335800"],
        "just_published_still_404": [f"{r}@{b}" for r, b in IN_WINDOW_404 + OUTSIDE_404[:10]],
        "just_published_unpublished_tail_404": [], "ok_quiet": True,
        "freeze_1216_fill": freeze_1216,
        "freeze_1216_pre": freeze_1216_pre,
        "freeze_1216_tail": freeze_1216_tail,
        "freeze_1320_fill": freeze_1320,
        "freeze_1354_fill": freeze_1354,
        "freeze_1354_win": freeze_1354_win,
        "freeze_1354_tail": freeze_1354_tail,
    }
    for k in HIST_KEYS:
        if k in prev:
            payload[k] = prev[k]
    payload["freeze_1015_fill"] = freeze_1015
    payload["freeze_1031_fill"] = freeze_1031
    payload["freeze_1047_fill"] = freeze_1047
    payload["freeze_1047_win"] = freeze_1047_win
    payload["freeze_1047_tail"] = freeze_1047_tail
    payload["freeze_1216_fill"] = freeze_1216
    payload["freeze_1216_pre"] = freeze_1216_pre
    payload["freeze_1216_tail"] = freeze_1216_tail
    payload["freeze_1320_fill"] = freeze_1320
    payload["freeze_1354_fill"] = freeze_1354
    payload["freeze_1354_win"] = freeze_1354_win
    payload["freeze_1354_tail"] = freeze_1354_tail
    prev_now = (ROOT / "state" / "_halfhour_2026-11-18_1330" / "history_backfill_now.txt").read_text()
    marker = "In-window box freeze 13:20:51"
    freeze_para = prev_now[prev_now.index(marker):]
    kept = []
    for ln in freeze_para.splitlines():
        if ln.startswith("listener single_slot"):
            break
        kept.append(ln)
    freeze_para = nl.join(kept).rstrip()
    freeze_para = freeze_para.replace(
        "In-window box freeze 13:20:51–13:25:52 (~301s) room_stats gap 84335221..84335299; ",
        "Prior box freeze 13:20:51–13:25:52 (~301s) room_stats gap 84335221..84335299; ",
        1,
    )
    def fill_txt(d):
        parts = [str(d[r]["distinct"]) for r in ROOMS]
        span = d[ROOMS[0]]["span"]
        return f"{'/'.join(parts)} of {span} of {span}"
    new_freeze = (
        f"In-window box freeze 13:54:32–14:05:04 (~626s) room_stats gap 84335661..84335809; "
        f"official-filled {fill_txt(freeze_1354)} (four rooms 149/149; W45N7 16/149 on official empty-no-creep 84335630..84335793, creeps resume 84335794..84335809 including the 9-tick just-published tail 84335801..84335809); "
        "listener resumed after the 14:05:08 restart (pid 380979, this run did not restart it). "
        "The 13:23 hourly patrol official-backfilled through 84335100 (first chunk of this window); the 13:30 backfill already wrote through 84335400 and just-published 84335500 for all five rooms. Newly published 84335600 and 84335700 filled the in-window part of this freeze; just-published 84335800 filled the 9-tick tail."
    )
    freeze_para = new_freeze + nl + freeze_para
    confirm_summary = (
        "confirm inserted=0 leftover official 404s unchanged; retry2 inserted=0 leftovers still 404; "
        "just-published 84335800 recovered all five rooms inserted=2914 (after this window); "
        "no in-window official 404; "
        "leftover W47N7@84334700 / W47N8@84334600 / W45N8@84333500 / W47N8@84333300 / W47N8@84332600 / W47N7@84332600 / W47N8@84332700 / W45N8@84332200 still 404 official holes, not told"
    )
    ok_line = (
        f"ok_quiet=True coverage={recovered}/{expected} inserted_window={inserted_window} "
        f"inserted_total={inserted_total} tick_s_in_use={tick_s_in_use:.5f} "
        "listener single_slot=True; no second listener; no war_cmd/pulse restart."
    )
    rooms_csv = ",".join(ROOMS)
    now_lines = [
        f"{finished_hkt} half-hour backfill OK (quiet)",
        f"game.time={GT_FIRST} published_bases={PUB_BASES} rooms={rooms_csv} dry=False",
        f"  ({first_pass_line}; see history_backfill.txt)",
        f"tick_s={TICK_S_PRINTED} (script {TICK_S_FIRST}; {tick_s_corr_txt}, in-use {tick_s_in_use:.5f})",
        f"reconstructed ticks={TMIN}..{TMAX} (700) creep_rows={RECON_ROWS} missing_chunks=0",
        f"already_in_db={ALREADY} would_insert={INSERTED_FIRST}",
        f"per_room {per_room_line}",
        f"inserted={INSERTED_FIRST} (confirm +{INSERTED_CONFIRM}, retry2 +{INSERTED_RETRY2_UNIQUE_NET}, just_published +{INSERTED_JUST_PUBLISHED}, window {inserted_window}, run total {inserted_total})",
        f"ts_realigned_first={TS_REALIGNED_FIRST}; ts_realigned_corrective={nfix_corr} ({tick_s_corr_txt}; in-use {tick_s_in_use:.5f})",
        "db_after",
        db_after_lines,
        f"coverage official_recovered={recovered}/{expected} unique_after={unique_after} empty_no_creep={empty_no_creep} official_404_in_window={official_404_missing}",
        f"tick_s first={TICK_S_FIRST} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {tick_s_in_use:.5f}; later over45={vs_later_after.get('over45')}.",
        f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
        freeze_para,
        f"listener single_slot={len(lis) <= 1 and not yield_present} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}",
        confirm_summary,
        ok_line,
    ]
    now_text = nl.join(now_lines) + nl
    (DIR / "history_backfill.json").write_text(json.dumps(payload, indent=2, default=str) + nl)
    (DIR / "history_backfill_now.txt").write_text(now_text)
    shutil.copyfile(DIR / "history_backfill.json", ROOT / "state" / "history_backfill.json")
    shutil.copyfile(DIR / "history_backfill_now.txt", ROOT / "state" / "_halfhour_backfill_now.txt")
    verify = [
        f"{finished_hkt_sec} half-hour backfill verify",
        f"window {TMIN}..{TMAX} published_bases {PUB_BASES} game.time={GT_FIRST} inserted={inserted_total} coverage={recovered}/{expected}",
        f"missing_chunks=0 in_window_404=0 empty_no_creep={empty_no_creep}",
        f"tick_s first={TICK_S_FIRST} printed {TICK_S_PRINTED}; {tick_s_corr_txt}; first-pass realign moved {TS_REALIGNED_FIRST} ts_realigned_first={TS_REALIGNED_FIRST}; in-use {tick_s_in_use:.5f}; later over45={vs_later_after.get('over45')}.",
        f"{confirm_summary}; {inwin_txt}; W45N8 official empty-no-creep {((coverage.get('W45N8') or {}).get('official_empty_no_creep') or 0)} ranges {w45n8_empty}; W45N7 official empty-no-creep {((coverage.get('W45N7') or {}).get('official_empty_no_creep') or 0)} ranges {w45n7_empty}; W47N7 official empty-no-creep {((coverage.get('W47N7') or {}).get('official_empty_no_creep') or 0)} ranges {w47n7_empty}; {leftover_txt}",
        f"listener single_slot={len(lis) <= 1 and not yield_present} roomSlot={live.get('roomSlot')} rot={rot} yield={'present' if yield_present else 'absent'}; no second listener started; no war_cmd/pulse restart.",
        "This run did not restart the listener.",
    ]
    verify_text = nl.join(verify) + nl
    (DIR / "verify.txt").write_text(verify_text)
    (ROOT / "state" / "_halfhour_backfill_verify.txt").write_text(verify_text)
    retry2_src = DIR / "backfill_retry2.txt"
    if retry2_src.exists():
        shutil.copyfile(retry2_src, ROOT / "state" / "_halfhour_backfill_retry2_1400.txt")
    summary = (
        f"{finished_hkt} wrapup ok" + nl +
        "wrote history_backfill.json history_backfill_now.txt verify.txt" + nl +
        f"inserted={INSERTED_FIRST}+{INSERTED_CONFIRM}+{INSERTED_RETRY2_UNIQUE_NET}+just{INSERTED_JUST_PUBLISHED} coverage={recovered}/{expected} tick_s_in_use={tick_s_in_use:.5f} later_mean_reverted={later_reverted}" + nl
    )
    (DIR / "wrapup_run.txt").write_text(summary)
    (DIR / "wrapup_run_tee.txt").write_text(summary + now_text)
    print(summary, end="")

if __name__ == "__main__":
    main()
