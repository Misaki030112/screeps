"""v4: evaluate gates per exit side. Design only."""
import json, heapq, sys
sys.argv=['x']; import defense_plan2 as D
R3=json.load(open(f'{D.ROOT}/data/defense_plan3.json'))
cut=[tuple(c) for c in R3['cut']]; cutset=set(cut); towers=[tuple(t) for t in R3['mc']]
exits={s:[] for s in 'NESW'}
for i in range(50):
    for s,(x,y) in {'N':(i,0),'S':(i,49),'W':(0,i),'E':(49,i)}.items():
        if not D.wall(x,y): exits[s].append((x,y))
def sp(start,goals,open_gates):
    goals=set(goals); pq=[(0,start)]; dist={start:0}; prev={}
    while pq:
        d,p=heapq.heappop(pq)
        if p in goals:
            out=[p]
            while p in prev: p=prev[p]; out.append(p)
            return d,out[::-1]
        if d>dist[p]: continue
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                n=(p[0]+dx,p[1]+dy)
                if n==p or not(0<=n[0]<50 and 0<=n[1]<50) or D.wall(*n): continue
                if n in cutset and n not in open_gates: continue
                c=d+(1 if n in D.roads else (5 if D.ter(*n)=='2' else 2))  # move-cost with roads(1)/plain(2)/swamp(10/2) for 1:1 MOVE-ish haulers
                if c<dist.get(n,1e9): dist[n]=c; prev[n]=p; heapq.heappush(pq,(c,n))
    return None,None
dmg=D.dmg; ch=D.ch
HOME=(36,32)
out={'exits':{k:len(v) for k,v in exits.items()}}
# baseline: only gate 47,16
for side in 'NESW':
    if not exits[side]: continue
    base,_=sp(HOME,exits[side],{(47,16)})
    free,fp=sp(HOME,exits[side],cutset)  # any gate
    g=[p for p in fp if p in cutset]
    out[side]=dict(exit_tiles=len(exits[side]),cost_single_gate=base,cost_best_gate=free,best_gate=g,
        saving=None if base is None else base-free,
        tower_dmg=[sum(dmg(ch(t,x)) for t in towers) for x in g])
# segment-wise alternate: top-left segment gate toward N/W
json.dump(out,open(f'{D.ROOT}/data/defense_gates4.json','w'),default=list)
print(json.dumps(out,default=list))
seg={'TL_north(26-28,7)':[(26,7),(27,7),(28,7)],'TL_west(26,8-12)':[(26,y) for y in range(8,13)],'L_mid(25,16-17)':[(25,16),(25,17)],
     'L(23,27-29)':[(23,27),(23,28),(23,29)],'BL(23,35-38)':[(23,y) for y in range(35,39)],
     'BR(42-46,26-28)':[(42,28),(43,28),(44,26),(44,27),(44,28),(45,26),(46,26)],'R(47,11-24)':[(47,y) for y in range(11,25)]}
segres={}
for name,tiles in seg.items():
    best=None
    for side in 'EW':
        for t in tiles:
            c,p=sp(HOME,exits[side],{t})
            if c is not None and (best is None or c<best[0] or (c==best[0] and side==best[2]=='')): 
                if best is None or c<best[0]: best=(c,t,side)
    # srcA miner to west exit (defender sortie from source A area)
    segres[name]=dict(best_gate=best[1] if best else None,reaches=best[2] if best else None,cost=best[0] if best else None,
        tower_dmg=sum(dmg(ch(tw,best[1])) for tw in towers) if best else None,
        repair_per_energy=max(D.dmg(ch(tw,best[1]),800)/10 for tw in towers) if best else None)
out['segments']=segres
json.dump(out,open(f'{D.ROOT}/data/defense_gates4.json','w'),default=list)
for k,v in segres.items(): print(k,v)
