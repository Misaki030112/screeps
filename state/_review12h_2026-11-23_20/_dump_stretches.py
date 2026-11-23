#!/usr/bin/env python3
import json
from pathlib import Path

rows = json.loads(Path("state/_review12h_2026-11-23_20/sql_stor_stretches.txt.json").read_text())
print("n_stretches", len(rows))
print("keys", list(rows[0].keys()) if rows else None)
if rows:
    print("sample", rows[0])

def ticks_of(r):
    for k in ("dticks", "ticks", "n", "span", "dt"):
        if r.get(k) is not None:
            return r[k]
    return 0

def show(pred, title, limit=25):
    sel = [r for r in rows if pred(r)]
    sel = sorted(sel, key=lambda r: -ticks_of(r))
    print("\n=====", title, "n="+str(len(sel)), "=====")
    for r in sel[:limit]:
        print(r)

# Try common field names
kind_keys = set()
for r in rows:
    for k in r:
        if "kind" in k or "band" in k or "label" in k or "type" in k or "thresh" in k or "cls" in k:
            kind_keys.add(k)
print("kind-like keys", kind_keys)

# dump unique values of likely classifiers
for k in rows[0].keys():
    vals = sorted({str(r[k]) for r in rows})
    if len(vals) <= 20:
        print("distinct", k, vals)
