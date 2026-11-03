// 2026-10-30 20:4x strategy: dayObs fills Memory.ops.w8day (bill/miss*/why); no layout side effects required.
const assert = require('assert'), path = require('path');
const d = path.join(__dirname, '..', 'src/rooms/w47n8');
const K = { LOOK_STRUCTURES: 'structure', LOOK_CONSTRUCTION_SITES: 'constructionSite', FIND_MY_SPAWNS: 112,
  FIND_MY_CONSTRUCTION_SITES: 114, FIND_MY_STRUCTURES: 108, FIND_STRUCTURES: 107, FIND_DROPPED_RESOURCES: 1006, FIND_MINERALS: 116, FIND_MY_CREEPS: 106, OK: 0,
  STRUCTURE_SPAWN: 'spawn', STRUCTURE_TOWER: 'tower', STRUCTURE_EXTENSION: 'extension', STRUCTURE_STORAGE: 'storage',
  STRUCTURE_RAMPART: 'rampart', STRUCTURE_WALL: 'wall', STRUCTURE_CONTAINER: 'container', STRUCTURE_LINK: 'link',
  STRUCTURE_TERMINAL: 'terminal', STRUCTURE_EXTRACTOR: 'extractor', STRUCTURE_LAB: 'lab', STRUCTURE_FACTORY: 'factory',
  STRUCTURE_ROAD: 'road', STRUCTURE_POWER_SPAWN: 'powerSpawn', STRUCTURE_NUKER: 'nuker', STRUCTURE_OBSERVER: 'observer', RESOURCE_ENERGY: 'energy',
  ERR_RCL_NOT_ENOUGH: -14 };
Object.assign(global, K, { _: require('lodash'), Memory: { ops: { w8layout: 'approved' } }, Game: { time: 42, rooms: {}, creeps: {} },
  CONTROLLER_STRUCTURES: { spawn: [0,1,1,1,1,1,1,2,3], extension: [0,0,5,10,20,30,40,50,60], tower: [0,0,0,1,1,2,2,3,6],
    link: [0,0,0,0,0,2,3,4,6], storage: [0,0,0,0,1,1,1,1,1], container: Array(9).fill(5), road: Array(9).fill(2500),
    wall: [0,0,2500,2500,2500,2500,2500,2500,2500], rampart: [0,0,2500,2500,2500,2500,2500,2500,2500],
    terminal: [0,0,0,0,0,0,1,1,1], extractor: [0,0,0,0,0,0,1,1,1], lab: [0,0,0,0,0,0,3,6,10], factory: [0,0,0,0,0,0,0,1,1],
    powerSpawn: Array(8).fill(0).concat([1]), nuker: Array(8).fill(0).concat([1]), observer: Array(8).fill(0).concat([1]) } });
const W = require(path.join(d, 'index.js')), L = require(path.join(d, 'layout'));
function mk(rcl, built, creeps, progressLeft) {
  const st = {}, sites = [];
  for (const [x, y, t] of built) (st[x * 50 + y] = st[x * 50 + y] || []).push({ structureType: t, pos: { x, y, inRangeTo(x2, y2, r) { return Math.max(Math.abs(this.x - x2), Math.abs(this.y - y2)) <= r; } }, store: t === 'tower' ? { energy: 900 } : undefined });
  const pt = 3645000, p = pt - (progressLeft == null ? 400000 : progressLeft);
  const room = {
    name: 'W47N8',
    lookForAt: (k, x, y) => k === LOOK_STRUCTURES ? (st[x * 50 + y] || []) : sites.filter(s => s.pos.x === x && s.pos.y === y),
    find: (k, o) => {
      let a = [];
      if (k === FIND_MY_STRUCTURES) a = Object.values(st).flat();
      else if (k === FIND_MY_CONSTRUCTION_SITES) a = sites;
      else if (k === FIND_MY_SPAWNS) a = Object.values(st).flat().filter(s => s.structureType === 'spawn');
      return o && o.filter ? a.filter(o.filter) : a;
    },
    controller: { level: rcl, progress: p, progressTotal: pt },
    storage: { store: { energy: 2100 } },
    energyAvailable: 1800, energyCapacityAvailable: 2300,
  };
  Game.creeps = {};
  (creeps || []).forEach((c, i) => { const m = Object.assign({ home: 'W47N8' }, (c && c.memory) || {}); Game.creeps['c' + i] = Object.assign({ name: 'c' + i, room, pos: { roomName: 'W47N8' } }, c, { memory: m }); });
  return room;
}
const base = [[34, 30, 'spawn'], [35, 32, 'storage'], [33, 35, 'tower'], [24, 8, 'tower']]
  .concat(L.ORDER.extension.slice(0, 40).map(([x, y]) => [x, y, 'extension']));
