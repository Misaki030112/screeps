#!/usr/bin/env python3
from pathlib import Path
D = Path("/workspace/screeps/state/_patrol_2026-11-23_0216")

def dump(name, nhead=60, ntail=40):
    p = D / name
    t = p.read_text() if p.exists() else ""
    ls = t.splitlines()
    print("=" * 20, name, "lines", len(ls), "bytes", len(t), "=" * 20)
    if len(ls) <= nhead + ntail:
        print("\n".join(ls))
    else:
        print("\n".join(ls[:nhead]))
        print("... [%d lines omitted] ..." % (len(ls) - nhead - ntail))
        print("\n".join(ls[-ntail:]))
    print()

dump("audit_patrol.txt", 80, 50)
dump("motion_1h.txt", 50, 40)
dump("motion_3h.txt", 50, 40)
dump("model_1h.txt", 80, 20)
dump("model_2h.txt", 80, 20)
dump("model_w8_1h.txt", 80, 20)
dump("model_w8_2h.txt", 80, 20)
