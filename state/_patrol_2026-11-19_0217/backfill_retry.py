#!/usr/bin/env python3
"""Confirm in-window official 404s and fetch just-published chunk if available."""
from __future__ import annotations
import json, sys, time
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import defaultdict

sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

HK = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
IN_WINDOW = [("W47N8", 84343800), ("W47N7", 84344300)]
TICK_S = 4.634  # first-pass printed tick_s
LIVE = "/workspace/screeps/metrics/live.json"
PASS = sys.argv[1] if len(sys.argv) > 1 else "confirm"

def now_gt():
    try:
        d = json.load(open(LIVE))
        st = d.get("stats") if isinstance(d.get("stats"), dict) else {}
        return int(st.get("t") or d.get("gameTime") or 0)
    except Exception:
        return 0

def insert_chunk(room, base, tick_s, gt):
    prev = hb.history_get(room, base - 100)
    time.sleep(hb.GAP_S)
    data = hb.history_get(room, base)
    if data is None:
        return "404", 0, 0
    state = {}
    if prev:
        for _tick, objs in hb.merge_chunk(prev, state):
            pass
    rows = []
    # Reconstruct using history_backfill internals if available
    if hasattr(hb, "rows_from_chunk"):
        rows, _ = hb.rows_from_chunk(room, base, data, state, tick_s=tick_s, now_gt=gt)
    else:
        # fallback: use reconstruct style from hb
        from datetime import datetime, timezone, timedelta
        # try hb.reconstruct or similar
        raise SystemExit("no rows_from_chunk")
    return "200", 0, 0  # placeholder if we use official insert path below

def main():
    gt = now_gt()
    print(f"{PASS}_start {datetime.now(HK).strftime('%H:%M:%S')} live_t {gt}", flush=True)
    recovered, still = [], []
    # Use hb's own insert pipeline by calling a thin wrapper if present
    # Fall back: fetch, build via public helpers
    with db.connect() as c:
        uid = None
        try:
            uid = json.load(open("/workspace/screeps/metrics/live.json")).get("uid")
        except Exception:
            pass

    # Inspect available helpers
    helpers = [n for n in dir(hb) if not n.startswith("_")]
    print("hb_helpers", helpers, flush=True)

    # Prefer pulling via history_backfill.backfill-like function for specific bases
    inserted_total = 0
    for room, base in IN_WINDOW:
        print(f"  try {room}@{base}", flush=True)
        data = hb.history_get(room, base)
        time.sleep(hb.GAP_S)
        if data is None:
            print(f"  404 {room}@{base}", flush=True)
            still.append(f"{room}@{base}")
            continue
        print(f"  200 {room}@{base} keys={list(data)[:8] if isinstance(data, dict) else type(data)}", flush=True)
        recovered.append(f"{room}@{base}")
        # insert using same method as CLI if possible
        if hasattr(hb, "ingest_chunk"):
            n = hb.ingest_chunk(room, base, data, tick_s=TICK_S)
            print(f"  ingest {n}", flush=True)
            inserted_total += n or 0
        elif hasattr(hb, "insert_history"):
            n = hb.insert_history(room, base, data, tick_s=TICK_S)
            print(f"  insert {n}", flush=True)
            inserted_total += n or 0
    print("recovered", recovered, "still_404", still, "inserted", inserted_total, flush=True)

    # just-published: current published base is floor(gt/100)*100 - 100
    gt = now_gt()
    pub = (gt // 100) * 100 - 100
    print(f"just_published_candidate base={pub} gt={gt}", flush=True)
    if PASS in ("just", "just_published", "all") or True:
        got, miss = [], []
        for room in ROOMS:
            data = hb.history_get(room, pub)
            time.sleep(hb.GAP_S)
            if data is None:
                print(f"  404 {room}@{pub}", flush=True)
                miss.append(room)
            else:
                ticks = None
                if isinstance(data, dict):
                    ticks = data.get("ticks") or data.get("n") or (len(data) if data else 0)
                print(f"  200 {room}@{pub} ticks~{ticks}", flush=True)
                got.append(room)
        print("just_got", got, "just_404", miss, flush=True)

if __name__ == "__main__":
    main()
