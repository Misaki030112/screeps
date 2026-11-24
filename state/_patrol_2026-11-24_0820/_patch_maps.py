#!/usr/bin/env python3
from pathlib import Path
import re, json

D = Path("/workspace/screeps/state/_patrol_2026-11-24_0820")
maps = (D / "tick_s_maps.py.txt").read_text()

# --- tick_s_check.py: fix DIR and splice maps ---
p = D / "tick_s_check.py"
t = p.read_text()
t = t.replace('"_patrol_2026-11-23_2321"', '"_patrol_2026-11-24_0522"')
# replace W46 = { ... }\nMIN_ALL = { ... } first two top-level dicts
# Find start of W46 = { at beginning of a line after the comments, and end of MIN_ALL dict
m = re.search(r"^W46 = \{", t, re.M)
if not m:
    raise SystemExit("no W46 in tick_s_check")
# find the second closing brace of top-level dicts: after MIN_ALL
m2 = re.search(r"^MIN_ALL = \{", t, re.M)
if not m2:
    raise SystemExit("no MIN_ALL")
# end of MIN_ALL dict: first line that is exactly }
# from m2, find matching close at indent 0
rest = t[m2.start():]
# naive: find "\n}\n" after MIN_ALL that is the dict close (line with only })
close = None
depth = 0
for i, ch in enumerate(rest):
    if ch == "{":
        depth += 1
    elif ch == "}":
        depth -= 1
        if depth == 0:
            close = i
            break
if close is None:
    raise SystemExit("no MIN_ALL close")
end = m2.start() + close + 1
new = t[:m.start()] + maps.strip() + "\n" + t[end:]
# header comments
new = re.sub(
    r"# Official chunk timestamps from history_backfill first pass --minutes 210\..*?# Run ONLY on this first-pass window \(do not point tick_s_check at a half-hour window\).",
    """# Official chunk timestamps from history_backfill first pass --minutes 210.
# reconstructed 84442901..84446100 (3200), game.time=84446176
# published_bases=84442900..84446000, inserted=35692 already_in_db=98486
# missing_chunks=7; first-pass realign committed ts_realigned=8600
# printed tick_s=4.268 (exact first-interval 4.26766, w46_first 4.26766)
# In-window leftover official 404s (retry at confirm; do not relabel already-told / still-untold as NEW):
#   already-told in 23:33 2321 USER_LOG: W47N7@84443300
#   still-untold from quiet 2330: W47N8@84443800
#   still-untold from quiet 0000: W46N8@84444200
#   still-untold from quiet 0030: W46N8@84444500
#   still-untold from quiet 0100: W45N7@84444900, W47N8@84445100
#   still-untold from quiet 0130: W46N8@84445500
# prev_later / tick_s_in_use carried from quiet 0130: 4.27742
# Run ONLY on this first-pass window (do not point tick_s_check at a half-hour window).""",
    new,
    count=1,
    flags=re.S,
)
p.write_text(new)
print("tick_s_check updated, DIR=", [line for line in new.splitlines() if "DIR" in line][:3])
print("W46 starts", new[new.find("W46 = {"):new.find("W46 = {")+80])

# --- coverage.py ---
c = (D / "coverage.py").read_text()
c2 = c.replace("TMIN, TMAX = 84440401, 84443600", "TMIN, TMAX = 84442901, 84446100")
c2 = c2.replace(
    'IN_WINDOW_404 = {("W47N7", 84440900), ("W45N7", 84441900), ("W47N7", 84443300)}',
    'IN_WINDOW_404 = {("W47N7", 84443300), ("W47N8", 84443800), ("W46N8", 84444200), ("W46N8", 84444500), ("W45N7", 84444900), ("W47N8", 84445100), ("W46N8", 84445500)}',
)
if c2 == c:
    print("WARNING coverage not changed")
    for i,line in enumerate(c.splitlines(),1):
        if "TMIN" in line or "IN_WINDOW" in line:
            print(i, line)
else:
    (D / "coverage.py").write_text(c2)
    print("coverage updated")

# --- backfill_confirm.py ---
b = (D / "backfill_confirm.py").read_text()
# replace IN_WINDOW and AGED lists
b2 = re.sub(
    r"IN_WINDOW = \[[^\]]*\]",
    """IN_WINDOW = [
    ("W47N7", 84443300),  # already told in 23:33 2321 USER_LOG; retry; do not relabel NEW
    ("W47N8", 84443800),  # still-untold from quiet 2330; retry; do not relabel NEW
    ("W46N8", 84444200),  # still-untold from quiet 0000; retry; do not relabel NEW
    ("W46N8", 84444500),  # still-untold from quiet 0030; retry; do not relabel NEW
    ("W45N7", 84444900),  # still-untold from quiet 0100; retry; do not relabel NEW
    ("W47N8", 84445100),  # still-untold from quiet 0100; retry; do not relabel NEW
    ("W46N8", 84445500),  # still-untold from quiet 0130; retry; do not relabel NEW
]""",
    b,
    count=1,
    flags=re.S,
)
b2 = re.sub(
    r"AGED = \[[^\]]*\]",
    """AGED = [
    ("W45N7", 84441900),  # already told in 23:33 2321 USER_LOG; aged out of 84442901; retry; do not relabel NEW
    ("W47N7", 84440900),  # already told in 20:44 2028 USER_LOG; aged out; retry; do not relabel NEW
]""",
    b2,
    count=1,
    flags=re.S,
)
b2 = b2.replace("TICK_S = 4.26544  # fallback tick_s_in_use from quiet 2300; load_tick_s overrides",
                "TICK_S = 4.27742  # fallback tick_s_in_use from quiet 0130; load_tick_s overrides")
if b2 == b:
    print("WARNING confirm lists not changed")
else:
    (D / "backfill_confirm.py").write_text(b2)
    print("confirm updated")

# --- just published base ---
jp = (D / "backfill_just_published.py").read_text()
jp2 = jp.replace("JUST_BASE = 84443600", "JUST_BASE = 84446100")
if jp2 == jp:
    print("WARNING jp base not changed; needles:")
    for i,line in enumerate(jp.splitlines(),1):
        if "JUST_BASE" in line or "8444" in line:
            print(i, line)
else:
    (D / "backfill_just_published.py").write_text(jp2)
    print("jp base updated")

# retry scripts may also have JUST_BASE
for name in ("backfill_just_published_retry.py", "backfill_just_published_retry2.py", "backfill_late_retry.py", "backfill_postjp_retry.py"):
    p = D / name
    if not p.exists():
        continue
    t = p.read_text()
    n = t.replace("JUST_BASE = 84443600", "JUST_BASE = 84446100")
    n = n.replace("84443600", "84446100")  # careful? only if leftover
    if n != t:
        p.write_text(n)
        print("updated", name)
    else:
        print("no change", name)
        for i,line in enumerate(t.splitlines(),1):
            if "BASE" in line or "84443" in line or "TMIN" in line or "TMAX" in line:
                print(" ", i, line)

print("done")
