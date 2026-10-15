import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools')); import neighbor_scan as N
sq = [dict(owner='BustJetter', name=f'b{i}', body={'heal': 7, 'move': 7}, x=2, y=20, hits=1400) for i in range(5)]
def s(r, cs=(), safe=None, t=100, hits=10000, tw=()): return dict(room=r, time=t, creeps=list(cs), towers=list(tw), safe_until=safe, struct_hits=hits)
assert N.classify({'W47N6': s('W47N6', sq, safe=500)})[0] == 'medium'
assert N.classify({'W47N6': s('W47N6', sq, safe=50)})[0] == 'high'                      # safe mode over
assert N.classify({'W47N6': s('W47N6', [], safe=500, hits=5000)}, {'W47N6': {'struct_hits': 10000}})[0] == 'high'
assert N.classify({'W47N8': s('W47N8', sq[:1])})[0] == 'high'                           # left toward us
probe = dict(owner='BustJetter', name='dp', body={'tough': 14, 'move': 14}, x=1, y=1, hits=2800)
assert N.classify({'W47N8': s('W47N8', [probe])})[0] == 'low'                           # non-combat probe
assert N.classify({'W47N9': s('W47N9', [], tw=[600, 700])})[0] == 'medium'
assert N.classify({'W47N9': s('W47N9', [], tw=[6, 10])})[0] == 'low'
print('neighbor_scan ok')
