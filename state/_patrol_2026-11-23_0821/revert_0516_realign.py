#!/usr/bin/env python3
"""Revert mistaken 08:27 realign of the 0516 window (84425101..84428500)
from tick_s=4.35668 back to 4.23049, then restore tick_s_realign.json from git."""
from __future__ import annotations
import sys, os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("/workspace/screeps")
os.chdir(ROOT)
sys.path.insert(0, "tools")
sys.path.insert(0, "scripts")
import db, api
import history_backfill as hb

TMIN, TMAX = 84425101, 84428500
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
TARGET = 4.23049  # 0516 tick_s_in_use / first-interval

def realign_chunk_safe(c, tmin, tmax, rooms, now_ts, gt, tick_s):
    nfix = c.execute(
        """UPDATE creep_ticks
              SET ts = %(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s
            WHERE tick BETWEEN %(t0)s AND %(t1)s AND room = ANY(%(rooms)s)
              AND abs(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) > 45
              AND (
                    date_trunc('day', %(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)
                    = date_trunc('day', ts)
                  )
        """,
        {"now": now_ts, "gt": gt, "tick_s": tick_s, "t0": tmin, "t1": tmax, "rooms": list(rooms)},
    ).rowcount
    skipped = c.execute(
        """SELECT count(*) FROM creep_ticks
            WHERE tick BETWEEN %(t0)s AND %(t1)s AND room = ANY(%(rooms)s)
              AND abs(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) > 45
              AND (
                    date_trunc('day', %(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)
                    <> date_trunc('day', ts)
                  )
        """,
        {"now": now_ts, "gt": gt, "tick_s": tick_s, "t0": tmin, "t1": tmax, "rooms": list(rooms)},
    ).fetchone()[0]
    return nfix, skipped

def counts(c, tick_s, now_ts, gt):
    row = c.execute(
        """SELECT count(*) AS n,
                  count(*) FILTER (WHERE abs(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) > 45) AS over45,
                  count(*) FILTER (WHERE abs(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) > 15) AS over15,
                  avg(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) AS mean_off,
                  min(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) AS min_off,
                  max(extract(epoch from (ts - (%(now)s + (tick - %(gt)s) * interval '1 second' * %(tick_s)s)))) AS max_off
             FROM creep_ticks
            WHERE tick BETWEEN %(t0)s AND %(t1)s AND room = ANY(%(rooms)s)
        """,
        {"now": now_ts, "gt": gt, "tick_s": tick_s, "t0": TMIN, "t1": TMAX, "rooms": list(ROOMS)},
    ).fetchone()
    return {"n": row[0], "over45": row[1], "over15": row[2], "mean_off": float(row[3] or 0), "min_off": float(row[4] or 0), "max_off": float(row[5] or 0)}

def main():
    now_ts = datetime.now(timezone.utc)
    gt = api.req("game/time?shard=shard3")["time"]
    print(f"revert anchor now={now_ts.isoformat()} game.time={gt} target={TARGET}")
    with db.connect() as c:
        print("BEFORE vs 4.23049", counts(c, 4.23049, now_ts, gt))
        print("BEFORE vs 4.35668", counts(c, 4.35668, now_ts, gt))
        try:
            nfix = hb.realign_ts(c, TMIN, TMAX, ROOMS, now_ts, gt, TARGET)
            skipped = 0
            print(f"full realign nfix={nfix}")
        except Exception as e:
            print(f"full realign failed ({e!r}), chunk-safe fallback")
            nfix, skipped = realign_chunk_safe(c, TMIN, TMAX, ROOMS, now_ts, gt, TARGET)
            print(f"chunk-safe nfix={nfix} skipped_cross_chunk={skipped}")
        print("AFTER vs 4.23049", counts(c, 4.23049, now_ts, gt))
        print("AFTER vs 4.35668", counts(c, 4.35668, now_ts, gt))

if __name__ == "__main__":
    main()