// RCL6 mid: why=upgrade, bill = 15k+5k+30k = 50k
W.dayObs(mk(6, base, [{ memory: { role: 'w8builder' } }, { memory: { role: 'w8upgrader' } }, { memory: { role: 'w8upgrader' } }, { memory: { role: 'w8upgrader' } }], 400000));
let d0 = Memory.ops.w8day;
assert.strictEqual(d0.why, 'upgrade');
assert.strictEqual(d0.missSpawn, 1);
assert.strictEqual(d0.missTower, 1);
assert.strictEqual(d0.missExt, 10);
assert.strictEqual(d0.bill, 50000);
assert.strictEqual(d0.builders, 1);
assert.strictEqual(d0.upgraders, 3);
assert.strictEqual(d0.towerMinE, 900);
assert.strictEqual(d0.towerHubE, 900); // 33,35 not inRange4 of stand 26,11
assert.strictEqual(d0.towerNorthE, 900); // 24,8 inRange4 of stand
assert.strictEqual(d0.nf, 0); // north ≥600 → northFeed idle
assert.strictEqual(d0.eAvail, 1800);
assert.strictEqual(d0.eCap, 2300);
assert.ok('looseE' in d0, '08:4x looseE obs');
assert.strictEqual(d0.looseE, 0, 'no drops/conts in mk → 0');
// near RCL7
W.dayObs(mk(6, base, [], 50000));
assert.strictEqual(Memory.ops.w8day.why, 'near');
// 17:4x: north tower low → nf=1 (hub stays high); towerMinE tracks the dip
const lowN = mk(6, base, [], 50000);
const nt = lowN.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === 'tower' && s.pos.x === 24 })[0];
nt.store.energy = 450;
W.dayObs(lowN);
assert.strictEqual(Memory.ops.w8day.towerNorthE, 450);
assert.strictEqual(Memory.ops.w8day.towerHubE, 900);
assert.strictEqual(Memory.ops.w8day.towerMinE, 450);
assert.strictEqual(Memory.ops.w8day.nf, 1);
// Pre-flip bank/dayof assertions need gate OFF (live default is now true after Misaki flip).
const Cgate = require(path.join(d, 'config'));
Cgate.RCL6_MINERALS = false;
// 20:4x: RCL7 day-crit (spawn2+tower3) done but missExt=10 → leanBank ON, why=done, phase=bank20
// (was stuck dayof/leanBank=0 waiting for 50ext — mismatch vs 17:4x intent)
const midExt = base.concat([[33, 30, 'spawn'], [22, 7, 'tower']]); // still 40ext
W.dayObs(mk(7, midExt, [], 0));
assert.strictEqual(Memory.ops.w8day.missSpawn, 0);
assert.strictEqual(Memory.ops.w8day.missTower, 0);
assert.strictEqual(Memory.ops.w8day.missExt, 10);
assert.strictEqual(Memory.ops.w8day.why, 'done', 'day-crit done → why=done even mid-ext');
assert.strictEqual(Memory.ops.w8day.phase, 'bank20');
assert.strictEqual(Memory.ops.w8day.leanBank, 1, 'leanBank arms without 50ext');
assert.ok(Memory.ops.w8day.bankEta > 0, 'bankEta positive mid-ext leanBank');
// still missing day-crit → dayof, leanBank off
const critMiss = base; // no spawn2/tower3
W.dayObs(mk(7, critMiss, [], 0));
assert.strictEqual(Memory.ops.w8day.why, 'dayof');
assert.strictEqual(Memory.ops.w8day.phase, 'dayof');
assert.strictEqual(Memory.ops.w8day.leanBank, 0, 'leanBank waits for spawn2+tower3');
assert.strictEqual(Memory.ops.w8day.bankEta, -1);
// RCL7 with spawn2+tower3+50ext done
const done = base.concat([[33, 30, 'spawn'], [22, 7, 'tower']], L.ORDER.extension.slice(40, 50).map(([x, y]) => [x, y, 'extension']));
W.dayObs(mk(7, done, [], 0));
assert.strictEqual(Memory.ops.w8day.why, 'done');
assert.strictEqual(Memory.ops.w8day.bill, 0);
assert.strictEqual(Memory.ops.w8day.missSpawn, 0);
// 08:4x: RCL7 day-of done + stor 2.1k → phase bank20, leanBank on, recycle surplus upgraders
assert.strictEqual(Memory.ops.w8day.phase, 'bank20');
assert.strictEqual(Memory.ops.w8day.leanBank, 1);
assert.strictEqual(Memory.ops.w8day.bankLeft, 20000 - 2100);
assert.ok(Memory.ops.w8day.bankEta > 0, 'bankEta positive while leanBank');
const ups = [{ memory: { role: 'w8upgrader' } }, { memory: { role: 'w8upgrader' } }, { memory: { role: 'w8upgrader' } }];
W.dayObs(mk(7, done, ups, 0));
assert.ok((Memory.ops.w8recycle || []).length >= 2, 'leanBank recycles surplus upgraders: ' + JSON.stringify(Memory.ops.w8recycle));
// stor ≥20k → ready, leanBank off
const rReady = mk(7, done, [], 0); rReady.storage.store.energy = 20000;
W.dayObs(rReady);
assert.strictEqual(Memory.ops.w8day.phase, 'ready');
assert.strictEqual(Memory.ops.w8day.leanBank, 0);
assert.strictEqual(Memory.ops.w8day.bankLeft, 0);
assert.strictEqual(Memory.ops.w8day.bankEta, 0);
assert.strictEqual(Memory.ops.w8day.bankWhy, 'soft'); // 08:4x 11-02: [20k,25k) soft-cap dead zone
assert.strictEqual(Memory.ops.w8day.softLeft, 5000);
assert.strictEqual(W.LEAN_ARM, 15000);
assert.strictEqual(W.LEAN_SOFT, 25000);
// soft exit at ≥25k
const rSoftDone = mk(7, done, [], 0); rSoftDone.storage.store.energy = 25000;
W.dayObs(rSoftDone);
assert.strictEqual(Memory.ops.w8day.bankWhy, 'ready');
assert.strictEqual(Memory.ops.w8day.softLeft, 0);
// 02:4x hysteresis: after ready, stor 18k does NOT re-arm; phase stays ready (bankWhy=hold)
Memory.ops.w8day.leanBank = 0;
const rHold = mk(7, done, [], 0); rHold.storage.store.energy = 18000;
W.dayObs(rHold);
assert.strictEqual(Memory.ops.w8day.leanBank, 0, 'hysteresis hold at 18k');
assert.strictEqual(Memory.ops.w8day.phase, 'ready');
assert.strictEqual(Memory.ops.w8day.bankWhy, 'hold');
assert.strictEqual(Memory.ops.w8day.bankLeft, 2000);
// soft recycle: 4 upgraders at stor 22k → keep ≤2
delete Memory.ops.w8recycle;
const softUps = [{ memory: { role: 'w8upgrader' } }, { memory: { role: 'w8upgrader' } },
  { memory: { role: 'w8upgrader' } }, { memory: { role: 'w8upgrader' } }];
