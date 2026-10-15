"""Min-cut outer defense + tower placement for W46N8 (design only, no deploy)."""
import json, re, itertools, networkx as nx
ROOT='/workspace/screeps'
T=open(f'{ROOT}/data/terrain_W46N8.txt').read().strip()
ter=lambda x,y:T[y*50+x]
wall=lambda x,y:ter(x,y)=='1'
L=json.loads(re.search(r'module.exports = (\{.*\});',open(f'{ROOT}/src/layouts/W46N8.js').read(),re.S).group(1))
S={}
for r,d in L['rcl'].items():
    for t,ps in d.items():
        for p in ps: S.setdefault(tuple(p),[]).append(t)
FAR={(30,11),(31,12),(41,22),(42,21),(43,20)}  # source A link/container + east remote road: outside wall, lane gated
core=[p for p,t in S.items() if p not in FAR and set(t)-{'road'}]
core+= [(28,32)]  # controller
core+= [tuple(p) for p in L['positions']['upgraders']]
MARGIN=2
prot=set()
for x,y in core:
    for dx in range(-MARGIN,MARGIN+1):
        for dy in range(-MARGIN,MARGIN+1):
            a,b=x+dx,y+dy
            if 0<=a<50 and 0<=b<50 and not wall(a,b): prot.add((a,b))
G=nx.DiGraph(); INF=10**9
def nb(x,y):
    for dx in(-1,0,1):
        for dy in(-1,0,1):
            if dx or dy:
                a,b=x+dx,y+dy
                if 0<=a<50 and 0<=b<50 and not wall(a,b): yield a,b
for x in range(50):
    for y in range(50):
        if wall(x,y): continue
        edge=x in(0,49) or y in(0,49); nearedge=x in(1,48) or y in(1,48)
        cap=INF if (edge or nearedge or (x,y) in prot) else 1
        G.add_edge(('i',x,y),('o',x,y),capacity=cap)
        for a,b in nb(x,y): G.add_edge(('o',x,y),('i',a,b),capacity=INF)
        if edge: G.add_edge('SRC',('i',x,y),capacity=INF)
        if (x,y) in prot: G.add_edge(('o',x,y),'SNK',capacity=INF)
val,(A,B)=nx.minimum_cut(G,'SRC','SNK')
cut=sorted({(n[1],n[2]) for n in A if n!='SRC' and n[0]=='i' and ('o',n[1],n[2]) in B})
# gates: cut tiles on any planned road / route, plus the exit lanes
roads={tuple(p) for r in L['routes'].values() for p in r}|{p for p,t in S.items() if 'road' in t}
gates=[c for c in cut if c in roads]
inside={(n[1],n[2]) for n in B if n!='SNK' and n[0]=='o'}-set(cut)
def dmg(r): return 600 if r<=5 else (150 if r>=20 else 600-600*0.75*(r-5)/15)
ch=lambda p,q:max(abs(p[0]-q[0]),abs(p[1]-q[1]))
def score(tw): return min(sum(dmg(ch(t,c)) for t in tw) for c in cut)
plan=[p for p,t in S.items() if 'tower' in t]
taken=set(S)|roads|set(map(tuple,L['positions']['upgraders']))|set(map(tuple,L['positions']['fillers']))
cand=[p for p in inside if p not in taken and not wall(*p) and ter(*p)!='2' or (p in plan)]
cand=list(set(cand)|set(plan))
# greedy + 1-swap local search
best=plan[:]
for _ in range(4):
    improved=False
    for i in range(6):
        for c in cand:
            if c in best: continue
            t=best[:]; t[i]=c
            if score(t)>score(best): best=t; improved=True
    if not improved: break
res=dict(cut=cut,gates=gates,cutsize=len(cut),plan_towers=plan,plan_min=score(plan),opt_towers=best,opt_min=score(best),
  plan_avg=sum(sum(dmg(ch(t,c)) for t in plan) for c in cut)/len(cut),
  opt_avg=sum(sum(dmg(ch(t,c)) for t in best) for c in cut)/len(cut),inside=len(inside),
  swamp_cut=sum(ter(*c)=='2' for c in cut))
