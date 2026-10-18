// quad pure helpers + inert gate + combat intel. node tests/quad.js
const path = require('path'), assert = require('assert'), src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, {
  _: require('lodash'),
  RANGED_ATTACK: 'ranged_attack', HEAL: 'heal', MOVE: 'move', CLAIM: 'claim', WORK: 'work', CARRY: 'carry', ATTACK: 'attack',
  RESOURCE_ENERGY: 'energy', STRUCTURE_ROAD: 'road', STRUCTURE_CONTAINER: 'container', STRUCTURE_RAMPART: 'rampart',
  STRUCTURE_TOWER: 'tower', TERRAIN_MASK_WALL: 1, TERRAIN_MASK_SWAMP: 2,
  BODYPART_COST: { ranged_attack:150, heal:250, move:50, claim:600, work:100, carry:50, attack:80 },
  Game: { time:1, creeps:{}, rooms:{}, map:{ getRoomTerrain:()=>({get:()=>0}) } }, Memory: {},
  PathFinder: { CostMatrix: class { constructor(){this.m={};} set(x,y,v){this.m[x+','+y]=v;} get(x,y){return this.m[x+','+y]||0;} } },
  RoomPosition: class { constructor(x,y,r){this.x=x;this.y=y;this.roomName=r;} },
});
const Q = require(src('roles/quad.js')), CQ = require(src('roles/conquest.js'));
const T = (w=new Set(), s=new Set()) => (x,y) => w.has(x+','+y)?'wall':s.has(x+','+y)?'swamp':'plain';
const P = (x,y,rn='R') => ({x,y,roomName:rn});
const creep = (parts, hits=1000, x=5, y=5) => ({
  body: parts.map(t=>({type:t,hits:100})), hits, hitsMax:1000, pos:P(x,y),
  getActiveBodyparts: t => parts.filter(p=>p===t).length,
});

// formation
assert.strictEqual(Q.anchorCost(10,10,T()), 2);
assert.strictEqual(Q.anchorCost(10,10,T(new Set(['11,11']))), 255);
assert.strictEqual(Q.anchorCost(10,10,T(new Set(), new Set(['10,11']))), 10);
assert.strictEqual(Q.anchorCost(48,10,T()), 255);
assert.deepStrictEqual(Q.formedAnchor({0:P(5,5),1:P(6,5),2:P(5,6),3:P(6,6)}), {x:5,y:5,roomName:'R'});
assert.strictEqual(Q.formedAnchor({0:P(5,5),1:P(6,5),2:P(5,6),3:P(7,6)}), null);

// heal
const me = Object.assign(creep(['heal'],1000,5,5),{n:'a'}); me.n='a';
const b = Object.assign(creep(['heal'],600,6,5),{n:'b'});
const c = Object.assign(creep(['heal'],300,8,5),{n:'c'});
assert.deepStrictEqual(Q.healPick(me,[me,b,c]).map(x=>x.n||x), ['b','heal']);
assert.deepStrictEqual(Q.healPick(me,[me,c]).map(x=>x.n||x), ['c','rangedHeal']);

// combat intel (Overmind-style)
assert.strictEqual(Q.towerDmg(1), 600);
assert.strictEqual(Q.towerDmg(20), 150);
assert.strictEqual(Q.towerDmg(12.5), 375);
const atk = creep(['attack','attack','move'],1000,5,5);
assert.strictEqual(Q.dmgAt(P(5,5),[atk],[]), 60); // r0<=2 melee
assert.strictEqual(Q.dmgAt(P(10,10),[atk],[]), 0);
const healer = creep(['heal','heal','move'],1000,5,5);
assert.strictEqual(Q.hostileHealTo(healer,[healer]), 24);

// score: CLAIM first
const res = Object.assign(creep(['claim','move'],100,20,5),{id:'res',hits:100});
const haul = Object.assign(creep(['carry','move'],100,6,5),{id:'haul',hits:100});
const team = [{pos:P(5,5),ra:4}];
assert.ok(Q.scoreTarget(res,team,[res,haul]) > Q.scoreTarget(haul,team,[res,haul]));

// useMass: 3 hostiles at range 1 -> mass 30 > 10
assert.ok(Q.useMass({pos:P(5,5)}, [creep(['a'],100,5,5),creep(['a'],100,5,6),creep(['a'],100,6,5)]));
assert.ok(!Q.useMass({pos:P(5,5)}, [creep(['a'],100,8,5)])); // range 3 = 1 < 10