const rSoft = mk(7, done, softUps, 0); rSoft.storage.store.energy = 22000;
Memory.ops.w8day.leanBank = 0;
W.dayObs(rSoft);
assert.strictEqual(Memory.ops.w8day.leanBank, 0, '22k still ready');
assert.strictEqual(Memory.ops.w8day.bankWhy, 'soft', '22k bankWhy=soft');
assert.ok((Memory.ops.w8recycle || []).length >= 2, 'soft-cap recycles to ≤2: ' + JSON.stringify(Memory.ops.w8recycle));
assert.strictEqual(Memory.ops.w8day.softE, 1, 'softE on at 22k while climbing');
assert.strictEqual(W.LEAN_SOFT_ARM, 22000);
// 08:4x 11-03: clear at 25k then dip to 23k — softEnergyCap stays OFF (hysteresis hold)
delete Memory.ops.w8recycle;
const rSoftClear = mk(7, done, softUps, 0); rSoftClear.storage.store.energy = 25000;
W.dayObs(rSoftClear);
assert.strictEqual(Memory.ops.w8day.softE, 0);
assert.strictEqual(Memory.ops.w8day.softCap2, 0);
assert.strictEqual(Memory.ops.w8day.bankWhy, 'ready');
rSoftClear.storage.store.energy = 23000;
Memory.ops.w8day.leanBank = 0;
W.dayObs(rSoftClear);
assert.strictEqual(Memory.ops.w8day.softE, 0, 'hysteresis hold softE off at 23k after clear');
assert.strictEqual(Memory.ops.w8day.softCap2, 0, 'softCap2 off in [ARM,SOFT) after clear');
assert.strictEqual(Memory.ops.w8day.bankWhy, 'ready', 'bankWhy=ready in soft hysteresis hold');
// feed-gate may trim 4→≤3 without HUB_LINK; softCap must NOT recycle to ≤2 in the hold band
assert.ok((Memory.ops.w8recycle || []).length <= 1, 'no softCap≤2 recycle while hysteresis hold: ' + JSON.stringify(Memory.ops.w8recycle));
// re-arm soft energy below LEAN_SOFT_ARM
rSoftClear.storage.store.energy = 21000;
W.dayObs(rSoftClear);
assert.strictEqual(Memory.ops.w8day.softE, 1, 'softE re-arms below 22k');
assert.strictEqual(Memory.ops.w8day.softCap2, 1);
assert.strictEqual(Memory.ops.w8day.bankWhy, 'soft');
assert.ok((Memory.ops.w8recycle || []).length >= 2, 'soft re-arm recycles to ≤2: ' + JSON.stringify(Memory.ops.w8recycle));
// re-arm leanBank below LEAN_ARM
Memory.ops.w8day.leanBank = 0;
const rArm = mk(7, done, [], 0); rArm.storage.store.energy = 14000;
W.dayObs(rArm);
assert.strictEqual(Memory.ops.w8day.leanBank, 1, 're-arm below 15k');
assert.strictEqual(Memory.ops.w8day.phase, 'bank20');
assert.strictEqual(Memory.ops.w8day.bankWhy, 'bank');
// opt-out Memory.ops.w8leanBank=false
Memory.ops.w8leanBank = false;
const rOff = mk(7, done, [], 0); rOff.storage.store.energy = 3000;
W.dayObs(rOff);
assert.strictEqual(Memory.ops.w8day.leanBank, 0);
assert.strictEqual(Memory.ops.w8day.phase, 'bank20'); // still wants bank, throttle off
assert.strictEqual(Memory.ops.w8day.bankEta, -1);
delete Memory.ops.w8leanBank;
// 23:4x lean KO readiness obs (gate-off path; live default is now true)
const C0 = require(path.join(d, 'config'));
C0.RCL6_MINERALS = false;
W.dayObs(mk(6, base, [], 400000));
const m = Memory.ops.w8min;
assert.ok(m, 'w8min present');
assert.strictEqual(m.minOk, 0);
assert.strictEqual(m.labsOk, 0);
assert.strictEqual(m.hasTerm, 0);
assert.strictEqual(m.hasMinCont, 0);
assert.ok(m.gaps.indexOf('gate') >= 0, 'gaps includes gate: ' + m.gaps);
assert.ok(m.gaps.indexOf('send') < 0, 'send code shipped — gaps must not include send: ' + m.gaps);
assert.strictEqual(m.why, 'gate');
assert.strictEqual(m.hasCode, 1);

