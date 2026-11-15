#!/usr/bin/env python3
import os, sys, json, csv
from datetime import datetime
sys.path.insert(0, "/workspace/screeps/tools")
import db as dbmod
from psycopg.rows import dict_row

OUT = "/workspace/screeps/state/_review12h_2026-11-15_20"
# lock to the window already chosen
START_TICK = 84274500
END_TICK = 84284720
CAP = 10935000
params = {"s": START_TICK, "e": END_TICK, "cap": CAP}

os.chdir("/workspace/screeps")
conn = dbmod.connect()
cur = conn.cursor(row_factory=dict_row)

def run(name, sql, args=None):
    cur.execute(sql, args or {})
    rows = cur.fetchall()
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        if not rows:
            f.write("(no rows)\n")
            return rows
        keys = list(rows[0].keys())
        f.write("\t".join(keys) + "\n")
        for r in rows:
            vals = ["" if r[k] is None else str(r[k]) for k in keys]
            f.write("\t".join(vals) + "\n")
    with open(path + ".json", "w") as f:
        json.dump(rows, f, indent=2, default=str)
    return rows

run("sql_cpu.txt", """
SELECT
  count(*) AS n,
  avg(cpu)::numeric(12,6) AS cpu_avg,
  percentile_cont(0.95) WITHIN GROUP (ORDER BY cpu)::numeric(12,6) AS cpu_p95,
  max(cpu) AS cpu_max,
  min(bucket) AS bucket_min,
  max(bucket) AS bucket_max,
  avg(bucket)::numeric(12,4) AS bucket_avg,
  count(*) FILTER (WHERE cpu >= 40) AS n_cpu_ge40
FROM room_stats
WHERE room='W46N8' AND tick >= %(s)s AND tick <= %(e)s;
""", params)

run("sql_cpu_spikes.txt", """
SELECT tick, ts, cpu, bucket, commit, room
FROM room_stats
WHERE room='W46N8' AND tick >= %(s)s AND tick <= %(e)s AND cpu >= 40
ORDER BY tick;
""", params)

run("sql_cpu_top.txt", """
SELECT tick, ts, cpu, bucket, commit
FROM room_stats
WHERE room='W46N8' AND tick >= %(s)s AND tick <= %(e)s
ORDER BY cpu DESC, tick
LIMIT 15;
""", params)

run("sql_sites_summary.txt", """
WITH s AS (
  SELECT room, tick, ts, sites
  FROM room_stats
  WHERE room IN ('W46N8','W47N8') AND tick >= %(s)s AND tick <= %(e)s
)
SELECT room,
  (SELECT sites FROM s x WHERE x.room=s.room ORDER BY tick ASC LIMIT 1) AS first_sites,
  (SELECT tick FROM s x WHERE x.room=s.room ORDER BY tick ASC LIMIT 1) AS first_tick,
  (SELECT sites FROM s x WHERE x.room=s.room ORDER BY tick DESC LIMIT 1) AS last_sites,
  (SELECT tick FROM s x WHERE x.room=s.room ORDER BY tick DESC LIMIT 1) AS last_tick,
  (SELECT max(tick) FROM s x WHERE x.room=s.room AND x.sites>0) AS last_nonzero_tick,
  (SELECT max(ts) FROM s x WHERE x.room=s.room AND x.sites>0) AS last_nonzero_ts,
  (SELECT sites FROM s x WHERE x.room=s.room AND x.sites>0 ORDER BY tick DESC LIMIT 1) AS last_nonzero_sites,
  (SELECT min(tick) FROM s x WHERE x.room=s.room AND x.sites=0) AS first_zero_tick,
  (SELECT min(ts) FROM s x WHERE x.room=s.room AND x.sites=0) AS first_zero_ts,
  count(*) FILTER (WHERE sites=0) AS n_zero,
  count(*) FILTER (WHERE sites>0) AS n_nonzero,
  min(sites) AS sites_min, max(sites) AS sites_max
FROM s
GROUP BY room
ORDER BY room;
""", params)

