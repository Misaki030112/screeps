#!/usr/bin/env python3
import sys, os
sys.path.insert(0, '/workspace/screeps/tools')
import history_backfill as hb
import db

chunks = [
    ('W47N7', 84272800),
    ('W47N8', 84273200),
    # leftover just outside / aged
    ('W45N7', 84272400),
    ('W47N7', 84269700),
]
c = db.connect()
out = []
def pr(*a):
    s=' '.join(str(x) for x in a)
    print(s, flush=True)
    out.append(s)

for room, base in chunks:
    lo, hi = base+1, base+100
    before = c.execute('SELECT count(*), count(distinct tick), min(tick), max(tick) FROM creep_ticks WHERE room=%s AND tick>=%s AND tick<=%s', (room, lo, hi)).fetchone()
    pr(f'GET {room}@{base} db_before rows={before[0]} distinct={before[1]} min={before[2]} max={before[3]}')
    data = hb.history_get(room, base)
    if data is None:
        pr('  still 404/empty')
        continue
    # insert via the same path as the tool if possible
    if hasattr(hb, 'ingest_chunk'):
        n = hb.ingest_chunk(room, base, data)
        pr('  ingest_chunk', n)
    else:
        # fall back: count official ticks
        ticks = data.get('ticks') or data
        pr('  got official keys', list(data)[:8] if isinstance(data, dict) else type(data), 'len', len(data) if hasattr(data,'__len__') else None)
        # try insert_chunk / apply
        for name in ('insert_chunk','store_chunk','load_chunk','write_chunk','ingest'):
            if hasattr(hb, name):
                pr('  calling', name)
                getattr(hb, name)(room, base, data)
                break
        else:
            pr('  no insert helper; not writing blindly')
    after = c.execute('SELECT count(*), count(distinct tick), min(tick), max(tick) FROM creep_ticks WHERE room=%s AND tick>=%s AND tick<=%s', (room, lo, hi)).fetchone()
    pr(f'  db_after rows={after[0]} distinct={after[1]} min={after[2]} max={after[3]}')

open('/workspace/screeps/state/_patrol_2026-11-15_0719/backfill_retry_404.txt','w').write('\n'.join(out)+'\n')
pr('DONE')