// combatStep: melee at range 2 south of the south cells -> step north (dir 1) to open the gap
const anc = {x:10,y:10,roomName:'R'};
const meleeH = [Object.assign(creep(['attack','move'],1000,10,13),{pos:P(10,13)})]; // range 2 from (10,11)
const step = Q.combatStep(anc, meleeH, [], null, (x,y)=>x>=1&&y>=1&&x<=48&&y<=48);
assert.ok(step === 1 || step === 8 || step === 2, 'step away northish, got '+step);
// stay when already at range >=3 from every cell to melee
const farMelee = [Object.assign(creep(['attack'],1000,10,15),{pos:P(10,15)})]; // min range from south cells = 4
const stay = Q.combatStep(anc, farMelee, [], null, (x,y)=>true);
assert.strictEqual(stay, 0, 'already safe at range>=3: stay and shoot');

// rotate: hurt member gets the back cell (farther from threat)
const m1 = Object.assign(creep(['heal'],200,10,10),{name:'hurt',hits:200});
const m2 = Object.assign(creep(['heal'],1000,11,10),{name:'tank',hits:1000});
const rot = Q.rotateAssign(anc, [m1,m2], {pos:P(10,5)});
// threat is north (y=5); back cells have higher y (OFF[2]=[0,1] y=11, OFF[3]=[1,1] y=11)
assert.ok([2,3].includes(rot.hurt), 'hurt assigned to back: '+rot.hurt);

// bodies
assert.strictEqual(Q.BODY().reduce((s,p)=>s+BODYPART_COST[p],0), 2300);
assert.strictEqual(CQ.BREAKER_BODY().reduce((s,p)=>s+BODYPART_COST[p],0), 1950);
assert.strictEqual(CQ.HAULER_BODY().reduce((s,p)=>s+BODYPART_COST[p],0), 1000);

// INERT gate
const room = {storage:{store:{energy:50000}}};
Memory.ops = {cq:{quadSpawn:true,spawn:true,claim:true,reinforce:8,cmd:'go'}};
assert.strictEqual(Q.wantSpawn(room), null);
assert.strictEqual(CQ.wantSpawn(room), null);
Memory.ops.cq.armed = true;
assert.strictEqual(Q.wantSpawn(room).role, 'cqquad');
Memory.ops.cq.cmd = 'retreat';
assert.strictEqual(Q.wantSpawn(room), null);
Memory.ops.cq.cmd = 'go';
// reinforce: after 4 spawned, still want more if reinforce=4 (want=0+4=4 wait, quadSpawn true so want=8)
Memory.ops.cq.quadSpawn = true; Memory.ops.cq.reinforce = 4;
Game.creeps = {};
for (let i=0;i<4;i++) Game.creeps['q'+i] = {memory:{role:'cqquad',qid:0,qi:i}};
// want = 4 (quadSpawn) + 4 (reinforce) = 8; n=4 -> still spawn
assert.strictEqual(Q.wantSpawn(room).role, 'cqquad');
// danger helper still exists but is NOT wired to auto-retreat (manual check)
assert.strictEqual(typeof CQ.danger, 'function');

// dynamic shapes
assert.deepStrictEqual(Q.shapeOf(2), [[0,0],[1,0]]);
assert.deepStrictEqual(Q.formedAnchor({0:P(5,5),1:P(6,5)}, 2), {x:5,y:5,roomName:'R'});
assert.strictEqual(Q.formedAnchor({0:P(5,5),1:P(6,6)}, 2), null);
assert.deepStrictEqual(Q.formedAnchor({0:P(5,5),1:P(6,5),2:P(5,6)}, 3), {x:5,y:5,roomName:'R'});
assert.strictEqual(Q.anchorCost(10,10,T(),undefined,Q.shapeOf(2)), 2);
assert.strictEqual(Q.shouldGo("go", true, 1, 2), false, "cmd=go alone must not advance size 1");
assert.strictEqual(Q.shouldGo("go", true, 2, 2), true);
assert.strictEqual(Q.shouldGo("hold", true, 2, 2), true, "earlyGo duo");
assert.strictEqual(Q.shouldGo("hold", false, 2, 2), false);
assert.strictEqual(Q.shouldGo("retreat", true, 4, 2), false);

// ensureIds: ≤4 members always collapse onto qid 0 (orphan qid=1 must not idle at rally)
Game.creeps = {
  a: {name:'a', memory:{role:'cqquad',born:1,qid:0,qi:0}},
  b: {name:'b', memory:{role:'cqquad',born:2,qid:0,qi:1}},
  c: {name:'c', memory:{role:'cqquad',born:3,qid:0,qi:2}},
  d: {name:'d', memory:{role:'cqquad',born:4,qid:1,qi:0}},
};
const g = Q.ensureIds(Object.values(Game.creeps));
assert.strictEqual(Object.keys(g).join(','), '0');
assert.strictEqual(g[0].length, 4);
assert.ok(Object.values(Game.creeps).every(c => c.memory.qid===0), 'all qid 0');

console.log("quad ok");


