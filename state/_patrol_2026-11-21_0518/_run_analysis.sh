#!/bin/bash
set -u
cd /workspace/screeps
D=state/_patrol_2026-11-21_0518

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
  PYTHONUNBUFFERED=1 .venv/bin/python "$D/official_retry.py" > "$D/official_retry.out" 2> "$D/official_retry.err"
  echo $? > "$D/official_retry_rc.txt"
) &
p9=$!
(
  .venv/bin/python "$D/_probe.py" > "$D/probe.txt" 2> "$D/probe.err"
  echo $? > "$D/probe_rc.txt"
) &
p10=$!

echo "launched pids $p1 $p2 $p3 $p4 $p5 $p6 $p7 $p8 $p9 $p10"
wait $p1 $p2 $p3 $p4 $p5 $p6 $p7 $p8 $p9 $p10
echo ALL_DONE
date '+%Y-%m-%d %H:%M:%S %Z'
for name in model_1h model_2h model_w8_1h model_w8_2h audit_patrol motion_1h motion_2h exact2h official_retry probe; do
  echo -n "$name rc="
  cat "$D/"$name"_rc.txt" 2>/dev/null || echo missing
  if [ -s "$D/"$name".err" ]; then echo "  ERR:"; tail -20 "$D/"$name".err"; fi
done
