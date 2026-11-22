#!/usr/bin/env python3
"""Compare first-interval tick_s with later W46N8 mean; realign if over the 45s gate."""
from __future__ import annotations
import json, sys, os, time
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-22_1830"
os.chdir(ROOT)
sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")
import db, api
import history_backfill as hb

# Official chunk timestamps printed by history_backfill.py
# First pass 29 of 35 official GETs 200, missing_chunks=6; insert committed
# inserted=400 already_in_db=24522; first-pass realign succeeded ts_realigned_first=5314.
# published_bases 84418600..84419200 at game.time=84419342; reconstructed
# 84418601..84419300 (700). First-pass tick_s used min-of-all-rooms on the
# first two published bases, computed (MIN 84418700-84418600)/1000/100 = 4.16594,
# script printed 4.166. 84418900 missing for all five rooms (not in W46/MIN_ALL);
# W45N7@84419000 first-pass 404 (MIN_ALL 84419000 uses the other four rooms).
# Already-told leftover W45N8@84415500 and older aged out of window start 84418601
# and were not retried. 18:00 half-hour already official-filled through 84418800 /
# just-published 84418900 still 404. NEW not-yet-told box freeze 17:41:00-18:04:50
# (1424s); STATS 84418531..84418879 overlaps this window at 84418601..84418879.
# Listener auto-restart 18:04:53, python 2582266 started 18:05:03 (parent 4035476).
# Do not restart. Already-told freezes 17:12 and 16:44 were told in the 17:35
# _patrol_2026-11-22_1722 USER_LOG. Do not write a patrol/12h-review folder.
W46 = {
    84418600: 1795341188236,
    84418700: 1795341605532,
    84418800: 1795342038373,
    84419000: 1795342882801,
    84419100: 1795343302081,
    84419200: 1795343713406,
}
MIN_ALL = {
    84418600: 1795341188236,  # W46N8
    84418700: 1795341604830,  # W45N7
    84418800: 1795342038373,  # W46N8
    84419000: 1795342882801,  # W46N8 (W45N7 404)
    84419100: 1795343302081,  # W46N8
    84419200: 1795343713406,  # W46N8
}
TMIN, TMAX = 84418601, 84419300
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84418700] - MIN_ALL[84418600]) / 1000.0 / 100  # script printed 4.166, exact 4.16594
GT_FIRST = 84419342
TS_REALIGNED_FIRST = 5314  # first-pass realign succeeded (inserted=400 already_in_db=24522)
PREV_LATER_MEAN = 4.23099  # tick_s_in_use from quiet 18:00 halfhour (all_mean)

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

