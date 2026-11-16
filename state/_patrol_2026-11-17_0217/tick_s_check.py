#!/usr/bin/env python3
"""Compare first-interval tick_s with later W46N8 mean; realign if over the 45s gate.

Careful about the known failure mode: later-mean can look over the 45s gate only
because rows are already aligned to first (or to a previous later-mean). Do not
blindly apply or undo a later-mean; pick the sane candidate with lowest over45
versus the live anchor, and revert if a corrective realign makes over45 worse.
"""
from __future__ import annotations
import json, sys, os, time
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_patrol_2026-11-17_0217"
os.chdir(ROOT)
sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")
import db, api
import history_backfill as hb

# Official chunk timestamps printed by history_backfill.py
W46 = {
    84307800: 1794850318517,
    84307900: 1794850799235,
    84308000: 1794851288863,
    84308100: 1794851772506,
    84308200: 1794852261448,
    84308300: 1794852772230,
    84308400: 1794853253516,
}
MIN_ALL = {
    84307800: 1794850318517,  # W46N8
    84307900: 1794850799235,  # W46N8
    84308000: 1794851288863,  # W46N8
    84308100: 1794851772506,  # W46N8
    84308200: 1794852261448,  # W46N8
    84308300: 1794852772230,  # W46N8
    84308400: 1794853253516,  # W46N8
}
TMIN, TMAX = 84307801, 84308500
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84307900] - MIN_ALL[84307800]) / 1000.0 / 100  # 4.80718; printed 4.807
GT_FIRST = 84308524
TS_REALIGNED_FIRST = 12221
PREV_LATER_MEAN = 4.83529  # 02:00 half-hour later-mean-robust (already inside 45s gate)
PREV_IN_USE = 4.87786      # 02:00 in-use
PREV_1H_PATROL = 4.84115   # last 1h patrol in-use

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
    print(f"all_mean={all_mean:.5f} span_mean={span_mean:.5f} script_tick_s={TICK_S_FIRST:.5f} prev_later={PREV_LATER_MEAN}")
    print(f"delta_first_minus_later_raw={first-later_mean_raw:.5f} s/tick; at tmin vs gt_first ~{(GT_FIRST-TMIN)*abs(first-later_mean_raw):.1f}s")
    print(f"delta_first_minus_later_robust={first-later_mean_robust:.5f} s/tick; at tmin vs gt_first ~{(GT_FIRST-TMIN)*abs(first-later_mean_robust):.1f}s")

    now_ts = datetime.now(timezone.utc)
    hk = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    gt, gerr = game_time()
    print(f"anchor {hk} game.time={gt}")

    def counts(tick_s, now_ts=now_ts, gt=gt, t0=TMIN, t1=TMAX):
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
                {"now": now_ts, "gt": gt, "tick_s": tick_s, "t0": t0, "t1": t1, "rooms": list(ROOMS)},
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
        "prev_in_use": PREV_IN_USE,
        "prev_1h_patrol": PREV_1H_PATROL,
    }
    vs = {k: counts(v) for k, v in candidates.items()}
    for k, v in candidates.items():
        print(f"vs_{k} tick_s={v:.5f}", vs[k])

    # Also report overlap with 02:00 half-hour (84307501..84308200) vs new tail
    for label, t0, t1 in (("overlap_to_84308200", TMIN, 84308200), ("new_tail_84308201", 84308201, TMAX)):
        print(f"subwindow_{label}:")
        for k in ("first", "later_robust", "prev_in_use"):
            print(f"  {k} tick_s={candidates[k]:.5f}", counts(candidates[k], t0=t0, t1=t1))

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
    reverted = False
    first_outlier = not (3.0 <= TICK_S_FIRST <= 6.0)
    reason = (
        f"first-interval tick_s={TICK_S_FIRST:.5f} (printed 4.807) "
        f"{'is an OUTLIER' if first_outlier else 'is in the sane 3-6s band'}; "
        f"later-mean-robust {later_mean_robust:.5f} (raw later-mean {later_mean_raw:.5f}; "
        f"delta first-robust {first-later_mean_robust:.5f} s/tick, "
        f"~{(GT_FIRST-TMIN)*abs(first-later_mean_robust):.1f}s at tmin); "
        f"02:00 in-use first-interval {PREV_IN_USE:.5f} (later-mean-robust already inside 45s gate, not applied); "
        f"last 1h patrol in-use was {PREV_1H_PATROL:.5f}"
    )
    best_sane_tick_s = candidates[best]
    # Known failure mode: later-mean looks over the gate only because rows already sit on first
    # (or another previous tick_s). Only realign if the BEST sane candidate is clearly better
    # than the current best-of-current-alignment, AND the current alignment is actually over
    # the 45s gate (over45>0 with meaningful mean_off, not a handful of boundary rows).
    first_inside = vs_first["over45"] == 0 or (vs_first["over45"] < 50 and abs(vs_first["mean_off"]) < 10)
    later_inside = vs_later["over45"] == 0 or (vs_later["over45"] < 50 and abs(vs_later["mean_off"]) < 10)
    best_inside = vs[best]["over45"] == 0 or (vs[best]["over45"] < 50 and abs(vs[best]["mean_off"]) < 10)
    # If first (this backfill's tick_s) is already inside the 45s gate, do not "correct"
    # onto later-mean just because later looks bad (rows were already on first / 00:09 mix).
    # Realign only when the current rows fail the gate versus the best candidate, or first is an outlier.
    need_realign = False
    target = best_sane_tick_s
    if first_outlier and not later_inside and best != "first":
        need_realign = True
        target = best_sane_tick_s
        reason += "; first is an outlier, will realign to best sane"
    elif not best_inside:
        # even the best candidate is over the gate — still try best
        need_realign = True
        target = best_sane_tick_s
        reason += "; no candidate is inside the 45s gate; will try best sane"
    elif vs[best]["over45"] < vs_first["over45"] and vs_first["over45"] > 50:
        # first fails the gate and another sane candidate is clearly better
        need_realign = True
        target = best_sane_tick_s
        reason += f"; first is over the 45s gate (over45={vs_first['over45']}) and {best} is clearly better"
    else:
        reason += (
            f"; best sane is {best} tick_s={best_sane_tick_s:.5f} over45={vs[best]['over45']} "
            f"mean_off={vs[best]['mean_off']:.3f}; first over45={vs_first['over45']} "
            f"mean_off={vs_first['mean_off']:.3f}; later_robust over45={vs_later['over45']} "
            f"mean_off={vs_later['mean_off']:.3f}. No corrective realign "
            f"(best already inside 45s gate or first is already the best / inside)."
        )
        print("corrective_applied=False")

    vs_later_after = vs_later
    after = None
    after_first = None
    gt_realign = gt
    now_realign = datetime.now(ZoneInfo("Asia/Hong_Kong")).isoformat()
    if need_realign:
        now2 = datetime.now(timezone.utc)
        gt2, _ = game_time()
        with db.connect(autocommit=False) as c:
            print(f"realign target tick_s={target:.5f} (best={best}, later_robust={later_mean:.5f})")
            nfix = hb.realign_ts(c, TMIN, TMAX, ROOMS, now2, gt2, target)
            c.commit()
        applied = True
        after = counts(target, now_ts=now2, gt=gt2)
        after_first = counts(TICK_S_FIRST, now_ts=now2, gt=gt2)
        after_best_pre = vs[best]
        print(f"corrective realign applied nfix={nfix} at game.time={gt2} tick_s={target:.5f}")
        print("after vs_target", after)
        print("after vs_first", after_first)
        # Revert if the realign made the live-anchor error worse than the pre-realign best
        if after["over45"] > vs[best]["over45"] and after["over45"] > 0:
            # If we realigned TO best, after should be vs best; if worse, something is off — revert to first if first was better before
            revert_to = TICK_S_FIRST if vs_first["over45"] <= after["over45"] else best_sane_tick_s
            # Actually: revert to the pre-realign alignment isn't stored as a single tick_s
            # (window may have been mixed). Prefer first if it was inside, else the previous best-inside.
            if first_inside:
                revert_to = TICK_S_FIRST
            elif later_inside:
                revert_to = later_mean
            else:
                revert_to = TICK_S_FIRST
            with db.connect(autocommit=False) as c:
                nrev = hb.realign_ts(c, TMIN, TMAX, ROOMS, now2, gt2, revert_to)
                c.commit()
            applied = False
            reverted = True
            nfix = 0
            print(f"REVERTED realign (nrev={nrev}) to {revert_to:.5f}; target worse than pre-realign best versus live anchor")
            reason += (
                f"; corrective realign onto {target:.5f} was immediately reverted to {revert_to:.5f} "
                f"(after over45={after['over45']} worse than pre best over45={vs[best]['over45']})"
            )
            vs_later_after = counts(later_mean, now_ts=now2, gt=gt2)
        else:
            vs_later_after = counts(later_mean, now_ts=now2, gt=gt2)
            reason += (
                f"; applied corrective realign of {nfix} rows at game.time={gt2} to tick_s={target:.5f} ({best}); "
                f"still_over_45s_vs_target={after['over45']}"
            )
        gt_realign = gt2
        now_realign = datetime.now(ZoneInfo("Asia/Hong_Kong")).isoformat()

    in_use = target if applied else (best_sane_tick_s if best_inside else TICK_S_FIRST)
    if not applied:
        # Prefer the candidate that currently fits the live anchor
        in_use = candidates[best]
    print(f"in-use tick_s={in_use:.5f} (applied={applied} reverted={reverted} best={best})")

    payload = {
        "first_interval": first,
        "later_mean_w46": later_mean,
        "later_mean_w46_raw": later_mean_raw,
        "later_mean_w46_robust": later_mean_robust,
        "all_mean_w46": all_mean,
        "span_mean": span_mean,
        "prev_later_mean": PREV_LATER_MEAN,
        "prev_in_use_0200": PREV_IN_USE,
        "prev_1h_patrol": PREV_1H_PATROL,
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
        "reverted": reverted,
        "ts_realigned_to_target": nfix,
        "in_use_tick_s": in_use,
        "reason": reason,
        "game_time_error": gerr,
        "lowest_over45_sane": best,
        "vs_first": vs_first,
        "vs_later_after": vs_later_after,
        "after_target": after,
        "after_first": after_first,
    }
    (DIR / "tick_s_realign.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print("wrote", DIR / "tick_s_realign.json")
    print(f"corrective_applied={applied} nfix={nfix} reverted={reverted}")
    print("reason:", reason)

if __name__ == "__main__":
    main()
