#!/usr/bin/env python3
import json
from pathlib import Path
rows = json.loads(Path("state/_review12h_2026-11-23_20/sql_stor_stretches.txt.json").read_text())

def ticks_of(r):
    return r.get("tick_span") or 0

for kind in ("under15", "ge20", "ge25", "ge30"):
    for room in ("W46N8", "W47N8"):
        sel = [r for r in rows if r["room"]==room and r["kind"]==kind]
        sel = sorted(sel, key=lambda r: -ticks_of(r))
        print("=====", room, kind, "n="+str(len(sel)), "=====")
        for r in sel:
            print(r)
        print()
