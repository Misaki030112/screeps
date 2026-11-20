#!/usr/bin/env python3
"""Pre-health check for the 30-min official-history backfill. No console queries, no second listener."""
from __future__ import annotations
import json, os, socket, subprocess, time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db

HK = ZoneInfo("Asia/Hong_Kong")
ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-20_1230"
PREV_END = 84372900  # last 12:00 half-hour official first-pass 84371901..84372600 + just-published 84372600 through 84372700 (written 12:09:45 at gt=84372741). Prior 1h patrol _patrol_2026-11-20_1220 already delivered ~12:25 and official-filled 84372201..84372900 (published_bases 84372200..84372800 at gt=84372905; first pass missing_chunks=3 W47N8/W45N8/W47N7@84372800, retry 12:26:02 gt=84372974 recovered all 3 inserted=2598). That patrol told: 11:36 short, 11:48-11:59 freeze, 12:01 short, NEW 12:13:48-12:19:38 freeze (STATS 84372791..84372889 99t), leftover official 404s including W46N8@84371600 still 404, and W45N7 Invader Core. Do not write into that patrol folder. Listener auto-restart 12:19:41 (current listener.py started 12:19; parent run_listener.sh pid 4035476 from Nov 13). This run must not itself restart the listener or war_cmd/pulse, and must not start a second listener. Measure any new STATS gap after PREV_END.
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
PREV_GAPS = [
    # last run documented freeze gaps; will also detect new ones from room_stats
]

def now():
    return datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S")

def sh(cmd):
    return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)

def http_code(host, port, path="/"):
    try:
        s = socket.create_connection((host, port), 3)
        s.sendall(f"GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n".encode())
        data = s.recv(64).decode("utf-8", "replace")
        s.close()
        return data.split()[1] if data.startswith("HTTP/") else data[:40]
    except Exception as e:
        return f"ERR {e}"

def pgrep_etime(pat):
    try:
        out = sh(f"pgrep -af '{pat}' || true")
    except Exception as e:
        return out if False else str(e)
    lines = []
    for line in out.splitlines():
        if not line.strip():
            continue
        pid = line.split(None, 1)[0]
        if not pid.isdigit():
            lines.append(line)
            continue
        try:
            et = sh(f"ps -o lstart=,cmd= -p {pid}").strip()
        except Exception:
            et = line
        lines.append(f"{pid:>8} {et}")
    return "\n".join(lines) or "none"

lines = []
def out(s=""):
    lines.append(s)
    print(s, flush=True)

out(f"{now()} HKT check")
out("==== processes (screeps/pg/grafana/listener) ====")
# Match last pre format
try:
    out(sh("ps -eo pid,lstart,cmd | awk '/postgresql\\/17\\/bin\\/postgres -D \\/workspace\\/screeps\\/var\\/pg17/ && !/awk/ {print}'").rstrip())
    out(sh("ps -eo pid,lstart,cmd | awk '/grafana server/ && !/awk/ && !/elasticsearch/ {print}'").rstrip())
    out(sh("ps -eo pid,lstart,cmd | awk '/http.server 8787/ && !/awk/ {print}'").rstrip())
    out(sh("ps -eo pid,lstart,cmd | awk '/tools\\/listener.py/ && !/awk/ {print}'").rstrip())
    out(sh("ps -eo pid,lstart,cmd | awk '/run_listener.sh/ && !/awk/ {print}'").rstrip())
except Exception as e:
    out(f"ps error: {e}")

out("==== pg_lsclusters ====")
out(sh("pg_lsclusters -h").rstrip())

# listener counts
def count_pat(pat):
    try:
        return int(sh(f"pgrep -cf '{pat}' || true").strip() or "0")
    except Exception:
        return -1

n_listener = count_pat("[t]ools/listener.py")
n_loop = count_pat("[r]un_listener.sh")
yield_path = ROOT / "metrics" / "listener_yield_rooms"
lock = ROOT / "metrics" / "listener.lock"
pidfile = ROOT / "metrics" / "listener.pid"
out("==== listener pids / locks ====")
out(f"listener.py count={n_listener}")
out(f"run_listener.sh count={n_loop}")
out(f"yield_files={'present' if yield_path.exists() else 'absent'}")
if lock.exists():
    out(f"listener.lock mtime={datetime.fromtimestamp(lock.stat().st_mtime, HK).strftime('%Y-%m-%d %H:%M')}")
if pidfile.exists():
    out(f"pidfile={pidfile.read_text().strip()} (run_listener.sh)")

out("==== listener_rot ====")
rotp = ROOT / "metrics" / "listener_rot.json"
if rotp.exists():
    out(rotp.read_text().strip())
    rot_age = time.time() - rotp.stat().st_mtime
    out(f"listener_rot.json age_s={rot_age:.1f}")
