exec(open('scan.py').read().split('rooms=')[0])
import re,collections
G={g['room']:g for g in json.load(open('good.json'))}
def nb(r,d=2):
    m=re.match(r'([WE])(\d+)([NS])(\d+)',r);a,x,b,y=m.groups();x,y=int(x),int(y)
    return [f"{a}{x+i}{b}{y+j}" for i in range(-d,d+1) for j in range(-d,d+1) if x+i>=0 and y+j>=0]
def bfs(t,s):
    D={s:0};q=collections.deque([s])
    while q:
        x,y=q.popleft()
        for dx in(-1,0,1):
            for dy in(-1,0,1):
                n=(x+dx,y+dy)
                if 0<n[0]<49 and 0<n[1]<49 and n not in D and t[n[1]*50+n[0]]!='1' and t[n[1]*50+n[0]]!='3':
                    D[n]=D[(x,y)]+(5 if t[n[1]*50+n[0]]=='2' else 1);q.append(n)
    return D
for r in ['W47N7','W46N8','W47N6','W4N28','W32S9']:
    g=G[r];t=open(f'terrain_{r}.txt').read()
    ms=req('game/map-stats',{"rooms":nb(r),"shard":"shard3","statName":"owner0"});u={k:v['username'] for k,v in ms['users'].items()}
    owners=[(k,u[s['own']['user']],s['own']['level']) for k,s in ms['stats'].items() if s.get('own')]
    Ds=[bfs(t,tuple(p)) for p in g['src']+[g['ctl']]]
    best=None
    for x in range(5,45):
        for y in range(5,45):
            if any(t[(y+j)*50+x+i]!='0' for i in(-2,-1,0,1,2) for j in(-2,-1,0,1,2)): continue
            if any((x,y) not in D for D in Ds): continue
            c=Ds[0][(x,y)]+Ds[1][(x,y)]+0.7*Ds[2][(x,y)]
            if not best or c<best[0]: best=(c,x,y,[D[(x,y)] for D in Ds])
    print(r,g,'spawn',best,'neighbors',owners)
