from tools.db import connect

c = connect()
with c.cursor() as cur:
    cur.execute(
        "select column_name, data_type from information_schema.columns "
        "where table_name='creep_ticks' order by ordinal_position"
    )
    print("creep_ticks columns:")
    for x in cur.fetchall():
        print(" ", x)

with c.cursor() as cur:
    cur.execute("select * from creep_ticks where creep='defender84418409' order by tick, ts limit 1")
    desc = [d.name for d in cur.description]
    print("desc", desc)
    print("first", cur.fetchone())
    cur.execute("select * from creep_ticks where creep='defender84418409' order by tick desc, ts desc limit 1")
    print("last", cur.fetchone())