run("sql_sites_changes.txt", """
WITH s AS (
  SELECT room, tick, ts, sites,
         lag(sites) OVER (PARTITION BY room ORDER BY tick) AS prev
  FROM room_stats
  WHERE room IN ('W46N8','W47N8') AND tick >= %(s)s AND tick <= %(e)s
)
SELECT room, tick, ts, prev AS sites_prev, sites
FROM s
WHERE prev IS DISTINCT FROM sites
ORDER BY room, tick;
""", params)

run("sql_commits.txt", """
SELECT commit, min(tick) AS t0, max(tick) AS t1, min(ts) AS ts0, max(ts) AS ts1, count(*) AS n
FROM room_stats
WHERE room='W46N8' AND tick >= %(s)s AND tick <= %(e)s
GROUP BY commit
ORDER BY t0;
""", params)

run("sql_deploys.txt", """
SELECT ts, tick, commit, note
FROM deploys
ORDER BY ts DESC
LIMIT 10;
""")

run("sql_gaps.txt", """
WITH s AS (
  SELECT room, tick, ts, lag(tick) OVER (PARTITION BY room ORDER BY tick) AS prev,
         lag(ts) OVER (PARTITION BY room ORDER BY tick) AS prev_ts
  FROM room_stats
  WHERE room IN ('W46N8','W47N8') AND tick >= %(s)s AND tick <= %(e)s
)
SELECT room, prev AS gap_from, tick AS gap_to, (tick-prev-1) AS missing, prev_ts AS ts_from, ts AS ts_to
FROM s
WHERE prev IS NOT NULL AND tick-prev > 20
ORDER BY (tick-prev) DESC, room, tick;
""", params)

run("sql_first_last_rows.txt", """
(SELECT room, tick, ts, rcl, progress, progress_total, energy, energy_cap, sites, hostiles, safe_mode, cpu, bucket, gcl_progress, creeps, commit, storage, ctl, ctl_ema
 FROM room_stats WHERE room='W46N8' AND tick>=%(s)s AND tick<=%(e)s ORDER BY tick ASC LIMIT 1)
UNION ALL
(SELECT room, tick, ts, rcl, progress, progress_total, energy, energy_cap, sites, hostiles, safe_mode, cpu, bucket, gcl_progress, creeps, commit, storage, ctl, ctl_ema
 FROM room_stats WHERE room='W46N8' AND tick>=%(s)s AND tick<=%(e)s ORDER BY tick DESC LIMIT 1)
UNION ALL
(SELECT room, tick, ts, rcl, progress, progress_total, energy, energy_cap, sites, hostiles, safe_mode, cpu, bucket, gcl_progress, creeps, commit, storage, ctl, ctl_ema
 FROM room_stats WHERE room='W47N8' AND tick>=%(s)s AND tick<=%(e)s ORDER BY tick ASC LIMIT 1)
UNION ALL
(SELECT room, tick, ts, rcl, progress, progress_total, energy, energy_cap, sites, hostiles, safe_mode, cpu, bucket, gcl_progress, creeps, commit, storage, ctl, ctl_ema
 FROM room_stats WHERE room='W47N8' AND tick>=%(s)s AND tick<=%(e)s ORDER BY tick DESC LIMIT 1);
""", params)

run("sql_hostiles.txt", """
SELECT room, tick, ts, hostiles, storage, sites, progress
FROM room_stats
WHERE room IN ('W46N8','W47N8','W45N8','W45N7','W47N7')
  AND tick >= %(s)s AND tick <= %(e)s AND hostiles > 0
ORDER BY tick, room;
""", params)

run("sql_incidents_full.txt", """
SELECT ts, tick, remote, inc, ev, from_state, state, why, inv, inv_ttl, def, dur, data
FROM incidents
WHERE tick >= %(s)s AND tick <= %(e)s
ORDER BY tick, remote, ev;
""", params)

