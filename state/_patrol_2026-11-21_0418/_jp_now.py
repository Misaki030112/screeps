#!/usr/bin/env python3
import json, sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import db, api, history_backfill as hb

HK = ZoneInfo("Asia/Hong_Kong")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
jp_base = 84385800
TICK_S = 4.120
OUT = "/workspace/screeps/state/_patrol_2026-11-21_0418/just_published_84385800.json"

def main():
    gt = api.req(f"game/time?shard={hb.SHARD}")["time"]
    print("game.time", gt, datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), flush=True)
    results = []
    if gt < jp_base + 100:
        print("still unpublished", gt, flush=True)
        open(OUT, "w").write(json.dumps({"gt": gt, "skipped": True}, indent=2) + "\n")
        return
    now_ts = datetime.now(timezone.utc)
    with db.connect() as c:
        cm = db.current_commit(c)
    for room in ROOMS:
        j = hb.history_get(room, jp_base)
        time.sleep(hb.GAP_S)
        rec = {"room": room, "base": jp_base, "status": 404 if not j else 200, "gt": gt}
        if not j:
            print("  404", room, jp_base, flush=True)
            rec["inserted"] = 0
            results.append(rec)
            continue
        state = {}
        prev = hb.history_get(room, jp_base - 100)
        time.sleep(hb.GAP_S)
        if prev:
            for _t, _o in hb.merge_chunk(prev, state):
                pass
        rows = []
        tmin = tmax = None
        for tick, objs in hb.merge_chunk(j, state):
            ts = hb.tick_time(now_ts, gt, tick, TICK_S)
            rows.extend(hb.creep_rows(tick, room, objs, hb.uid(), ts, cm))
            tmin = tick if tmin is None else min(tmin, tick)
            tmax = tick if tmax is None else max(tmax, tick)
        with db.connect() as c:
            exist = hb.already(c, tmin, tmax, [room]) if tmin else set()
        new_rows = [r for r in rows if (r[3], r[1]) not in exist]
        if new_rows:
            sql = ("INSERT INTO creep_ticks (ts,tick,room,creep,role,x,y,hits,store,state,commit) "
                   "SELECT %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s "
                   "WHERE NOT EXISTS (SELECT 1 FROM creep_ticks c WHERE c.creep=%s AND c.tick=%s)")
            packed = [r + (r[3], r[1]) for r in new_rows]
            with db.connect(autocommit=False) as cx:
                with cx.cursor() as cur:
                    cur.executemany(sql, packed)
                cx.commit()
        rec.update({"nticks": len(j.get("ticks") or {}), "tmin": tmin, "tmax": tmax, "inserted": len(new_rows), "nrows": len(rows)})
        print(f"  {room}@{jp_base} 200 ticks={rec['nticks']} range={tmin}..{tmax} inserted={len(new_rows)}", flush=True)
        results.append(rec)
    with db.connect() as c:
        print("=== coverage 84385801..84385900 after jp ===", flush=True)
        cov = {}
        for room in ROOMS:
            n, mn, mx = c.execute(
                "SELECT count(DISTINCT tick),min(tick),max(tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN 84385801 AND 84385900",
                (room,),
            ).fetchone()
            cov[room] = {"n": n, "min": mn, "max": mx}
            print(room, n, mn, mx, flush=True)
        print("=== W47N8 404 hole 84385301..84385400 ===", flush=True)
        fill = {}
        for room in ROOMS:
            n = c.execute(
                "SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick BETWEEN 84385301 AND 84385400",
                (room,),
            ).fetchone()[0]
            fill[room] = f"{n}/19"
            print(room, f"{n}/19", flush=True)
    open(OUT, "w").write(json.dumps({"gt": gt, "results": results, "cov": cov, "short_fill": fill}, indent=2, default=str) + "\n")
    print("wrote", OUT, flush=True)

if __name__ == "__main__":
    main()
