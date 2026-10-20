# north_watch classification: only non-Misaki creeps count; trigger rules (14:27)
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools')); sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import north_watch as N
U = {'u1': 'Misaki', 'u2': 'BustJetter'}
objs = [{'type': 'creep', 'user': 'u1', 'body': [{'type': 'attack'}]}, {'type': 'creep', 'user': 'u2', 'body': [{'type': 'attack'}]}, {'type': 'spawn', 'user': 'u2'}]
h = N.hostile_creeps(objs, U); assert [x['user'] for x in h] == ['u2'], h
assert N.triggers('W48N9', [1, 2], []) and not N.triggers('W48N9', [1], [1]) and N.triggers('W47N9', [], [1]) and not N.triggers('W47N8', [1, 2], [])
U['u3'] = 'Invader'; objs.append({'type': 'creep', 'user': 'u3', 'body': [{'type': 'attack'}]})
assert len(N.hostile_creeps(objs, U, 'W48N9')) == 1 and len(N.hostile_creeps(objs, U, 'W47N8')) == 2 and len(N.hostile_creeps(objs, U)) == 2  # NPC ignored only in neighbour rooms
print('north_watch ok')
# 05:4x: verdict must count healers; 2RA (8/9) + 2 healers (7/5) at the seal: 1 tower r32 loses, +24,8 tower (r5) wins
P = [{'ranged_attack': 8, 'move': 8}, {'ranged_attack': 9, 'move': 9}]
H = [{'heal': 7, 'move': 7}, {'heal': 5, 'move': 5}]
assert N.verdict(P).startswith('towers win'), N.verdict(P)
assert N.verdict(P + H).startswith('towers+2 defenders win'), N.verdict(P + H)
assert N.verdict(P + H, tr=[32, 5]).startswith('towers win'), N.verdict(P + H, tr=[32, 5])
T = [{'type': 'tower', 'user': 'u1', 'x': 33, 'y': 35}, {'type': 'tower', 'user': 'u1', 'x': 24, 'y': 8}, {'type': 'tower', 'user': 'u2', 'x': 27, 'y': 4}]
assert N.seal_ranges(T, U) == [32, 5], N.seal_ranges(T, U)
assert N.seal_ranges(T, U, N.SEAL_WEST) == [32, 14], N.seal_ranges(T, U, N.SEAL_WEST)
assert N.seal_ranges(T, U, N.SPAWN_PT) == [5, 22], N.seal_ranges(T, U, N.SPAWN_PT)
# 23:4x: BustJetter's 21:45 W48N9 group (3 melee, 3x6RA, 28 HEAL) + 2 more 4H healers (36 HEAL): east seal holds, west seal needs defenders
B = [{'tough': 5, 'move': 15, 'attack': 10}, {'tough': 4, 'move': 12, 'attack': 8}, {'tough': 6, 'move': 18, 'attack': 12}] + [{'ranged_attack': 6, 'move': 6}] * 3 \
    + [{'heal': h, 'move': h} for h in (4, 4, 4, 5, 6, 5, 4, 4)]
N.TR[:], N.TRW[:], N.TRS[:] = [32, 5], [32, 16], [5, 22]
v = N.verdict_at(B, mean_x=10); assert v.startswith('west seal: towers+2') and 'east seal: towers win' in v, v
v = N.verdict_at(B, mean_x=None); assert v.startswith('east seal: towers win'), v
assert N.verdict_at(B, inside=True).startswith('towers win'), N.verdict_at(B, inside=True)
print('north_watch verdict ok')
# 14:3x: spawn-move gate w8n9a only for armed creeps near our border (W47N9 y >= 35), not BustJetter's home guard at 28,30
assert not N.n9_near([{'pos': [28, 30]}]) and N.n9_near([{'pos': [28, 30]}, {'pos': [29, 44]}]) and not N.n9_near([])
print('north_watch n9_near ok')
