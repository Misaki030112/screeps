#!/bin/bash
set -u
cd /workspace/screeps
D=state/_patrol_2026-11-21_0418
PYTHONUNBUFFERED=1 .venv/bin/python $D/q_live1.py > $D/q_live1.out 2>$D/q_live1.err; echo $? > $D/q_live1_rc.txt
PYTHONUNBUFFERED=1 .venv/bin/python $D/q_live2.py > $D/q_live2.out 2>$D/q_live2.err; echo $? > $D/q_live2_rc.txt
PYTHONUNBUFFERED=1 .venv/bin/python $D/q_live3.py > $D/q_live3.out 2>$D/q_live3.err; echo $? > $D/q_live3_rc.txt
date "+%Y-%m-%d %H:%M:%S %Z"
echo Q_ALL_DONE