else:
    out("MISSING")

out("==== live.json summary ====")
livep = ROOT / "metrics" / "live.json"
if livep.exists():
    d = json.loads(livep.read_text())
    age = time.time() - livep.stat().st_mtime
    stats = d.get("stats") or {}
    out(f"  gameTime= {d.get('gameTime')}")
    out(f"  uid= {d.get('uid')}")
    out(f"  roomSlot= {d.get('roomSlot')}")
    out(f"  updated= {d.get('updated')}")
    out(f"  cpu= {d.get('cpu')}")
    out(f"  stats.t= {stats.get('t')} cpu= {stats.get('cpu')} b= {stats.get('b')}")
    objs = d.get("objects") or []
    out(f"  objects_n= {len(objs)} ({d.get('roomSlot')} slot)")
    out(f"  live.json_mtime_age_s= {age:.1f}")
    out(f"  live.json_mtime= {datetime.fromtimestamp(livep.stat().st_mtime, HK).strftime('%Y-%m-%d %H:%M:%S')} HKT")
else:
    out("MISSING live.json")

out("==== HTTP ====")
out(f"grafana :3000 -> {http_code('127.0.0.1', 3000)}")
out(f"dashboard 127.0.0.1:8787 -> {http_code('127.0.0.1', 8787)}")

out("==== listener restarts / errors ====")
try:
    out(sh("grep ' restart$' /workspace/screeps/metrics/listener.out | tail -8").rstrip())
except Exception as e:
    out(str(e))
# recent errors after last restart
try:
    last_restart = sh("grep ' restart$' /workspace/screeps/metrics/listener.out | tail -1").strip()
    out(f"last_restart_line={last_restart}")
    # any error lines after last restart
    # Use the timestamp from the last restart line, not a hardcoded earlier run.
    ts = last_restart.split(" restart")[0].strip() if last_restart else ""
    if ts:
        pat = ts + " restart"
        err = sh(
            "awk -v pat=" + repr(pat) + r""" 'index($0, pat){p=1} p && /error|Error|ERROR|Traceback|429|frozen|box /' /workspace/screeps/metrics/listener.out | tail -20 || true"""
        ).rstrip()
    else:
        err = ""
    out("errors/pauses after last restart:")
    out(err or "(none)")
except Exception as e:
    out(str(e))

out("==== box_pauses.jsonl last ====")
bp = ROOT / "metrics" / "box_pauses.jsonl"
if bp.exists():
    out(sh(f"tail -6 {bp}").rstrip())
else:
    out("MISSING")

out("==== concurrent processes of note ====")
war = sh("pgrep -af 'war_cmd|war_pulse|war_listen' || true").strip()
# filter our grep
war_lines = [l for l in war.splitlines() if 'war_cmd' in l or 'war_pulse' in l or 'war_listen' in l]
war_lines = [l for l in war_lines if 'pgrep' not in l]
out("\n".join(war_lines) if war_lines else "none")

