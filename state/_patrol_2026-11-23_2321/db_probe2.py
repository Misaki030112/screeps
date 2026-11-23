#!/usr/bin/env python3
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import db

HK = ZoneInfo("Asia/Hong_Kong")
LAST_TIP = 84420810  # previous patrol analysis tip
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")

def gaps(ticks):
    if not ticks:
        return []
    ticks = sorted(set(ticks))
    out = []
    expect = ticks[0]
    for t in ticks:
        if t > expect:
            out.append((expect, t - 1, t - expect))
        expect = t + 1
    return out

with db.connect() as c:
    print("=== room_stats latest ===")
    for r in c.execute("SELECT room, max(tick), max(ts) FROM room_stats GROUP BY room ORDER BY 1"):
        print(" ", r)
    tip = c.execute("SELECT max(tick) FROM room_stats WHERE room='W46N8'").fetchone()[0]
    print("analysis candidate tip", tip)

    print("=== storage / controller / cpu this hour (since last tip) ===")
    for room in ("W46N8", "W47N8"):
        rows = c.execute(
            """SELECT tick, ts, storage, progress, energy, cpu, bucket, hostiles, creeps, sites
                 FROM room_stats WHERE room=%s AND tick>=%s ORDER BY tick""",
            (room, LAST_TIP),
        ).fetchall()
        print(f" {room} n={len(rows)} first={rows[0] if rows else None}")
        print(f"          last={rows[-1] if rows else None}")
        if not rows:
            continue
        stor = [(r[0], r[2], r[1]) for r in rows if r[2] is not None]
        if stor:
            vals = [s[1] for s in stor]
            mn = min(stor, key=lambda x: x[1])
            mx = max(stor, key=lambda x: x[1])
            print(f"  storage n={len(stor)} min={mn[1]}@{mn[0]} {mn[2].astimezone(HK)} max={mx[1]}@{mx[0]} {mx[2].astimezone(HK)} tip={stor[-1][1]}@{stor[-1][0]}")
            if room == "W46N8":
                under = [s for s in stor if s[1] < 15000]
                print(f"  under15k={len(under)}/{len(stor)}={len(under)/len(stor)*100:.1f}%")
                # spans
                if under:
                    spans = []
                    a, b = under[0][0], under[0][0]
                    prev = under[0][0]
                    for t, v, ts in under[1:]:
                        if t - prev > 40:
                            spans.append((a, b))
                            a = t
                        b = t
                        prev = t
                    spans.append((a, b))
                    print("  under spans", spans[:12], "nspans", len(spans))
                over20 = [s for s in stor if s[1] >= 20000]
                print(f"  n>=20k={len(over20)} max20={max(vals)}")
            if room == "W47N8":
                over40 = [s for s in stor if s[1] >= 40000]
                print(f"  n>=40k={len(over40)} max={mx[1]}")
        cpus = [r[5] for r in rows if r[5] is not None]
        bucks = [r[6] for r in rows if r[6] is not None]
        if cpus:
            mx = max(range(len(rows)), key=lambda i: rows[i][5] or -1)
            print(f"  cpu n={len(cpus)} min={min(cpus):.2f} max={max(cpus):.2f}@{rows[mx][0]} {rows[mx][1].astimezone(HK)} mean={sum(cpus)/len(cpus):.2f}")
        if bucks:
            print(f"  bucket min={min(bucks)} max={max(bucks)} last={bucks[-1]}")
        host = [r for r in rows if (r[7] or 0) > 0]
        print(f"  hostiles_nonzero={len(host)}")

    print("=== 3h / 12h / 24h storage maxima ===")
    for room, hours in (("W46N8", 3), ("W46N8", 12), ("W47N8", 3), ("W47N8", 12), ("W47N8", 24)):
        rows = c.execute(
            """SELECT tick, storage, ts FROM room_stats
                WHERE room=%s AND tick>=%s AND storage IS NOT NULL
                ORDER BY storage DESC, tick LIMIT 3""",
            (room, tip - int(hours * 3600 / 4.19)),
        ).fetchall()
        print(f"  {room} {hours}h top", [(r[0], r[1], r[2].astimezone(HK).strftime('%H:%M:%S')) for r in rows])

    print("=== STATS gap 19:12 short WS 84419821..84419849 ===")
    for room in ROOMS:
        n = c.execute(
            "SELECT count(DISTINCT tick) FROM room_stats WHERE room=%s AND tick>=84419821 AND tick<=84419849",
            (room,),
        ).fetchone()[0]
        print(f"  room_stats {room} {n}/29")
    print(" creep_ticks official fill of 19:12 gap:")
    for room in ROOMS:
        n = c.execute(
            "SELECT count(DISTINCT tick) FROM creep_ticks WHERE room=%s AND tick>=84419821 AND tick<=84419849",
            (room,),
        ).fetchone()[0]
        mn, mx = c.execute(
            "SELECT min(tick), max(tick) FROM creep_ticks WHERE room=%s AND tick>=84419821 AND tick<=84419849",
            (room,),
        ).fetchone()
        print(f"  {room} {n}/29 range={mn}..{mx}")

    print("=== leftover 404 chunk presence (in-window + already told recent) ===")
    for room, base in [
        ("W45N7", 84419300), ("W45N8", 84419600),
        ("W45N7", 84419000),
        ("W46N8", 84418900), ("W47N8", 84418900), ("W45N8", 84418900), ("W45N7", 84418900), ("W47N7", 84418900),
    ]:
        lo, hi = base + 1, base + 100
        n, mn, mx = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick) FROM creep_ticks WHERE room=%s AND tick>=%s AND tick<=%s",
            (room, lo, hi),
        ).fetchone()
        print(f"  {room}@{base} distinct={n}/100 range={mn}..{mx}")

    print("=== box freeze 17:41 STATS already told, just confirm ===")
    # 84418531..84418879
    for lo, hi, want, label in [
        (84418531, 84418879, 349, "1741"),
        (84419821, 84419849, 29, "1912"),
    ]:
        print(f" {label} {lo}..{hi} want={want}")

    print("=== creep_cpu / path_arrivals tips ===")
    for table in ("creep_cpu", "path_arrivals"):
        try:
            r = c.execute(f"SELECT max(tick) FROM {table}").fetchone()
            print(f"  {table}", r)
        except Exception as e:
            print(f"  {table}", e)

    print("=== room_stats last 8 home ===")
    rows = c.execute(
        "SELECT tick, ts, storage, cpu, bucket, progress FROM room_stats WHERE room='W46N8' ORDER BY tick DESC LIMIT 8"
    ).fetchall()
    for r in rows:
        print(" ", r[0], r[1].astimezone(HK), "stor", r[2], "cpu", r[3], "b", r[4], "prog", r[5])
