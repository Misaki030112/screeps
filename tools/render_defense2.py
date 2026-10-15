import json,re,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, numpy as np
ROOT='/workspace/screeps'; R=json.load(open(f'{ROOT}/data/defense_plan2.json'))
T=open(f'{ROOT}/data/terrain_W46N8.txt').read().strip(); ter=lambda x,y:T[y*50+x]
L=json.loads(re.search(r'module.exports = (\{.*\});',open(f'{ROOT}/src/layouts/W46N8.js').read(),re.S).group(1))
S={}
for r,d in L['rcl'].items():
    for t,ps in d.items():
        for p in ps: S.setdefault(tuple(p),[]).append(t)
roads={tuple(p) for r in L['routes'].values() for p in r}|{p for p,t in S.items() if 'road' in t}
ch=lambda p,q:max(abs(p[0]-q[0]),abs(p[1]-q[1]))
dmg=lambda r:600 if r<=5 else (150 if r>=20 else 600-450*(r-5)/15)
sym={'spawn':('o','#ff00ff'),'extension':('s','#f5c518'),'storage':('D','#fff'),'link':('d','#00e0ff'),'lab':('p','#9b59b6'),'terminal':('H','#2ecc71'),'factory':('P','#888'),'nuker':('X','#000'),'observer':('*','#0af'),'powerSpawn':('8','#f60'),'container':('s','#8b5a2b'),'extractor':('h','#aaa')}
B=R['B_srcA_outside']; A=R['A_srcA_inside']
cut=[tuple(c) for c in B['cut']]; gates=[tuple(g) for g in B['gates']]
fig,axs=plt.subplots(1,2,figsize=(21,10.5))
for ax,(title,tw) in zip(axs,[('Current plan towers 现行塔位',[tuple(t) for t in B['plan']]),('RECOMMENDED 推荐塔位 (multi-criteria)',[tuple(t) for t in B['mc']])]):
    col={'1':(.12,.12,.12),'2':(.33,.42,.2),'0':(.85,.85,.8)}
    ax.imshow(np.array([[col[ter(x,y)] for x in range(50)] for y in range(50)]))
    for p in roads: ax.add_patch(plt.Rectangle((p[0]-.5,p[1]-.5),1,1,color='#b0a080'))
    for p,ts in S.items():
        for t in ts:
            if t in sym: ax.plot(*p,sym[t][0],color=sym[t][1],ms=6,mec='k',mew=.4)
    d=[sum(dmg(ch(t,c)) for t in tw) for c in cut]
    sc=ax.scatter(*zip(*cut),c=d,cmap='RdYlGn',vmin=900,vmax=3600,s=170,marker='s',edgecolors=['cyan' if c in gates else 'k' for c in cut],linewidths=[3 if c in gates else .5 for c in cut])
    for c,v in zip(cut,d): ax.text(c[0],c[1],int(v//100),fontsize=5.5,ha='center',va='center')
    for p in [(31,12),(30,11)]: ax.add_patch(plt.Rectangle((p[0]-.5,p[1]-.5),1,1,fill=False,ec='cyan',lw=2.5))
    ax.plot(*zip(*[tuple(c) for c in A['cut'] if tuple(c) not in cut]),'x',color='#ff7f00',ms=7,mew=2,label='option A extra cut (src A inside)')
    for t in tw: ax.plot(*t,'^',color='#e02020',ms=12,mec='w')
    ax.plot(28,32,'*',color='#00ff88',ms=15,mec='k'); ax.plot(32,11,'o',color='yellow',ms=10,mec='k'); ax.plot(39,33,'o',color='yellow',ms=10,mec='k')
    sc_=B['plan_score'] if 'Current' in title else B['mc_score']
    ax.set_title(f"{title}\nmin boundary dmg={sc_['bmin']:.0f}  core min={sc_['cmin']:.0f}  gate min={sc_['gmin']:.0f}  refill avg={sc_['refill_avg']}  score={sc_['score']}",fontname='Noto Serif CJK SC')
    ax.set_xlim(20,49.5); ax.set_ylim(41,7); ax.legend(loc='lower right',fontsize=8)
    plt.colorbar(sc,ax=ax,fraction=.04,label='6-tower attack dmg/tick on boundary tile (labels x100)')
fig.suptitle('W46N8 RCL8 final layout — Option B: min-cut 32 tiles (padding 3) + gates (cyan) + local ramparts on source A container/link (cyan squares)\nred ^ towers; black=terrain wall, olive=swamp; orange x = extra tiles if source A is enclosed (option A, 37 tiles)')
plt.tight_layout(); plt.savefig(f'{ROOT}/docs/final_layout_defense.png',dpi=110)
