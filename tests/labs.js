// Lab scaffold (managers/labs.js): dormant without flag, output = lab in range 2 of both, reaction + task + labReady. node tests/labs.js
const path = require('path'), assert = require('assert');
Object.assign(global, {
  FIND_MY_STRUCTURES: 108, STRUCTURE_LAB: 'lab', OK: 0, Memory: {},
  Game: { time: 84001000 },
});
const L = require(path.join(__dirname, '..', 'src', 'managers', 'labs.js'));
let ran = 0;
const lab = (id, x, y, store = {}) => ({ id, structureType: 'lab', store, cooldown: 0, pos: { x, y, getRangeTo: o => Math.max(Math.abs(o.pos.x - x), Math.abs(o.pos.y - y)) }, runReaction: () => (ran++, 0) });
const mk = (s1, s2, s3, term = {}, stor = null) => {
  const labs = [lab('o', 34, 22, s1), lab('a', 33, 21, s2), lab('b', 35, 21, s3)];
  return {
    name: 'W46N8', labs, terminal: { id: 't', store: term },
    storage: stor ? { store: stor } : { store: { energy: 20000 } },
    find: () => labs,
  };
};
let r = mk({}, { K: 100 }, { O: 100 });
assert.strictEqual(L.run(r), 0, 'no flag -> dormant'); assert.strictEqual(L.task(r, r.labs), null);
assert.ok(Memory.ops && Memory.ops.labReady, 'labReady written while dormant');
assert.strictEqual(Memory.ops.labReady.why, 'noK', 'no K in terminal/storage');
assert.strictEqual(Memory.ops.labReady.propose, 0);
assert.strictEqual(Memory.ops.labReady.hasCode, 1);

const bump = () => { Game.time += L.READY_EVERY; };
r = mk({}, {}, {}, { K: 1000, O: 30000 });
bump();
L.readyObs(r);
assert.strictEqual(Memory.ops.labReady.propose, 1, 'K≥1000 + O → propose');
assert.strictEqual(Memory.ops.labReady.why, 'ready');
assert.strictEqual(Memory.ops.labReady.k, 1000);

r = mk({}, {}, {}, { K: 500, O: 30000 }, { K: 600 });
bump();
L.readyObs(r);
assert.strictEqual(Memory.ops.labReady.propose, 1, 'K term+stor counts');
assert.strictEqual(Memory.ops.labReady.k, 1100);

r = mk({}, {}, {}, { K: 1000, O: 50 });
bump();
L.readyObs(r);
assert.strictEqual(Memory.ops.labReady.why, 'noO');
assert.strictEqual(Memory.ops.labReady.propose, 0);

// 23:4x actOk checklist: propose can fire at K≥1k, but safe nod wants kBuf≥3k + homeStor≥15k
r = mk({}, {}, {}, { K: 1000, O: 30000 }, { energy: 20000 });
bump();
L.readyObs(r);
assert.strictEqual(Memory.ops.labReady.propose, 1);
assert.strictEqual(Memory.ops.labReady.actOk, 0, 'kTerm 1k < ACT_K_BUF 3k');
assert.ok(Memory.ops.labReady.actGaps.includes('kBuf'));

r = mk({}, {}, {}, { K: 3000, O: 30000 }, { energy: 10000 });
bump();
L.readyObs(r);
assert.strictEqual(Memory.ops.labReady.actOk, 0, 'homeStor under floor');
assert.ok(Memory.ops.labReady.actGaps.includes('homeStor'));

r = mk({ KO: 100 }, {}, {}, { K: 5000, O: 30000, KO: 200 }, { energy: 16000 });
bump();
L.readyObs(r);
assert.strictEqual(Memory.ops.labReady.actOk, 1, 'floors met');
assert.strictEqual(Memory.ops.labReady.actGaps, '');
assert.strictEqual(Memory.ops.labReady.ko, 300, 'koTerm+koLab');
assert.strictEqual(Memory.ops.labReady.homeStor, 16000);

