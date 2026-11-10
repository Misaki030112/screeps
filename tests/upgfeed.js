// Home upgrade-feed obs (strategy 2026-10-31 02:4x). node tests/upgfeed.js
const path = require('path'), assert = require('assert');
const src = p => path.join(__dirname, '..', 'src', p);
Object.assign(global, {
  STRUCTURE_LINK: 'link', STRUCTURE_CONTAINER: 'container', STRUCTURE_STORAGE: 'storage',
  STRUCTURE_SPAWN: 'spawn', STRUCTURE_EXTENSION: 'extension', STRUCTURE_TOWER: 'tower',
  RESOURCE_ENERGY: 'energy', WORK: 'work', LOOK_STRUCTURES: 'structure',
  _: require('lodash'),
  Memory: { ops: {}, remote: {} },
  Game: { time: 83968000, rooms: {}, creeps: {} },
});
const stub = (p, exp) => { require.cache[require.resolve(src(p))] = { id: p, filename: src(p), loaded: true, exports: exp }; };

const P = {
  pos: { controllerContainer: [30, 30], controllerLink: [30, 31], upgraders: [[30, 29]] },
  raw: { stamps: {} },
};
stub('utils/plan.js', { get: n => n === 'W46N8' ? P : null, LINK_PLAN: { hub: [37, 29], ctl: [30, 31] }, STATIONARY_FILL: false });

let world = { ctl: 200, ctlLink: 100, hub: 400, src: 600, floor: 15000, stor: 16000, rem: {} };
stub('utils/roomcache.js', {
  at: (room, x, y, type) => {
    if (type === STRUCTURE_CONTAINER && x === 30 && y === 30) return { store: { energy: world.ctl } };
    if (type === STRUCTURE_LINK && x === 30 && y === 31) return { store: { energy: world.ctlLink } };
    if (type === STRUCTURE_LINK && x === 37 && y === 29) return { store: { energy: world.hub } };
    if (type === STRUCTURE_LINK && x === 30 && y === 11) return { store: { energy: world.src } };
    return null;
  },
  all: (room, type) => {
    if (type !== STRUCTURE_LINK) return [];
    return [
      { pos: { x: 30, y: 31 }, store: { energy: world.ctlLink } },
      { pos: { x: 37, y: 29 }, store: { energy: world.hub } },
      { pos: { x: 30, y: 11 }, store: { energy: world.src } },
    ];
  },
});
stub('roles/queen.js', { storageFloor: () => world.floor });
stub('managers/links.js', {
  CTL_LOW: 400, SEND: 400,
  roles: () => ({
    hub: { store: { energy: world.hub } },
    ctl: { store: { energy: world.ctlLink } },
    sources: [{ store: { energy: world.src } }],
    fillers: [], links: [],
  }),
});
stub('managers/remote.js', { CFG: { W45N8: { home: 'W46N8' }, W45N7: { home: 'W46N8' } } });
stub('managers/threat.js', { state: r => ({ st: (world.rem[r] || 'SAFE') }) });

const U = require(src('managers/upgfeed.js'));

function mkRoom(ctlEma) {
  return {
    name: 'W46N8', memory: { ctlEma: ctlEma == null ? 500 : ctlEma },
    controller: { my: true, level: 7 },
    storage: { store: { energy: world.stor } },
  };
}
function setUps(energies) {
  Game.creeps = {};
  energies.forEach((e, i) => {
    Game.creeps['u' + i] = {
      name: 'u' + i, spawning: false, room: { name: 'W46N8' },
      memory: { role: 'upgrader', home: 'W46N8' },
      store: { energy: e }, getActiveBodyparts: p => p === WORK ? 14 : 0,
    };
  });
}

// Case 1: W45N7 DEFEND → remote_pause, idealAdj ~21.8
world.rem = { W45N8: 'SAFE', W45N7: 'DEFEND' };
setUps([50, 0]);
let out = U.run(mkRoom(500));
assert.strictEqual(out.why, 'remote_pause');
assert.ok(out.pausedNet > 4 && out.pausedNet < 5, 'pausedNet≈4.54 got ' + out.pausedNet);
assert.ok(out.idealAdj > 21 && out.idealAdj < 22.5, 'idealAdj≈21.8 got ' + out.idealAdj);
assert.strictEqual(out.nUp, 2);
assert.strictEqual(out.work, 28);
assert.strictEqual(out.surplus, 1000);
assert.ok(out.rem.indexOf('W45N7:DEFEND') >= 0);
assert.strictEqual(Memory.ops.upgFeed.why, 'remote_pause');

// Case 2: remotes SAFE, feed present → ok
world.rem = { W45N8: 'SAFE', W45N7: 'SAFE' };
world.ctl = 200; world.ctlLink = 100; world.stor = 16000;
out = U.run(mkRoom(500));
assert.strictEqual(out.pausedNet, 0);
assert.strictEqual(out.why, 'ok');

// Case 3: SAFE + empty feed + hungry + low ctlEma → ctl_starved
world.ctl = 0; world.ctlLink = 0; world.stor = 20000;
out = U.run(mkRoom(100));
assert.strictEqual(out.why, 'ctl_starved');
assert.ok(out.hungry >= 1);

// Case 4: SAFE + feed ok + thin surplus + low ctlEma → thin_surplus
world.ctl = 300; world.ctlLink = 200; world.stor = 15500; // surplus 500
setUps([50, 50]); // not hungry
out = U.run(mkRoom(400));
assert.strictEqual(out.why, 'thin_surplus');
assert.strictEqual(out.surplus, 500);

// Case 5: upBank set → floor_bank (beats thin_surplus); exposes obs fields
world.ctl = 300; world.ctlLink = 200; world.stor = 15200; // surplus 200
setUps([50, 50]);
{
  const room = mkRoom(400);
  room.memory.upBank = 1;
  room.memory.roleTargets = { upgrader: 0 };
  out = U.run(room);
}
assert.strictEqual(out.why, 'floor_bank');
assert.strictEqual(out.upBank, 1);
assert.strictEqual(out.tUp, 0);
assert.strictEqual(out.allowExtra, 20000);
assert.strictEqual(out.upExtra, 0);
assert.strictEqual(out.boundHint, 'energy'); // 28 WORK > ideal 26

// Case 6: remote_pause still beats floor_bank
world.rem = { W45N8: 'SAFE', W45N7: 'DEFEND' };
{
  const room = mkRoom(400);
  room.memory.upBank = 1;
  out = U.run(room);
}
assert.strictEqual(out.why, 'remote_pause');

console.log('upgfeed ok (+floor_bank)');
