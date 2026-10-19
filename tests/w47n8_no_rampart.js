// 17:15 (Misaki): W47N8 places no rampart sites (drops unbuilt ones) and builders/wall mode raise seal walls only
const assert = require('assert'), fs = require('fs'), path = require('path');
const d = path.join(__dirname, '..', 'src', 'rooms', 'w47n8');
const idx = fs.readFileSync(path.join(d, 'index.js'), 'utf8'), roles = fs.readFileSync(path.join(d, 'roles.js'), 'utf8');
const prio = idx.match(/const PRIO = \[([^\]]*)\]/)[1];
assert.ok(!/rampart/.test(prio), 'no rampart in PRIO');
assert.ok(!/createConstructionSite\([^)]*STRUCTURE_RAMPART/.test(idx), 'no rampart site creation');
assert.ok(/FIND_MY_CONSTRUCTION_SITES, \{ filter: s => s\.structureType === STRUCTURE_RAMPART \}\)\) s\.remove\(\)/.test(idx), 'unbuilt rampart sites removed');
const wl = idx.match(/const wallsLow = [^\n]*/)[0]; assert.ok(!/RAMPART/.test(wl), 'wall mode ignores ramparts');
const wj = roles.slice(roles.indexOf('function wallJob'), roles.indexOf('// ---- W47N7 remote')); assert.ok(!/RAMPART/.test(wj), 'wallJob seal walls only');
console.log('w47n8 no rampart ok');
