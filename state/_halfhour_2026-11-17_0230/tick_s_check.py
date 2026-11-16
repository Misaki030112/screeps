#!/usr/bin/env python3
"""Compare first-interval tick_s with later W46N8 mean; realign if over the 45s gate."""
from __future__ import annotations
import json, sys, os, time
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-17_0230"
os.chdir(ROOT)
sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")
import db, api
import history_backfill as hb

# Official chunk timestamps printed by history_backfill.py
W46 = {
    84307900: 1794850799235,
    84308000: 1794851288863,
    84308100: 1794851772506,
    84308200: 1794852261448,
    84308300: 1794852772230,
    84308400: 1794853253516,
    84308500: 1794853741722,
}
# Min timestamp across rooms: W46N8 on every published base except 84308500 (W45N7 slightly earlier).
MIN_ALL = {
    84307900: 1794850799235,  # W46N8
    84308000: 1794851288863,  # W46N8
    84308100: 1794851772506,  # W46N8
    84308200: 1794852261448,  # W46N8
    84308300: 1794852772230,  # W46N8
    84308400: 1794853253516,  # W46N8
    84308500: 1794853740919,  # W45N7 slightly earlier than W46N8 1794853741722
}
TMIN, TMAX = 84307901, 84308600
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = (MIN_ALL[84308000] - MIN_ALL[84307900]) / 1000.0 / 100  # 4.89628; printed 4.896
GT_FIRST = 84308640
TS_REALIGNED_FIRST = 7180
PREV_LATER_MEAN = 4.83529  # 02:00 half-hour later-mean-robust (already inside 45s gate)

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
    first_outlier = not (3.0 <= TICK_S_FIRST <= 6.0)
    reason = (
        f"first-interval tick_s={TICK_S_FIRST:.5f} (printed 4.896) "
        f"{'is an OUTLIER' if first_outlier else 'is in the sane 3-6s band'}; "
        f"later-mean-robust {later_mean_robust:.5f} (raw later-mean {later_mean_raw:.5f}; "
        f"delta first-robust {first-later_mean_robust:.5f} s/tick, "
        f"~{(GT_FIRST-TMIN)*abs(first-later_mean_robust):.1f}s at tmin)"
    )
    # Apply corrective only if first is an outlier or current rows are over the 45s gate vs later mean.
    if vs_later["over45"] > 0 or first_outlier:
        now2 = datetime.now(timezone.utc)
        gt2, _ = game_time()
        with db.connect(autocommit=False) as c:
            nfix = hb.realign_ts(c, TMIN, TMAX, ROOMS, now2, gt2, later_mean)
            c.commit()
        applied = True
        after = counts(later_mean, now_ts=now2, gt=gt2)
        after_first = counts(TICK_S_FIRST, now_ts=now2, gt=gt2)
        print(f"corrective realign applied nfix={nfix} at game.time={gt2} tick_s={later_mean:.5f}")
        print("after vs_later_mean_robust", after)
        print("after vs_first", after_first)
        if after["over45"] > vs_first["over45"] and after["over45"] > 0:
            with db.connect(autocommit=False) as c:
                nrev = hb.realign_ts(c, TMIN, TMAX, ROOMS, now2, gt2, TICK_S_FIRST)
                c.commit()
            applied = False
            nfix = 0
            print(f"REVERTED later-robust realign (nrev={nrev}); later_robust worse than first versus live anchor")
            reason += (
                f"; later-mean-robust realign of rows was immediately reverted "
                f"(after over45={after['over45']} worse than first over45={vs_first['over45']})"
            )
            vs_later_after = counts(later_mean, now_ts=now2, gt=gt2)
        else:
            vs_later_after = after
            reason += (
                f"; applied corrective later-mean-robust realign of {nfix} rows at game.time={gt2}; "
                f"still_over_45s_vs_later={after['over45']}"
            )
        gt_realign = gt2
        now_realign = datetime.now(ZoneInfo("Asia/Hong_Kong")).isoformat()
    else:
        vs_later_after = vs_later
        gt_realign = gt
        now_realign = datetime.now(ZoneInfo("Asia/Hong_Kong")).isoformat()
        reason += "; later-mean-robust already inside 45s gate, no corrective realign"
        print("corrective_applied=False")

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
        "vs_first": vs_first,
        "vs_later_after": vs_later_after,
    }
    (DIR / "tick_s_realign.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print("wrote", DIR / "tick_s_realign.json")
    print(f"corrective_applied={applied} nfix={nfix}")
    print("reason:", reason)

if __name__ == "__main__":
    main()
