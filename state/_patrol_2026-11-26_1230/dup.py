import sys; sys.path.insert(0,'tools'); import db
c=db.connect()
print(c.execute("select column_name from information_schema.columns where table_name='creep_ticks'").fetchall())
for t in (84470000, 84490000, 84492000, 84493000):
    print(t, c.execute("select count(*), count(distinct creep), count(distinct room) from creep_ticks where tick=%s",(t,)).fetchone())
print(c.execute("select room, count(*) from creep_ticks where tick=84490000 group by room").fetchall())
