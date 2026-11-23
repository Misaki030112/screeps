#!/usr/bin/env python3
from pathlib import Path
import re
D = Path("/workspace/screeps/state/_patrol_2026-11-23_2028")

def dump(name, n=0, head=0, tail=0, pats=None):
    t = (D / name).read_text(errors="replace")
    print("=" * 20, name, "lines", len(t.splitlines()), "=" * 20)
    if pats:
        for pat in pats:
            hits = [ln for ln in t.splitlines() if re.search(pat, ln, re.I)]
            for ln in hits[:n or 80]:
                print(ln)
            if n and len(hits) > n:
                print(f"  ... {len(hits)-n} more for /{pat}/")
        return
    lines = t.splitlines()
    if head:
        print("\n".join(lines[:head]))
        if tail:
            print("...")
            print("\n".join(lines[-tail:]))
    elif tail:
        print("\n".join(lines[-tail:]))
    else:
        print(t)

# exact2h key sections
ex = (D/"exact2h.txt").read_text(errors="replace")
print("=" * 20, "exact2h SELECTED", "=" * 20)
# print around TIP, exact2h rates, storage, cpu, later
keys = ("TIP ", "exact2h", "last20", "last200", "last800", "last1500", "INTERP",
        "storage", "stor", "under15", "40k", "upLatched", "keep", "since_last",
        "cpu", "bucket", "max ", "min ", "host", "RCL", "progress", "later",
        "nUp", "w8up", "upgrade", "FORMAL")
for i, ln in enumerate(ex.splitlines()):
    if any(k.lower() in ln.lower() for k in ("TIP", "exact", "last20", "last200", "last800", "last1500", "1h INTERP", "2h", "under15", "40k", "storage-floor", "since_last cpu", "CPU ", "bucket", "W46N8", "W47N8", "later", "nUp", "w8up", "upgrade e", "ideal", "alert", "formal", "min stor", "max stor", "tip stor")):
        if i < 400 or "later" in ln.lower() or "TIP" in ln or "exact" in ln or "last8" in ln or "under" in ln or "40k" in ln or "cpu" in ln.lower() or "INTERP" in ln:
            print(f"{i+1}: {ln}")
