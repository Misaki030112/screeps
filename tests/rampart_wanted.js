// Empty filler/manager stand-tile ramparts are not built/repaired while STATIONARY_FILL=false (decision 2026-10-15).
const assert = require('assert');
Object.assign(global, { LOOK_STRUCTURES: 'structure', STRUCTURE_ROAD: 'road', STRUCTURE_RAMPART: 'rampart', _: require('lodash') });
const plan = require('../src/utils/plan');
assert.strictEqual(plan.STATIONARY_FILL, false);
const P = plan.get('W46N8');
const room = (m) => ({ lookForAt: (_t, x, y) => (m[`${x},${y}`] || []).map(t => ({ structureType: t })) });
const R = room({ '35,28': ['spawn', 'rampart'], '34,25': ['rampart'], '36,30': ['rampart', 'road'], '37,31': ['storage', 'rampart'] });
assert(plan.rampartWanted(P, R, 35, 28), 'spawn rampart kept');
assert(plan.rampartWanted(P, R, 37, 31), 'storage rampart kept');
assert(!plan.rampartWanted(P, R, 34, 25), 'filler stand rampart dropped');
assert(!plan.rampartWanted(P, R, 36, 30), 'manager stand (road only) dropped');
assert(plan.rampartWanted(P, R, 47, 16), 'approved gate kept');
console.log('rampart_wanted ok');
