# Peacetime listener holds one room slot, weights 5:5:1:1. node is not involved.
# .venv/bin/python tests/listener_rot_test.py
import os, sys
from collections import Counter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))
import room_rot as R

ROOT = os.path.join(os.path.dirname(__file__), '..')
assert [r for r, _ in R.WEIGHTS] == ['W46N8', 'W47N8', 'W45N8', 'W45N7']
assert [w for _, w in R.WEIGHTS] == [5, 5, 1, 1]
assert [r for r, _ in R.ROT] == [r for r, _ in R.WEIGHTS]
assert [s for _, s in R.ROT] == [5 * R.UNIT_S, 5 * R.UNIT_S, R.UNIT_S, R.UNIT_S]
assert R.PEACETIME_SLOTS == 1 and R.WARTIME_OPS_SLOTS == 0
assert R.YIELD_FILE == 'listener_yield_rooms'
assert R.cycle_s() == 1440

d = R.duty()
assert abs(d['W46N8'] - 5 / 12) < 1e-12
assert abs(d['W47N8'] - 5 / 12) < 1e-12
assert abs(d['W45N8'] - 1 / 12) < 1e-12
assert abs(d['W45N7'] - 1 / 12) < 1e-12
assert abs(sum(d.values()) - 1) < 1e-12

# One slot for the whole cycle: every second maps to exactly one of the four rooms.
counts = Counter(R.room_at(t) for t in range(R.cycle_s()))
assert counts == {'W46N8': 600, 'W47N8': 600, 'W45N8': 120, 'W45N7': 120}, counts
assert R.room_at(0) == 'W46N8'
assert R.room_at(599) == 'W46N8' and R.room_at(600) == 'W47N8'
assert R.room_at(1199) == 'W47N8' and R.room_at(1200) == 'W45N8'
assert R.room_at(1319) == 'W45N8' and R.room_at(1320) == 'W45N7'
assert R.room_at(1439) == 'W45N7' and R.room_at(1440) == 'W46N8'
assert R.room_at(1440 + 600) == 'W47N8'
try:
    R.room_at(-1)
    raise SystemExit('negative elapsed must fail')
except ValueError:
    pass

# Auth must not pin a second room beside the rotating slot (the old home-always design).
src = open(os.path.join(ROOT, 'tools', 'listener.py')).read()
assert "f'room:{SHARD}/{ROOM}'" not in src
assert src.count("ws.send(f'subscribe room:") == 1
assert 'YIELD_FILE' in src and 'subscribe_slot' in src
print('listener rot ok')