assert.strictEqual(m.sendOk, 1);
// 23:4x flipReady checklist (propose-only; gate/terminal/minCont excluded from flipGaps)
assert.strictEqual(m.flipReady, 0, 'stor 2.1k → not flipReady');
assert.ok(m.flipGaps.indexOf('stor20k') >= 0, 'flipGaps=' + m.flipGaps);
assert.ok(m.flipGaps.indexOf('daycrit') >= 0, 'RCL6 missing spawn2/tower3 → daycrit: ' + m.flipGaps);
// RCL7 daycrit done + stor20k + tower healthy + home stor≥15k → flipReady
Game.rooms.W46N8 = { storage: { store: { energy: 16000 } } };
const flipOk = mk(7, done, [], 0); flipOk.storage.store.energy = 20000;
W.dayObs(flipOk);
assert.strictEqual(Memory.ops.w8day.phase, 'ready');
assert.strictEqual(Memory.ops.w8min.flipReady, 1, 'flipGaps=' + Memory.ops.w8min.flipGaps);
assert.strictEqual(Memory.ops.w8min.flipGaps, '');
assert.strictEqual(Memory.ops.w8min.homeStor, 16000);
assert.strictEqual(Memory.ops.w8min.minBuild, 0);
// home thin → homeStor gap
Game.rooms.W46N8.storage.store.energy = 12000;
W.dayObs(flipOk);
assert.strictEqual(Memory.ops.w8min.flipReady, 0);
assert.ok(Memory.ops.w8min.flipGaps.indexOf('homeStor') >= 0);
Game.rooms.W46N8.storage.store.energy = 16000;
// tower low → towerE gap
const lowT = mk(7, done, [], 0); lowT.storage.store.energy = 20000;
lowT.find(FIND_MY_STRUCTURES, { filter: s => s.structureType === 'tower' }).forEach(t => { t.store.energy = 400; });
W.dayObs(lowT);
assert.ok(Memory.ops.w8min.flipGaps.indexOf('towerE') >= 0);
// post-flip minBuild: gate on, no terminal → leanBank stays ON, phase=minBuild
const C = require(path.join(d, 'config'));
C.RCL6_MINERALS = true;
const postFlip = mk(7, done, [], 0); postFlip.storage.store.energy = 5000; // dipped during build
W.dayObs(postFlip);
assert.strictEqual(Memory.ops.w8day.phase, 'minBuild');
assert.strictEqual(Memory.ops.w8day.leanBank, 1, 'leanBank holds through mineral build');
assert.strictEqual(Memory.ops.w8min.minBuild, 1);
assert.ok(Memory.ops.w8min.flipGaps.indexOf('already') >= 0);
assert.strictEqual(Memory.ops.w8min.flipReady, 0);
// 20:4x: terminal + minCont live + stor low → leanBank RE-ARMS (was permanently off via gate)
Memory.ops.w8day = { leanBank: 0 };
const withTerm = mk(7, done.concat([[35, 33, 'terminal'], [37, 44, 'container']]), [], 0);
withTerm.storage.store.energy = 5000;
withTerm.terminal = { store: {} };
W.dayObs(withTerm);
assert.strictEqual(Memory.ops.w8min.minBuild, 0);
assert.strictEqual(Memory.ops.w8day.leanBank, 1, '20:4x post-gate stor5k re-arms leanBank');
assert.strictEqual(Memory.ops.w8day.phase, 'bank20');
assert.strictEqual(Memory.ops.w8day.bankWhy, 'bank');
assert.ok(Memory.ops.w8day.bankLeft > 0, 'bankLeft honest post-gate');
assert.ok((Memory.ops.w8min.flipGaps || '').indexOf('already') >= 0);
assert.ok((Memory.ops.w8min.flipGaps || '').indexOf('stor20k') < 0, 'stor20k not in flipGaps once already');
assert.ok((Memory.ops.w8min.gaps || '').indexOf('stor20k') >= 0, 'stor20k still in cushion gaps');
// post-gate hysteresis hold at 18k still off
Memory.ops.w8day.leanBank = 0;
withTerm.storage.store.energy = 18000;
W.dayObs(withTerm);
assert.strictEqual(Memory.ops.w8day.leanBank, 0, 'post-gate hysteresis hold at 18k');
assert.strictEqual(Memory.ops.w8day.bankWhy, 'hold');
assert.strictEqual(Memory.ops.w8day.phase, 'ready');
// cushion filled → ready
withTerm.storage.store.energy = 20000;
W.dayObs(withTerm);
assert.strictEqual(Memory.ops.w8day.leanBank, 0);
assert.strictEqual(Memory.ops.w8day.phase, 'ready');
assert.strictEqual(Memory.ops.w8day.bankWhy, 'soft'); // soft-cap still on at 20k
withTerm.storage.store.energy = 25000;
W.dayObs(withTerm);
assert.strictEqual(Memory.ops.w8day.bankWhy, 'ready');
assert.strictEqual(Memory.ops.w8day.threatSoft, 0, 'peacetime threatSoft off');
assert.strictEqual(Memory.ops.w8day.softCap2, 0, 'stor≥LEAN_SOFT peacetime lifts ≤2');
assert.strictEqual(W.FEED_MIN, 800, '11:4x strategy FEED_MIN');
assert.strictEqual(Memory.ops.w8day.ctlBat, 0, 'mk has no CTL cont/link → ctlBat 0');
assert.strictEqual(Memory.ops.w8day.feedOk, 0, 'empty battery → feedOk 0');
// 11:4x: local threat (w8soft.why=threat / TH.localOn) holds ≤2 even after LEAN_SOFT.
// Neighbor w8threatN must NOT — chronic W47N9 camp would pin the cap forever.
delete Memory.ops.w8recycle;
Memory.ops.w8day = { leanBank: 0 };
const threatUps = [{ memory: { role: 'w8upgrader' } }, { memory: { role: 'w8upgrader' } },
  { memory: { role: 'w8upgrader' } }, { memory: { role: 'w8upgrader' } }];
