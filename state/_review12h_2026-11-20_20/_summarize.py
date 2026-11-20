#!/usr/bin/env python3
from pathlib import Path
from collections import defaultdict
import json, ast

out = Path("/workspace/screeps/state/_review12h_2026-11-20_20")
lines = (out / "sql_stor_stretches.txt").read_text().strip().splitlines()
h = lines[0].split("\t")
rows = [dict(zip(h, line.split("\t"))) for line in lines[1:]]
print("======= LONGEST STRETCHES =======")
by = defaultdict(list)
for r in rows:
    r["tick_span"] = int(r["tick_span"])
    r["n"] = int(r["n"])
    r["stor_min"] = int(r["stor_min"])
    r["stor_max"] = int(r["stor_max"])
    by[(r["room"], r["kind"])].append(r)
for key in sorted(by):
    items = sorted(by[key], key=lambda x: -x["tick_span"])
    tot_n = sum(x["n"] for x in items)
    print(f"{key[0]} {key[1]} n_stretches={len(items)} samples={tot_n}")
    for x in items[:6]:
        ts0 = x["ts0"][5:19]
        ts1 = x["ts1"][5:19]
        print(f"  span={x['tick_span']} n={x['n']} {ts0}->{ts1} t{x['t0']}-{x['t1']} min={x['stor_min']} max={x['stor_max']}")

pauses = json.loads((out / "sql_box_pauses.txt.json").read_text())
secs = []
for p in pauses:
    data = p["data"]
    if isinstance(data, str):
        data = ast.literal_eval(data)
    secs.append(int(data["sec"]))
print("======= PAUSE TOTAL =======")
print(f"n={len(secs)} total_s={sum(secs)} total_h={sum(secs)/3600:.2f} max={max(secs)}")

print("======= incidents_full matching core or 15:29 =======")
text = (out / "sql_incidents_full.txt").read_text()
lines = text.splitlines()
print(lines[0])
for line in lines[1:]:
    low = line.lower()
    if any(s in line for s in ("843754", "843755", "843756", "843757", "843702", "843728", "843779", "843712")) or "core" in low:
        print(line[:600])
