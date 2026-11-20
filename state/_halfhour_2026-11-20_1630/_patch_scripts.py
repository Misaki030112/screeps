from pathlib import Path
import re

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-20_1630")
SRC = Path("/workspace/screeps/state/_halfhour_2026-11-20_1600")
OLD = "_halfhour_2026-11-20_1600"
NEW = "_halfhour_2026-11-20_1630"

text = (DIR / "history_backfill_first_attempt.txt").read_text()
pat = re.compile(r"ok  (W\d+N\d+)@(\d+) ticks=\d+ ts=(\d+)")
by = {}
for m in pat.finditer(text):
    room, base, ts = m.group(1), int(m.group(2)), int(m.group(3))
    by.setdefault(base, {})[room] = ts
print("parsed bases", sorted(by))
for b in sorted(by):
    print(b, {k: by[b][k] for k in sorted(by[b])})

W46 = {b: rooms["W46N8"] for b, rooms in by.items() if "W46N8" in rooms}
MIN_ALL = {b: min(rooms.values()) for b, rooms in by.items()}
min_rooms = {b: min(rooms, key=rooms.get) for b, rooms in by.items()}
print("W46", W46)
print("MIN_ALL", MIN_ALL, "via", min_rooms)

TICK_S_FIRST = (MIN_ALL[84375900] - MIN_ALL[84375800]) / 1000.0 / 100
print("TICK_S_FIRST", TICK_S_FIRST)

def repl_dict(src, name, mapping, comments):
    lines = [name + " = {"]
    for b in sorted(mapping):
        c = comments.get(b, "")
        lines.append("    %s: %s,%s" % (b, mapping[b], c))
    lines.append("}")
    newblk = chr(10).join(lines)
    pat = re.compile(name + r" = \{.*?\n\}", re.S)
    if not pat.search(src):
        raise SystemExit(name + " block not found")
    return pat.sub(newblk, src, count=1)

t = (SRC / "tick_s_check.py").read_text()
t = t.replace(OLD, NEW)
t = repl_dict(t, "W46", W46, {})
t = repl_dict(t, "MIN_ALL", MIN_ALL, {b: "  # " + min_rooms[b] for b in MIN_ALL})
t = t.replace("TMIN, TMAX = 84375401, 84376100", "TMIN, TMAX = 84375801, 84376500")
t2, n = re.subn(
    r"TICK_S_FIRST = \(MIN_ALL\[84375500\] - MIN_ALL\[84375400\]\) / 1000\.0 / 100  # script printed 4\.146",
    "TICK_S_FIRST = (MIN_ALL[84375900] - MIN_ALL[84375800]) / 1000.0 / 100  # script printed 4.100, exact " + str(TICK_S_FIRST),
    t,
    count=1,
)
if n != 1:
    raise SystemExit("TICK_S_FIRST replace failed n=%s" % n)
t = t2
t = t.replace("GT_FIRST = 84376148", "GT_FIRST = 84376577")
t2, n = re.subn(
    r"TS_REALIGNED_FIRST = 0  #.*",
    "TS_REALIGNED_FIRST = 112  # first-pass realign moved 112 (inserted=3034, already_in_db=22754, missing_chunks=1 W46N8@84376100)",
    t,
    count=1,
)
if n != 1:
    raise SystemExit("TS_REALIGNED_FIRST replace failed n=%s" % n)
t = t2
t2, n = re.subn(
    r"PREV_LATER_MEAN = .*",
    "PREV_LATER_MEAN = 4.157911666666666  # 16:00 half-hour tick_s_in_use (all_mean)",
    t,
    count=1,
)
if n != 1:
    raise SystemExit("PREV_LATER_MEAN replace failed n=%s" % n)
t = t2
(DIR / "tick_s_check.py").write_text(t)

c = (SRC / "backfill_confirm.py").read_text().replace(OLD, NEW)
c2, n = re.subn(r"IN_WINDOW = \[.*?\]  #.*", "IN_WINDOW = [(\"W46N8\", 84376100)]  # first pass missing_chunks=1 W46N8@84376100 leftover official 404", c, count=1)
if n != 1:
    raise SystemExit("IN_WINDOW replace failed n=%s lines=%s" % (n, [ln for ln in c.splitlines() if "IN_WINDOW" in ln][:5]))
c = c2
c2, n = re.subn(r"AGED = \[.*?\]", "AGED = []", c, count=1)
if n != 1:
    raise SystemExit("AGED replace failed n=%s" % n)
c = c2
c2, n = re.subn(r"TICK_S = 4\.14626", "TICK_S = " + str(TICK_S_FIRST), c, count=1)
if n != 1:
    raise SystemExit("TICK_S replace failed n=%s" % n)
c = c2
(DIR / "backfill_confirm.py").write_text(c)

j = (SRC / "backfill_just_published.py").read_text().replace(OLD, NEW)
j = j.replace("JUST_BASE = 84376100", "JUST_BASE = 84376500")
j = j.replace(
    "Fetch just-published official history base 84376100 once game.time is safely past 84376240.",
    "Fetch just-published official history base 84376500 once game.time is safely past 84376640.",
)
(DIR / "backfill_just_published.py").write_text(j)

cv = (SRC / "coverage.py").read_text().replace(OLD, NEW)
cv = cv.replace("TMIN, TMAX = 84375401, 84376100", "TMIN, TMAX = 84375801, 84376500")
cv2, n = re.subn(r"IN_WINDOW_404 = set\(\)  #.*", "IN_WINDOW_404 = {(\"W46N8\", 84376100)}  # first pass missing_chunks=1 leftover official 404", cv, count=1)
if n != 1:
    raise SystemExit("IN_WINDOW_404 replace failed n=%s" % n)
cv = cv2
(DIR / "coverage.py").write_text(cv)

print("wrote scripts ok")
for name in ("tick_s_check.py", "backfill_confirm.py", "backfill_just_published.py", "coverage.py"):
    pth = DIR / name
    print(name, "bytes", pth.stat().st_size)
    for ln in pth.read_text().splitlines():
        if any(s in ln for s in ("DIR =", "JUST_BASE", "TMIN", "IN_WINDOW", "GT_FIRST", "TICK_S_FIRST", "TICK_S =", "PREV_LATER", "TS_REALIGNED", "WAIT_UNTIL")):
            print(" ", ln[:200])
