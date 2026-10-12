exec(open('scan.py').read().split('rooms=')[0])
import time,re
Z=json.load(open('zones.json')); good=[]
for r,n,a in Z:
    try: o=req(f'game/room-objects?room={r}&shard=shard3')['objects']
    except Exception as e: print(r,e); continue
    src=[(x['x'],x['y']) for x in o if x['type']=='source']
    c=[x for x in o if x['type']=='controller']
    if len(src)!=2 or not c or c[0].get('reservation') or any(x['type'] in('spawn','keeperLair','invaderCore') for x in o): continue
    m=[(x['mineralType'],x['x'],x['y']) for x in o if x['type']=='mineral']
    t=req(f'game/room-terrain?room={r}&shard=shard3&encoded=1')['terrain'][0]['terrain']
    open(f'terrain_{r}.txt','w').write(t)
    g=dict(room=r,novice=n,resp=a,src=src,ctl=(c[0]['x'],c[0]['y']),min=m,wall=round((t.count('1')+t.count('3'))/25),swamp=round(t.count('2')/25),creeps=sum(x['type']=='creep' for x in o))
    print(g); good.append(g); time.sleep(.25)
json.dump(good,open('good.json','w'))
