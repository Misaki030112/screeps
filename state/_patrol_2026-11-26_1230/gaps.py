import sys; sys.path.insert(0,'tools'); import db
c=db.connect()
rows=c.execute("select tick, ts from room_stats where room='W46N8' and ts > now()-interval '52 hours' order by tick").fetchall()
print('rows',len(rows), rows[0], rows[-1])
prev=None
for t,ts in rows:
    if prev and t-prev[0]>40: print('gap', prev[0], prev[1].strftime('%m-%d %H:%M:%S'), '->', t, ts.strftime('%m-%d %H:%M:%S'), t-prev[0])
    prev=(t,ts)
r=c.execute("select date_trunc('hour',ts) h, count(*), min(tick), max(tick) from creep_ticks where ts>now()-interval '52 hours' group by 1 order by 1").fetchall()
for x in r: print(x[0].strftime('%m-%d %H'), x[1:])
