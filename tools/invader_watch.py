#!/usr/bin/env python3
"""NPC Invader raid counter watch (strategy review 2026-10-21 23:5x).
Each run snapshots source.invaderHarvested for our rooms + remotes via room-objects (no user/memory quota; the in-game
Source object does NOT expose invaderHarvested, so Memory.remote.*.invaderHarvested is always null) and appends to
metrics/invader_counters.jsonl. A drop in a room's total = the server's raid cron fired (counter reset to 0).
Prints per room: total, growth rate since last sample, resets seen, and an ETA band for the next raid assuming
goal 70k-130k (open-source backend: INVADERS_ENERGY_GOAL 100k x U(0.7,1.3), 10% x2 or x0.5).
Open question this tool answers: do counters reset in rooms where no raid can enter (all exits lead to owned/reserved
rooms: home W46N8, W47N7) - the open-source cron skips those without resetting; the official server may differ
(W47N8 got a raid from the W47N9 side at 12:34 although W47N9 is owned)."""
import json, os, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import api
ROOMS = ['W46N8', 'W47N8', 'W45N8', 'W45N7', 'W47N7']
LOG = os.path.join(ROOT, 'metrics', 'invader_counters.jsonl')

def snap():
    t = api.req('game/time?shard=shard3')['time']
    out = {'tick': t, 'ts': int(time.time()), 'rooms': {}}
    for r in ROOMS:
        objs = api.req(f'game/room-objects?room={r}&shard=shard3').get('objects', [])
        src = [o.get('invaderHarvested') or 0 for o in objs if o.get('type') == 'source']
        inv = sum(1 for o in objs if o.get('type') == 'creep' and str(o.get('user')) == '2')
        out['rooms'][r] = {'total': sum(src), 'sources': src, 'invaders': inv}
    return out

def history():
    try:
        with open(LOG) as f: return [json.loads(l) for l in f if l.strip()]
    except OSError: return []

def main():
    h = history(); s = snap()
    with open(LOG, 'a') as f: f.write(json.dumps(s) + '\n')
    h.append(s)
    for r in ROOMS:
        pts = [(x['tick'], x['rooms'][r]['total']) for x in h if r in x.get('rooms', {})]
        resets = [pts[i][0] for i in range(1, len(pts)) if pts[i][1] < pts[i - 1][1]]
        cur = pts[-1][1]
        # rate from samples since the last reset
        seg = [p for p in pts if not resets or p[0] >= resets[-1]]
        rate = (seg[-1][1] - seg[0][1]) / (seg[-1][0] - seg[0][0]) if len(seg) > 1 and seg[-1][0] > seg[0][0] else None
        eta = f"next raid in {max(0,(70000-cur)/rate):.0f}-{max(0,(130000-cur)/rate):.0f} t" if rate else 'rate n/a (need 2 samples)'
        print(f"{r}: total {cur} rate {rate and round(rate,1)} e/t resets {resets[-3:]} invaders {s['rooms'][r]['invaders']} | {eta}")

if __name__ == '__main__':
    main()
