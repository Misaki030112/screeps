#!/usr/bin/env python3
"""Market / mineral snapshot (read-only, one console query, no trades): python3 tools/market.py [--json]
Prints credits, mineral stock per room (storage + terminal), mineral amount + regen ETA, the best buy orders for our minerals
net of terminal transfer energy, and the cheapest DELIVERED energy (credits per net energy after the transfer cost we pay on deal).
Writes state/market.json. See docs/MARKET.md. Any deal/createOrder is Misaki's decision (credits/market = major)."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from q import q
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
# console expressions are capped at ~1000 chars by the server ('expression size is too large'), so two queries
EXPR_ROOM = r"""(function(n){const r=Game.rooms[n];if(!r)return null;const m=r.find(FIND_MINERALS)[0],t=m.mineralType;
const st=s=>s?_.pick(s.store,(v,k)=>k!=='energy'&&v>0):{},ty=k=>r.find(FIND_STRUCTURES).filter(s=>s.structureType===k).length;
const bids=Game.market.getAllOrders({type:'buy',resourceType:t}).filter(o=>o.remainingAmount>=100).map(o=>[+o.price.toFixed(3),o.remainingAmount,o.roomName,Game.market.calcTransactionCost(1000,n,o.roomName)]).sort((a,b)=>b[0]-a[0]).slice(0,5);
return {min:[t,m.mineralAmount,m.ticksToRegeneration||0],ex:ty('extractor'),labs:ty('lab'),term:!!r.terminal,termE:r.terminal?r.terminal.store.energy:0,stor:st(r.storage),termS:st(r.terminal),bids}})('ROOM')"""
EXPR_MKT = r"""({cr:Game.market.credits,energyAsk:Game.market.getAllOrders({type:'sell',resourceType:'energy'}).filter(o=>o.remainingAmount>=1000).map(o=>[+o.price.toFixed(3),o.remainingAmount,o.roomName,Game.market.calcTransactionCost(1000,'W46N8',o.roomName)]).sort((a,b)=>a[0]/(1000-a[3])-b[0]/(1000-b[3])).slice(0,3),
hist:['O','K','energy'].reduce((a,k)=>{a[k]=Game.market.getHistory(k).slice(-3).map(d=>[d.date.slice(5),+d.avgPrice.toFixed(2),d.volume]);return a},{})})"""
one = lambda e: " ".join(e.split("\n"))
def main():
    m = q(one(EXPR_MKT), timeout=40); t, v = m['t'], m['v']
    if isinstance(v, str): sys.exit(v)
    v['rooms'] = {}
    for n in ('W46N8', 'W47N8'):
        r = q(one(EXPR_ROOM).replace('ROOM', n), timeout=40)['v']
        if isinstance(r, str): sys.exit(r)
        if r: v['rooms'][n] = r
    v['tick'] = t; v['at'] = time.strftime('%Y-%m-%d %H:%M UTC+8')
    with open(os.path.join(ROOT, 'state', 'market.json'), 'w') as f: json.dump(v, f, separators=(',', ':'))
    if '--json' in sys.argv: print(json.dumps(v)); return
    spt = 4.22
    print(f"tick {t}  credits {v['cr']}")
    for n, r in v['rooms'].items():
        typ, amt, ttr = r['min'] or ('?', 0, 0); stock = r['stor'].get(typ, 0) + r['termS'].get(typ, 0)
        eta = time.strftime('%m-%d %H:%M', time.localtime(time.time() + ttr * spt)) if ttr else '-'
        print(f"{n}: mineral {typ} {amt} (regen in {ttr} t ~{eta} UTC+8)  extractor {r['ex']} labs {r['labs']} terminal {r['term']} (energy {r['termE']})  stock {typ} {stock}  other {dict((k, val) for k, val in {**r['stor'], **r['termS']}.items() if k != typ)}")
        for p, a, rn, c in r['bids']:
            print(f"   bid {typ} {p:7.3f} x{a:<6} {rn:8} transfer {c/1000:.2f} e/unit -> {p/(c/1000):5.1f} cr per energy spent")
    for p, a, rn, c in v['energyAsk']:
        net = 1000 - c
        print(f"   energy ask {p:7.3f} x{a:<6} {rn:8} transfer {c/1000:.2f} e/unit -> {p*1000/net:6.1f} cr per NET delivered energy")
    print('history (date, avg, volume):', json.dumps(v['hist']))
if __name__ == '__main__': main()
