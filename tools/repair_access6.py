"""v6 repair access: standing spots + spur roads per wall segment. Design only."""
import json, heapq, re, sys
sys.argv=['x']; import defense_plan2 as D
ROOT=D.ROOT; R3=json.load(open(f'{ROOT}/data/defense_plan3.json'))
Lf=f'{ROOT}/src/layouts/W46N8.js'; L=json.loads(re.search(r'module.exports = (\{.*\});',open(Lf).read(),re.S).group(1))
DEF=L['defense']; walls=[tuple(w) for w in DEF['walls_in_build_order']]; gates={tuple(g) for v in DEF['gates'].values() for g in v}
cut=set(map(tuple,R3['cut']))
_,inside=D.mincut(D.protB|D.dil(D.SRCA,3)|D.dil(D.srcA_road,1))
trunk_tr={tuple(p) for p in DEF['trunks']['TR']['path']}
roads=set(D.roads)|trunk_tr
blocked={p for p,t in D.S.items() if set(t)-{'road','rampart','container'}}
ch=D.ch
# segments: 8-connected groups of wall tiles
segs=[];left=set(walls)
while left:
    st=[left.pop()];g=set(st)
    while st:
        p=st.pop()
        for q in list(left):
            if ch(p,q)<=1: left.remove(q);g.add(q);st.append(q)
    segs.append(sorted(g))
def dij(src):
    pq=[(0,src)];dist={src:0};prev={}
    while pq:
        d,p=heapq.heappop(pq)
        if d>dist[p]:continue
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                n=(p[0]+dx,p[1]+dy)
                if n==p or n not in inside or n in blocked or n in cut: continue
                c=d+(1 if n in roads else (10 if D.ter(*n)=='2' else 2))
                if c<dist.get(n,1e9): dist[n]=c;prev[n]=p;heapq.heappush(pq,(c,n))
    return dist,prev
dist,prev=dij((36,32))
BUILDER_CARRY=800  # 16 CARRY builder
UPKEEP=1.4          # energy/tick body cost amortised (~2100/1500)
HITS={'RCL6':300000,'RCL7':1000000,'RCL8':3000000}
out=[]
for seg in segs:
    cand=[p for p in inside if p not in blocked and p not in cut and p in dist and any(ch(p,w)<=3 for w in seg)]
    spots=[];unc=set(seg)
    while unc:
        b=max(cand,key=lambda p:(sum(ch(p,w)<=3 for w in unc),-dist[p]))
        spots.append(b);unc-={w for w in unc if ch(b,w)<=3}
    seg_res=dict(tiles=seg,spots=spots,spot_cost=[dist[s] for s in spots])
    # spur: from nearest road tile (on path to spot) to spot
    spur=[]
    for s in spots:
        p=s;path=[]
        while p not in roads and p in prev: path.append(p);p=prev[p]
        spur+=path
    spur=sorted(set(spur)-roads)
    sw=sum(D.ter(*q)=='2' for q in spur)
    build=300*(len(spur)-sw)+1500*sw; decay10k=10*((len(spur)-sw)+5*sw)
    # time saved per trip: off-road tiles cost 2 (plain)/10(swamp) vs road 1
    saved_per_trip=2*sum(((10 if D.ter(*q)=='2' else 2)-1) for q in spur)/max(1,len(spots))
    ev={}
    for k,h in HITS.items():
        energy=len(seg)*h/100; trips=energy/BUILDER_CARRY
        ev[k]=dict(energy=int(energy),trips=round(trips,1),ticks_saved=int(trips*saved_per_trip),value=int(trips*saved_per_trip*UPKEEP))
    seg_res.update(spur=spur,spur_tiles=len(spur),spur_swamp=sw,build=build,decay_per_10k=decay10k,saved_per_trip=saved_per_trip,eval=ev,
        justified=any(v['value']>build+decay10k*3 for k,v in ev.items() if k!='RCL8') )
    out.append(seg_res)
json.dump(out,open(f'{ROOT}/data/repair_access6.json','w'),default=list)
for s in out: print(s['tiles'][0],len(s['tiles']),s['spots'],s['spot_cost'],s['spur_tiles'],s['build'],s['saved_per_trip'],{k:v['value'] for k,v in s['eval'].items()},s['justified'])
