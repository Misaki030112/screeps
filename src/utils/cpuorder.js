// Creep run order under a low CPU bucket (strategy review 2026-10-20 01:4x, docs/CPU.md "Siege budget").
// Bucket full (normal): Game.creeps order, unchanged. Bucket < LOW: combat creeps first, then the creeps that refill
// spawns/towers, then economy; and once used CPU nears tickLimit, the rest skip this tick (an idle tick) so the
// script is never hard-terminated with defenders unrun and stats/report unwritten.
const LOW = 2000, MARGIN = 5;
const PRI = { guard: 0, defender: 0, w8defender: 0, w8healer: 0, w8guard: 0, cqsquad: 0, cqbreaker: 0, cqatk: 0, cqquad: 0, raid9: 0,
  queen: 1, w8filler: 1 };
const pri = c => { const p = PRI[c.memory.role]; return p === undefined ? 2 : p; };
module.exports = {
  LOW, PRI,
  low: bucket => bucket < LOW,
  order(creeps, bucket) {
    const names = Object.keys(creeps);
    if (bucket >= LOW) return names;
    return names.map((n, i) => [n, pri(creeps[n]), i]).sort((a, b) => a[1] - b[1] || a[2] - b[2]).map(x => x[0]);
  },
  // true -> skip this (non-priority) creep this tick
  shed(c, bucket, used, tickLimit) { return bucket < LOW && pri(c) >= 2 && used > tickLimit - MARGIN; },
};
