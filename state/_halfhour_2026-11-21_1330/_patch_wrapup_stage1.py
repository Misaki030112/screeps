#!/usr/bin/env python3
from pathlib import Path
p = Path("/workspace/screeps/state/_halfhour_2026-11-21_1330/wrapup_write.py")
src = p.read_text()

def rep(old, new, label):
    global src
    n = src.count(old)
    if n != 1:
        raise SystemExit(f"{label}: found {n} occurrences, expected 1\n---OLD---\n{old[:300]}")
    src = src.replace(old, new)
    print("ok", label)

rep('"""Write 13:00 half-hour backfill wrap artifacts (quiet success)."""',
    '"""Write 13:30 half-hour backfill wrap artifacts (quiet success)."""',
    "docstring")

rep("WIN_TMIN, WIN_TMAX = 84393201, 84393900",
    "WIN_TMIN, WIN_TMAX = 84393701, 84394400",
    "WIN")

rep("JUST_BASE = 84393900",
    "JUST_BASE = 84394400",
    "JUST_BASE")

rep('''want_err = (
    "First-pass realign with tick_s=4.27231 (printed 4.272) moved 0 rows "
    "(ts_realigned_first=0, inserted=5897, already_in_db=19540, missing_chunks=0)."
)''',
    '''want_err = (
    "First-pass realign with tick_s=4.23635 (printed 4.236) moved 0 rows "
    "(ts_realigned_first=0, inserted=531, already_in_db=26099, missing_chunks=1)."
)''',
    "want_err")

rep('reason = reason.replace("(printed 4.206, min-all-rooms first two bases)", "(printed 4.272, min-all-rooms first two bases)")',
    'reason = reason.replace("(printed 4.206, min-all-rooms first two bases)", "(printed 4.236, min-all-rooms first two bases)")',
    "printed-a")
rep('reason = reason.replace("(printed 4.206)", "(printed 4.272)")',
    'reason = reason.replace("(printed 4.206)", "(printed 4.236)")',
    "printed-b")
rep('reason = reason.replace("(printed 4.224)", "(printed 4.272)")',
    'reason = reason.replace("(printed 4.224)", "(printed 4.236)")',
    "printed-c")
rep(
    '"(ts_realigned_first=0, inserted=3305, already_in_db=21922, missing_chunks=0).",\n    "(ts_realigned_first=0, inserted=5897, already_in_db=19540, missing_chunks=0).",',
    '"(ts_realigned_first=0, inserted=3305, already_in_db=21922, missing_chunks=0).",\n    "(ts_realigned_first=0, inserted=531, already_in_db=26099, missing_chunks=1).",',
    "reason-insert")
rep('    "First-pass realign with tick_s=4.27231 (printed 4.272) moved 0 rows (ts_realigned_first=0, inserted=3305, already_in_db=21922, missing_chunks=0).",',
    '    "First-pass realign with tick_s=4.23635 (printed 4.236) moved 0 rows (ts_realigned_first=0, inserted=3305, already_in_db=21922, missing_chunks=0).",',
    "reason-firstpass-line")
rep('if "inserted=5897" not in reason:',
    'if "inserted=531" not in reason:',
    "inserted-guard")
rep("inserted_first = 5897",
    "inserted_first = 531",
    "inserted_first")

rep('    hole866_d, hole866_n, hole866_mn, hole866_mx = hole("W45N8", 84386601, 84386700)',
    '    hole866_d, hole866_n, hole866_mn, hole866_mx = hole("W45N8", 84386601, 84386700)\n    hole943_d, hole943_n, hole943_mn, hole943_mx = hole("W46N8", 84394301, 84394400)',
    "hole943")

rep('tick_s_first = float(tick.get("tick_s_used_first_pass") or tick.get("first_interval") or 4.27231)',
    'tick_s_first = float(tick.get("tick_s_used_first_pass") or tick.get("first_interval") or 4.23635)',
    "tick_s_fallback")

p.write_text(src)
print("wrote stage1", p.stat().st_size)
