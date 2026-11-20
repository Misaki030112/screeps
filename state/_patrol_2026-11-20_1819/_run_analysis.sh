#!/bin/bash
set -u
cd /workspace/screeps
D=state/_patrol_2026-11-20_1819

python3 - <<'PY'
from pathlib import Path
p = Path("state/_patrol_2026-11-20_1819/exact2h.py")
t = p.read_text()
t = t.replace("BF_LO, BF_HI = 84376601, 84377300", "BF_LO, BF_HI = 84377301, 84378000")
p.write_text(t)
print("exact2h BF patched")
p = Path("state/_patrol_2026-11-20_1819/official_retry.py")
t = p.read_text()
old = '''IN_WINDOW = [
    ("W45N7", 84376800),
    ("W47N8", 84377100),
    ("W47N8", 84377200),
    ("W45N8", 84377200),
    ("W47N7", 84377200),
]
# leftover already-told, retry once in case it published
LEFTOVER = [
    ("W46N8", 84376100),
    ("W45N8", 84375300),
]
TICK_S = 4.190
'''
new = '''IN_WINDOW = [
    ("W46N8", 84377600),  # first-pass 404 this hour; first recorded by 18:00 half-hour, still untold
]
# leftover already-told, retry once in case it published
LEFTOVER = [
    ("W47N8", 84377100),  # already told by 17:40 1h patrol; aged out of hour window start 84377351
    ("W45N7", 84376800),  # already told; aged out
]
TICK_S = 4.074  # 18:00 half-hour first-pass in-use (this hour first-pass 4.227 is freeze-inflated)
'''
if old not in t:
    raise SystemExit('IN_WINDOW block not found')
p.write_text(t.replace(old, new))
print("official_retry patched")
PY

(
  .venv/bin/python tools/model.py --hours 1 > "$D/model_1h.txt" 2> "$D/model_1h.err"
  echo $? > "$D/model_1h_rc.txt"
) &
p1=$!
(
  .venv/bin/python tools/model.py --hours 2 > "$D/model_2h.txt" 2> "$D/model_2h.err"
  echo $? > "$D/model_2h_rc.txt"
) &
p2=$!
(
  .venv/bin/python tools/model_w8.py --hours 1 > "$D/model_w8_1h.txt" 2> "$D/model_w8_1h.err"
  echo $? > "$D/model_w8_1h_rc.txt"
) &
p3=$!
(
  .venv/bin/python tools/model_w8.py --hours 2 > "$D/model_w8_2h.txt" 2> "$D/model_w8_2h.err"
  echo $? > "$D/model_w8_2h_rc.txt"
) &
p4=$!
(
  .venv/bin/python tools/creep_audit.py --patrol > "$D/audit_patrol.txt" 2> "$D/audit_patrol.err"
  echo $? > "$D/audit_patrol_rc.txt"
) &
p5=$!
(
  .venv/bin/python tools/creep_motion.py --hours 1 --patrol > "$D/motion_1h.txt" 2> "$D/motion_1h.err"
  echo $? > "$D/motion_1h_rc.txt"
) &
p6=$!
(
  .venv/bin/python tools/creep_motion.py --hours 2 --patrol > "$D/motion_2h.txt" 2> "$D/motion_2h.err"
  echo $? > "$D/motion_2h_rc.txt"
) &
p7=$!
(
  .venv/bin/python "$D/exact2h.py" > "$D/exact2h.txt" 2> "$D/exact2h.err"
  echo $? > "$D/exact2h_rc.txt"
) &
p8=$!
(
  .venv/bin/python "$D/official_retry.py" > "$D/official_retry.out" 2> "$D/official_retry.err"
  echo $? > "$D/official_retry_rc.txt"
) &
p9=$!

echo "launched pids $p1 $p2 $p3 $p4 $p5 $p6 $p7 $p8 $p9"
wait $p1 $p2 $p3 $p4 $p5 $p6 $p7 $p8 $p9
echo ALL_DONE
date '+%Y-%m-%d %H:%M:%S %Z'
for name in model_1h model_2h model_w8_1h model_w8_2h audit_patrol motion_1h motion_2h exact2h official_retry; do
  echo -n "$name rc="
  cat "$D/${name}_rc.txt" 2>/dev/null || echo missing
done