out("==== db health + recent ingest ====")
with db.connect() as conn:
    c = db.cursor(conn) if hasattr(db, "cursor") else conn.cursor()
    # try standard
    try:
        c.execute("select now()")
        db_now = c.fetchone()[0]
    except Exception:
        c = conn.cursor()
        c.execute("select now()")
        db_now = c.fetchone()[0]
    out(f"db_now {db_now}")
    c.execute("select max(tick) from room_stats")
    tip_rs = c.fetchone()[0]
    out(f"tip_room_stats={tip_rs}")
    tcut = tip_rs - 2000 if tip_rs else 0
    for table in ("creep_ticks", "creep_cpu", "path_arrivals", "room_stats"):
        c.execute(f"select min(tick), max(tick), count(*) from {table} where tick>=%s", (tcut,))
        mn, mx, n = c.fetchone()
        out(f"  {table}: last2h-ish ticks={mn}..{mx} rows={n}")

    start_after = PREV_END + 1
    out(f"creep_ticks since tick {start_after} (after 12:25 1h patrol official reconstructed through 84372900 / 12:00 half-hour just-published through 84372700; leftover 404 W46N8@84371600 should have aged out of this 40-min window; older leftover 404s aged out; prior 1h patrol _patrol_2026-11-20_1220 already delivered ~12:25 and told freezes/gaps through 12:13 and leftover 404s; listener auto-restart 12:19:41 (current listener.py from 12:19); this run must not restart the listener):")
    for room in ROOMS:
        c.execute(
            "select min(tick), max(tick), count(*), count(distinct tick) from creep_ticks where room=%s and tick>=%s",
            (room, start_after),
        )
        mn, mx, n, d = c.fetchone()
        if n:
            out(f"  {room} {mn}..{mx} rows={n} distinct={d}")
        else:
            out(f"  {room} (none)")

    c.execute("select min(tick), max(tick), count(*) from creep_cpu where tick>=%s", (PREV_END,))
    mn, mx, n = c.fetchone()
    out(f"creep_cpu tick>={PREV_END}: ticks={mn}..{mx} rows={n}")
    c.execute("select min(tick), max(tick), count(*) from path_arrivals where tick>=%s", (PREV_END,))
    mn, mx, n = c.fetchone()
    out(f"path_arrivals tick>={PREV_END}: ticks={mn}..{mx} rows={n}")

    # after reconnect ~06:01:35 / pid 1159748; also 05:57:02 after freeze 05:53:08-05:56:59; estimate from live stats
    # find room_stats gaps since last window start-ish
    c.execute(
        """
        with s as (
          select tick, lag(tick) over (order by tick) as prev
          from room_stats
          where tick >= %s
        )
        select prev+1 as gap_start, tick-1 as gap_end, (tick-1)-(prev+1)+1 as span
        from s
        where prev is not null and tick - prev > 15
        order by 1
        """,
        (PREV_END - 1100,),
    )
    gaps = c.fetchall()
    out(f"room_stats significant gaps since {PREV_END-1100} (ignoring normal ~9-tick STATS cadence):")
    if not gaps:
        out("  (none)")
    for gs, ge, span in gaps:
        out(f"  {gs}..{ge} ({span})")
        out(f"creep_ticks in room_stats gap {gs}..{ge}:")
        for room in ROOMS:
            c.execute(
                "select min(tick), max(tick), count(*), count(distinct tick) from creep_ticks where room=%s and tick between %s and %s",
                (room, gs, ge),
            )
            mn, mx, n, d = c.fetchone()
            missing = span - (d or 0)
            if n:
                # find missing ranges briefly
                c.execute(
                    "select array_agg(t) from (select generate_series(%s,%s) t except select distinct tick from creep_ticks where room=%s and tick between %s and %s) x",
                    (gs, ge, room, gs, ge),
                )
                miss = c.fetchone()[0] or []
                miss_s = ""
                if miss:
                    # compress
                    ranges = []
                    a = b = miss[0]
                    for t in miss[1:]:
                        if t == b + 1:
                            b = t
                        else:
                            ranges.append(f"{a}..{b}" if a != b else str(a))
                            a = b = t
                    ranges.append(f"{a}..{b}" if a != b else str(a))
                    miss_s = " missing " + ", ".join(ranges) + f" ({len(miss)})"
                out(f"  {room} {mn}..{mx} rows={n} distinct={d}{miss_s}")
            else:
                out(f"  {room} none (missing all {span})")

    # reconnect freshness: last 30 ticks of room_stats and live room
    c.execute("select min(tick), max(tick), count(*) from room_stats where tick >= %s", (tip_rs - 20 if tip_rs else 0,))
    mn, mx, n = c.fetchone()
    out(f"room_stats recent tip window: ticks={mn}..{mx} rows={n}")
    slot = None
    livep = ROOT / "metrics" / "live.json"
    if livep.exists():
        slot = json.loads(livep.read_text()).get("roomSlot")
    if slot and tip_rs:
        c.execute(
            "select min(tick), max(tick), count(*), count(distinct tick) from creep_ticks where room=%s and tick>=%s",
            (slot, tip_rs - 20),
        )
        mn, mx, n, d = c.fetchone()
        out(f"{slot} live near tip >= {tip_rs-20}: ticks={mn}..{mx} rows={n} distinct={d}")

out("==== health verdict ====")
ok = True
reasons = []
if n_listener != 1:
    ok = False
    reasons.append(f"listener.py count={n_listener} (want 1)")
if n_loop != 1:
    ok = False
    reasons.append(f"run_listener.sh count={n_loop} (want 1)")
if yield_path.exists():
    reasons.append("yield file present (commander may hold slots; will not start a second listener)")
if livep.exists():
    age = time.time() - livep.stat().st_mtime
    if age > 90:
        ok = False
        reasons.append(f"live.json stale age_s={age:.1f}")
else:
    ok = False
    reasons.append("live.json missing")
out(f"ok={ok}")
if reasons:
    out("notes: " + "; ".join(reasons))
else:
    out("infra healthy: single listener, postgres/grafana/dashboard up, live.json fresh, no yield file")

text = "\n".join(lines) + "\n"
(DIR / "pre.txt").write_text(text)
(DIR / "pre_raw.txt").write_text(text)
print("wrote", DIR / "pre.txt")