run("sql_incidents.txt", """
SELECT remote, inc,
       min(tick) AS t0, max(tick) AS t1, (max(tick)-min(tick)) AS tick_span,
       min(ts) AS ts0, max(ts) AS ts1,
       max(dur) AS max_dur,
       (ARRAY_AGG(ev ORDER BY tick)) AS evs,
       (ARRAY_AGG(DISTINCT def) FILTER (WHERE def IS NOT NULL)) AS defs,
       (ARRAY_AGG(why ORDER BY tick) FILTER (WHERE why IS NOT NULL)) AS whys,
       (ARRAY_AGG(state ORDER BY tick)) AS states
FROM incidents
WHERE tick >= %(s)s AND tick <= %(e)s
GROUP BY remote, inc
ORDER BY t0, remote;
""", params)

run("sql_alerts.txt", """
SELECT ts, tick, kind, room, severity, episode, msg, data
FROM events
WHERE kind LIKE 'alert' || '%' AND tick >= %(s)s AND tick <= %(e)s
ORDER BY tick, kind;
""", params)

run("sql_box_pauses.txt", """
SELECT ts, tick, kind, room, msg, data
FROM events
WHERE kind='box_pause' AND ts >= (
  SELECT min(ts) FROM room_stats WHERE room='W46N8' AND tick>=%(s)s
) AND ts <= (
  SELECT max(ts) FROM room_stats WHERE room='W46N8' AND tick<=%(e)s
)
ORDER BY ts;
""", params)

run("sql_event_kinds.txt", """
SELECT kind, count(*) AS n, min(tick) AS t0, max(tick) AS t1
FROM events
WHERE tick >= %(s)s AND tick <= %(e)s
GROUP BY kind
ORDER BY n DESC;
""", params)

run("sql_coverage.txt", """
SELECT room, count(*) AS n,
       count(DISTINCT tick) AS n_ticks,
       min(tick) AS t0, max(tick) AS t1
FROM room_stats
WHERE room IN ('W46N8','W47N8') AND tick >= %(s)s AND tick <= %(e)s
GROUP BY room;
""", params)

