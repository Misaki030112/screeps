"""v5 road trunks hub->gates, reusing planned roads. Design only."""
import json, heapq, sys
sys.argv=['x']; import defense_plan2 as D
R3=json.load(open(f'{D.ROOT}/data/defense_plan3.json'))
cut=set(map(tuple,R3['cut']))
GATES={'TR':[(47,16),(47,17)],'BL':[(23,35)],'TL':[(25,16)],'BR':[(44,27)]}
gateset={g for v in GATES.values() for g in v}
blocked={p for p,t in D.S.items() if set(t)-{'road','rampart','container'}}
def sp(start,goal,have):
    pq=[(0,start)];dist={start:0};prev={}
    while pq:
        d,p=heapq.heappop(pq)
        if p==goal:
            out=[p]
            while p in prev: p=prev[p]; out.append(p)
            return out[::-1]
        if d>dist[p]: continue
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                n=(p[0]+dx,p[1]+dy)
                if n==p or not(0<=n[0]<50 and 0<=n[1]<50) or D.wall(*n) or (n in blocked and n!=goal): continue
                if n in cut and n!=goal: continue
                c=d+(1 if n in have else (10 if D.ter(*n)=='2' else 2))  # build-cost-aware: reuse roads, avoid swamp
                if c<dist.get(n,1e9): dist[n]=c; prev[n]=p; heapq.heappush(pq,(c,n))
have=set(D.roads)
res={}
for name in ['TR','BR','BL','TL']:
    g=GATES[name][0]
    p=sp((36,32),g,have)
    new=[q for q in p if q not in have and q not in cut]  # gate tile itself: rampart, road optional on top
    sw=sum(D.ter(*q)=='2' for q in new)
    res[name]=dict(gate=GATES[name],path=p,len=len(p)-1,new_tiles=new,new=len(new),swamp=sw,
        build=300*(len(new)-sw)+1500*sw, decay_per_10k=10*((len(new)-sw)*1+sw*5))
    if name=='TR': have|=set(p)
for k,v in res.items(): print(k,v['len'],v['new'],v['swamp'],v['build'],v['decay_per_10k'])
json.dump(res,open(f'{D.ROOT}/data/trunks5.json','w'),default=list)