Memory.ops = { labs: { W46N8: 'KO' } };
r = mk({}, { K: 100 }, { O: 100 }, { K: 5000, O: 30000 });
assert.strictEqual(L.run(r), 1, 'reacts'); assert.strictEqual(ran, 1);
assert.strictEqual(Memory.ops.labReady.why, 'active');
assert.strictEqual(Memory.ops.labReady.propose, 0, 'already on → no re-propose');
assert.strictEqual(L.roles(r.labs).out.id, 'o', 'output 34,22'); assert.deepStrictEqual(L.roles(r.labs).ins.map(l => l.id), ['a', 'b']);

r = mk({}, { K: 3 }, { O: 100 }); assert.strictEqual(L.run(r), 0, 'short reagent');
r = mk({}, {}, {}, { K: 500, O: 30000 }); assert.deepStrictEqual(L.task(r, r.labs), { from: 't', to: 'a', res: 'K' }, 'load K');
r = mk({}, { O: 50 }, {}, { K: 500 }); assert.deepStrictEqual(L.task(r, r.labs), { from: 'a', to: 't', res: 'O' }, 'empty wrong');
r = mk({ KO: 1500 }, { K: 2000 }, { O: 2000 }); assert.deepStrictEqual(L.task(r, r.labs), { from: 'o', to: 't', res: 'KO' }, 'unload output');
Memory.ops = { labs: { W46N8: 'XX' } }; assert.strictEqual(L.cfg(r), null, 'unknown compound ignored');

// Commander: an order on an input lab skips the reaction and does not clear ops.labs.
const cmd = require(path.join(__dirname, '..', 'src', 'utils', 'cmd.js'));
Memory.ops = { labs: { W46N8: 'KO' } };
cmd.setStruct('a', { act: 'idle', ttl: 5 });
ran = 0;
r = mk({}, { K: 100 }, { O: 100 }, { K: 5000, O: 30000 });
assert.strictEqual(L.run(r), 0, 'input lab order skips reaction');
assert.strictEqual(ran, 0);
assert.strictEqual(Memory.ops.labs.W46N8, 'KO');
cmd.releaseStruct('a');
cmd.disarm();
ran = 0;
r = mk({}, { K: 100 }, { O: 100 }, { K: 5000, O: 30000 });
assert.strictEqual(L.run(r), 1, 'disarm resumes reaction');
assert.strictEqual(ran, 1);

// Dormant readyObs: one FIND_MY_STRUCTURES, then skip until READY_EVERY. Does not arm labs or react.
{
  assert.ok(L.READY_EVERY >= 10 && L.READY_EVERY <= 50, 'READY_EVERY in 10–50');
  let finds = 0;
  const room = mk({}, {}, {}, { K: 0, O: 0 });
  room.find = () => { finds++; return room.labs; };
  delete Memory.ops.labs;
  Game.time += L.READY_EVERY;
  assert.strictEqual(L.run(room), 0, 'labs off does not react');
  assert.strictEqual(finds, 1, 'first dormant tick scans');
  assert.ok(!Memory.ops.labs, 'scan does not flip ops.labs');
  const why = Memory.ops.labReady.why;
  Game.time += 1;
  room.terminal.store = { K: 9000, O: 9000 };
  assert.strictEqual(L.run(room), 0);
  assert.strictEqual(finds, 1, 'next tick while labs are off does not scan');
  assert.strictEqual(Memory.ops.labReady.why, why, 'snapshot held across the skipped tick');
  Game.time += L.READY_EVERY - 1;
  L.readyObs(room);
  assert.strictEqual(finds, 2, 'scan resumes once the window elapses');
  assert.strictEqual(Memory.ops.labReady.propose, 1, 'fresh scan sees the new terminal stock');
  assert.strictEqual(L.run(room), 0, 'still no reaction');
  assert.ok(!Memory.ops.labs);
}
console.log('labs ok');
