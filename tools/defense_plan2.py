"""v2: margin-3 min-cut, source-A options, multi-criteria tower scoring. Design only."""
import json, re, collections, networkx as nx
ROOT='/workspace/screeps'
T=open(f'{ROOT}/data/terrain_W46N8.txt').read().strip()
ter=lambda x,y:T[y*50+x]; wall=lambda x,y:ter(x,y)=='1'
L=json.loads(re.search(r'module.exports = (\{.*\});',open(f'{ROOT}/src/layouts/W46N8.js').read(),re.S).group(1))
S={}
for r,d in L['rcl'].items():
    for t,ps in d.items():
        for p in ps: S.setdefault(tuple(p),[]).append(t)
MINER_FEED=False
roads={tuple(p) for r in L['routes'].values() for p in r}|{p for p,t in S.items() if 'road' in t}
SRCA={(30,11),(31,12),(32,11)}; EASTRD={(41,22),(42,21),(43,20)}
core=[p for p,t in S.items() if p not in SRCA|EASTRD and set(t)-{'road'}]+[(28,32)]+[tuple(p) for p in L['positions']['upgraders']]
ch=lambda p,q:max(abs(p[0]-q[0]),abs(p[1]-q[1]))
def dmg(r,base=600): return base if r<=5 else (base/4 if r>=20 else base-base*0.75*(r-5)/15)
def dil(pts,m):
    s=set()
    for x,y in pts:
        for dx in range(-m,m+1):
            for dy in range(-m,m+1):
                a,b=x+dx,y+dy
                if 0<=a<50 and 0<=b<50 and not wall(a,b): s.add((a,b))
    return s
def mincut(prot):
    G=nx.DiGraph(); INF=10**9
    for x in range(50):
        for y in range(50):
            if wall(x,y): continue
            e=x in(0,49) or y in(0,49); ne=x in(1,48) or y in(1,48)
            G.add_edge(('i',x,y),('o',x,y),capacity=INF if (e or ne or (x,y) in prot) else 1)
            for dx in(-1,0,1):
                for dy in(-1,0,1):
                    a,b=x+dx,y+dy
                    if (dx or dy) and 0<=a<50 and 0<=b<50 and not wall(a,b): G.add_edge(('o',x,y),('i',a,b),capacity=INF)
            if e: G.add_edge('SRC',('i',x,y),capacity=INF)
            if (x,y) in prot: G.add_edge(('o',x,y),'SNK',capacity=INF)
    v,(A,B)=nx.minimum_cut(G,'SRC','SNK')
    cut=sorted({(n[1],n[2]) for n in A if n!='SRC' and n[0]=='i' and ('o',n[1],n[2]) in B})
    inside={(n[1],n[2]) for n in B if n!='SNK' and n[0]=='o'}-set(cut)
    return cut,inside
protB=dil(core,3)
cutB,inB=mincut(protB)
srcA_road=set(map(tuple,L['routes']['srcA']))
protA=protB|dil(SRCA,1)|dil(srcA_road,1)
cutA,inA=mincut(protA)
built=[(36,29),(37,33)]; plan=[p for p,t in S.items() if 'tower' in t]
taken=set(S)|roads|set(map(tuple,L['positions']['upgraders']))|set(map(tuple,L['positions']['fillers']))
storage=(37,31)
def bfs(start,inside):
    D={start:0}; q=collections.deque([start])
    while q:
        p=q.popleft()
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                n=(p[0]+dx,p[1]+dy)
                if n in D or n not in inside: continue
                if n in taken and n not in roads and set(S.get(n,[]))-{'road','rampart','container'}: continue
                D[n]=D[p]+1; q.append(n)
    return D
def evaluate(cut,inside,tag):
    gates=sorted(set(c for c in cut if c in roads)|({(47,20)}&set(cut)))
    outside_walk={(x,y) for x in range(50) for y in range(50) if not wall(x,y)}-inside-set(cut)
    D=bfs((36,32),inside|set(cut))  # storage door
    corepts=[(35,28),(37,31),(28,32),(35,31),(30,34)]
    def feats(t):
        exp=min(ch(t,o) for o in outside_walk)  # range to nearest tile enemy can stand on
        if MINER_FEED and ch(t,(31,12))<=1 and exp>=4: return exp,0  # source-A miner fills tower directly
        if ch(t,(36,30))<=1: return min(ch(t,o) for o in outside_walk),0  # stationary manager fills directly
        reach=min((D.get((t[0]+dx,t[1]+dy),99) for dx in(-1,0,1) for dy in(-1,0,1)),default=99)
        return exp,reach
    def score(tw):
        pass
    def score(tw):
        bmin=min(sum(dmg(ch(t,c)) for t in tw) for c in cut)
        cmin=min(sum(dmg(ch(t,c)) for t in tw) for c in corepts)
        gmin=min(sum(dmg(ch(t,c)) for t in tw) for c in gates) if gates else 0
        rep=sum(sum(dmg(ch(t,c),800) for t in tw) for c in cut)/len(cut)
        F=[feats(t) for t in tw]
        expo=sum(1 for e,_ in F if e<=3)       # towers shootable by ranged from outside
        refill=sum(r for _,r in F)/len(F)
        # weights: boundary dmg 35%, core 15%, gates 10%, repair 10%, refill 20%, exposure 10%
        s=0.35*bmin/3600+0.15*cmin/3600+0.10*gmin/3600+0.10*rep/4800+0.20*max(0,1-refill/15)+0.10*(1-expo/6)
        return dict(score=round(s,4),bmin=bmin,cmin=cmin,gmin=gmin,rep_avg=round(rep),refill_avg=round(refill,1),exposed=expo)
    cand=[p for p in inside if p not in taken and ter(*p)!='2' and feats(p)[1]<=10 and feats(p)[0]>=4]+plan
    rest=[p for p in plan if p not in built]
    planS=score(plan)
    best=rest[:]
    for _ in range(5):
        imp=False
        for i in range(4):
            for c in cand:
                if c in best or c in built: continue
                t=best[:]; t[i]=c
                if score(built+t)['score']>score(built+best)['score']: best=t; imp=True
        if not imp: break
    # pure-damage variant for comparison
    dmgbest=rest[:]
    for _ in range(5):
        imp=False
        for i in range(4):
            for c in cand:
                if c in dmgbest or c in built: continue
                t=dmgbest[:]; t[i]=c
                if score(built+t)['bmin']>score(built+dmgbest)['bmin']: dmgbest=t; imp=True
        if not imp: break
    srcA_cov=sum(dmg(ch(t,(31,12))) for t in built+best)
    return dict(tag=tag,cut=cut,cutsize=len(cut),swamp=sum(ter(*c)=='2' for c in cut),gates=gates,inside=len(inside),
        plan=plan,plan_score=planS,mc=built+best,mc_score=score(built+best),dmg=built+dmgbest,dmg_score=score(built+dmgbest),
        srcA_dmg_mc=srcA_cov,tower_feats={str(t):feats(t) for t in built+best})
R={'B_srcA_outside':evaluate(cutB,inB,'B'),'A_srcA_inside':evaluate(cutA,inA,'A')}
json.dump(R,open(f'{ROOT}/data/defense_plan2.json','w'),default=list)
for k,v in R.items(): print(k,{x:v[x] for x in v})
