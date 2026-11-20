#!/usr/bin/env python3
from pathlib import Path
p = Path("/workspace/screeps/state/_halfhour_2026-11-21_0730/_gen_scripts.py")
lines = p.read_text().splitlines(True)
for i, line in enumerate(lines):
    if "PREV_LATER_MEAN = 4.22596" in line:
        print("line", i + 1, "repr=", repr(line))
        lines[i] = '    f"PREV_LATER_MEAN = 4.22596  # 07:00 half-hour tick_s_in_use (all_mean)\\n\\n\\n"\n'
        print("now", repr(lines[i]))
        break
else:
    raise SystemExit("line not found")
p.write_text("".join(lines))
print("fixed")
