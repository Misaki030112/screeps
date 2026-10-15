import json,re,matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, numpy as np
from matplotlib.lines import Line2D; from matplotlib.patches import Patch
plt.rcParams['font.family']='Noto Serif CJK SC'
ROOT='/workspace/screeps'; R=json.load(open(f'{ROOT}/data/defense_plan3.json'))
T=open(f'{ROOT}/data/terrain_W46N8.txt').read().strip(); ter=lambda x,y:T[y*50+x]
L=json.loads(re.search(r'module.exports = (\{.*\});',open(f'{ROOT}/src/layouts/W46N8.js').read(),re.S).group(1))
S={}
for r,d in L['rcl'].items():
    for t,ps in d.items():
        for p in ps: S.setdefault(tuple(p),[]).append(t)
cut=[tuple(c) for c in R['cut']]
G4={'TR 右上 (外矿主路)':[(47,16),(47,17)],'BR 右下':[(44,27)],'BL 左下 (西出口主门)':[(23,35)],'TL 左上 (能源A侧)':[(25,16)]}
gates=[g for v in G4.values() for g in v]
towers=[tuple(t) for t in R['mc']]; built=[(36,29),(37,33)]
fig,ax=plt.subplots(figsize=(13,16))
col={'1':(.15,.15,.15),'2':(.55,.62,.42),'0':(.93,.92,.88)}
ax.imshow(np.array([[col[ter(x,y)] for x in range(50)] for y in range(50)]))
sym={'spawn':('o','#ff00ff',9),'extension':('s','#f5c518',6),'storage':('D','#ffffff',10),'link':('d','#00b8d4',9),'lab':('p','#9b59b6',8),'terminal':('H','#2ecc71',9),'factory':('P','#777',8),'nuker':('X','#000',8),'observer':('*','#0af',9),'powerSpawn':('8','#f60',8),'container':('s','#8b5a2b',8),'extractor':('h','#888',9)}
for p,ts in S.items():
    if 'rampart' in ts and p not in towers: ax.add_patch(plt.Rectangle((p[0]-.5,p[1]-.5),1,1,fill=False,ec='#1e90ff',lw=2))
    for t in ts:
        if t in sym: m,c,s=sym[t]; ax.plot(*p,m,color=c,ms=s,mec='k',mew=.5)
def line(pts,c,ls='-',lw=3.5): ax.plot([p[0] for p in pts],[p[1] for p in pts],ls,color=c,lw=lw,alpha=.85,solid_capstyle='round')
line(L['routes']['srcA'],'#ff8c00')
line([(38,32),(37,31)],'#c71585',lw=5)
line(R['remote_path'],'#228b22','--')
line([(37,29),(30,31)],'#00b8d4',':',4)
line(L['positions']['queenRoute'],'#9932cc','-',2)
for t in towers[2:]:
    if t==(31,11): line([(31,12),t],'#e02020',':',3)
    else: line([(36,32),(38,31),(38,25),t] if t[1]<26 else [(36,32),(34,31),t],'#e02020',':',3)
TRK=json.load(open(f'{ROOT}/data/trunks5.json'))
for n,v in TRK.items():
    pts=v['path']; c='#000000' if n=='TR' else '#888888'
    for q in v['new_tiles']: ax.add_patch(plt.Rectangle((q[0]-.5,q[1]-.5),1,1,color=c if n=='TR' else '#bbbbbb',alpha=.55))
    ax.plot([p[0] for p in pts],[p[1] for p in pts],color=c,lw=2.5,ls='-' if n=='TR' else (0,(1,1.5)))
for c in cut:
    if c in gates: ax.add_patch(plt.Rectangle((c[0]-.5,c[1]-.5),1,1,color='#00e5ff',ec='k',lw=2))
    else: ax.add_patch(plt.Rectangle((c[0]-.5,c[1]-.5),1,1,color='#5a3a1a',ec='k',lw=.5))