json.dump(res,open(f'{ROOT}/data/defense_plan.json','w'))
print({k:v for k,v in res.items()})
# variant: keep built towers (36,29),(37,33); optimise remaining 4 within planned-free tiles
fixed=[(36,29),(37,33)]
rest=[p for p in plan if p not in fixed]
for _ in range(4):
    ch_=False
    for i in range(4):
        for c in cand:
            if c in rest or c in fixed: continue
            t=rest[:]; t[i]=c
            if score(fixed+t)>score(fixed+rest): rest=t; ch_=True
    if not ch_: break
res['keep2_towers']=fixed+rest; res['keep2_min']=score(fixed+rest)
res['keep2_avg']=sum(sum(dmg(ch(t,c)) for t in fixed+rest) for c in cut)/len(cut)
corepts=[(35,28),(37,31),(28,32),(35,31)]
for k in('plan_towers','opt_towers','keep2_towers'):
    res[k+'_core_min']=min(sum(dmg(ch(t,c)) for t in res[k]) for c in corepts)
json.dump(res,open(f'{ROOT}/data/defense_plan.json','w'))
print(res['keep2_towers'],res['keep2_min'],res['keep2_avg'],[res[k+'_core_min'] for k in('plan_towers','opt_towers','keep2_towers')])
# render
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, numpy as np
from matplotlib.colors import ListedColormap
fig,axs=plt.subplots(1,2,figsize=(20,10))
col={'1':(0.12,0.12,0.12),'2':(0.33,0.42,0.2),'0':(0.85,0.85,0.8)}
sym={'spawn':('o','#ff00ff'),'extension':('s','#f5c518'),'tower':('^','#e02020'),'storage':('D','#ffffff'),'link':('d','#00e0ff'),
 'lab':('p','#9b59b6'),'terminal':('H','#2ecc71'),'factory':('P','#888'),'nuker':('X','#000'),'observer':('*','#0af'),'powerSpawn':('8','#f60'),'container':('s','#8b5a2b'),'extractor':('h','#aaa')}
for ax,(name,tw) in zip(axs,[('现行规划塔位 Plan towers',plan),('建议塔位 Keep-2 proposal',res['keep2_towers'])]):
    img=np.array([[col[ter(x,y)] for x in range(50)] for y in range(50)])
    ax.imshow(img,origin='upper')
    for p in roads: ax.add_patch(plt.Rectangle((p[0]-.5,p[1]-.5),1,1,color='#b0a080',alpha=.8))
    for p,ts in S.items():
        for t in ts:
            if t in sym and t!='tower': ax.plot(*p,sym[t][0],color=sym[t][1],ms=6,mec='k',mew=.4)
    d=[sum(dmg(ch(t,c)) for t in tw) for c in cut]
    sc=ax.scatter([c[0] for c in cut],[c[1] for c in cut],c=d,cmap='RdYlGn',vmin=1500,vmax=3600,s=150,marker='s',edgecolors=['cyan' if c in gates else 'k' for c in cut],linewidths=[2.5 if c in gates else .5 for c in cut])
    for c,v in zip(cut,d): ax.text(c[0],c[1],int(v//100),fontsize=5,ha='center',va='center')
    for t in tw: ax.plot(*t,'^',color='#e02020',ms=11,mec='w')
    ax.plot(28,32,'*',color='#00ff88',ms=15,mec='k'); ax.plot(32,11,'o',color='yellow',ms=9,mec='k'); ax.plot(39,33,'o',color='yellow',ms=9,mec='k')
    ax.set_title(f'{name}\n边界最低塔伤 min={score(tw):.0f}  平均 avg={sum(d)/len(d):.0f}',fontname='Noto Serif CJK SC')
    ax.set_xlim(14,52-1.5); ax.set_ylim(46,8); ax.grid(alpha=.15)
    plt.colorbar(sc,ax=ax,fraction=.04,label='6-tower damage per tick (x100 labels)')
fig.suptitle('W46N8 RCL8 final layout + min-cut outer defense (30 tiles: 28 wall, 2 rampart gates in cyan)\nterrain: black=wall, olive=swamp; red ^ = towers; green * = controller; yellow = sources')
plt.tight_layout(); plt.savefig(f'{ROOT}/docs/final_layout_defense.png',dpi=110)
