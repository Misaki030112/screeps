#!/usr/bin/env python3
"""Compare first-interval tick_s with later W46N8 mean; realign if over the 45s gate."""
from __future__ import annotations
import json, sys, os, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-15_2130"
os.chdir(ROOT)
sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")
import db, api
import history_backfill as hb

# Official chunk timestamps printed by history_backfill.py (W46N8 min-ts per base)
W46 = {
    84284900: 1794746694719,
    84285000: 1794747120321,
    84285100: 1794747537261,
    84285200: 1794747962203,
    84285300: 1794748392565,
    84285400: 1794748822846,
    84285500: 1794749243135,
}
TMIN, TMAX = 84284901, 84285600
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = 4.256
GT_FIRST = 84285677
TS_REALIGNED_FIRST = 1496

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
    later_mean = sum(later) / len(later)
    all_mean = sum(x[2] for x in iv) / len(iv)
    print("intervals_w46:")
    for a, b, s in iv:
        print(f"  {a}..{b} {s:.5f}")
    print(f"first={first:.5f} later_mean={later_mean:.5f} all_mean={all_mean:.5f} script_tick_s={TICK_S_FIRST}")
    print(f"delta_first_minus_later={first-later_mean:.5f} s/tick; at tmin ~{(GT_FIRST-TMIN)*(first-later_mean):.1f}s")

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
                  count(*) AS n
                FROM creep_ticks
                WHERE tick BETWEEN %(t0)s AND %(t1)s AND room = ANY(%(rooms)s)
                """,
                {"now": now_ts, "gt": gt, "tick_s": tick_s, "t0": TMIN, "t1": TMAX, "rooms": list(ROOMS)},
            ).fetchone()
        return {"over45": row[0], "over15": row[1], "n": row[2]}

    vs_first = counts(TICK_S_FIRST)
    vs_later = counts(later_mean)
    print("vs_first_tick_s", vs_first)
    print("vs_later_mean", vs_later)

    applied = False
    nfix = 0
    reason = (
        f"first-interval tick_s={TICK_S_FIRST:.3f} vs later-mean {later_mean:.5f} "
        f"(delta {first-later_mean:.5f} s/tick, ~{(GT_FIRST-TMIN)*abs(first-later_mean):.1f}s at tmin)"
    )
    if vs_later["over45"] > 0:
        now2 = datetime.now(timezone.utc)
        gt2, _ = game_time()
        with db.connect(autocommit=False) as c:
            nfix = hb.realign_ts(c, TMIN, TMAX, ROOMS, now2, gt2, later_mean)
            c.commit()
        applied = True
        after = counts(later_mean, now_ts=now2, gt=gt2)
        print(f"corrective realign applied nfix={nfix} at game.time={gt2}")
        print("after vs_later_mean", after)
        vs_later_after = after
        gt_realign = gt2
        now_realign = datetime.now(ZoneInfo("Asia/Hong_Kong")).isoformat()
        reason += (
            f"; applied corrective later-mean realign of {nfix} rows at game.time={gt2}; "
            f"still_over_45s_vs_later={after['over45']}"
        )
    else:
        vs_later_after = vs_later
        gt_realign = gt
        now_realign = datetime.now(ZoneInfo("Asia/Hong_Kong")).isoformat()
        reason += "; later-mean already inside 45s gate, no corrective realign"
        print("corrective_applied=False")

    payload = {
        "first_interval": first,
        "later_mean_w46": later_mean,
        "all_mean_w46": all_mean,
        "intervals": [{"from": a, "to": b, "tick_s": s} for a, b, s in iv],
        "gt_first": GT_FIRST,
        "gt_check": gt,
        "gt_realign": gt_realign,
        "now_check": datetime.now(ZoneInfo("Asia/Hong_Kong")).isoformat(),
        "now_realign": now_realign,
        "tick_s_used_first_pass": TICK_S_FIRST,
        "ts_realigned_first_pass": TS_REALIGNED_FIRST,
        "still_over_45s_vs_first": vs_first["over45"],
        "still_over_15s_vs_first": vs_first["over15"],
        "still_over_45s_vs_later_before": vs_later["over45"],
        "still_over_15s_vs_later_before": vs_later["over15"],
        "still_over_45s_vs_later": vs_later_after["over45"],
        "still_over_15s_vs_later": vs_later_after["over15"],
        "corrective_applied": applied,
        "ts_realigned_to_later_mean": nfix,
        "reason": reason,
    }
    (DIR / "tick_s_realign.json").write_text(json.dumps(payload, indent=2) + "\n")
    print("wrote", DIR / "tick_s_realign.json")
    print(f"corrective_applied={applied} nfix={nfix}")

if __name__ == "__main__":
    main()
