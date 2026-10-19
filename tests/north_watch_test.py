# north_watch classification: only non-Misaki creeps count; trigger rules (14:27)
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools')); sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import north_watch as N
U = {'u1': 'Misaki', 'u2': 'BustJetter'}
objs = [{'type': 'creep', 'user': 'u1', 'body': [{'type': 'attack'}]}, {'type': 'creep', 'user': 'u2', 'body': [{'type': 'attack'}]}, {'type': 'spawn', 'user': 'u2'}]
h = N.hostile_creeps(objs, U); assert [x['user'] for x in h] == ['u2'], h
assert N.triggers('W48N9', [1, 2], []) and not N.triggers('W48N9', [1], [1]) and N.triggers('W47N9', [], [1]) and not N.triggers('W47N8', [1, 2], [])
print('north_watch ok')
