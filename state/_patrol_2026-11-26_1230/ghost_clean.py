"""Delete ghost creep_ticks rows left by the pre-fix history_backfill merge (dead creeps carried forward).
A creep named <role><spawnTick> cannot exist after spawnTick + spawn time (<=150) + lifespan (1500; 600 with CLAIM).
Margin +50. No renewCreep in src. Usage: ghost_clean.py [--apply]"""
import sys; sys.path.insert(0,'tools'); import db
APPLY='--apply' in sys.argv
LO=84440000
where = """tick >= %s AND creep ~ '[0-9]{8}$' AND
 tick > (substring(creep from '([0-9]{8})$'))::bigint + CASE WHEN role IN ('reserver','reserve','claimer') THEN 800 ELSE 1700 END"""
c=db.connect()
print('candidates by room', c.execute(f"select room, count(*), count(distinct creep), min(tick), max(tick) from creep_ticks where {where} group by room order by 1",(LO,)).fetchall())
print('by role', c.execute(f"select role, count(*) from creep_ticks where {where} group by role order by 2 desc limit 12",(LO,)).fetchall())
if APPLY:
    cur=c.execute(f"delete from creep_ticks where {where}",(LO,)); print('deleted', cur.rowcount)
    try: c.commit()
    except Exception: pass
for t in (84470000, 84490000, 84492000, 84493400):
    print(t, c.execute("select count(*) from creep_ticks where tick=%s",(t,)).fetchone())