const rThreat = mk(7, done.concat([[35, 33, 'terminal'], [37, 44, 'container']]), threatUps, 0);
rThreat.storage.store.energy = 30000;
rThreat.terminal = { store: {} };
Memory.ops.w8threat = Game.time; // local threat soft
delete Memory.ops.w8threatN;
W.dayObs(rThreat);
assert.strictEqual(W.threatSoft(), true, 'threatSoft tracks TH.localOn');
assert.strictEqual(W.softCap2(30000), true, 'softCap2 holds above LEAN_SOFT under local threat');
assert.strictEqual(Memory.ops.w8day.threatSoft, 1);
assert.strictEqual(Memory.ops.w8day.softCap2, 1);
assert.strictEqual(Memory.ops.w8day.bankWhy, 'threatSoft');
assert.strictEqual(Memory.ops.w8day.leanBank, 0, 'threat soft is not leanBank');
assert.ok((Memory.ops.w8recycle || []).length >= 2, 'threat soft recycles 4→≤2 above 25k: ' + JSON.stringify(Memory.ops.w8recycle));
delete Memory.ops.w8threat;
delete Memory.ops.w8recycle;
Memory.ops.w8threatN = Game.time; // neighbor staging only
W.dayObs(rThreat);
assert.strictEqual(W.threatSoft(), false, 'w8threatN is not threat soft');
assert.strictEqual(W.softCap2(30000), false, 'neighbor camp does not hold ≤2');
assert.strictEqual(Memory.ops.w8day.threatSoft, 0);
assert.strictEqual(Memory.ops.w8day.softCap2, 0);
assert.strictEqual(Memory.ops.w8day.bankWhy, 'ready');
// w8threatN alone must NOT softCap2-recycle to ≤2; thin battery may still trim surplus 4→≤3 (feed-gate).
assert.ok((Memory.ops.w8recycle || []).length <= 1, 'w8threatN must not softCap2-recycle to ≤2: ' + JSON.stringify(Memory.ops.w8recycle));
if ((Memory.ops.w8recycle || []).length) {
  assert.strictEqual((Memory.ops.w8recycle || []).length, 1, 'feed-starve only trims surplus above 3');
}
delete Memory.ops.w8threatN;
delete Memory.ops.w8recycle;
W.dayObs(rThreat);
assert.strictEqual(Memory.ops.w8day.bankWhy, 'ready', 'window clear → normal soft-cap resumes');
assert.strictEqual(Memory.ops.w8day.softCap2, 0);
assert.strictEqual(Memory.ops.w8day.feedOk, 0, 'peace ≥25k still feedOk=0 without CTL battery');
assert.ok((Memory.ops.w8recycle || []).length >= 1, '11:4x strategy: thin ctl battery recycles 4→≤3: ' + JSON.stringify(Memory.ops.w8recycle));
// peacetime ≥25k + ctl battery filled → no recycle (surplus allowed once feedOk)
delete Memory.ops.w8recycle;
Memory.ops.w8day = { leanBank: 0 };
const Ccfg = require(path.join(d, 'config'));
const batBuilt = done.concat([[35, 33, 'terminal'], [37, 44, 'container'],
  [Ccfg.CTL_CONT[0], Ccfg.CTL_CONT[1], 'container'], [Ccfg.CTL_LINK[0], Ccfg.CTL_LINK[1], 'link']]);
