import sys; sys.path.insert(0,'tools'); import db
c=db.connect()
rows=c.execute("select creep, role, x, y, hits, state from creep_ticks where tick=84490000 and room='W47N8' order by creep").fetchall()
for r in rows[:100]: print(r)
