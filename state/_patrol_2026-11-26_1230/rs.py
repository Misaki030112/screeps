import sys; sys.path.insert(0,'tools'); import db
c=db.connect()
for t in ('room_stats','creep_ticks','creep_cpu'):
    print(t, c.execute(f'select max(tick), max(ts), now()-max(ts) from {t}').fetchone())
tip=c.execute("select max(tick) from room_stats where room='W47N8'").fetchone()[0]
for room in ('W46N8','W47N8'):
    rows=c.execute("select tick, ts, rcl, progress, storage, cpu, bucket, commit from room_stats where room=%s and tick>=%s order by tick",(room,tip-2600)).fetchall()
    print(room, len(rows), 'first', rows[0][:8], 'last', rows[-1][:8])
    # windows
    for w in (2400,1200,800,500,200,100):
        sub=[r for r in rows if r[0]>=rows[-1][0]-w]
        a,b=sub[0],sub[-1]; dt=b[0]-a[0]
        if dt>0 and a[3] is not None and b[3] is not None and a[2]==b[2]:
            print(f'  last{w}: span {dt} upg {(b[3]-a[3])/dt:.2f} e/t  stor {a[4]}->{b[4]} ({(b[4]-a[4])/dt:+.2f}/t)')
    st=[r[4] for r in rows]; print('  stor min',min(st),'max',max(st))
    cp=[r[5] for r in rows if r[5] is not None]; bk=[r[6] for r in rows if r[6] is not None]
    if cp: print('  cpu avg %.1f max %.1f bucket min %s'%(sum(cp)/len(cp),max(cp),min(bk)))
    print('  commits', sorted(set(r[7] for r in rows if r[7])))
