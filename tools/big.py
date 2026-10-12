exec(open('scan.py').read().split('rooms=')[0])
import time
now=time.time()*1000; Z=[]
for q in ['E','W']:
  for v in ['N','S']:
    rs=[f"{q}{x}{v}{y}" for x in range(0,61) for y in range(0,61)]
    for i in range(0,len(rs),500):
      try: ms=req('game/map-stats',{"rooms":rs[i:i+500],"shard":"shard3","statName":"owner0"})
      except Exception as e: print(e); continue
      for r,s in ms['stats'].items():
        if s.get('status')=='normal' and not s.get('own') and ((s.get('novice') or 0)>now or (s.get('respawnArea') or 0)>now):
          Z.append((r,s.get('novice'),s.get('respawnArea')))
print(len(Z)); json.dump(Z,open('zones.json','w'))
for z in Z: print(z)
