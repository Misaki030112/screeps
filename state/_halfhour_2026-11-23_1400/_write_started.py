from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
d = Path("/workspace/screeps/state/_halfhour_2026-11-23_1400")
now = datetime.now(ZoneInfo("Asia/Hong_Kong"))
d.joinpath("started_at.txt").write_text(now.strftime("%Y-%m-%dT%H:%M:%S+0800") + "\n")
d.joinpath("started_at.epoch.txt").write_text(str(int(now.timestamp())) + "\n")
d.joinpath("started_at_human.txt").write_text(now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong") + "\n")
print("started_at", now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong"))
