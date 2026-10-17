#!/usr/bin/env python3
"""Flood-fill from W46N8 exits; barriers = planned walls + gate ramparts. Prints whether core is sealed and leak path."""
import json, re, sys
T = open('terrain.txt').read().strip()
src = open('src/layouts/W46N8.js').read(); L = json.loads(src[src.index('{'):src.rindex('}')+1]); D = L['defense']
gates = [tuple(t) for g in D['gates'].values() for t in g]; walls = [tuple(t) for t in D['walls_in_build_order']]
def wall(x, y): return T[y*50+x] in '13'
def flood(block):
    seen = set(); st = [(x, y) for x in range(50) for y in range(50) if (x in (0, 49) or y in (0, 49)) and not wall(x, y) and (x, y) not in block]
    seen.update(st)
    while st:
        x, y = st.pop()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                n = (x+dx, y+dy)
                if 0 <= n[0] < 50 and 0 <= n[1] < 50 and n not in seen and not wall(*n) and n not in block: seen.add(n); st.append(n)
    return seen
if __name__ == '__main__':
    out = flood(set(gates) | set(walls)); core = [(37, 31), (35, 28), (36, 29), (30, 30), (31, 12), (38, 32)]
    print('outside tiles', len(out), 'core reached:', [c for c in core if c in out])
    for drop in walls:  # each wall is necessary?
        if (37, 31) not in flood(set(gates) | set(walls) - {drop}): print('redundant wall', drop)
