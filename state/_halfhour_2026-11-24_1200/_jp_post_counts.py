import json, sys
from pathlib import Path
sys.path.insert(0, "tools")
import db

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-24_1200")
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
pre = json.loads((DIR / "just_published_pre_counts.json").read_text())
base = 84454200
t0, t1 = base + 1, base + 100
script = {"W46N8": 901, "W47N8": 36, "W45N8": 496, "W45N7": 383, "W47N7": 0}  # JP tool inserted
post = {}
nl = chr(10)
with db.connect() as c:
    for room in ROOMS:
        d, mn, mx, n = c.execute(
            "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
            (room, t0, t1),
        ).fetchone()
        post[room] = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}
        pr = pre[room]
        actual_rows = int(n or 0) - int(pr.get("rows") or 0)
        print(
            f"{room} pre distinct={pr.get('distinct')} rows={pr.get('rows')} range={pr.get('min')}..{pr.get('max')}  "
            f"post distinct={d} rows={n} range={mn}..{mx}  "
            f"script={script[room]} actual_rows={actual_rows}"
        )
(DIR / "just_published_post_counts.json").write_text(json.dumps(post, indent=2) + nl)
print("script_total", sum(script.values()), "actual_total", sum(post[r]["rows"] - int(pre[r].get("rows") or 0) for r in ROOMS))
print("wrote post_counts")