const rFeed = mk(7, batBuilt, threatUps, 0);
rFeed.storage.store.energy = 30000;
rFeed.terminal = { store: {} };
const ctlC = rFeed.lookForAt(LOOK_STRUCTURES, Ccfg.CTL_CONT[0], Ccfg.CTL_CONT[1])[0];
ctlC.store = { energy: 1500 };
const ctlL = rFeed.lookForAt(LOOK_STRUCTURES, Ccfg.CTL_LINK[0], Ccfg.CTL_LINK[1])[0];
ctlL.store = { energy: 400 };
assert.strictEqual(W.ctlBattery(rFeed), 1900, 'ctlBattery sums cont+link');
assert.ok(W.ctlBattery(rFeed) >= W.FEED_MIN);
W.dayObs(rFeed);
assert.strictEqual(Memory.ops.w8day.softCap2, 0);
assert.strictEqual(Memory.ops.w8day.ctlBat, 1900);
assert.strictEqual(Memory.ops.w8day.feedOk, 1, 'battery ≥FEED_MIN → feedOk');
// 14:4x: without HUB_LINK, peacetime still recycles 4→≤3 (A→ctl cannot sustain WORK40)
assert.ok((Memory.ops.w8recycle || []).length >= 1, 'no HUB_LINK: recycle surplus above base 3: ' + JSON.stringify(Memory.ops.w8recycle));
assert.strictEqual(Ccfg.HUB_LINK, false, 'test assumes HUB_LINK off');
assert.ok('hubLinkE' in Memory.ops.w8day, '23:4x hubLinkE obs');
assert.strictEqual(Memory.ops.w8day.hubLinkE, -1, 'no hub link structure → -1');
assert.strictEqual(Memory.ops.w8day.hubReady, 0, 'HUB_LINK off → hubReady 0');
assert.strictEqual(Memory.ops.w8day.hubLink, 0, 'hubLink flag obs 0');

