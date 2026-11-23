#!/bin/bash
DIR=/workspace/screeps/state/_halfhour_2026-11-24_0330
stamp() {
  local step="$1" kind="$2"
  python3 - "$DIR" "$step" "$kind" <<'PY'
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
d = Path(sys.argv[1])
step, kind = sys.argv[2], sys.argv[3]
now = datetime.now(ZoneInfo("Asia/Hong_Kong"))
d.joinpath(f"{step}_{kind}.txt").write_text(str(int(now.timestamp())) + "\n")
d.joinpath(f"{step}_{kind}_human.txt").write_text(now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong") + "\n")
print(now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"), step, kind)
PY
}

# also support being sourced: first arg is command
if [ "${1:-}" = "stamp" ]; then
  stamp "$2" "$3"
fi
