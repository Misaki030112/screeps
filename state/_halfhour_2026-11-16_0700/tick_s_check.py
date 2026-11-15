#!/usr/bin/env python3
"""Compare first-interval tick_s with later W46N8 mean; realign if over the 45s gate.

This window's first official interval is the known-short 84292900..84293000 (4.16927),
and 84293300..84293400 has a ~9.1s official-timestamp gap (likely history publish delay
and/or a shard slowdown). We evaluate several tick_s candidates against a live anchor
before applying any corrective realign.
"""
from __future__ import annotations
import json, sys, os, time
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-16_0700"
os.chdir(ROOT)
sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")
import db, api
import history_backfill as hb

# Official chunk timestamps printed by history_backfill.py (W46N8 ts per base).
# Script tick_s uses min timestamp across all rooms of the two earliest published bases:
#   min 84292900 = W46N8 ts=1794780791417, min 84293000 = W46N8 ts=1794781208344
#   → 4.16927s (printed 4.169).
W46 = {
    84292900: 1794780791417,
    84293000: 1794781208344,
    84293100: 1794781643737,
    84293200: 1794782066130,
    84293300: 1794782499129,
    84293400: 1794783409305,
    84293500: 1794783829705,
}
# min timestamp across all five rooms per base (same as history_backfill.tick_seconds inputs)
MIN_ALL = {
    84292900: 1794780791417,  # W46N8
    84293000: 1794781208344,  # W46N8
    84293100: 1794781643737,  # W46N8
    84293200: 1794782066130,  # W46N8
    84293300: 1794782499129,  # W46N8
    84293400: 1794783407364,  # W45N7 (slightly earlier than W46N8)
    84293500: 1794783829705,  # W46N8
}
TMIN, TMAX = 84292901, 84293600
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = 4.16927  # exact first-interval used by the script (printed 4.169)
GT_FIRST = 84293626
TS_REALIGNED_FIRST = 14847
# Previous 06:30 run later-mean, already inside 45s gate for 84292501..84293200
PREV_LATER_MEAN = 4.29335

def intervals(d):
    bases = sorted(d)
    out = []
    for a, b in zip(bases, bases[1:]):
        sec = (d[b] - d[a]) / 1000.0 / (b - a)
        out.append((a, b, sec))
    return out

def game_time():
    err = None
    for attempt in range(3):
        try:
            return api.req("game/time?shard=shard3")["time"], None
        except Exception as e:
            err = repr(e)
            print(f"game/time attempt {attempt+1} failed: {err}")
            time.sleep(3 * (attempt + 1))
    live = json.load(open(ROOT / "metrics/live.json"))
    stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
    gt = live.get("gameTime") or stats.get("t")
    print(f"fell back to live.json gameTime/stats.t={gt}")
    return gt, err