// 11-03 05:4x: upgCeil/recycle gate on hubLinkLive (structure), not config flag alone.
// Flag ON + no structure → still recycle 4→≤3 (same as pre-flip); hubReady stays 0.
{
  delete Memory.ops.w8recycle;
  Memory.ops.w8day = { leanBank: 0 };
  Ccfg.HUB_LINK = true;
  assert.strictEqual(W.hubLinkLive(rFeed), false, 'flag on without structure → !hubLinkLive');
  W.dayObs(rFeed);
  assert.strictEqual(Memory.ops.w8day.hubLink, 1, 'flag obs 1 while HUB_LINK true');
  assert.strictEqual(Memory.ops.w8day.hubReady, 0, 'no structure → hubReady 0 even with flag');
  assert.ok((Memory.ops.w8recycle || []).length >= 1, 'flag-on site-phase still recycles >3: ' + JSON.stringify(Memory.ops.w8recycle));
  // Structure stands + battery full → hubReady 1, surplus allowed (no recycle)
  delete Memory.ops.w8recycle;
  Memory.ops.w8day = { leanBank: 0 };
  const hubBuilt = done.concat([[35, 33, 'terminal'], [37, 44, 'container'],
    [Ccfg.CTL_CONT[0], Ccfg.CTL_CONT[1], 'container'], [Ccfg.CTL_LINK[0], Ccfg.CTL_LINK[1], 'link'],
    [33, 34, 'link']]);
  const rHub = mk(7, hubBuilt, threatUps, 0);
  rHub.storage.store.energy = 30000;
  rHub.terminal = { store: {} };
  const ctlC2 = rHub.lookForAt(LOOK_STRUCTURES, Ccfg.CTL_CONT[0], Ccfg.CTL_CONT[1])[0];
  ctlC2.store = { energy: 1500 };
  const ctlL2 = rHub.lookForAt(LOOK_STRUCTURES, Ccfg.CTL_LINK[0], Ccfg.CTL_LINK[1])[0];
  ctlL2.store = { energy: 400 };
  assert.ok(W.hubLinkLive(rHub), 'hub structure + flag → hubLinkLive');
  const hubL = rHub.lookForAt(LOOK_STRUCTURES, 33, 34).find(s => s.structureType === 'link');
  assert.ok(hubL, 'mk placed hub link 33,34');
  hubL.store = { energy: 200 }; // mock store so hubLinkE is numeric
  W.dayObs(rHub);
  assert.strictEqual(Memory.ops.w8day.hubReady, 1, 'structure + flag → hubReady 1');
  assert.strictEqual(Memory.ops.w8day.hubLinkE, 200, 'hubLinkE from structure store');
  assert.ok(!(Memory.ops.w8recycle || []).length, 'hub live + feedOk → no recycle: ' + JSON.stringify(Memory.ops.w8recycle));
  Ccfg.HUB_LINK = false;
}

// 05:4x/20:4x: soft-cap still works; at stor5k leanBank now ON → recycle to ≤1 (stricter than soft ≤2)
delete Memory.ops.w8recycle;
Memory.ops.w8day = { leanBank: 0 };
const postSoftUps = [{ memory: { role: 'w8upgrader' } }, { memory: { role: 'w8upgrader' } },
  { memory: { role: 'w8upgrader' } }, { memory: { role: 'w8upgrader' } }];
const withTermSoft = mk(7, done.concat([[35, 33, 'terminal'], [37, 44, 'container']]), postSoftUps, 0);
withTermSoft.storage.store.energy = 5000;
withTermSoft.terminal = { store: {} };
W.dayObs(withTermSoft);
assert.strictEqual(Memory.ops.w8day.leanBank, 1, '20:4x post-minBuild leanBank re-arms at 5k');
assert.ok((Memory.ops.w8recycle || []).length >= 3, 'leanBank recycles to ≤1: ' + JSON.stringify(Memory.ops.w8recycle));
// soft-cap alone at hold-band 18k (leanBank off): still ≤2
delete Memory.ops.w8recycle;
Memory.ops.w8day = { leanBank: 0 };
const withTermSoftHold = mk(7, done.concat([[35, 33, 'terminal'], [37, 44, 'container']]), postSoftUps, 0);
withTermSoftHold.storage.store.energy = 18000;
withTermSoftHold.terminal = { store: {} };
W.dayObs(withTermSoftHold);
assert.strictEqual(Memory.ops.w8day.leanBank, 0, 'hold-band leanBank off');
assert.ok((Memory.ops.w8recycle || []).length >= 2, '05:4x soft-cap post-gate recycles to ≤2 at 18k: ' + JSON.stringify(Memory.ops.w8recycle));

