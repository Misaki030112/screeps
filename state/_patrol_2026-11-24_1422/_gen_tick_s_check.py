#!/usr/bin/env python3
from pathlib import Path
import json, py_compile

d = Path("/workspace/screeps/state/_patrol_2026-11-24_1422")
parsed = json.loads((d / "backfill_first_parsed.json").read_text())
src = Path("/workspace/screeps/state/_halfhour_2026-11-24_1100/tick_s_check.py").read_text()
src = src.replace(
    'DIR = ROOT / "state" / "_halfhour_2026-11-24_1100"',
    'DIR = ROOT / "state" / "_patrol_2026-11-24_1422"',
)
start = src.find("# Official chunk timestamps")
end = src.find(chr(10) + "def intervals")
assert start != -1 and end != -1, (start, end)

W46 = {int(k): v for k, v in parsed["W46"].items()}
MIN_ALL = {int(k): v for k, v in parsed["MIN_ALL"].items()}
MIN_ALL_ROOM = {}
for k, v in parsed["MIN_ALL_ROOM"].items():
    MIN_ALL_ROOM[int(k) if str(k).isdigit() else k] = v
bases = sorted(MIN_ALL)
tmin, tmax = parsed["TMIN"], parsed["TMAX"]
first_exact = parsed["tick_s_first_exact"]
gt = 84456226
prev = 4.51214
b0, b1 = bases[0], bases[1]

def lit_w46(mp):
    lines = ["W46 = {"]
    for b in sorted(mp):
        lines.append("    %s: %s," % (b, mp[b]))
    lines.append("}")
    return chr(10).join(lines)

def lit_min(mp, rooms):
    lines = ["MIN_ALL = {"]
    for b in sorted(mp):
        room = rooms.get(b) or rooms.get(str(b)) or ""
        lines.append("    %s: %s,  # %s" % (b, mp[b], room))
    lines.append("}")
    return chr(10).join(lines)

nl = chr(10)
header = (
    "# Official chunk timestamps printed by history_backfill.py" + nl
    + "# First pass --minutes 210 at game.time=%s; published_bases 84453000..84456100;" % gt + nl
    + "# reconstructed %s..%s (3200). first pass 156/160 official GETs 200," % (tmin, tmax) + nl
    + "# missing_chunks=4 W46N8@84454100, W47N7@84454200, W46N8@84454300," + nl
    + "# W47N8@84455300 (all still-untold this 3h). inserted=31267" + nl
    + "# already_in_db=115199; first-pass ts_realigned=96899" + nl
    + "# (first-pass used printed tick_s=4.272)." + nl
    + "# tick_s printed 4.272, exact first-interval %.5f" % first_exact + nl
    + "# (min-all %s..%s). prev tick_s_in_use from quiet 1400: %.5f." % (b0, b1, prev) + nl
    + lit_w46(W46) + nl
    + lit_min(MIN_ALL, MIN_ALL_ROOM) + nl
    + "TMIN, TMAX = %s, %s" % (tmin, tmax) + nl
    + 'ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")' + nl
    + "TICK_S_FIRST = (MIN_ALL[%s] - MIN_ALL[%s]) / 1000.0 / %s  # printed 4.272, exact %.5f" % (b1, b0, b1-b0, first_exact) + nl
    + "GT_FIRST = %s" % gt + nl
    + "TS_REALIGNED_FIRST = 96899" + nl
    + "PREV_LATER_MEAN = %s  # tick_s_in_use from quiet 1400 half-hour" % prev + nl + nl + nl
)
new = src[:start] + header + src[end+1:]
out = d / "tick_s_check.py"
out.write_text(new)
py_compile.compile(str(out), doraise=True)
print("wrote", out, "lines", new.count(nl)+1)
for line in new.splitlines()[:80]:
    if any(s in line for s in ("DIR ", "TMIN", "TMAX", "TICK_S_FIRST", "GT_FIRST", "PREV_LATER", "1129", "0820")):
        print(line)
