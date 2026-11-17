#!/bin/bash
# Health snapshot for half-hour history backfill. Read-only besides writing pre.txt.
set -e
ROOT=/workspace/screeps
OUT=$ROOT/state/_halfhour_2026-11-17_1630/pre.txt
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
echo "==== recent listener log (last 40 lines) ===="
tail -n 40 metrics/listener.out
echo "==== recent errors / box pauses ===="
echo "---- box_pauses last ----"
ls -la metrics/box_pauses.jsonl metrics/war_cmd_pause metrics/errors.log 2>/dev/null
echo "metrics/errors.log"
echo "---- errors.log last listener lines ----"
grep '\[listener\]' metrics/errors.log | tail -n 15
echo "==== HTTP ===="
curl -s -o /dev/null -w 'grafana :3000 -> %{http_code}\n' http://127.0.0.1:3000/ || true
curl -s -o /dev/null -w 'dashboard 127.0.0.1:8787 -> %{http_code}\n' http://127.0.0.1:8787/ || true
echo "---- box_pauses.jsonl last ----"
tail -n 20 metrics/box_pauses.jsonl
echo "==== concurrent processes of note ===="
pgrep -af 'history_backfill|exact2h|patrol_|war_cmd|war_pulse|creep_audit|q_rest' || true
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
    print('creep_ticks since tick 84318201 (prev 16:00 official window start):')
    rows=c.execute("""
      SELECT room, min(tick), max(tick), count(*), count(distinct tick)
      FROM creep_ticks WHERE tick>=84318201
      GROUP BY room ORDER BY 1
    """).fetchall()
    for r in rows:
        print(' ', r)
    print('creep_ticks since tick 84318901 (after prev 16:00 reconstructed end):')
    rows=c.execute("""
      SELECT room, min(tick), max(tick), count(*), count(distinct tick)
      FROM creep_ticks WHERE tick>=84318901
      GROUP BY room ORDER BY 1
    """).fetchall()
    for r in rows:
        print(' ', r)
    if not rows:
        print('  (none yet)')
    for table in ('creep_cpu','path_arrivals'):
        row=c.execute(f"select max(tick), max(ts), count(*) from {table} where tick>=84317901").fetchone()
        print(f'{table} since tick 84317901:', row)
        row=c.execute(f"""
          select min(tick), max(tick), count(*) from {table}
          where tick >= (select max(tick)-200 from {table})
        """).fetchone()
        print(f'{table} last200ticks:', row)
        # New reconnect after 16:19:45-16:24:50 freeze
        row=c.execute(f"""
          select min(tick), max(tick), count(*), min(ts), max(ts)
          from {table}
          where ts >= '2026-11-17 16:24:50+08'
        """).fetchone()
        print(f'{table} ingested after 16:24:50 reconnect (post 16:19:45-16:24:50 freeze):', row)
        # Reconnect after 15:44:05-16:01:24 freeze
        row=c.execute(f"""
          select min(tick), max(tick), count(*), min(ts), max(ts)
          from {table}
          where ts >= '2026-11-17 16:01:24+08'
        """).fetchone()
        print(f'{table} ingested after 16:01:24 reconnect (post 15:44:05-16:01:24 freeze):', row)
        # Prior reconnect after 15:16:17-15:20:45 freeze
        row=c.execute(f"""
          select min(tick), max(tick), count(*), min(ts), max(ts)
          from {table}
          where ts >= '2026-11-17 15:20:45+08'
        """).fetchone()
        print(f'{table} ingested after 15:20:45 reconnect (post 15:16:17-15:20:45 freeze):', row)
        row=c.execute(f"""
          select min(tick), max(tick), count(*), min(ts), max(ts)
          from {table}
          where ts >= '2026-11-17 15:03:38+08'
        """).fetchone()
        print(f'{table} ingested after 15:03:38 reconnect (post 14:49:29-15:03:38 freeze):', row)
        # Prior reconnect after 14:12:36-14:19:51 freeze
        row=c.execute(f"""
          select min(tick), max(tick), count(*), min(ts), max(ts)
          from {table}
          where ts >= '2026-11-17 14:19:51+08'
        """).fetchone()
        print(f'{table} ingested after 14:19:51 reconnect (post 14:12:36-14:19:51 freeze):', row)
        row=c.execute(f"""
          select min(tick), max(tick), count(*), min(ts), max(ts)
          from {table}
          where ts >= '2026-11-17 13:59:17+08'
        """).fetchone()
        print(f'{table} ingested after 13:59:17 reconnect (post 13:48:54-13:59:17 freeze):', row)
        row=c.execute(f"""
          select min(tick), max(tick), count(*), min(ts), max(ts)
          from {table}
          where ts >= '2026-11-17 13:26:04+08'
        """).fetchone()
        print(f'{table} ingested after 13:26:04 reconnect (post 13:18:38-13:26:04 freeze):', row)
        row=c.execute(f"""
          select min(tick), max(tick), count(*), min(ts), max(ts)
          from {table}
          where ts >= '2026-11-17 13:00:29+08'
        """).fetchone()
        print(f'{table} ingested after 13:00:29 reconnect (post 12:57:07-13:00:29 freeze):', row)
        row=c.execute(f"""
          select min(tick), max(tick), count(*), min(ts), max(ts)
          from {table}
          where ts >= '2026-11-17 12:54:44+08'
        """).fetchone()
        print(f'{table} ingested after 12:54:44 reconnect (post 12:52:46-12:54:44 freeze):', row)
    row=c.execute("select max(tick), max(ts) from room_stats").fetchone()
    print('room_stats tip:', row)
    row=c.execute("select max(tick), max(ts) from creep_ticks").fetchone()
    print('creep_ticks tip:', row)
    print('room_stats recent tick gaps since 84305000 (known freezes + new-gap hunt):')
    rs=c.execute("""
      SELECT tick FROM room_stats WHERE tick>=84305000 ORDER BY 1
    """).fetchall()
    ticks=[r[0] for r in rs]
    if ticks:
        print(f'  room_stats since 84305000: n={len(ticks)} min={ticks[0]} max={ticks[-1]}')
        gaps=[]
        prev=ticks[0]
        for t in ticks[1:]:
            if t>prev+1:
                gaps.append((prev+1, t-1, t-prev-1))
            prev=t
        if gaps:
            for a,b,n in gaps[-25:]:
                print(f'  room_stats gap {a}..{b} ({n} ticks)')
            if len(gaps)>25:
                print(f'  ... {len(gaps)-25} older gaps omitted, total_gaps={len(gaps)}')
        else:
            print('  no room_stats gaps since 84305000')
    else:
        print('  (no room_stats rows since 84305000)')
    print('room_stats / live ingest since last wrapup official tip 84318800 / room_stats tip 84319070 (hunt NEW freeze after 16:00):')
    rs=c.execute("""
      SELECT tick, ts FROM room_stats WHERE tick>=84318800 ORDER BY 1
    """).fetchall()
    if rs:
        ticks=[r[0] for r in rs]
        print(f'  room_stats since 84318800: n={len(ticks)} min={ticks[0]} max={ticks[-1]} first_ts={rs[0][1]} last_ts={rs[-1][1]}')
        gaps=[]
        prev=ticks[0]
        for t in ticks[1:]:
            if t>prev+1:
                gaps.append((prev+1, t-1, t-prev-1))
            prev=t
        if gaps:
            for a,b,n in gaps:
                print(f'  NEW room_stats gap {a}..{b} ({n} ticks)')
        else:
            print('  no room_stats gaps since 84318800')
    else:
        print('  (no room_stats rows since 84318800)')
    tip=c.execute("select max(tick) from room_stats").fetchone()[0]
    print('creep_ticks coverage around expected new freeze and prior bands:')
    for lo,hi,label in (
        (84318800, tip or 84319800, f'post-16:00 wrapup official tip band 84318800..{tip}'),
        (84319200, tip or 84319800, f'new 16:19 freeze hunt band 84319200..{tip}'),
        (84318741, 84318979, 'prior 15:44 freeze band 84318741..84318979'),
        (84318391, 84318459, 'prior 15:16 freeze band 84318391..84318459'),
        (84318051, 84318239, 'prior 14:49 freeze band 84318051..84318239'),
        (84317571, 84317679, 'prior 14:12 freeze band 84317571..84317679'),
        (84317271, 84317419, 'prior 13:48 freeze band 84317271..84317419'),
        (84316901, 84316999, 'prior 13:18 freeze band 84316901..84316999'),
        (84316561, 84316599, 'prior 12:52 freeze band 84316561..84316599'),
        (84316621, 84316679, 'prior 12:57 freeze band 84316621..84316679'),
        (84315741, 84315789, 'prior 11:48 freeze band 84315741..84315789'),
        (84315261, 84315469, 'prior 11:11 freeze band 84315261..84315469'),
        (84315041, 84315119, 'prior 10:54 freeze band 84315041..84315119'),
        (84314921, 84314959, 'prior 10:44 freeze band 84314921..84314959'),
        (84314501, 84314639, 'prior 10:11 freeze band 84314501..84314639'),
    ):
        for room in ('W46N8','W47N8','W45N8','W45N7','W47N7'):
            row=c.execute("""
              SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
              FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s
            """, (room, lo, hi)).fetchone()
            print(f'  {room} {label}:', row)
        row=c.execute("""
          SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
          FROM room_stats WHERE tick BETWEEN %s AND %s
        """, (lo, hi)).fetchone()
        print(f'  room_stats {label}:', row)
    if tip:
        print('creep_ticks coverage in last ~200 room_stats ticks (live dark-gap hunt):')
        t0=tip-200
        for room in ('W46N8','W47N8','W45N8','W45N7','W47N7'):
            row=c.execute("""
              SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
              FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s
            """, (room, t0, tip)).fetchone()
            print(f'  {room} {t0}..{tip}:', row)
        row=c.execute("""
          SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
          FROM room_stats WHERE tick BETWEEN %s AND %s
        """, (t0, tip)).fetchone()
        print(f'  room_stats {t0}..{tip}:', row)
    checks = [
        ('W46N8', 84318501, 84318568, 'W46N8 hole 84318501..84318568 (official 404 @84318500, 32 live 84318569..84318600)'),
        ('W45N8', 84318001, 84318100, 'W45N8 hole 84318001..84318100 (official 404 @84318000)'),
        ('W47N7', 84315101, 84315200, 'W47N7 hole 84315101..84315200 (official 404 @84315100)'),
        ('W45N8', 84314901, 84315000, 'W45N8 hole 84314901..84315000 (official 404 @84314900)'),
        ('W45N7', 84314501, 84314600, 'W45N7 hole 84314501..84314600 (official 404 @84314500)'),
        ('W47N8', 84314001, 84314100, 'W47N8 hole 84314001..84314100 (official 404 @84314000, 49 live / 51 empty)'),
        ('W46N8', 84313201, 84313300, 'W46N8 hole 84313201..84313300 (official 404 @84313200, 96 live / 4 empty)'),
        ('W46N8', 84310501, 84310600, 'W46N8 hole 84310501..84310600 (official 404 @84310500, 11 live)'),
        ('W47N7', 84309001, 84309100, 'W47N7 hole 84309001..84309100 (official 404 @84309000)'),
        ('W45N8', 84309101, 84309200, 'W45N8 hole 84309101..84309200 (official 404 @84309100)'),
        ('W45N8', 84306501, 84306600, 'W45N8 hole 84306501..84306600 (official 404 @84306500)'),
        ('W45N7', 84305101, 84305200, 'W45N7 hole 84305101..84305200 (official 404 @84305100)'),
        ('W47N8', 84304701, 84304800, 'W47N8 hole 84304701..84304800 (official 404 @84304700)'),
        ('W45N7', 84303901, 84304000, 'W45N7 hole 84303901..84304000 (official 404 @84303900)'),
        ('W45N8', 84302201, 84302300, 'W45N8 hole 84302201..84302300 (official 404 @84302200)'),
        ('W47N8', 84300901, 84301000, 'W47N8 leftover 84300901..84301000'),
        ('W45N8', 84300901, 84301000, 'W45N8 leftover 84300901..84301000'),
        ('W45N8', 84300001, 84300100, 'W45N8 leftover 84300001..84300100'),
        ('W47N8', 84298001, 84298100, 'W47N8 leftover 84298001..84298100'),
        ('W47N8', 84297201, 84297300, 'W47N8 leftover 84297201..84297300'),
        ('W47N7', 84296501, 84296600, 'W47N7 leftover 84296501..84296600'),
        ('W45N8', 84295901, 84296000, 'W45N8 leftover 84295901..84296000'),
        ('W45N7', 84295801, 84295900, 'W45N7 leftover 84295801..84295900'),
        ('W46N8', 84292001, 84292100, 'W46N8 aged leftover 84292001..84292100'),
    ]
    print('leftover official-404 hole status:')
    for room, lo, hi, label in checks:
        row=c.execute("""
          SELECT count(DISTINCT tick), min(tick), max(tick), count(*)
          FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s
        """, (room, lo, hi)).fetchone()
        print(f'  {label}:', row)
PY
} | tee "$OUT"
echo "wrote $OUT"
