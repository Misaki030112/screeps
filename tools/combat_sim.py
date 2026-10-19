#!/usr/bin/env python3
"""W47N8 combat model (docs/DEFENSE_W47N8.md). Tick model of towers + our ranged defenders vs a hostile squad.
Assumptions (deliberately pessimistic for us, unboosted unless stated):
  - tower dmg 600 at r<=5 -> 150 at r>=20 (linear), 10 energy per shot; tower heal 400 -> 100, repair 800 -> 200.
  - bodies lose parts front to back; enemy bodies are ordered TOUGH, MOVE, work parts (work parts die last = worst case).
  - enemy healers stay adjacent to their target (12/HEAL); each healer heals the most damaged ally (self first if hurt).
  - enemy RA focus the weakest of our defenders in range 3 (our RA range = theirs, so no out-ranging); melee reach a
    defender only `melee_uptime` of ticks (kiting quality; 0 = perfect kiting behind the seal walls).
  - our side: towers and defenders focus ONE target: healer > ranged > melee, first one with net damage > 0.
    If no target has net > 0 the towers hold fire (no energy burnt) and defenders pull back (fight lost/stalled).
  - defenders retreat at 60% hp (out of the fight, no longer shooting).
Outcome: 'win' (squad dead), 'lose' (defenders out and squad free to hit structures), 'stall' (nobody can kill anybody).
usage: python3 tools/combat_sim.py [--json]"""
import sys, json, copy
def tdmg(r): return 600 if r <= 5 else 150 if r >= 20 else 600 - (r - 5) * 30
def body(**k):  # order: tough, move, then work parts (attack/ranged_attack/heal)
    b = []
    for t in ('tough', 'move', 'attack', 'ranged_attack', 'heal'): b += [t] * k.get(t, 0)
    return b
class Cr:
    def __init__(s, name, b, rt=0): s.name, s.b, s.hits, s.rt = name, b, len(b) * 100, rt; s.max = s.hits; s.out = False
    def n(s, t):  # live parts of type t
        dead = (s.max - s.hits) // 100; return sum(1 for i, p in enumerate(s.b) if p == t and i >= dead)
    @property
    def alive(s): return s.hits > 0
    def cls(s): return 0 if s.n('heal') else 1 if s.n('ranged_attack') else 2 if s.n('attack') else 3