def realign_chunk_safe(c, tmin, tmax, rooms, now_ts, gt, tick_s):
    """Same 45s-gate realign, but only move a row when the new ts stays in its Timescale chunk."""
    cur = c.execute(
        """UPDATE creep_ticks ct
              SET ts = %(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s
            WHERE tick BETWEEN %(t0)s AND %(t1)s AND room = ANY(%(rooms)s)
              AND abs(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) > 45
              AND EXISTS (
                    SELECT 1
                      FROM timescaledb_information.chunks ch
                     WHERE ch.hypertable_name = 'creep_ticks'
                       AND ct.ts >= ch.range_start
                       AND ct.ts < ch.range_end
                       AND (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s) >= ch.range_start
                       AND (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s) < ch.range_end
              )""",
        {"now": now_ts, "gt": gt, "tick_s": tick_s, "t0": tmin, "t1": tmax, "rooms": list(rooms)},
    )
    nfix = cur.rowcount
    skipped = c.execute(
        """SELECT count(*)
             FROM creep_ticks ct
            WHERE tick BETWEEN %(t0)s AND %(t1)s AND room = ANY(%(rooms)s)
              AND abs(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) > 45
              AND NOT EXISTS (
                    SELECT 1
                      FROM timescaledb_information.chunks ch
                     WHERE ch.hypertable_name = 'creep_ticks'
                       AND ct.ts >= ch.range_start
                       AND ct.ts < ch.range_end
                       AND (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s) >= ch.range_start
                       AND (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s) < ch.range_end
              )""",
        {"now": now_ts, "gt": gt, "tick_s": tick_s, "t0": tmin, "t1": tmax, "rooms": list(rooms)},
    ).fetchone()[0]
    return nfix, skipped

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
    print(f"all_mean={all_mean:.5f} span_mean={span_mean:.5f} script_tick_s={TICK_S_FIRST:.5f} prev_later={PREV_LATER_MEAN}")
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

    def score(name):
        s = vs[name]
        return (s["over45"], abs(s["mean_off"]), s["over15"])
    sane = [n for n, v in candidates.items() if 3.0 <= v <= 6.0]
    best = min(sane, key=score) if sane else "later_robust"
    print(f"lowest_over45_among_sane={best} {vs[best]}")
    vs_first = vs["first"]
    vs_later = vs["later_robust"]
    later_mean = later_mean_robust

    applied = False
    nfix = 0
    skipped_chunk = 0
    first_outlier = not (3.0 <= TICK_S_FIRST <= 6.0)
    first_pass_realign_error = (
        f"First-pass realign with tick_s={TICK_S_FIRST:.5f} (printed 4.166) succeeded, "
        f"ts_realigned_first=5314 (inserted=400 already_in_db=24522, missing_chunks=6)."
    )
    reason = (
        f"first-interval tick_s={TICK_S_FIRST:.5f} (printed 4.166, min-all-rooms first two bases) "
        f"{'is an OUTLIER' if first_outlier else 'is in the sane 3-6s band'}; "
        f"later-mean-robust {later_mean_robust:.5f} (raw later-mean {later_mean_raw:.5f}; "
        f"delta first-robust {first-later_mean_robust:.5f} s/tick, "
        f"~{(GT_FIRST-TMIN)*abs(first-later_mean_robust):.1f}s at tmin). "
        f"{first_pass_realign_error}"
    )
    # Prefer the live-anchor-best tick_s (lowest over45, then abs mean_off).
    # Do not blindly apply later-mean-robust if it is worse than first/prev_later.
    # If a worse later-mean does get applied, immediately revert onto the better estimate.
    target_name = best
    target = candidates[best]
    need_corrective = vs[best]["over45"] > 0 or (first_outlier and best != "first")
    later_is_worse_than_best = best != "later_robust" and (
        vs_later["over45"] > vs[best]["over45"]
        or (vs_later["over45"] == vs[best]["over45"] and abs(vs_later["mean_off"]) > abs(vs[best]["mean_off"]))
    )
    tick_s_in_use = target
    vs_later_after = vs_later
    if later_is_worse_than_best:
        reason += (
            f"; later-mean-robust {later_mean_robust:.5f} is worse than live-anchor-best {best} {target:.5f} "
            f"(later over45={vs_later['over45']} mean_off={vs_later['mean_off']:.1f} vs best over45={vs[best]['over45']} "
            f"mean_off={vs[best]['mean_off']:.1f}); will not blindly apply later"
        )
        print(f"refusing later-mean-robust; live-anchor-best={best} {target:.5f}")
    if need_corrective:
        now2 = datetime.now(timezone.utc)
        gt2, _ = game_time()
        try:
            with db.connect(autocommit=False) as c:
                nfix = hb.realign_ts(c, TMIN, TMAX, ROOMS, now2, gt2, target)
                c.commit()
            applied = True
            print(f"corrective realign applied nfix={nfix} at game.time={gt2} tick_s={target:.5f} ({target_name})")
        except Exception as e:
            print(f"corrective realign FAILED: {e!r}; trying chunk-safe update")
            try:
                with db.connect(autocommit=False) as c:
                    nfix, skipped_chunk = realign_chunk_safe(c, TMIN, TMAX, ROOMS, now2, gt2, target)
                    c.commit()
                applied = nfix > 0
                print(f"chunk-safe realign nfix={nfix} skipped_cross_chunk={skipped_chunk} at game.time={gt2} tick_s={target:.5f} ({target_name})")
                reason += f"; full {target_name} realign failed ({e!r}), fell back to chunk-safe nfix={nfix} skipped_cross_chunk={skipped_chunk}"
            except Exception as e2:
                nfix = 0
                applied = False
                print(f"chunk-safe realign also FAILED: {e2!r}; leaving ts as inserted")
                reason += f"; full {target_name} realign failed ({e!r}); chunk-safe also failed ({e2!r}); left ts as inserted"
        after = counts(target, now_ts=now2, gt=gt2)
        after_first = counts(TICK_S_FIRST, now_ts=now2, gt=gt2)
        after_later = counts(later_mean, now_ts=now2, gt=gt2)
        print(f"after vs_{target_name}", after)
        print("after vs_first", after_first)
        print("after vs_later_mean_robust", after_later)
        # Safety: if we somehow aligned to a worse later-mean, revert onto best.
        if applied and target_name == "later_robust" and later_is_worse_than_best:
            revert_to = candidates[best] if best != "later_robust" else TICK_S_FIRST
            revert_name = best if best != "later_robust" else "first"
            try:
                with db.connect(autocommit=False) as c:
                    nrev, sk2 = realign_chunk_safe(c, TMIN, TMAX, ROOMS, now2, gt2, revert_to)
                    c.commit()
                applied = False
                nfix = 0
                tick_s_in_use = revert_to
                print(f"REVERTED later-robust realign (nrev={nrev} skipped={sk2}); later_robust worse than {revert_name} versus live anchor")
                reason += (
                    f"; later-mean-robust realign of rows was immediately reverted onto {revert_name} {revert_to:.5f} "
                    f"(nrev={nrev})"
                )
                vs_later_after = counts(later_mean, now_ts=now2, gt=gt2)
            except Exception as e:
                print(f"revert failed: {e!r}; leaving post-corrective ts")
                vs_later_after = after_later
                tick_s_in_use = target
                reason += f"; revert failed ({e!r})"
        else:
            vs_later_after = after_later
            tick_s_in_use = target
            if applied:
                reason += (
                    f"; applied corrective {target_name} realign of {nfix} rows at game.time={gt2} tick_s={target:.5f}; "
                    f"still_over_45s_vs_target={after['over45']}; skipped_cross_chunk={skipped_chunk}"
                )
        gt_realign = gt2
        now_realign = datetime.now(ZoneInfo("Asia/Hong_Kong")).isoformat()
    else:
        vs_later_after = vs_later
        tick_s_in_use = target
        gt_realign = gt
        now_realign = datetime.now(ZoneInfo("Asia/Hong_Kong")).isoformat()
        reason += (
            f"; live-anchor-best {best} {target:.5f} already inside 45s gate "
            f"(over45={vs[best]['over45']}), no corrective realign"
        )
        print("corrective_applied=False")
    print(f"tick_s_in_use={tick_s_in_use:.5f} ({target_name})")

    payload = {
        "first_interval": first,
        "later_mean_w46": later_mean,
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
        "ts_realigned_first_pass_error": first_pass_realign_error,
        "still_over_45s_vs_first": vs_first["over45"],
        "still_over_15s_vs_first": vs_first["over15"],
        "vs_candidates": {k: {**vs[k], "tick_s": candidates[k]} for k in candidates},
        "still_over_45s_vs_later_before": vs_later["over45"],
        "still_over_15s_vs_later_before": vs_later["over15"],
        "still_over_45s_vs_later": vs_later_after["over45"],
        "still_over_15s_vs_later": vs_later_after["over15"],
        "corrective_applied": applied,
        "ts_realigned_to_later_mean": nfix,
        "skipped_cross_chunk": skipped_chunk,
        "reason": reason,
        "game_time_error": gerr,
        "lowest_over45_sane": best,
        "vs_first": vs_first,
        "vs_later_after": vs_later_after,
        "tick_s_in_use": tick_s_in_use,
        "tick_s_in_use_name": target_name,
        "later_is_worse_than_best": later_is_worse_than_best,
    }
    (DIR / "tick_s_realign.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print("wrote", DIR / "tick_s_realign.json")
    print(f"corrective_applied={applied} nfix={nfix} skipped_cross_chunk={skipped_chunk}")
    print("reason:", reason)

if __name__ == "__main__":
    main()
