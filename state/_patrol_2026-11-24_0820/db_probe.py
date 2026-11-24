import sys
sys.path.insert(0, "/workspace/screeps/tools")
import db
c = db.connect()

print("=== tables incid|threat|hostil|core|pause|event ===")
rows = c.execute("SELECT tablename FROM pg_tables WHERE schemaname=%s AND tablename ~ %s ORDER BY 1", ("public", "incid|threat|hostil|core|pause|event")).fetchall()
for t in rows:
    print("table", t[0])

print("=== room_stats columns ===")
cols = c.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position", ("room_stats",)).fetchall()
for r in cols:
    print(r[0], r[1])

print("=== incidents? ===")
try:
    names = [d.name for d in c.execute("SELECT * FROM incidents LIMIT 0").description]
    print("cols", names)
    rows = c.execute("SELECT * FROM incidents WHERE tick>=84446200 ORDER BY tick").fetchall()
    print("n", len(rows))
    for r in rows:
        print(dict(zip(names, r)))
except Exception as e:
    print("incidents ERR", type(e).__name__, e)
