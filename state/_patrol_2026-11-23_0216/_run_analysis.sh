#!/bin/bash
set -u
cd /workspace/screeps
D=state/_patrol_2026-11-23_0216
(.venv/bin/python tools/model.py --hours 1 > "$D/model_1h.txt" 2> "$D/model_1h.err"; echo $? > "$D/model_1h_rc.txt") &
p1=$!
(.venv/bin/python tools/model.py --hours 2 > "$D/model_2h.txt" 2> "$D/model_2h.err"; echo $? > "$D/model_2h_rc.txt") &
p2=$!
(.venv/bin/python tools/model_w8.py --hours 1 > "$D/model_w8_1h.txt" 2> "$D/model_w8_1h.err"; echo $? > "$D/model_w8_1h_rc.txt") &
p3=$!
(.venv/bin/python tools/model_w8.py --hours 2 > "$D/model_w8_2h.txt" 2> "$D/model_w8_2h.err"; echo $? > "$D/model_w8_2h_rc.txt") &
p4=$!
(.venv/bin/python tools/creep_audit.py --patrol > "$D/audit_patrol.txt" 2> "$D/audit_patrol.err"; echo $? > "$D/audit_patrol_rc.txt") &
p5=$!
(.venv/bin/python tools/creep_motion.py --hours 1 --patrol > "$D/motion_1h.txt" 2> "$D/motion_1h.err"; echo $? > "$D/motion_1h_rc.txt") &
p6=$!
(.venv/bin/python tools/creep_motion.py --hours 2 --patrol > "$D/motion_2h.txt" 2> "$D/motion_2h.err"; echo $? > "$D/motion_2h_rc.txt") &
p7=$!
(.venv/bin/python tools/creep_motion.py --hours 3 --patrol > "$D/motion_3h.txt" 2> "$D/motion_3h.err"; echo $? > "$D/motion_3h_rc.txt") &
p8=$!
(.venv/bin/python "$D/exact2h.py" > "$D/exact2h.txt" 2> "$D/exact2h.err"; echo $? > "$D/exact2h_rc.txt") &
p9=$!
echo "launched pids $p1 $p2 $p3 $p4 $p5 $p6 $p7 $p8 $p9"
wait $p1 $p2 $p3 $p4 $p5 $p6 $p7 $p8 $p9
echo ALL_DONE
date '+%Y-%m-%d %H:%M:%S %Z'
echo -n "model_1h rc="; cat "$D/model_1h_rc.txt" 2>/dev/null || echo missing
echo -n "model_2h rc="; cat "$D/model_2h_rc.txt" 2>/dev/null || echo missing
echo -n "model_w8_1h rc="; cat "$D/model_w8_1h_rc.txt" 2>/dev/null || echo missing
echo -n "model_w8_2h rc="; cat "$D/model_w8_2h_rc.txt" 2>/dev/null || echo missing
echo -n "audit_patrol rc="; cat "$D/audit_patrol_rc.txt" 2>/dev/null || echo missing
echo -n "motion_1h rc="; cat "$D/motion_1h_rc.txt" 2>/dev/null || echo missing
echo -n "motion_2h rc="; cat "$D/motion_2h_rc.txt" 2>/dev/null || echo missing
echo -n "motion_3h rc="; cat "$D/motion_3h_rc.txt" 2>/dev/null || echo missing
echo -n "exact2h rc="; cat "$D/exact2h_rc.txt" 2>/dev/null || echo missing
for err in "$D/model_1h.err" "$D/model_2h.err" "$D/model_w8_1h.err" "$D/model_w8_2h.err" "$D/audit_patrol.err" "$D/motion_1h.err" "$D/motion_2h.err" "$D/motion_3h.err" "$D/exact2h.err"; do
  if [ -s "$err" ]; then echo "ERR $err"; tail -20 "$err"; fi
done