// 14:4x wartime: pauseCivilians → bankWhy=war + warMode=1 + recycle keep≤1 (upgraderKeep 0 when TTL high)
delete Memory.ops.w8recycle;
Memory.ops.w8day = { leanBank: 0 };
Memory.ops.w47n9 = { on: true, pauseCivilians: true };
const warUps = [{ memory: { role: 'w8upgrader' } }, { memory: { role: 'w8upgrader' } },
  { memory: { role: 'w8upgrader' } }, { memory: { role: 'w8builder' } }];
const warRoom = mk(7, done.concat([[35, 33, 'terminal'], [37, 44, 'container']]), warUps, 0);
warRoom.storage.store.energy = 30000;
warRoom.terminal = { store: {} };
warRoom.controller.ticksToDowngrade = 100000;
W.dayObs(warRoom);
assert.strictEqual(Memory.ops.w8day.warMode, 1, 'warMode obs');
assert.strictEqual(Memory.ops.w8day.bankWhy, 'war', 'bankWhy war overrides threatSoft/ready');
assert.ok((Memory.ops.w8recycle || []).length >= 3, 'war recycles surplus upgraders+builder: ' + JSON.stringify(Memory.ops.w8recycle));
delete Memory.ops.w47n9;

C.RCL6_MINERALS = true; // leave matching live config
delete Game.rooms.W46N8;


// sealMinE / sealRaise / sealPark obs (02:4x soft-gate; default LEAN_SOFT=25k)
delete Memory.defense;
delete Memory.ops.w47n9;
delete Memory.ops.w8sealPark;
W.dayObs(mk(7, done, [], 0));
assert.strictEqual(Memory.ops.w8day.sealMinE, 25000, 'default sealMinE exposed');
assert.strictEqual(Memory.ops.w8day.sealRaise, 0, 'no w8seal knob → sealCap=STAGE3 → sealRaise 0');
assert.strictEqual(Memory.ops.w8day.sealPark, 1, 'stor 2.1k → sealPark ON');
Memory.defense = { w8seal: 1000000 };
const rSeal = mk(7, done, [], 0); rSeal.storage.store.energy = 20000;
W.dayObs(rSeal);
assert.strictEqual(Memory.ops.w8day.sealMinE, 25000);
assert.strictEqual(Memory.ops.w8day.sealRaise, 0, 'stor 20k < 25k → sealRaise 0 even with w8seal=1M');
assert.strictEqual(Memory.ops.w8day.sealPark, 1, 'softCap parks seal');
// sticky: stor≥25k but 0 upgraders → park holds, sealRaise stays 0
rSeal.storage.store.energy = 25000;
W.dayObs(rSeal);
assert.strictEqual(Memory.ops.w8day.sealPark, 1, 'sticky park until nUp recovers');
assert.strictEqual(Memory.ops.w8day.sealRaise, 0, 'stor≥25k alone does not lift sealRaise while park sticky');
// 3 upgraders + stor≥25k clears park → sealRaise 1
const ups3 = [{ memory: { role: 'w8upgrader' } }, { memory: { role: 'w8upgrader' } }, { memory: { role: 'w8upgrader' } }];
const rSealOk = mk(7, done, ups3, 0); rSealOk.storage.store.energy = 25000;
W.dayObs(rSealOk);
assert.strictEqual(Memory.ops.w8day.sealPark, 0, 'nUp>=base clears sticky park');
assert.strictEqual(Memory.ops.w8day.sealRaise, 1, 'stor≥25k + nUp3 + w8seal=1M → sealRaise 1');
// 02:4x: override below LEAN_SOFT no longer deep-seals under softCap2 (was the 17:4x failure mode)
Memory.defense.w8sealMinE = 5000;
rSealOk.storage.store.energy = 10000;
W.dayObs(rSealOk);
assert.strictEqual(Memory.ops.w8day.sealMinE, 5000, 'Memory override visible in obs');
assert.strictEqual(Memory.ops.w8day.sealRaise, 0, 'override 5k at stor 10k still softCap-parked (soft-gate)');
assert.strictEqual(Memory.ops.w8day.sealPark, 1);
delete Memory.defense;
delete Memory.ops.w8sealPark;

console.log('w47n8_dayobs ok');
