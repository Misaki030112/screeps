#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DIR = Path("/workspace/screeps/state/_halfhour_2026-11-23_1330")
ROOT = Path("/workspace/screeps")
HK = ZoneInfo("Asia/Hong_Kong")
now = datetime.now(HK)
wrap_at = now.strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
wrap_at_iso = now.strftime("%Y-%m-%dT%H:%M:%S+0800")

pre = json.loads((DIR / "just_published_pre_counts_first.json").read_text())
snap = json.loads((DIR / "wrapup_snap.json").read_text())
jp_post = snap["jp_post"]
(DIR / "just_published_post_counts.json").write_text(json.dumps(jp_post, indent=2) + "\n")
script_by = {"W46N8": 967, "W47N8": 444, "W45N8": 656, "W45N7": 281, "W47N7": 592}
actual_by = {}
for room, post in jp_post.items():
    actual_by[room] = int(post["rows"] or 0) - int(pre[room]["rows"] or 0)
script_total = sum(script_by.values())
actual_total = sum(actual_by.values())
if actual_total != 2590:
    raise SystemExit("unexpected just_actual %s %s" % (actual_total, actual_by))

sys.path.insert(0, str(ROOT / "tools"))
import db
tips = {}
with db.connect() as c:
    for table in ("room_stats", "creep_cpu", "path_arrivals"):
        tips[table] = c.execute("SELECT max(tick) FROM %s" % table if False else f"SELECT max(tick) FROM {table}").fetchone()[0]

live = json.loads((ROOT / "metrics/live.json").read_text())
st = live.get("stats") if isinstance(live.get("stats"), dict) else {}
rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
window_db = json.dumps(snap["window_db"], separators=(",", ":"))
jp_post_s = json.dumps(jp_post, separators=(",", ":"))
inserted_total = 9873 + 1440 + actual_total

first = (DIR / "history_backfill.txt").read_text().rstrip() + "\n"
wrap_path = DIR / "wrap_body.txt"
wrap_body = wrap_path.read_text().format(
    wrap_at=wrap_at,
    script_total=script_total,
    actual_total=actual_total,
    inserted_total=inserted_total,
    window_db=window_db,
    jp_post=jp_post_s,
    script_by=script_by,
    actual_by=actual_by,
    tips_room=tips["room_stats"],
    tips_cpu=tips["creep_cpu"],
    tips_path=tips["path_arrivals"],
    listener=snap["listener"],
    rot=rot,
    yield_absent=snap["yield_absent"],
)
now_txt = first + wrap_body
(DIR / "_halfhour_backfill_now.txt").write_text(now_txt)
(DIR / "history_backfill_now.txt").write_text(now_txt)

verify_path = DIR / "verify_body.txt"
verify = verify_path.read_text().format(
    wrap_at=wrap_at,
    inserted_total=inserted_total,
    actual_total=actual_total,
)
(DIR / "_halfhour_backfill_verify.txt").write_text(verify)
(DIR / "verify.txt").write_text(verify)
(DIR / "wrap_at.txt").write_text(wrap_at_iso + "\n")
(DIR / "wrap_at_human.txt").write_text(wrap_at + "\n")
(DIR / "wrapup_run.txt").write_text("wrap %s ok_quiet=True wrote now+verify\n" % wrap_at)
print("wrap_at", wrap_at)
print("just_script", script_total, "just_actual", actual_total, "total", inserted_total)
print("tips", tips)
print("rot", rot)
print("ok")
