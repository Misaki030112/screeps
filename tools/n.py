exec(open('scan.py').read().split('rooms=')[0])
import time
R="E21N56 E22N51 E22N52 E23N53 E25N52 E25N54 E25N55 E26N51 E26N52 E26N54 E26N55 E26N56 E27N53 E27N55 E27N58 E28N58 E28N59 E29N52".split()
for r in R:
    o=req(f'game/room-objects?room={r}&shard=shard3')['objects']
    src=[(x['x'],x['y']) for x in o if x['type']=='source']
    c=[(x['x'],x['y'],x.get('reservation',{}).get('user') if x.get('reservation') else None,x.get('user')) for x in o if x['type']=='controller']
    m=[(x['mineralType'],x['x'],x['y']) for x in o if x['type']=='mineral']
    other=sorted(set(x['type'] for x in o)-{'source','controller','mineral'})
    t=req(f'game/room-terrain?room={r}&shard=shard3&encoded=1')['terrain'][0]['terrain']
    print(r,src,c,m,other,'wall',round((t.count('1')+t.count('3'))/25),'swamp',round(t.count('2')/25))
    open(f'terrain_{r}.txt','w').write(t); time.sleep(.3)