def defender(e, mx=12):  # 17:34: RA+MOVE only (src/rooms/w47n8/defense.js raBody); home W46N8 sends mx=25 (11RA11M at cap 2300)
    k = max(1, min(mx, e // 200)); return body(ranged_attack=k, move=k), k * 200
SQUAD = lambda: [Cr('RA11', body(ranged_attack=11, move=11)), Cr('RA7', body(ranged_attack=7, move=7)),
                 Cr('M10', body(tough=5, move=15, attack=10)), Cr('M8', body(tough=4, move=12, attack=8)),
                 Cr('H6a', body(heal=6, move=6)), Cr('H7', body(heal=7, move=7)), Cr('H6b', body(heal=6, move=6))]
def fight(enemy, tower_r, ndef=2, cap=1300, melee_uptime=0.0, tower_e=890, max_t=1500, refill=0):
    """tower_r: list of tower ranges to the fight (one entry per tower)."""
    db, dcost = defender(cap); ours = [Cr(f'D{i}', db) for i in range(ndef)]
    energy, burnt, t, mel = tower_e * len(tower_r), 0, 0, 0.0
    while t < max_t:
        t += 1
        en = [x for x in enemy if x.alive]; us = [x for x in ours if x.alive and not x.out]
        if not en: return dict(result='win', ticks=t, tower_energy=burnt, defenders_lost=sum(not x.alive for x in ours), def_cost=dcost * ndef)
        heal_parts = sum(x.n('heal') for x in en)
        # our pick: priority class, net>0
        ra = sum(x.n('ranged_attack') for x in us) * 10
        shots = [r for r in tower_r] if energy >= 10 * len(tower_r) else []
        tw = sum(tdmg(r) for r in shots)
        tgt = None
        for x in sorted(en, key=lambda x: (x.cls(), x.hits)):
            heal_on = heal_parts * 12  # all healers can stack on the focused target (worst case)
            if tw + ra - heal_on > 0: tgt = x; break
        mel += melee_uptime
        # enemy damage on our weakest defender
        edmg = sum(x.n('ranged_attack') for x in en) * 10
        if mel >= 1: mel -= 1; edmg += sum(x.n('attack') for x in en) * 30
        if tgt:
            if shots: energy -= 10 * len(shots); burnt += 10 * len(shots)
            tgt.hits -= tw + ra
            if tgt.hits <= 0: tgt.hits = 0
        if us and edmg:
            v = min(us, key=lambda x: x.hits); v.hits -= edmg
            for d in us: d.hits = min(d.max, d.hits + 12 * d.n('heal')) if d.alive and d.hits > 0 else d.hits
            for d in us:
                if d.hits <= 0: d.hits = 0
                elif d.hits < 0.6 * d.max: d.out = True
        # enemy heal: spread to most damaged, unless dead
        en = [x for x in enemy if x.alive]
        pool = heal_parts * 12
        while pool > 0 and en:
            m = min(en, key=lambda x: x.hits - x.max)
            need = m.max - m.hits
            if need <= 0: break
            g = min(need, pool); m.hits += g; pool -= g
        energy += refill
        us = [x for x in ours if x.alive and not x.out]
        if not tgt and not us:
            return dict(result='lose' if any(x.n('attack') or x.n('ranged_attack') for x in en) else 'stall', ticks=t, tower_energy=burnt,
                        defenders_lost=sum(not x.alive for x in ours), def_cost=dcost * ndef, enemy_left=[x.name for x in en])
        if not tgt and not edmg:
            return dict(result='stall', ticks=t, tower_energy=burnt, defenders_lost=0, def_cost=dcost * ndef, enemy_left=[x.name for x in en])
    return dict(result='timeout', ticks=t, tower_energy=burnt)
def breach(enemy, hp=50000, tower_r=(32,), tower_e=890):
    """squad hitting one seal wall unopposed, tower repairing it (repair 800->200 like tdmg/0.75)."""
    dps = sum(x.n('attack') * 30 + x.n('ranged_attack') * 10 for x in enemy)
    rep = sum(min(800, max(200, 800 - (r - 5) * 40)) for r in tower_r)
    ticks_no = hp / dps; ticks_rep = min(tower_e / 10 + (hp - tower_e / 10 * (dps - rep)) / dps if dps > rep else 1e9, 1e9)
    return dict(dps=dps, ticks_no_repair=round(ticks_no), ticks_with_repair=round(ticks_rep), repair_energy=tower_e)
SCEN = [
    # name, enemy factory, tower ranges, defenders, cap
    ('A full squad at the north seal, RCL4 (1 tower r32)', SQUAD, [32], 2, 1300),
    ('B full squad at Spawn2 15,18, RCL4 (1 tower r18-20)', SQUAD, [19], 2, 1300),
    ('C full squad in the core 33,33, RCL4 (tower r<=5)', SQUAD, [3], 2, 1300),
    ('D full squad at Spawn2, RCL5 (2 towers r19/19, 1800 def)', SQUAD, [19, 19], 2, 1800),
    ('E full squad in the core, RCL5 (2 towers r<=5)', SQUAD, [3, 3], 2, 1800),
    ('F full squad at Spawn2, towers only RCL4', SQUAD, [19], 0, 1300),
    ('F2 full squad at Spawn2, towers only RCL5 (2 towers)', SQUAD, [19, 19], 0, 1800),
    ('F3 full squad at the north seal, towers only RCL5 (r32/r28)', SQUAD, [32, 28], 0, 1800),
    ('F4 melee + 2 healers at the seal, RCL4 towers only', lambda: [Cr('M10', body(tough=5, move=15, attack=10)), Cr('H6', body(heal=6, move=6)), Cr('H7', body(heal=7, move=7))], [32], 0, 1300),
    ('F5 melee + 2 healers at the seal, RCL4 + 2 def', lambda: [Cr('M10', body(tough=5, move=15, attack=10)), Cr('H6', body(heal=6, move=6)), Cr('H7', body(heal=7, move=7))], [32], 2, 1300),
    ('N 17:34 pair 8RA+6RA at the seal, tower + 1 home def (11RA11M)', lambda: [Cr('RA8', body(ranged_attack=8, move=8)), Cr('RA6', body(ranged_attack=6, move=6))], [32], 1, 2300),
    ('O 17:34 pair + 2 healers (7H,7H) at the seal, tower + 1 home def', lambda: [Cr('RA8', body(ranged_attack=8, move=8)), Cr('RA6', body(ranged_attack=6, move=6)), Cr('H7', body(heal=7, move=7)), Cr('H7b', body(heal=7, move=7))], [32], 1, 2300),
    ('G 1 RA (7RA7M) at the seal, 2 def', lambda: [Cr('RA7', body(ranged_attack=7, move=7))], [32], 2, 1300),
    ('H 1 RA + 1 healer (11RA + 6H) at the seal, 2 def', lambda: [Cr('RA11', body(ranged_attack=11, move=11)), Cr('H6', body(heal=6, move=6))], [32], 2, 1300),
    ('I 2 RA + 1 healer at the seal, 2 def', lambda: [Cr('RA11', body(ranged_attack=11, move=11)), Cr('RA7', body(ranged_attack=7, move=7)), Cr('H6', body(heal=6, move=6))], [32], 2, 1300),
    ('J 2 melee (no heal) at the seal, 2 def kiting', lambda: [Cr('M10', body(tough=5, move=15, attack=10)), Cr('M8', body(tough=4, move=12, attack=8))], [32], 2, 1300),
    ('K drain tank 14T14M + 7H at the seal, tower only', lambda: [Cr('T', body(tough=14, move=14)), Cr('H7', body(heal=7, move=7))], [32], 0, 1300),
    ('L lone drain tank 14T14M at the seal, tower only', lambda: [Cr('T', body(tough=14, move=14))], [32], 0, 1300),
]
def main():
    out = []
    for name, f, tr, nd, cap in SCEN:
        r = fight(f(), tr, nd, cap); r['scenario'] = name; out.append(r)
    out.append(dict(scenario='M seal wall 50k vs full squad (720 dps), tower repairs at r32', **breach(SQUAD())))
    if '--json' in sys.argv: print(json.dumps(out, indent=1)); return
    for r in out: print(r.pop('scenario'), '->', r)
if __name__ == '__main__': main()
