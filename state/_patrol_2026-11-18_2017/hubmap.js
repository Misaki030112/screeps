const path=require('path');
const ROOT='/workspace/screeps';
const fs=require('fs');
const T=fs.readFileSync(path.join(ROOT,'data/terrain_W47N8.txt'),'utf8').trim();
const L=require(path.join(ROOT,'src/rooms/w47n8/layout.js'));
const R=require(path.join(ROOT,'src/rooms/w47n8/roads.js'));
const C=require(path.join(ROOT,'src/rooms/w47n8/config.js'));
const roads=new Set(R.ROADS.map(p=>p[0]+','+p[1]));
const typ={};
for (const [k,arr] of Object.entries(L.ORDER||{})) {
  if (!Array.isArray(arr)) continue;
  for (const p of arr) typ[p[0]+','+p[1]]=(typ[p[0]+','+p[1]]?typ[p[0]+','+p[1]]+'/':'')+k;
}
function cell(x,y){
  const t=T[y*50+x];
  const terr=t==='1'?'WALL':t==='2'?'SWAMP':'plain';
  const rd=roads.has(x+','+y)?' ROAD':'';
  const st=typ[x+','+y]?' '+typ[x+','+y]:'';
  return x+','+y+' '+terr+rd+st;
}
console.log('SPAWN config', C.SPAWN, 'HUB_CONT', C.HUB_CONT, 'storage', L.ORDER.storage);
console.log('--- 31-37, 29-36 ---');
for(let y=29;y<=36;y++){
  const row=[];
  for(let x=31;x<=37;x++) row.push(cell(x,y));
  console.log(row.join(' | '));
}
