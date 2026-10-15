// v5 defense plan: walls/gates/trunks live only in layout.defense (never auto-placed); towers v3 in rcl7/8.
const assert=require('assert'),fs=require('fs'),path=require('path');
const L=require('../src/layouts/W46N8'); const LJ=fs.readFileSync(path.join(__dirname,'../src/managers/layout.js'),'utf8');
const k=p=>p.join(',');
assert.deepStrictEqual(L.rcl['7'].tower.map(k),['39,23']);
assert.deepStrictEqual(L.rcl['8'].tower.map(k).sort(),['31,11','32,30','40,23']);
for(const r in L.rcl) for(const t in L.rcl[r]) assert.ok(t!=='constructedWall','walls must not be in rcl[]');
assert.ok(!/defense/.test(LJ),'layout.js must not read defense.*');
const g=Object.values(L.defense.gates).flat().map(k); assert.deepStrictEqual(g.sort(),['20,44','25,16','44,27','47,16','47,17','6,28']);
assert.strictEqual(L.defense.walls_in_build_order.length,41);
const all=new Set(); for(const r in L.rcl) for(const t in L.rcl[r]) for(const p of L.rcl[r][t]) if(t!=='rampart'&&t!=='road') { assert.ok(!all.has(k(p)),'dup '+k(p)); all.add(k(p)); }
console.log('defense_gate OK');
// v6 repair access: spurs only in defense.repair, phases set, never in rcl roads
const rep=L.defense.repair; assert.ok(rep&&rep['NW_26-28_7-12']&&rep['W_6_24-32']&&rep['S_10_46-48']&&rep['S_20_44-47']&&!rep['W_23_27-29']);
const roads=new Set(); for(const r in L.rcl) for(const p of (L.rcl[r].road||[])) roads.add(k(p));
for(const n in rep) for(const p of rep[n].spur) assert.ok(!roads.has(k(p)),'spur in rcl roads '+k(p));
for(const o of ['23,27','23,28','23,29','23,35','23,36','23,37','23,38']) assert.ok(!L.defense.walls_in_build_order.map(k).includes(o),'obsolete v6 wall '+o);
assert.ok(!L.defense.trunks.BL&&L.defense.trunks.W&&L.defense.trunks.S,'trunks W/S replace BL');
console.log('repair access OK');
