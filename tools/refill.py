#!/usr/bin/env python3
"""Spawn refill time: episodes energy<cap -> energy==cap from room_stats (W46N8). usage: refill.py '<from ts>' '<to ts>'"""
import sys; sys.path.insert(0, 'tools'); import db
with db.connect() as c:
    R = c.execute("select tick,energy,energy_cap,sites from room_stats where room='W46N8' and ts between %s and %s order by tick", (sys.argv[1], sys.argv[2])).fetchall()
ep, start, deficit = [], None, 0
for t, e, cap, _ in R:
    if e is None: continue
    if e < cap and start is None: start, deficit = t, cap - e
    elif e < cap: deficit = max(deficit, cap - e)
    elif start is not None: ep.append((t - start, deficit)); start = None
big = [d for d, df in ep if df >= 600]
print(f"samples {len(R)} episodes {len(ep)} median {sorted(d for d,_ in ep)[len(ep)//2] if ep else None}  deficit>=600: n {len(big)} median {sorted(big)[len(big)//2] if big else None} ticks/1000e {round(sum(d for d,df in ep if df>=600)/max(1,sum(df for d,df in ep if df>=600))*1000,1)}")
