import json,urllib.request,time
T=open('.env').read().split('=')[1].strip()
def req(p,body=None):
    r=urllib.request.Request('https://screeps.com/api/'+p,data=json.dumps(body).encode() if body else None,headers={'X-Token':T,'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(r))
import sys
rooms=[f"E{x}N{y}" for x in range(20,30) for y in range(50,60)]
ms=req('game/map-stats',{"rooms":rooms,"shard":"shard3","statName":"owner0"})
users={k:v['username'] for k,v in ms['users'].items()}
cand=[]
for r,s in ms['stats'].items():
    own=s.get('own'); 
    if own: print('OWN',r,users.get(own['user']),own['level']); continue
    if s.get('respawnArea') or s.get('novice'): print('Z',r,s.get('novice'),s.get('respawnArea'))
    if s.get('status')!='normal': continue
    cand.append((r,s.get('novice'),s.get('respawnArea'),s.get('sign')))
print(len(cand))
out=[]
for r,nov,resp,_ in cand:
    o=req(f'game/room-objects?room={r}&shard=shard3')['objects']
    src=[(x['x'],x['y']) for x in o if x['type']=='source']
    c=[(x['x'],x['y'],x.get('reservation')) for x in o if x['type']=='controller']
    m=[(x['mineralType'],x['x'],x['y']) for x in o if x['type']=='mineral']
    hostile=[x['type'] for x in o if x['type'] in('invaderCore','keeperLair')]
    if len(src)==2 and c and not hostile:
        t=req(f'game/room-terrain?room={r}&shard=shard3&encoded=1')['terrain'][0]['terrain']
        sw=t.count('1')+t.count('3');print(r,'nov',nov,'resp',resp,'src',src,'ctl',c,'min',m,'wall%',round(sw/25),'swamp%',round(t.count('2')/25))
        out.append(dict(room=r,src=src,ctl=c,terrain=t,min=m))
    time.sleep(0.3)
json.dump(out,open('cands2.json','w'))
