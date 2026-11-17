#!/bin/bash
# Health snapshot for half-hour history backfill. Read-only besides writing pre.txt.
set -e
ROOT=/workspace/screeps
OUT=$ROOT/state/_halfhour_2026-11-17_1030/pre.txt
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
    print('creep_ticks since tick 84313601 (prev 10:00 official window start):')
    rows=c.execute("""
      SELECT room, min(tick), max(tick), count(*), count(distinct tick)
      FROM creep_ticks WHERE tick>=84313601
      GROUP BY room ORDER BY 1
    """).fetchall()
    for r in rows:
        print(' ', r)
    print('creep_ticks since tick 84314301 (after prev 10:00 reconstructed end):')
    rows=c.execute("""
      SELECT room, min(tick), max(tick), count(*), count(distinct tick)
      FROM creep_ticks WHERE tick>=84314301
      GROUP BY room ORDER BY 1
    """).fetchall()
    for r in rows:
        print(' ', r)
    if not rows:
        print('  (none yet)')
    for table in ('creep_cpu','path_arrivals'):
        row=c.execute(f"select max(tick), max(ts), count(*) from {table} where tick>=84313601").fetchone()
        print(f'{table} since tick 84313601:', row)
        row=c.execute(f"""
          select min(tick), max(tick), count(*) from {table}
          where tick >= (select max(tick)-200 from {table})
        """).fetchone()
        print(f'{table} last200ticks:', row)
        row=c.execute(f"""
          select min(tick), max(tick), count(*), min(ts), max(ts)
          from {table}
          where ts >= '2026-11-17 08:04:17+08'
        """).fetchone()
        print(f'{table} ingested after 08:04:17 reconnect (post 07:43:34-08:04:17 freeze):', row)
        row=c.execute(f"""
          select min(tick), max(tick), count(*), min(ts), max(ts)
          from {table}
          where ts >= '2026-11-17 09:25:37+08'
        """).fetchone()
        print(f'{table} ingested after 09:25:37 reconnect (post 09:17:21-09:25:37 freeze):', row)
        row=c.execute(f"""
          select min(tick), max(tick), count(*), min(ts), max(ts)
          from {table}
          where ts >= '2026-11-17 09:58:12+08'
        """).fetchone()
        print(f'{table} ingested after 09:58:12 reconnect (post 09:43:21-09:58:12 freeze):', row)
        row=c.execute(f"""
          select min(tick), max(tick), count(*), min(ts), max(ts)
          from {table}
          where ts >= '2026-11-17 09:25:37+08' and ts < '2026-11-17 09:43:21+08'
        """).fetchone()
        print(f'{table} ingested 09:25:37..09:43:21 (between 09:25 and 09:58 reconnects):', row)
        row=c.execute(f"""
          select min(tick), max(tick), count(*), min(ts), max(ts)
          from {table}
          where ts >= '2026-11-17 08:04:17+08' and ts < '2026-11-17 09:17:21+08'
        """).fetchone()
        print(f'{table} ingested 08:04:17..09:17:21 (between 08:04 and 09:25 reconnects):', row)
        row=c.execute(f"""
          select min(tick), max(tick), count(*), min(ts), max(ts)
          from {table}
          where ts >= '2026-11-17 07:26:06+08' and ts < '2026-11-17 07:43:34+08'
        """).fetchone()
        print(f'{table} ingested 07:26:06..07:43:34 (between 07:26 and 08:04 reconnects):', row)
        row=c.execute(f"""
          select min(tick), max(tick), count(*), min(ts), max(ts)
          from {table}
          where ts >= '2026-11-17 07:26:06+08'
        """).fetchone()
        print(f'{table} ingested after 07:26:06 reconnect (includes later freeze):', row)
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
            for a,b,n in gaps:
                print(f'  room_stats gap {a}..{b} ({n} ticks)')
        else:
            print('  no room_stats gaps since 84305000')
    else:
        print('  (no room_stats rows since 84305000)')
    print('room_stats / live ingest since last wrapup tip 84314300 (hunt NEW freeze after 10:00):')
    rs=c.execute("""
      SELECT tick, ts FROM room_stats WHERE tick>=84314300 ORDER BY 1
    """).fetchall()
    if rs:
        ticks=[r[0] for r in rs]
        print(f'  room_stats since 84314300: n={len(ticks)} min={ticks[0]} max={ticks[-1]} first_ts={rs[0][1]} last_ts={rs[-1][1]}')
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
            print('  no room_stats gaps since 84314300')
    else:
        print('  (no room_stats rows since 84314300)')
    print('creep_ticks coverage around expected new freeze and prior bands:')
    tip=c.execute("select max(tick) from room_stats").fetchone()[0]
    for lo,hi,label in (
        (84314300, tip or 84317000, f'post-10:00 wrapup tip band 84314300..{tip}'),
        (84314141, 84314339, 'prior 09:43 freeze band 84314141..84314339'),
        (84313811, 84313929, 'prior 09:17 freeze band 84313811..84313929'),
        (84312611, 84312889, 'prior 07:43 freeze band 84312611..84312889'),
        (84312221, 84312399, 'prior 07:13 freeze band 84312221..84312399'),
        (84311861, 84312069, 'prior 06:44 freeze band 84311861..84312069'),
        (84311431, 84311519, 'prior 06:10 freeze band 84311431..84311519'),
        (84311131, 84311269, 'prior 05:47 freeze band 84311131..84311269'),
        (84311041, 84311069, 'prior 05:41 pingpong band 84311041..84311069'),
        (84310921, 84310949, 'prior 05:30 freeze unpublished band 84310921..84310949'),
        (84310671, 84310779, 'prior 05:11 freeze published band 84310671..84310779'),
        (84310281, 84310529, 'prior 04:41 freeze published+unpub band 84310281..84310529'),
        (84309881, 84310079, 'prior 04:09 freeze published band 84309881..84310079'),
        (84309601, 84309729, 'prior 03:47 freeze published+unpub band 84309601..84309729'),
        (84309201, 84309249, 'prior 03:16 freeze band 84309201..84309249'),
        (84308771, 84309029, 'prior 02:42 freeze band 84308771..84309029'),
        (84308421, 84308469, 'prior 02:14 freeze band 84308421..84308469'),
        (84307931, 84308269, 'prior 01:34 freeze band 84307931..84308269'),
        (84307621, 84307799, 'prior 01:09 freeze band 84307621..84307799'),
        (84307351, 84307539, 'prior 00:47 freeze band 84307351..84307539'),
        (84306961, 84307069, 'prior 00:16 freeze band 84306961..84307069'),
        (84306571, 84306809, 'prior 23:44 freeze band 84306571..84306809'),
        (84306261, 84306349, 'prior 23:18 freeze band 84306261..84306349'),
        (84305871, 84306079, 'prior 22:47 freeze band 84305871..84306079'),
        (84305691, 84305719, 'prior 22:33 freeze band 84305691..84305719'),
        (84305401, 84305529, 'prior 22:09 freeze band 84305401..84305529'),
        (84305031, 84305249, 'prior 21:39 freeze band 84305031..84305249'),
        (84304671, 84304829, 'prior 21:11 freeze band 84304671..84304829'),
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
        ('W47N8', 84314001, 84314100, 'W47N8 hole 84314001..84314100 (prev in-window leftover official 404 @84314000, 49 live / 51 empty)'),
        ('W46N8', 84313201, 84313300, 'W46N8 hole 84313201..84313300 (leftover official 404 @84313200, 96 live / 4 empty)'),
        ('W47N8', 84312301, 84312400, 'W47N8 84312301..84312400 (patrol first-pass 404, recovered 07:29)'),
        ('W45N8', 84312301, 84312400, 'W45N8 84312301..84312400 (patrol first-pass 404, recovered 07:29)'),
        ('W47N7', 84312301, 84312400, 'W47N7 84312301..84312400 (patrol first-pass 404, recovered 07:29)'),
        ('W46N8', 84310501, 84310600, 'W46N8 hole 84310501..84310600 (prev official 404 @84310500, 11 live)'),
        ('W47N7', 84309001, 84309100, 'W47N7 hole 84309001..84309100 (leftover official 404 @84309000)'),
        ('W45N8', 84309101, 84309200, 'W45N8 hole 84309101..84309200 (leftover official 404 @84309100)'),
        ('W45N8', 84306501, 84306600, 'W45N8 hole 84306501..84306600 (leftover official 404 @84306500)'),
        ('W45N7', 84305101, 84305200, 'W45N7 hole 84305101..84305200 (leftover official 404 @84305100)'),
        ('W47N8', 84304701, 84304800, 'W47N8 hole 84304701..84304800 (leftover official 404 @84304700)'),
        ('W45N7', 84303901, 84304000, 'W45N7 hole 84303901..84304000 (leftover official 404 @84303900)'),
        ('W45N8', 84302201, 84302300, 'W45N8 hole 84302201..84302300 (leftover official 404 @84302200)'),
        ('W47N8', 84300901, 84301000, 'W47N8 leftover 84300901..84301000 (74 live + holes)'),
        ('W45N8', 84300901, 84301000, 'W45N8 leftover 84300901..84301000 (7 live + 93 empty)'),
        ('W45N8', 84300001, 84300100, 'W45N8 leftover 84300001..84300100 (26 live + 74 empty)'),
        ('W47N8', 84298001, 84298100, 'W47N8 leftover 84298001..84298100 (still empty)'),
        ('W47N8', 84297201, 84297300, 'W47N8 leftover 84297201..84297300 (already live-filled)'),
        ('W47N7', 84296501, 84296600, 'W47N7 leftover 84296501..84296600 (still empty)'),
        ('W45N8', 84295901, 84296000, 'W45N8 leftover 84295901..84296000 (still empty)'),
        ('W45N7', 84295801, 84295900, 'W45N7 leftover 84295801..84295900 (still empty)'),
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