for t in towers:
    b=t in built
    ax.plot(*t,'^',color='#d00000' if b else '#ff9999',ms=17,mec='k',mew=1.5)
    ax.add_patch(plt.Rectangle((t[0]-.5,t[1]-.5),1,1,fill=False,ec='#1e90ff',lw=2))
    ax.annotate(f'{t[0]},{t[1]}'+(' 已建' if b else ''),t,xytext=(t[0]+(1.2 if t!=(39,23) else -3.5),t[1]+(-0.9 if t!=(39,23) else -1.6)),fontsize=12,weight='bold',color='k',bbox=dict(fc='w',alpha=.85,pad=1))
off={'TR':(-9,-3),'BR':(-3,4),'BL':(-2,3.5),'TL':(-4,-3.5)}
for name,gs in G4.items():
    g=gs[0]; o=off[name[:2]]
    ax.annotate(f"{name}\n门 {' + '.join(f'{a},{b}' for a,b in gs)} 宽{len(gs)}",g,xytext=(g[0]+o[0],g[1]+o[1]),fontsize=12,weight='bold',color='#006064',bbox=dict(fc='w',pad=1),arrowprops=dict(arrowstyle='->',lw=2))
ax.plot(28,32,'*',color='#00c853',ms=22,mec='k'); ax.annotate('控制器',(28,32),xytext=(25,34),fontsize=12,weight='bold')
for s,n in [((32,11),'能源A'),((39,33),'能源B')]: ax.plot(*s,'o',color='yellow',ms=15,mec='k'); ax.annotate(n,s,xytext=(s[0]+1,s[1]+1.3),fontsize=12,weight='bold')
ax.annotate('矿物',(40,24),xytext=(42,25.5),fontsize=11,weight='bold')
h=[Patch(color='#5a3a1a',label=f'实心墙 constructedWall ({len(cut)-len(gates)})'),Patch(color='#00e5ff',ec='k',label=f'rampart 门 ({len(gates)})'),
   Patch(fill=False,ec='#1e90ff',lw=2,label='rampart 覆盖关键建筑'),
   Line2D([],[],marker='^',ls='',color='#d00000',mec='k',ms=14,label='塔(已建)'),Line2D([],[],marker='^',ls='',color='#ff9999',mec='k',ms=14,label='塔(规划)'),
   Line2D([],[],color='#ff8c00',lw=3.5,label='能源A ↔ 仓库 (RCL6 后走 link)'),Line2D([],[],color='#c71585',lw=5,label='能源B 矿工 → 仓库'),
   Line2D([],[],color='#228b22',ls='--',lw=3.5,label='外矿 W45N8 路线(经门)'),Line2D([],[],color='#00b8d4',ls=':',lw=4,label='中心 link → 控制器 link'),
   Line2D([],[],color='#000',lw=2.5,label='干道 TR（随门一起修，5 格新路）'),Line2D([],[],color='#888',ls=(0,(1,1.5)),lw=2.5,label='干道 BL/TL/BR（按需再修）'),
   Line2D([],[],color='#9932cc',lw=2,label='queen 填充路线'),Line2D([],[],color='#e02020',ls=':',lw=3,label='塔补能路线')]
ax.legend(handles=h,loc='upper center',bbox_to_anchor=(0.5,-0.04),ncol=2,fontsize=13,framealpha=.95)
s=R['mc_score']
ax.set_title(f"W46N8 RCL8 最终布局 v5（墙+门+塔+干道）\n边界最低塔伤 {s['bmin']:.0f}/tick · 核心最低 {s['cmin']:.0f} · 门 {s['gmin']:.0f} · 综合分 {s['score']}",fontsize=16,weight='bold')
ax.set_xlim(20.5,49.5); ax.set_ylim(41.5,5.5); ax.set_xticks(range(21,50,2)); ax.set_yticks(range(6,42,2)); ax.tick_params(labelsize=10); ax.grid(alpha=.2)
plt.tight_layout(); plt.savefig(f'{ROOT}/docs/final_layout_v5.png',dpi=100)
