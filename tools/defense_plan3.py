"""v3: enclose core + source A (padding 3 where feasible), walls everywhere except gates on routes leaving room."""
import json, collections, sys
sys.argv=['x']; import defense_plan2 as D
SRCA_PROT=D.dil(D.SRCA,3)|D.dil(D.srcA_road,1)
prot=D.protB|SRCA_PROT
cut,inside=D.mincut(prot)
# route to remote W45N8: BFS from (43,20) to east edge (x=49) through non-wall, preferring plains
import heapq
def path(start,goal_fn):
    pq=[(0,start)];dist={start:0};prev={}
    while pq:
        d,p=heapq.heappop(pq)
        if goal_fn(p): 
            out=[p]
            while p in prev: p=prev[p]; out.append(p)
            return out[::-1]
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                n=(p[0]+dx,p[1]+dy)
                if not(0<=n[0]<50 and 0<=n[1]<50) or D.wall(*n) or n==p: continue
                c=d+(1 if n in D.roads else (5 if D.ter(*n)=='2' else 2))
                if c<dist.get(n,1e9): dist[n]=c; prev[n]=p; heapq.heappush(pq,(c,n))
remote=path((36,32),lambda p:p[0]==49 and abs(p[1]-12)<=2)
gates=[c for c in cut if c in set(remote)]
D.roads|=set(remote)
D.MINER_FEED=True
res=D.evaluate(cut,inside,'v3')
res['gates']=gates; res['remote_path']=remote
res['srcA_inside']=all(p in inside for p in [(31,12),(30,11)])
res['ctrl_inside']=(28,32) in inside or (28,32) in D.protB
json.dump(res,open(f'{D.ROOT}/data/defense_plan3.json','w'),default=list)
print({k:v for k,v in res.items() if k not in('remote_path',)})
