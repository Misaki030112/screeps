"""Which W47N8 sides can BustJetter reach from W47N9/W48N9 without crossing our W46N8? Tile-level Dijkstra over a 4x4 room block."""
import sys, os, heapq
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import terrain
def rn(cx, cy): return f'W{cx}N{cy}'
ROOMS = [(cx, cy) for cx in range(44, 53) for cy in range(3, 13)]
G = {}
for cx, cy in ROOMS:
    try: t = terrain(rn(cx, cy))
    except Exception as e: print('no terrain', rn(cx, cy), e); continue
    ox, oy = (52 - cx) * 50, (12 - cy) * 50
    for i, ch in enumerate(t):
        v = int(ch); G[(ox + i % 50, oy + i // 50)] = (rn(cx, cy), 255 if v & 1 else 10 if v & 2 else 2)
def run(start_room, sx, sy, banned):
    cx, cy = int(start_room[1:3]), int(start_room[4:])
    s = ((52 - cx) * 50 + sx, (12 - cy) * 50 + sy); D = {s: 0}; pq = [(0, s)]; entry = {}
    while pq:
        d, p = heapq.heappop(pq)
        if d > D[p]: continue
        r = G[p][0]
        if r == 'W47N8':
            lx, ly = p[0] % 50, p[1] % 50
            side = 'N' if ly == 0 else 'S' if ly == 49 else 'E' if lx == 49 else 'W' if lx == 0 else None
            if side and side not in entry: entry[side] = (d, lx, ly)
            continue
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (p[0] + dx, p[1] + dy)
                if q not in G or G[q][1] == 255 or G[q][0] in banned: continue
                # room crossing only orthogonal on edges (approx fine)
                nd = d + G[q][1]
                if nd < D.get(q, 1e9): D[q] = nd; heapq.heappush(pq, (nd, q))
    return entry
for home in ('W47N9', 'W48N9'):
    print(home, 'avoiding W46N8:', run(home, 25, 25, {'W46N8'}))
    print(home, 'avoiding W46N8+W47N7:', run(home, 25, 25, {'W46N8', 'W47N7'}))
