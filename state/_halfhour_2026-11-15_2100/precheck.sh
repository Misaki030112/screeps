#!/bin/bash
# Health snapshot for half-hour history backfill. Read-only besides writing pre.txt.
set -e
ROOT=/workspace/screeps
OUT=$ROOT/state/_halfhour_2026-11-15_2100/pre.txt
cd "$ROOT"
set -a; . ./.env; set +a
{
echo "$(TZ=Asia/Hong_Kong date '+%Y-%m-%d %H:%M:%S %Z') check"
echo "==== processes (screeps/pg/grafana/listener) ===="
ps -eo pid,lstart,cmd | grep -E '[p]ostgres|[g]rafana|[l]istener.py|[r]un_listener.sh|[h]ttp.server 8787' | grep -v 'grafana_elasticsearch' || true
echo "==== pg_lsclusters ===="
pg_lsclusters
echo "==== listener pids / locks ===="
pgrep -af 'tools/listener.py' || true
pgrep -af 'tools/run_listener.sh' || true
echo "listener.py count=$(pgrep -fc 'tools/listener.py' || true)"
echo "run_listener.sh count=$(pgrep -fc 'tools/run_listener.sh' || true)"
if ls metrics/listener_yield_rooms metrics/*yield* >/dev/null 2>&1; then
  echo "yield_files=present"; ls -la metrics/listener_yield_rooms metrics/*yield* 2>/dev/null
else
  echo "yield_files=absent"
fi
echo "==== listener locks/pids ===="
ls -la metrics/listener.lock metrics/listener.loop.lock metrics/listener.pid 2>/dev/null
echo "pidfile=$(cat metrics/listener.pid 2>/dev/null)"
echo
echo "==== listener_rot ===="
cat metrics/listener_rot.json 2>/dev/null; echo
echo "==== live.json summary ===="
.venv/bin/python - <<'PY'
import json, os, time
from datetime import datetime
from zoneinfo import ZoneInfo
TZ=ZoneInfo('Asia/Hong_Kong')
p='metrics/live.json'
j=json.load(open(p))
st=os.stat(p)
age=time.time()-st.st_mtime
print('keys', list(j.keys()))
print('  gameTime=', j.get('gameTime'))
print('  uid=', j.get('uid'))
print('  roomSlot=', j.get('roomSlot'))
print('  updated=', j.get('updated'))
print('  cpu=', j.get('cpu'))
stats=j.get('stats') if isinstance(j.get('stats'), dict) else {}
print('  stats.t=', stats.get('t'), 'cpu=', stats.get('cpu'), 'b=', stats.get('b'))
print('  live.json_mtime_age_s=', round(age,1))
print('  live.json_mtime=', datetime.fromtimestamp(st.st_mtime,TZ).strftime('%Y-%m-%d %H:%M:%S %Z'))
objs=j.get('objects')
if isinstance(objs, dict):
    print('  objects=', len(objs))
elif isinstance(objs, list):
    print('  objects=', len(objs))
print('  note: live.json objects/gameTime only filled while slot is on HOME W46N8')
PY
echo "==== recent listener log (last 20 lines) ===="
tail -n 20 metrics/listener.out
echo "==== recent errors / box pauses ===="
echo "---- box_pauses last ----"
ls -la metrics/box_pauses.jsonl metrics/war_cmd_pause metrics/errors.log 2>/dev/null
echo "metrics/errors.log"
echo "---- errors.log last ----"
tail -n 25 metrics/errors.log 2>/dev/null | tail -n 25
echo "==== HTTP ===="
curl -s -o /dev/null -w 'grafana :3000 -> %{http_code}\n' http://127.0.0.1:3000/ || true
curl -s -o /dev/null -w 'dashboard 127.0.0.1:8787 -> %{http_code}\n' http://127.0.0.1:8787/ || true
echo "---- box_pauses.jsonl last ----"
tail -n 16 metrics/box_pauses.jsonl
echo "==== db health + recent ingest ===="
.venv/bin/python - <<'PY'
import sys
sys.path.insert(0, 'tools')
import db
with db.connect() as c:
    now=c.execute("select now()").fetchone()[0]
    print('db_now', now)
    tip=c.execute("select max(tick) from room_stats").fetchone()[0]
    print(f'tip_room_stats={tip} window_from={tip-1700 if tip else None}')
    t0 = (tip-1700) if tip else 0
    for table in ('creep_ticks','creep_cpu','path_arrivals','room_stats'):
        row=c.execute(f"select min(tick), max(tick), count(*), max(tick), max(ts) from {table} where tick>=%s", (t0,)).fetchone()
        print(f'  {table}: last2h ticks={row[0]}..{row[1]} rows={row[2]} max_tick={row[3]} max_ts={row[4]}')
    print('creep_ticks since tick 84284101 (prev 20:30 official window start):')
    rows=c.execute("""
      SELECT room, min(tick), max(tick), count(*), count(distinct tick)
      FROM creep_ticks WHERE tick>=84284101
      GROUP BY room ORDER BY 1
    """).fetchall()
    for r in rows:
        print(' ', r)
    print('creep_ticks since tick 84284800 (prev 20:30 published/reconstructed end):')
    rows=c.execute("""
      SELECT room, min(tick), max(tick), count(*), count(distinct tick)
      FROM creep_ticks WHERE tick>=84284800
      GROUP BY room ORDER BY 1
    """).fetchall()
    for r in rows:
        print(' ', r)
    if not rows:
        print('  (none yet)')
    for table in ('creep_cpu','path_arrivals'):
        row=c.execute(f"select max(tick), max(ts), count(*) from {table} where tick>=84284101").fetchone()
        print(f'{table} since tick 84284101:', row)
        row=c.execute(f"""
          select min(tick), max(tick), count(*) from {table}
          where tick >= (select max(tick)-200 from {table})
        """).fetchone()
        print(f'{table} last200ticks:', row)
    row=c.execute("select max(tick), max(ts) from room_stats").fetchone()
    print('room_stats tip:', row)
    row=c.execute("select max(tick), max(ts) from creep_ticks").fetchone()
    print('creep_ticks tip:', row)
    row=c.execute("""
      SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
      FROM creep_ticks WHERE room='W45N8' AND tick BETWEEN 84279701 AND 84279800
    """).fetchone()
    print('W45N8 hole 84279701..84279800 leftover:', row)
    row=c.execute("""
      SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
      FROM creep_ticks WHERE room='W47N8' AND tick BETWEEN 84281501 AND 84281600
    """).fetchone()
    print('W47N8 hole 84281501..84281600 leftover:', row)
    row=c.execute("""
      SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
      FROM creep_ticks WHERE room='W45N8' AND tick BETWEEN 84281501 AND 84281600
    """).fetchone()
    print('W45N8 hole 84281501..84281600 leftover:', row)
    row=c.execute("""
      SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
      FROM creep_ticks WHERE room='W45N8' AND tick BETWEEN 84282501 AND 84282600
    """).fetchone()
    print('W45N8 hole 84282501..84282600 leftover (aged out of prev 20:30 window):', row)
PY
echo "==== note ===="
echo "precheck complete. Did not kill/restart listener, war_cmd, or pulse. Did not start a second listener."
echo "Listener auto-reconnected at 21:00:26 after box frozen ~905s since 20:45:17; single slot still polling."
} > "$OUT" 2>&1
echo "wrote $OUT"
wc -l "$OUT"
