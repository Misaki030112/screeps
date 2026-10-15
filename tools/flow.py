"""Source-rooted energy flow (steady state) + stochastic event layer. Used by tools/model.py.

Steady state, per source: gross -> downtime -> transport losses -> source upkeep = net delivered.
Shared upkeep (queen, builder-lite, roads, ramparts, towers idle) is subtracted once; what is left goes to the sinks:
upgrade (with upgrader upkeep 1300/1500/12 per upgrade/t), and in a measured window also build + storage delta.
Stochastic layer (separate): expected value = frequency (from events) x per-event delta, with a min..max range.
"""
LINK_LOSS = 0.03          # LINK_LOSS_RATIO
CONGESTION = 1.10         # measured hauler cycles 70/64, rhauler 92/84 (10-15): swaps, pickup waits, blocked tiles
MINER = 700 / 1500        # 5W1C3M (home)
RMINER = 800 / 1500       # 6W1C3M: remote repair ticks block harvest, 5W only ~9/t
RESERVER = 1300 / (2 * 530)  # 2 CLAIM x ~530 working ticks per life vs decay 1/t, spawned only below 2000 (was 1300/600 = back-to-back)
UP_UPKEEP = 1300 / 1500 / 12

def haul_cost(inc, rt):   # 2C:1M road hauler: carry parts * 75e per 1500
    carry = inc * (rt * CONGESTION + 4) / 50
    return carry * 75 / 1500, carry

def steady(M, n_ramparts=0, link_share_B=1.0, queen=650, builder=600):
    S, out = M['sources'], {}
    for k, s in S.items():
        gross = 10.0  # 3000/300, owned or reserved (unreserved remote would be 5)
        rt = s['roundtrip_1to1'] - 4 if s['dist'] else 0
        hc, carry = haul_cost(gross, rt) if rt else (0, 0)
        loss = {'container_decay': s['container_decay_e'],
                'link': gross * LINK_LOSS * link_share_B if k == 'B' else 0.0}
        upkeep = {'miner': RMINER if s['room'] != 'W46N8' else MINER, 'haulers': hc, 'reserver': RESERVER if s['room'] != 'W46N8' else 0.0}
        net = gross - sum(loss.values()) - sum(upkeep.values())
        out[k] = dict(gross=gross, losses=loss, upkeep=upkeep, carry=round(carry, 1), net=round(net, 2))
    shared = {'queen': queen / 1500, 'builder_lite': builder / 1500, 'roads': M.get('road_decay', 0), 'ramparts': 0.03 * n_ramparts}
    net = sum(v['net'] for v in out.values()) - sum(shared.values())
    return dict(sources=out, shared=shared, gross=sum(v['gross'] for v in out.values()), net=round(net, 2),
                upgrade=round(net / (1 + UP_UPKEEP), 2))

def events(c, q, hours=24 * 7):
    """Invader episodes in the remote from events: (start, end). Unpaired 'new' -> 15 min."""
    rows = q(c, f"SELECT ts, kind FROM events WHERE room='W45N8' AND msg ILIKE '%%invader%%' AND kind IN ('alert_new','alert_ended') AND ts > now()-interval '{hours} hours' ORDER BY ts")
    eps, start = [], None
    for ts, kind in rows:
        if kind == 'alert_new':
            if start and (ts - start).total_seconds() > 6 * 3600: eps.append((start, None)); start = None
            start = start or ts
        elif start: eps.append((start, ts)); start = None
    if start: eps.append((start, None))
    span = q(c, f"SELECT extract(epoch from max(ts)-min(ts)) FROM room_stats WHERE room='W46N8' AND ts > now()-interval '{hours} hours'")[0][0] or 1
    defenders = q(c, f"SELECT count(DISTINCT creep) FROM creep_ticks WHERE role='defender' AND ts > now()-interval '{hours} hours'")[0][0] or 0
    return eps, float(span), defenders

def stochastic(eps, span_s, defenders, tick_s):
    ticks = span_s / tick_s
    down = [((e - s).total_seconds() if e else 900) / tick_s for s, e in eps]
    n = len(eps) or 1
    per = dict(downtime_e=10 * sum(down) / n, defender_e=1300 * defenders / n, container_e=5000 * 0.25)  # ~1 rebuild per 4 episodes
    freq = len(eps) / ticks if ticks else 0
    ev = {k: v * freq for k, v in per.items()}
    # gains: Invader tombstones hold only what they carried (Invaders carry nothing), body energy is not refunded -> ~0
    gains = {'invader_tombstone': 0.0}
    lo = min(down) * 10 * freq if down else 0; hi = max(down) * 10 * freq + 1300 * freq + 5000 * freq if down else 0
    return dict(episodes=len(eps), ticks_per_episode=round(ticks / len(eps)) if eps else None,
                remote_e_per_episode=round(10 * ticks / len(eps)) if eps else None,
                per_episode=per, expected_loss=round(sum(ev.values()), 2), loss_terms={k: round(v, 3) for k, v in ev.items()},
                range=(round(lo, 2), round(hi, 2)), gains=gains)
