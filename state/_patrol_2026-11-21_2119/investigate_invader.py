#!/usr/bin/env python3
import json, sys
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import db
HK = ZoneInfo("Asia/Hong_Kong")
OUT = "/workspace/screeps/state/_patrol_2026-11-21_2119/investigate_invader.txt"

def tick_hk(ts):
    if ts is None: return None
    if getattr(ts, "tzinfo", None) is None: return str(ts)
    return ts.astimezone(HK).strftime("%Y-%m-%d %H:%M:%S")

lines=[]
def P(*a):
    s=" ".join(str(x) for x in a)
    print(s, flush=True)
    lines.append(s)

with db.connect() as c:
    P("=== episode ===")
    for r in c.execute("SELECT * FROM alert_state WHERE episode=%s", ("remote-W47N7-84400223",)):
        P("AL", dict(r) if hasattr(r,'keys') else r)
    ev=c.execute("""
      SELECT tick, ts, kind, room, severity, episode, msg, data
      FROM events
      WHERE tick>=84400200 AND (kind ILIKE '%alert%' OR episode='remote-W47N7-84400223' OR kind='box_pause')
      ORDER BY tick
    """).fetchall()
    for r in ev:
        P("EVT", r[0], tick_hk(r[1]), r[2], r[3], r[4], r[5], r[6], json.dumps(r[7], default=str)[:500] if r[7] is not None else "")

    P("=== rdef84400224 ===")
    dfd=c.execute("""
      SELECT tick, ts, room, x, y, hits, state, store
      FROM creep_ticks WHERE creep='rdef84400224' ORDER BY tick
    """).fetchall()
    P("rdef rows", len(dfd), "first", dfd[0][0] if dfd else None, "last", dfd[-1][0] if dfd else None)
    if dfd:
        for r in dfd[:6]:
            P(" first", r[0], tick_hk(r[1]), r[2], r[3], r[4], "hits", r[5], "st", r[6], "store", r[7])
        # hatch estimate: last tick still at spawn tile with no movement, or first move
        spawn_pos=None
        first_move=None
        first_w47n7=None
        rooms=[]
        prev=None
        hits_chg=[]
        for r in dfd:
            if spawn_pos is None:
                spawn_pos=(r[2], r[3], r[4])
            if first_move is None and (r[2], r[3], r[4]) != spawn_pos:
                first_move=r
            if first_w47n7 is None and r[2]=="W47N7":
                first_w47n7=r
            if prev is not None and r[2]!=prev[2]:
                rooms.append((r[0], tick_hk(r[1]), prev[2], "->", r[2], r[3], r[4], "st", r[6]))
            if prev is not None and r[5]!=prev[5]:
                hits_chg.append((r[0], tick_hk(r[1]), prev[5], r[5], r[2], r[3], r[4]))
            prev=r
        P("spawn_pos", spawn_pos)
        if first_move:
            P("first_move/hatch+", first_move[0], tick_hk(first_move[1]), first_move[2], first_move[3], first_move[4], "st", first_move[6])
        else:
            P("first_move none")
        if first_w47n7:
            P("first_W47N7", first_w47n7[0], tick_hk(first_w47n7[1]), first_w47n7[3], first_w47n7[4], "hits", first_w47n7[5], "st", first_w47n7[6])
        else:
            P("first_W47N7 none")
        for x in rooms:
            P(" ROOM", *x)
        P("hits_changes", len(hits_chg))
        for x in hits_chg:
            P(" HITSchange", *x)
        # path around 84400370-84400450
        around=[r for r in dfd if 84400360<=r[0]<=84400450]
        P("around hatch-end n", len(around))
        for r in around:
            P(" path", r[0], tick_hk(r[1]), r[2], r[3], r[4], "hits", r[5], "st", r[6])
        for r in dfd[-5:]:
            P(" last", r[0], tick_hk(r[1]), r[2], r[3], r[4], "hits", r[5], "st", r[6])
        # ticks present?
        ticks=[r[0] for r in dfd]
        miss=[]
        for a,b in zip(ticks, ticks[1:]):
            if b>a+1: miss.append((a+1,b-1,b-a-1))
        P("rdef missing_spans", miss[:15], "n", len(miss))

    P("=== W47N7 creeps 84400200..84400520 ===")
    rows=c.execute("""
      SELECT creep, role, min(tick), max(tick), min(hits), max(hits), count(distinct tick)
      FROM creep_ticks
      WHERE room='W47N7' AND tick BETWEEN 84400200 AND 84400520
      GROUP BY 1,2 ORDER BY 3
    """).fetchall()
    for r in rows: P(" ", r)

    P("=== W47N7 coverage 84400200..84401000 ===")
    ticks=[r[0] for r in c.execute("""
      SELECT DISTINCT tick FROM creep_ticks
      WHERE room='W47N7' AND tick BETWEEN 84400200 AND 84401000 ORDER BY 1
    """).fetchall()]
    want=set(range(84400200, 84401001))
    missing=sorted(want-set(ticks))
    def spans(xs):
        if not xs: return []
        out=[]; a=b=xs[0]
        for t in xs[1:]:
            if t==b+1: b=t
            else: out.append((a,b,b-a+1)); a=b=t
        out.append((a,b,b-a+1)); return out
    P("distinct", len(ticks), "missing", len(missing), "spans", spans(missing))

    P("=== first creeps back in W47N7 after evac (tick>=84400300) ===")
    firsts=c.execute("""
      SELECT tick, ts, creep, role, x, y, hits, state
      FROM creep_ticks WHERE room='W47N7' AND tick>=84400300
      ORDER BY tick, creep LIMIT 40
    """).fetchall()
    for r in firsts:
        P(" back", r[0], tick_hk(r[1]), r[2], r[3], r[4], r[5], "hits", r[6], "st", r[7])

    P("=== civilian return unique after 84400430 ===")
    ret=c.execute("""
      SELECT creep, role, min(tick), max(tick)
      FROM creep_ticks
      WHERE room='W47N7' AND tick BETWEEN 84400430 AND 84401050
      GROUP BY 1,2 ORDER BY 3
    """).fetchall()
    for r in ret: P(" ret", r)

    P("=== other rdef names ever ===")
    defs=c.execute("""
      SELECT creep, role, min(tick), max(tick), count(*), min(hits), max(hits)
      FROM creep_ticks
      WHERE tick>=84400200 AND (creep ILIKE '%def%' OR coalesce(role,'') ILIKE '%def%')
      GROUP BY 1,2 ORDER BY 3
    """).fetchall()
    for r in defs: P(" DEF", r)

    P("=== box_pauses since 20:00 ===")
    try:
        rows=c.execute("SELECT * FROM box_pauses WHERE ts >= '2026-11-21 20:00:00+08' OR COALESCE(started_at, '1970-01-01') >= '2026-11-21 20:00:00+08' ORDER BY 1").fetchall()
        P("box_pauses n", len(rows))
        for r in rows: P(" BP", dict(r) if hasattr(r,'keys') else r)
    except Exception as e:
        P("box_pauses err", type(e), e)
        cols=[x[0] for x in c.execute("SELECT column_name FROM information_schema.columns WHERE table_name='box_pauses' ORDER BY ordinal_position")]
        P("box_pauses cols", cols)
        rows=c.execute("SELECT * FROM box_pauses ORDER BY 1 DESC LIMIT 8").fetchall()
        for r in rows: P(" BP", r)

open(OUT,"w").write("\n".join(lines)+"\n")
print("wrote", OUT, "lines", len(lines))
