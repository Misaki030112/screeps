#!/usr/bin/env python3
from pathlib import Path
p = Path("/workspace/screeps/state/iterations.log")
line = Path("/workspace/screeps/state/_patrol_2026-11-23_0516/iterations_line.txt").read_text().rstrip() + "\n"
text = p.read_text()
if "2026-11-23T05:38+08 3h patrol" in text:
    print("already appended, skip")
else:
    if not text.endswith("\n"):
        text += "\n"
    p.write_text(text + "\n" + line)
    print("appended", len(line), "final_size", p.stat().st_size)
