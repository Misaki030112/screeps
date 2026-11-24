#!/usr/bin/env python3
import json
from pathlib import Path
rows = json.loads(Path("state/_review12h_2026-11-24_08/sql_stor_stretches.txt.json").read_text())
chunks = []
for kind in ["under15", "ge20", "ge25", "ge30", "ge40"]:
    for room in ["W46N8", "W47N8"]:
        sub = [r for r in rows if r["room"] == room and r["kind"] == kind]
        sub.sort(key=lambda r: -(r.get("tick_span") or 0))
        chunks.append("===== %s %s n=%d =====" % (room, kind, len(sub)))
        for r in sub[:15]:
            ts0 = str(r["ts0"])[11:19]
            ts1 = str(r["ts1"])[11:19]
            chunks.append("%s-%s span=%s n=%s stor %s-%s %s-%s" % (
                r["t0"], r["t1"], r["tick_span"], r["n"], r["stor_min"], r["stor_max"], ts0, ts1))
        if len(sub) > 15:
            chunks.append("... +%d more" % (len(sub) - 15))
        chunks.append("")
text = chr(10).join(chunks) + chr(10)
Path("state/_review12h_2026-11-24_08/stretches_sorted.txt").write_text(text)
print(text)
