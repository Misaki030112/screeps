#!/usr/bin/env python3
"""Compare first-interval tick_s with later W46N8 mean; count rows over the 45s gate."""
from __future__ import annotations
import json, sys, os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-15_2000"
os.chdir(ROOT)
sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")
import db, api

# Official chunk timestamps printed by history_backfill.py (W46N8 min-ts per base)
W46 = {
    84283600: 1794741209069,
    84283700: 1794741635069,
    84283800: 1794742070696,
    84283900: 1794742491724,
    84284000: 1794742910677,
    84284100: 1794743338106,
    84284200: 1794743748292,
}
TMIN, TMAX = 84283601, 84284300
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TICK_S_FIRST = 4.260
GT_FIRST = 84284397

def intervals(d):
    bases = sorted(d)
    out = []
    for a, b in zip(bases, bases[1:]):
        sec = (d[b] - d[a]) / 1000.0 / (b - a)
        out.append((a, b, sec))
    return out

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

    # Fresh live anchor
    now_ts = datetime.now(timezone.utc)
    hk = datetime.now(ZoneInfo("Asia/Hong_Kong")).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    gt = None
    err = None
    for attempt in range(3):
        try:
            gt = api.req("game/time?shard=shard3")["time"]
            break
        except Exception as e:
            err = repr(e)
            print(f"game/time attempt {attempt+1} failed: {err}")
            import time; time.sleep(3 * (attempt + 1))
    if gt is None:
        live = json.load(open(ROOT / "metrics/live.json"))
        stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
        gt = live.get("gameTime") or stats.get("t")
        print(f"fell back to live.json gameTime/stats.t={gt}")
    print(f"anchor {hk} game.time={gt}")

    def counts(tick_s):
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

    payload = {
        "first_interval": first,
        "later_mean_w46": later_mean,
        "all_mean_w46": all_mean,
        "intervals": [{"from": a, "to": b, "tick_s": s} for a, b, s in iv],
        "gt_first": GT_FIRST,
        "gt_check": gt,
        "now_check": datetime.now(ZoneInfo("Asia/Hong_Kong")).isoformat(),
        "tick_s_used_first_pass": TICK_S_FIRST,
        "ts_realigned_first_pass": 4273,
        "still_over_45s_vs_first": vs_first["over45"],
        "still_over_15s_vs_first": vs_first["over15"],
        "still_over_45s_vs_later": vs_later["over45"],
        "still_over_15s_vs_later": vs_later["over15"],
        "corrective_applied": False,
        "ts_realigned_to_later_mean": 0,
        "reason": (
            "first-interval tick_s=4.260 is close to later-mean "
            f"{later_mean:.5f} (delta {first-later_mean:.5f} s/tick, ~{(GT_FIRST-TMIN)*abs(first-later_mean):.1f}s at tmin); "
            "no corrective realign"
        ),
    }
    (DIR / "tick_s_realign.json").write_text(json.dumps(payload, indent=2) + "\n")
    print("wrote", DIR / "tick_s_realign.json")
    print("corrective_applied=False")

if __name__ == "__main__":
    main()
