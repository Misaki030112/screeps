#!/usr/bin/env python3
"""Parse first-pass backfill and patch confirm / tick_s_check / exact2h / just_published."""
from __future__ import annotations
import json, re
from collections import defaultdict
from pathlib import Path

D = Path("/workspace/screeps/state/_patrol_2026-11-23_0516")
text = (D / "backfill_first.txt").read_text()
m = re.search(r"game\.time=(\d+) published_bases=(\d+)\.\.(\d+)", text)
gt, b0, b1 = int(m.group(1)), int(m.group(2)), int(m.group(3))
rec = re.search(r"reconstructed ticks=(\d+)\.\.(\d+) \((\d+)\) creep_rows=(\d+) missing_chunks=(\d+)", text)
ins = re.search(r"^inserted=(\d+)", text, re.M)
already = re.search(r"already_in_db=(\d+)", text)
realign = re.search(r"^ts_realigned=(\d+)", text, re.M)
ticks = re.search(r"^tick_s=([0-9.]+)", text, re.M)
ok_re = re.compile(r"  ok  (W\d+N\d+)@(\d+) ticks=(\d+) ts=(\d+)")
rows = ok_re.findall(text)
by_base: dict[int, dict[str, int]] = defaultdict(dict)
for room, base, n, ts in rows:
    by_base[int(base)][room] = int(ts)
missing = [(r, int(b)) for r, b in re.findall(r"  404 (W\d+N\d+)@(\d+)", text)]
W46 = {}
MIN_ALL = {}
min_room = {}
for base in sorted(by_base):
    if "W46N8" in by_base[base]:
        W46[base] = by_base[base]["W46N8"]
    room, ts = min(by_base[base].items(), key=lambda kv: kv[1])
    MIN_ALL[base] = ts
    min_room[base] = room
bases = sorted(MIN_ALL)
first_s = (MIN_ALL[bases[1]] - MIN_ALL[bases[0]]) / 1000.0 / (bases[1] - bases[0])
tmin, tmax = int(rec.group(1)), int(rec.group(2))
payload = {
    "gt_first": gt,
    "published_bases": [b0, b1],
    "tmin": tmin,
    "tmax": tmax,
    "n_ticks": int(rec.group(3)),
    "missing_chunks": int(rec.group(5)),
    "inserted": int(ins.group(1)),
    "already_in_db": int(already.group(1)),
    "ts_realigned_first": int(realign.group(1)),
    "tick_s_printed": float(ticks.group(1)),
    "tick_s_first_exact": first_s,
    "missing_404": missing,
    "W46": W46,
    "MIN_ALL": MIN_ALL,
    "min_room": min_room,
    "JUST_BASE": b1 + 100,
}
(D / "chunk_ts.json").write_text(json.dumps(payload, indent=2) + "\n")
print("wrote chunk_ts.json", "gt", gt, "bases", b0, b1, "tmin/tmax", tmin, tmax)
print("404s", missing)
print("first_s", first_s, "JUST_BASE", payload["JUST_BASE"])

# --- patch confirm IN_WINDOW / AGED ---
cp = D / "backfill_confirm.py"
ct = cp.read_text()
in_window = ", ".join(f'("{r}", {b})' for r, b in missing)
# aged leftovers already told and outside this window
aged = '[]  # W45N8@84422100 and W45N8@84422400 aged out of window start %s, already told, not retried' % tmin
ct2 = re.sub(r"IN_WINDOW = \[.*?\]", f"IN_WINDOW = [{in_window}]", ct, count=1)
ct2 = re.sub(r"AGED = \[.*?\][^\n]*", f"AGED = {aged}", ct2, count=1)
# also refresh TICK_S default to printed first tick_s
ct2 = re.sub(r"^TICK_S = [0-9.]+", f"TICK_S = {ticks.group(1)}", ct2, count=1, flags=re.M)
if ct2 == ct:
    raise SystemExit("confirm.py patch failed")
cp.write_text(ct2)
print("patched confirm IN_WINDOW", in_window)

# --- patch just_published JUST_BASE ---
for name in ("backfill_just_published.py", "backfill_just_published_retry.py", "backfill_just_published_retry2.py"):
    p = D / name
    t = p.read_text()
    t2 = re.sub(r"JUST_BASE = \d+", f"JUST_BASE = {payload['JUST_BASE']}", t, count=1)
    # docstring sometimes mentions old base; leave it
    if t2 == t:
        print("WARN no JUST_BASE in", name)
    else:
        p.write_text(t2)
        print("patched", name, "JUST_BASE", payload["JUST_BASE"])

# --- patch exact2h BF_LO/HI ---
ep = D / "exact2h.py"
et = ep.read_text()
et2 = re.sub(
    r"BF_LO, BF_HI = \d+, \d+[^\n]*",
    f"BF_LO, BF_HI = {tmin}, {tmax}  # first-pass official window this 3h, missing_chunks={payload['missing_chunks']}",
    et,
    count=1,
)
if et2 == et:
    print("WARN exact2h BF patch failed")
else:
    ep.write_text(et2)
    print("patched exact2h BF", tmin, tmax)

# --- patch tick_s_check constants ---
tp = D / "tick_s_check.py"
tt = tp.read_text()

def fmt_dict(d, rooms=None):
    lines = ["{"]
    for k in sorted(d):
        if rooms:
            lines.append(f"    {k}: {d[k]},  # {rooms[k]}")
        else:
            lines.append(f"    {k}: {d[k]},")
    lines.append("}")
    return "\n".join(lines)

# Replace W46 = { ... } and MIN_ALL = { ... } blocks at top
tt2 = re.sub(r"W46 = \{.*?\}\n", f"W46 = {fmt_dict(W46)}\n", tt, count=1, flags=re.S)
tt2 = re.sub(r"MIN_ALL = \{.*?\}\n", f"MIN_ALL = {fmt_dict(MIN_ALL, min_room)}\n", tt2, count=1, flags=re.S)
tt2 = re.sub(r"TMIN, TMAX = \d+, \d+", f"TMIN, TMAX = {tmin}, {tmax}", tt2, count=1)
# TICK_S_FIRST line
tt2 = re.sub(
    r"TICK_S_FIRST = .*",
    f"TICK_S_FIRST = (MIN_ALL[{bases[1]}] - MIN_ALL[{bases[0]}]) / 1000.0 / {bases[1]-bases[0]}  # printed {ticks.group(1)}, exact {first_s:.5f}",
    tt2,
    count=1,
)
tt2 = re.sub(r"GT_FIRST = \d+", f"GT_FIRST = {gt}", tt2, count=1)
tt2 = re.sub(
    r"TS_REALIGNED_FIRST = \d+[^\n]*",
    f"TS_REALIGNED_FIRST = {payload['ts_realigned_first']}  # first-pass realign; inserted={payload['inserted']} already_in_db={payload['already_in_db']}; printed tick_s={ticks.group(1)}",
    tt2,
    count=1,
)
# keep PREV_LATER_MEAN from last half-hour if present; 0500 used 4.356684 later_raw
tt2 = re.sub(
    r"PREV_LATER_MEAN = [0-9.]+[^\n]*",
    "PREV_LATER_MEAN = 4.356684  # tick_s_in_use from quiet 05:00 half-hour (later_raw)",
    tt2,
    count=1,
)
if tt2 == tt:
    raise SystemExit("tick_s_check patch failed to change anything")
tp.write_text(tt2)
print("patched tick_s_check")
print("OK")
