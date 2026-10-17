// Wrap a function; record exceptions into Memory.stats.errors instead of crashing the tick.
const buf = [];
module.exports = {
  // CPU profile (2026-10-18): per-section ms accumulated this tick, keyed by label's first word (creep rows -> role via trace)
  prof: {},
  wrap(label, fn) {
    const t0 = Game.cpu.getUsed(), k = label.split(' ')[0];
    try { return fn(); } catch (e) {
      const msg = `${Game.time} ${label}: ${e && e.stack ? e.stack.split('\n').slice(0, 3).join(' | ') : e}`;
      console.log('[ERR] ' + msg); buf.push(msg);
    } finally { module.exports.prof[k] = (module.exports.prof[k] || 0) + Game.cpu.getUsed() - t0; }
  },
  flush() { const out = buf.splice(0); return out; },
};
