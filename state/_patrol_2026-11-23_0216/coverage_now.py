#!/usr/bin/env python3
import sys, json
from pathlib import Path
sys.path.insert(0, "tools")
import db

D = Path("state/_patrol_2026-11-23_0216")
rooms = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
conn = db.connect()
cur = conn.cursor()

def cov(lo, hi, label):
    want = hi - lo + 1
    print("=== %s %d..%d want=%d ===" % (label, lo, hi, want))
    out = {}
    for room in rooms:
        cur.execute(
            "select count(distinct tick), min(tick), max(tick), count(*) from creep_ticks where room=%s and tick between %s and %s",
            (room, lo, hi),
        )
        d, mn, mx, n = cur.fetchone()
        out[room] = {
            "distinct": d,
            "min": mn,
            "max": mx,
            "rows": n,
            "missing": want - (d or 0),
        }
        print("  %s distinct=%s missing=%s rows=%s range=%s..%s" % (room, d, out[room]["missing"], n, mn, mx))
    (D / ("coverage_%s.json" % label)).write_text(json.dumps(out, indent=2) + "\n")
    return out

cov(84422901, 84426000, "official_first")
cov(84422901, 84426100, "official_plus_jp")
cov(84425951, 84426089, "new_freeze")
for room, base in [("W45N8", 84425500), ("W45N8", 84425800)]:
    lo, hi = base + 1, base + 100
    cur.execute(
        "select count(distinct tick), min(tick), max(tick) from creep_ticks where room=%s and tick between %s and %s",
        (room, lo, hi),
    )
    print("404 hole %s@%s %s..%s:" % (room, base, lo, hi), cur.fetchone())

for table in ("room_stats", "creep_cpu", "path_arrivals"):
    try:
        cur.execute("select max(tick) from %s" % table)
        print(table, "tip", cur.fetchone())
    except Exception as e:
        print(table, "err", e)
        conn.rollback()
