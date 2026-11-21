#!/bin/bash
set -u
cd /workspace/screeps
D=state/_patrol_2026-11-21_2020
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
  .venv/bin/python "$D/freeze_clock.py" > "$D/freeze_clock.txt" 2> "$D/freeze_clock.err"
  echo $? > "$D/freeze_clock_rc.txt"
) &
p8=$!

echo "launched pids $p1 $p2 $p3 $p4 $p5 $p6 $p7 $p8"
wait $p1 $p2 $p3 $p4 $p5 $p6 $p7 $p8
echo ALL_DONE
date '+%Y-%m-%d %H:%M:%S %Z'
for name in model_1h model_2h model_w8_1h model_w8_2h audit_patrol motion_1h motion_2h freeze_clock; do
  echo -n "$name rc="
  cat "$D/${name}_rc.txt" 2>/dev/null || echo missing
  if [ -s "$D/${name}.err" ]; then echo "  ERR:"; tail -20 "$D/${name}.err"; fi
done
