#!/usr/bin/env python3
"""Render /workspace/w47n8_tower_plan.png (Misaki 17:52): terrain, seal walls, roads, energy, old vs new tower slots, combined tower
damage heat on the north approach (y<=2). usage: .venv/bin/python tools/w47n8_tower_png.py"""
import sys, os; sys.argv = sys.argv[:1]; H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
import w47n8_tower_plan as P
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, numpy as np
OLD, NEW = [(33, 35), (34, 31)], [(24, 8), (22, 7)]
fig, axs = plt.subplots(1, 2, figsize=(16, 8.6))
for ax, tw, ttl in ((axs[0], [(33, 35)], 'NOW (RCL4): 33,35 only'), (axs[1], [(33, 35), (24, 8)], 'RCL5 plan (Misaki 18:06): 33,35 + 24,8 (22,7 at RCL7)')):
    img = np.ones((50, 50, 3))
    for y in range(50):
        for x in range(50):
            if P.wall(x, y): img[y, x] = (.25, .25, .25)
    ax.imshow(img, extent=(-.5, 49.5, 49.5, -.5))
    heat = np.full((50, 50), np.nan)
    for (x, y) in P.OUT: heat[y, x] = sum(P.tdmg(P.cheb(t, (x, y))) for t in tw)
    im = ax.imshow(heat, cmap='RdYlGn', vmin=150, vmax=900, extent=(-.5, 49.5, 49.5, -.5), alpha=.9)
    for (x, y) in P.ROADS: ax.plot(x, y, 's', ms=2.2, color='#b08850')
    for seg in P.SEAL:
        for (x, y) in seg: ax.plot(x, y, 's', ms=5, color='black')
    for (x, y), n in P.FIXED.items():
        if 'cont' in n or 'source' in n or 'link' in n: ax.plot(x, y, 'o', ms=6, color='gold', mec='k')
    ax.plot(35, 32, 'D', ms=7, color='orange', mec='k'); ax.text(36, 32, 'storage', fontsize=7)
    ax.text(28, 11.6, 'src A cont 26,11', fontsize=7)
    for (x, y) in OLD: ax.plot(x, y, 'X', ms=11, color='red', mec='k'); ax.text(x + .8, y, f'old {x},{y}', fontsize=7, color='red')
    for (x, y) in NEW: ax.plot(x, y, '*', ms=15, color='blue', mec='w'); ax.text(x + .8, y + .3, f'new {x},{y}', fontsize=8, color='blue')
    e = [heat[y, x] for (x, y) in P.EXT[0]]; w = [heat[y, x] for (x, y) in P.EXT[1]]
    ax.set_title(f'{ttl}\nnorth approach dmg/t: east min {min(e):.0f} avg {np.mean(e):.0f} | west min {min(w):.0f}', fontsize=10)
    ax.set_xlim(-.5, 49.5); ax.set_ylim(49.5, -.5)
fig.colorbar(im, ax=axs, shrink=.6, label='tower damage/tick on y<=2 tiles (600 at r<=5 -> 150 at r>=20)')
fig.suptitle('W47N8 towers: black = seal walls (y=3), brown = roads, gold = energy, red X = old slots, blue * = new north slots')
fig.savefig('/workspace/w47n8_tower_plan.png', dpi=110); print('ok')
