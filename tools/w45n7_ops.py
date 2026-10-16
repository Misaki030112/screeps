"""W45N7 ops plan: spawn budget formula + tick sim (analysis only)."""
import json, random, heapq
COST={'W':100,'C':50,'M':50,'K':600,'R':150,'H':250,'A':80}
def body(s):  # "6W1C3M"
    import re; return [(int(n),t) for n,t in re.findall(r'(\d+)([A-Z])',s)]
def cost(s): return sum(n*COST[t] for n,t in body(s))
def parts(s): return sum(n for n,_ in body(s))
# role, body, count, lifetime, lead(travel ticks to job)
def roster(rcl, w7=True, w7hauler='8C8M', n7=6):
    r=[('miner','5W1C3M',2,1500,10),('upgrader','12W1C1M',3,1500,8),('queen','12C6M',1,1500,2),('hauler','14C7M',1,1500,5),
       ('rminer8','6W1C3M',1,1500,35),('rhauler8','8C8M',2,1500,35),('reserver8','2K2M',1,600,35)]
    # W45N8 reserver: buffer -> one per ~1060t => model as lifetime 1060 equivalent
    r[-1]=('reserver8','2K2M',1,1060,35)
    if w7:
        r+= [('rminer7','6W1C3M',1,1500,140),('rhauler7',w7hauler,n7,1500,140),('reserver7','2K2M',1,922,140)]
    if rcl>=6: r=[x if x[0]!='upgrader' else ('upgrader','15W2C3M',3,1500,8) for x in r]
    return r
def budget(rs):
    t=sum(parts(b)*3*n*1500/l for _,b,n,l,_ in rs); e=sum(cost(b)*n/l for _,b,n,l,_ in rs)
    return t, t/1500, e
def sim(rs, T=6000, seed=1, defender_at=(2000,4100), deaths_sync=False):
    random.seed(seed); due=[]  # (tick needed, prio, role, spawnticks)
    prio={'queen':0,'defender':1,'miner':2,'hauler':3,'rminer8':4,'rminer7':4,'reserver8':5,'reserver7':5,'rhauler8':6,'rhauler7':6,'upgrader':7}
    for role,b,n,l,lead in rs:
        st=parts(b)*3
        for i in range(n):
            first= 0 if deaths_sync else random.randint(0,l)
            t=first
            while t<T: heapq.heappush(due,(max(0,t-st-lead),prio[role],role,st,t)); t+=l
    for d in defender_at: heapq.heappush(due,(d,1,'defender',36,d))
    busy=0; t=0; delays={}; q=[]; util=0
    pending=sorted(due)
    i=0; maxq=0
    while t<T:
        while i<len(pending) and pending[i][0]<=t: q.append(pending[i]); i+=1
        maxq=max(maxq,len(q))
        if busy<=t and q:
            q.sort(key=lambda x:(x[1],x[0])); want,p,role,st,need=q.pop(0)
            done=t+st; late=max(0,done-(need- {'rminer7':140,'rhauler7':140,'reserver7':140}.get(role,35 if role[-1]=='8' else 0)))
            delays.setdefault(role,[]).append(t-want); busy=done; util+=st
        t+=1
    return {r:(max(v),round(sum(v)/len(v),1)) for r,v in delays.items()}, round(util/T*100,1), maxq
out={}
for rcl in (5,6):
  for name,rs in [('only_W45N8',roster(rcl,False)),('W45N7_6x8C8M',roster(rcl)),('W45N7_4x16C8M',roster(rcl,True,'16C8M',4))]:
    t,u,e=budget(rs)
    res=[sim(rs,seed=s) for s in range(20)]
    worst={}
    for d,_,_ in res:
        for k,v in d.items(): worst[k]=max(worst.get(k,0),v[0])
    sync=sim(rs,deaths_sync=True)
    out[f'RCL{rcl}|{name}']={'spawn_ticks_per1500':round(t),'util_formula_%':round(u*100,1),'energy_per_t':round(e,2),
        'util_sim_%':sum(r[1] for r in res)/20,'worst_wait_by_role':worst,'peak_queue':max(r[2] for r in res),'sync_deaths_worst':max(v[0] for v in sync[0].values())}
json.dump(out,open('/workspace/screeps/metrics/w45n7_ops.json','w'),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False,indent=1))