# series dump for stretch math
cur.execute("""
SELECT room, tick, ts, storage, progress, cpu, bucket, sites, hostiles, ctl, ctl_ema, commit
FROM room_stats
WHERE room IN ('W46N8','W47N8') AND tick >= %(s)s AND tick <= %(e)s
ORDER BY room, tick;
""", params)
rows = cur.fetchall()
csv_path = os.path.join(OUT, "sql_series.csv")
keys = list(rows[0].keys()) if rows else []
with open(csv_path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(keys)
    for r in rows:
        w.writerow([r[k] for k in keys])
print(f"series n={len(rows)}")

# Python stretches: break when sample gap > 20 ticks
KINDS = {
    "under15": lambda s: s is not None and s < 15000,
    "ge20": lambda s: s is not None and s >= 20000,
    "ge25": lambda s: s is not None and s >= 25000,
    "ge30": lambda s: s is not None and s >= 30000,
    "ge40": lambda s: s is not None and s >= 40000,
}

from collections import defaultdict
by_room = defaultdict(list)
for r in rows:
    by_room[r["room"]].append(r)

stretches = []
for room, series in by_room.items():
    series = sorted(series, key=lambda r: r["tick"])
    for kind, pred in KINDS.items():
        cur_run = None
        prev = None
        for r in series:
            gap_break = prev is not None and (r["tick"] - prev["tick"] > 20)
            on = pred(r["storage"])
            if gap_break or not on:
                if cur_run:
                    stretches.append(cur_run)
                    cur_run = None
            if on and not (gap_break and not on):
                # if gap_break and on, start a new run
                if cur_run is None:
                    cur_run = {
                        "room": room, "kind": kind,
                        "t0": r["tick"], "t1": r["tick"],
                        "ts0": r["ts"], "ts1": r["ts"],
                        "n": 1,
                        "stor_min": r["storage"], "stor_max": r["storage"],
                    }
                else:
                    cur_run["t1"] = r["tick"]
                    cur_run["ts1"] = r["ts"]
                    cur_run["n"] += 1
                    cur_run["stor_min"] = min(cur_run["stor_min"], r["storage"])
                    cur_run["stor_max"] = max(cur_run["stor_max"], r["storage"])
            prev = r
        if cur_run:
            stretches.append(cur_run)
            cur_run = None

for st in stretches:
    st["tick_span"] = st["t1"] - st["t0"] + 1
    st["open_at_tip"] = (st["t1"] == END_TICK)

stretches.sort(key=lambda s: (s["room"], s["kind"], -s["tick_span"], s["t0"]))

# write all
path = os.path.join(OUT, "sql_stor_stretches.txt")
keys = ["room","kind","t0","t1","ts0","ts1","tick_span","n","stor_min","stor_max","open_at_tip"]
with open(path, "w") as f:
    f.write("\t".join(keys)+"\n")
    for st in stretches:
        f.write("\t".join(str(st[k]) for k in keys)+"\n")
with open(path+".json","w") as f:
    json.dump(stretches, f, indent=2, default=str)

# longest + open-at-tip per room/kind
summary = []
for room in ("W46N8","W47N8"):
    for kind in KINDS:
        cand = [s for s in stretches if s["room"]==room and s["kind"]==kind]
        longest = cand[0] if cand else None
        open_ones = [s for s in cand if s["open_at_tip"]]
        summary.append({
            "room": room, "kind": kind,
            "n_stretches": len(cand),
            "longest": longest,
            "open_at_tip": open_ones[-1] if open_ones else None,  # last open (should be at most one)
            "could_arm_300": bool(longest and kind=="ge20" and longest["tick_span"]>=300),
            "could_arm_500": bool(longest and kind=="ge40" and longest["tick_span"]>=500),
        })
with open(os.path.join(OUT, "sql_stor_longest.txt"), "w") as f:
    f.write(json.dumps(summary, indent=2, default=str))
    f.write("\n")

# also list all home ge20 and W47 ge30/ge40 explicitly
home20 = [s for s in stretches if s["room"]=="W46N8" and s["kind"]=="ge20"]
w47_30 = [s for s in stretches if s["room"]=="W47N8" and s["kind"]=="ge30"]
w47_40 = [s for s in stretches if s["room"]=="W47N8" and s["kind"]=="ge40"]
w47_25 = [s for s in stretches if s["room"]=="W47N8" and s["kind"]=="ge25"]
home15 = [s for s in stretches if s["room"]=="W46N8" and s["kind"]=="under15"]
with open(os.path.join(OUT, "sql_stor_key_stretches.txt"), "w") as f:
    f.write("HOME ge20 (20k/300t gate)\n")
    f.write(json.dumps(home20, indent=2, default=str)+"\n\n")
    f.write("HOME under15 (top 8 by span)\n")
    f.write(json.dumps(home15[:8], indent=2, default=str)+"\n\n")
    f.write("W47 ge25 (top 8)\n")
    f.write(json.dumps(w47_25[:8], indent=2, default=str)+"\n\n")
    f.write("W47 ge30 (all)\n")
    f.write(json.dumps(w47_30, indent=2, default=str)+"\n\n")
    f.write("W47 ge40 (all)\n")
    f.write(json.dumps(w47_40, indent=2, default=str)+"\n")

print("stretches", len(stretches))
print("home ge20", home20)
print("home under15 longest", home15[0] if home15 else None)
print("w47 ge25 longest", w47_25[0] if w47_25 else None)
print("w47 ge30 longest", w47_30[0] if w47_30 else None)
print("w47 ge40", w47_40)
print("SQL rest done")
conn.close()
