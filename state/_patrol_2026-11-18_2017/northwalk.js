const path=require('path');
const ROOT='/workspace/screeps';
const fs=require('fs');
const T=fs.readFileSync(path.join(ROOT,'data/terrain_W47N8.txt'),'utf8').trim();
const L=require(path.join(ROOT,'src/rooms/w47n8/layout.js'));
const R=require(path.join(ROOT,'src/rooms/w47n8/roads.js'));
const C=require(path.join(ROOT,'src/rooms/w47n8/config.js'));
const F=require(path.join(ROOT,'src/rooms/w47n8/fill.js'));
const roads=new Set();
for (const p of R.ROADS) roads.add(p[0]+','+p[1]);
for (const p of L.ORDER.road || []) roads.add(p[0]+','+p[1]);
const block=new Set();
function mark(list){ for (const [x,y] of list) block.add(x+','+y); }
mark(L.ORDER.spawn.slice(0,2));
mark(L.ORDER.tower.slice(0,3));
mark(L.ORDER.extension.slice(0,50));
mark(L.ORDER.storage);
mark([[32,33],[13,25],[26,12]]);
mark(L.ORDER.terminal);
function route(sx,sy,gx,gy,range,extra,costExtra){
  const key=(x,y)=>x*50+y;
  const h=(x,y)=>Math.max(Math.abs(x-gx),Math.abs(y-gy));
  const cost=(x,y)=>{
    if(x<0||y<0||x>49||y>49) return 255;
    if(T[y*50+x]==='1'||block.has(x+','+y)) return 255;
    if(extra&&extra.has(x+','+y)) return 255;
    if(costExtra&&costExtra.has(x+','+y)) return costExtra.get(x+','+y);
    if(x===34&&y===32) return F.POST_COST;
    if(roads.has(x+','+y)) return 1;
    return T[y*50+x]==='2'?10:2;
  };
  const open=[[0,0,sx,sy]];
  const gs=new Map([[key(sx,sy),0]]), prev=new Map(), seen=new Set();
  while(open.length){
    open.sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
    const [,g,x,y]=open.shift();
    const k=key(x,y);
    if(seen.has(k)||g!==gs.get(k)) continue;
    seen.add(k);
    if(!(x===sx&&y===sy)&&h(x,y)<=range){
      const path=[]; let c=k;
      while(c!==undefined){ path.push(Math.floor(c/50)+','+(c%50)); c=prev.get(c); }
      return {path:path.reverse(), cost:g};
    }
    for(let dy=-1;dy<=1;dy++) for(let dx=-1;dx<=1;dx++) if(dx||dy){
      const nx=x+dx, ny=y+dy, cc=(nx===sx&&ny===sy)?0:cost(nx,ny);
      if(cc>=255) continue;
      const nk=key(nx,ny), ng=g+cc;
      if(ng<(gs.get(nk)??1e9)){ gs.set(nk,ng); prev.set(nk,k); open.push([ng+1.2*h(nx,ny),ng,nx,ny]); }
    }
  }
  return null;
}
function show(label, r){
  if(!r){ console.log(label, 'NO PATH'); return; }
  console.log(label, 'cost='+r.cost, 'len='+r.path.length, r.path.slice(0,20).join(' -> ')+(r.path.length>20?' ...':'') );
  console.log('  has 32,29='+r.path.includes('32,29')+' 34,32='+r.path.includes('34,32')+' 33,34='+r.path.includes('33,34')+' 32,35='+r.path.includes('32,35')+' 32,32='+r.path.includes('32,32'));
}
// designed occupied-hub (pocket raised)
const viaPost=new Map([['32,32', F.POCKET_COST],['33,33', F.POCKET_COST]]);
show('open 34,30->12,25', route(34,30,12,25,0));
show('occ hub 34,30->12,25', route(34,30,12,25,0,null,viaPost));
// 33,34 blocked
show('33,34 blocked 34,30->12,25', route(34,30,12,25,0,new Set(['33,34']),viaPost));
show('33,34 blocked no pocket raise', route(34,30,12,25,0,new Set(['33,34'])));
show('33,34+34,32 blocked', route(34,30,12,25,0,new Set(['33,34','34,32']),viaPost));
// 33,34 high cost not 255
for (const c of [8,10,12,16,20]) {
  const m=new Map([['32,32',F.POCKET_COST],['33,33',F.POCKET_COST],['33,34',c]]);
  show('33,34 cost '+c+' occ-hub', route(34,30,12,25,0,null,m));
}
show('from 32,32 33,34 blocked', route(32,32,12,25,0,new Set(['33,34']),viaPost));
show('from 32,30 33,34 blocked', route(32,30,12,25,0,new Set(['33,34']),viaPost));
show('from 33,31 33,34 blocked', route(33,31,12,25,0,new Set(['33,34']),viaPost));
