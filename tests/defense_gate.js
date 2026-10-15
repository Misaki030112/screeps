// v5 defense plan: walls/gates/trunks live only in layout.defense (never auto-placed); towers v3 in rcl7/8.
const assert=require('assert'),fs=require('fs'),path=require('path');
const L=require('../src/layouts/W46N8'); const LJ=fs.readFileSync(path.join(__dirname,'../src/managers/layout.js'),'utf8');
const k=p=>p.join(',');
assert.deepStrictEqual(L.rcl['7'].tower.map(k),['39,23']);
assert.deepStrictEqual(L.rcl['8'].tower.map(k).sort(),['31,11','32,30','40,23']);
for(const r in L.rcl) for(const t in L.rcl[r]) assert.ok(t!=='constructedWall','walls must not be in rcl[]');
assert.ok(!/defense/.test(LJ),'layout.js must not read defense.*');
const g=Object.values(L.defense.gates).flat().map(k); assert.deepStrictEqual(g.sort(),['23,35','25,16','44,27','47,16','47,17']);
assert.strictEqual(L.defense.walls_in_build_order.length,33);
const all=new Set(); for(const r in L.rcl) for(const t in L.rcl[r]) for(const p of L.rcl[r][t]) if(t!=='rampart'&&t!=='road') { assert.ok(!all.has(k(p)),'dup '+k(p)); all.add(k(p)); }
console.log('defense_gate OK');