def main():
    iv = intervals(W46)
    first = iv[0][2]
    later = [x[2] for x in iv[1:]]
    later_mean_raw = sum(later) / len(later)
    all_mean = sum(x[2] for x in iv) / len(iv)
    robust_later = [x for x in later if 3.0 <= x <= 6.0]
    later_mean_robust = sum(robust_later) / len(robust_later) if robust_later else later_mean_raw
    iv_min = intervals(MIN_ALL)
    span_mean = (MIN_ALL[max(MIN_ALL)] - MIN_ALL[min(MIN_ALL)]) / 1000.0 / (max(MIN_ALL) - min(MIN_ALL))
    print("intervals_w46:")
    for a, b, s in iv:
        flag = " OUTLIER" if not (3.0 <= s <= 6.0) else ""
        print(f"  {a}..{b} {s:.5f}{flag}")
    print("intervals_min_all_rooms:")
    for a, b, s in iv_min:
        flag = " OUTLIER" if not (3.0 <= s <= 6.0) else ""
        print(f"  {a}..{b} {s:.5f}{flag}")
    print(f"first={first:.5f} later_mean_raw={later_mean_raw:.5f} later_mean_robust={later_mean_robust:.5f}")
    print(f"all_mean={all_mean:.5f} span_mean={span_mean:.5f} script_tick_s={TICK_S_FIRST} prev_later={PREV_LATER_MEAN}")
    print(f"delta_first_minus_later_raw={first-later_mean_raw:.5f} s/tick; at tmin vs gt_first ~{(GT_FIRST-TMIN)*abs(first-later_mean_raw):.1f}s")
    print(f"delta_first_minus_later_robust={first-later_mean_robust:.5f} s/tick; at tmin vs gt_first ~{(GT_FIRST-TMIN)*abs(first-later_mean_robust):.1f}s")

    now_ts = datetime.now(timezone.utc)
    hk = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    gt, gerr = game_time()
    print(f"anchor {hk} game.time={gt}")

    def counts(tick_s, now_ts=now_ts, gt=gt):
        with db.connect() as c:
            row = c.execute(
                """
                SELECT
                  count(*) FILTER (WHERE abs(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) > 45) AS over45,
                  count(*) FILTER (WHERE abs(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) > 15) AS over15,
                  count(*) AS n,
                  avg(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) AS mean_off,
                  min(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) AS min_off,
                  max(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) AS max_off
                FROM creep_ticks
                WHERE tick BETWEEN %(t0)s AND %(t1)s AND room = ANY(%(rooms)s)
                """,
                {"now": now_ts, "gt": gt, "tick_s": tick_s, "t0": TMIN, "t1": TMAX, "rooms": list(ROOMS)},
            ).fetchone()
        return {"over45": row[0], "over15": row[1], "n": row[2],
                "mean_off": float(row[3] or 0), "min_off": float(row[4] or 0), "max_off": float(row[5] or 0)}

    candidates = {
        "first": TICK_S_FIRST,
        "later_raw": later_mean_raw,
        "later_robust": later_mean_robust,
        "all_mean": all_mean,
        "span_mean": span_mean,
        "prev_later": PREV_LATER_MEAN,
    }
    vs = {k: counts(v) for k, v in candidates.items()}
    for k, v in candidates.items():
        print(f"vs_{k} tick_s={v:.5f}", vs[k])

    # Live-row probe: ticks the listener almost certainly wrote itself
    # (W46N8 84293201..84293317 before the 06:43 freeze; W47N8 after reconnect if any after TMAX skipped)
    with db.connect() as c:
        probes = c.execute(
            """
            SELECT room, tick, ts
            FROM creep_ticks
            WHERE (room='W46N8' AND tick BETWEEN 84293300 AND 84293317)
               OR (room='W47N8' AND tick BETWEEN 84293350 AND 84293370)
            ORDER BY room, tick
            LIMIT 8
            """
        ).fetchall()
    print("sample_existing_ts (pre-freeze live-ish):")
    for room, tick, ts in probes:
        pred_first = now_ts + timedelta(seconds=(tick - gt) * TICK_S_FIRST)
        pred_rob = now_ts + timedelta(seconds=(tick - gt) * later_mean_robust)
        pred_prev = now_ts + timedelta(seconds=(tick - gt) * PREV_LATER_MEAN)
        # ts may be offset-aware
        def off(pred, ts=ts):
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=ZoneInfo("Asia/Hong_Kong"))
            return (ts - pred).total_seconds()
        print(f"  {room} {tick} ts={ts} off_first={off(pred_first):.1f}s off_robust={off(pred_rob):.1f}s off_prev={off(pred_prev):.1f}s")

    # Choose tick_s for a possible corrective realign:
    # Prefer a candidate that brings over45 to 0 (or the lowest over45),
    # but do not use later_raw / all_mean if they are pulled above 6s by the
    # 84293300..84293400 official-timestamp gap. Prefer later_robust, then prev_later.
    chosen_name = "later_robust"
    chosen = later_mean_robust
    # If later_robust still leaves many over45 and prev_later/first is better, say so.
    def score(name):
        s = vs[name]
        return (s["over45"], abs(s["mean_off"]), s["over15"])
    best = min(("later_robust", "prev_later", "first", "span_mean"), key=score)
    print(f"lowest_over45_among_sane={best} {vs[best]}")
    # Apply corrective only if current rows are over the 45s gate versus the chosen sane later mean
    vs_first = vs["first"]
    vs_later = vs["later_robust"]
    later_mean = later_mean_robust  # stored as later_mean_w46 for confirm.py

    applied = False
    nfix = 0
    reason = (
        f"first-interval tick_s={TICK_S_FIRST:.5f} (printed 4.169) vs later-mean-robust {later_mean_robust:.5f} "
        f"(raw later-mean {later_mean_raw:.5f} includes 84293300..84293400 official-ts gap "
        f"{[x[2] for x in iv if x[0]==84293300][0]:.5f}s/tick, treated as publish-delay outlier; "
        f"delta first-robust {first-later_mean_robust:.5f} s/tick, "
        f"~{(GT_FIRST-TMIN)*abs(first-later_mean_robust):.1f}s at tmin)"
    )
    # Use a fresh anchor at apply time
    if vs_later["over45"] > 0:
        now2 = datetime.now(timezone.utc)
        gt2, _ = game_time()
        with db.connect(autocommit=False) as c:
            nfix = hb.realign_ts(c, TMIN, TMAX, ROOMS, now2, gt2, later_mean)
            c.commit()
        applied = True
        after = counts(later_mean, now_ts=now2, gt=gt2)
        print(f"corrective realign applied nfix={nfix} at game.time={gt2} tick_s={later_mean:.5f}")
        print("after vs_later_mean_robust", after)
        vs_later_after = after
        gt_realign = gt2
        now_realign = datetime.now(ZoneInfo("Asia/Hong_Kong")).isoformat()
        reason += (
            f"; applied corrective later-mean-robust realign of {nfix} rows at game.time={gt2}; "
            f"still_over_45s_vs_later={after['over45']}"
        )
    else:
        vs_later_after = vs_later
        gt_realign = gt
        now_realign = datetime.now(ZoneInfo("Asia/Hong_Kong")).isoformat()
        reason += "; later-mean-robust already inside 45s gate, no corrective realign"
        print("corrective_applied=False")

    payload = {
        "first_interval": first,
        "later_mean_w46": later_mean,  # confirm.py reads this; use the sane robust mean
        "later_mean_w46_raw": later_mean_raw,
        "later_mean_w46_robust": later_mean_robust,
        "all_mean_w46": all_mean,
        "span_mean": span_mean,
        "prev_later_mean": PREV_LATER_MEAN,
        "intervals": [{"from": a, "to": b, "tick_s": s, "outlier": not (3.0 <= s <= 6.0)} for a, b, s in iv],
        "gt_first": GT_FIRST,
        "gt_check": gt,
        "gt_realign": gt_realign,
        "now_check": datetime.now(ZoneInfo("Asia/Hong_Kong")).isoformat(),
        "now_realign": now_realign,
        "tick_s_used_first_pass": TICK_S_FIRST,
        "ts_realigned_first_pass": TS_REALIGNED_FIRST,
        "still_over_45s_vs_first": vs_first["over45"],
        "still_over_15s_vs_first": vs_first["over15"],
        "vs_candidates": {k: {**vs[k], "tick_s": candidates[k]} for k in candidates},
        "still_over_45s_vs_later_before": vs_later["over45"],
        "still_over_15s_vs_later_before": vs_later["over15"],
        "still_over_45s_vs_later": vs_later_after["over45"],
        "still_over_15s_vs_later": vs_later_after["over15"],
        "corrective_applied": applied,
        "ts_realigned_to_later_mean": nfix,
        "reason": reason,
        "game_time_error": gerr,
        "lowest_over45_sane": best,
    }
    (DIR / "tick_s_realign.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print("wrote", DIR / "tick_s_realign.json")
    print(f"corrective_applied={applied} nfix={nfix}")
    print("reason:", reason)

if __name__ == "__main__":
    main()
