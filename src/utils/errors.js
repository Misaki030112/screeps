// Wrap a function; record exceptions into Memory.stats.errors instead of crashing the tick.
const buf = [];
module.exports = {
  wrap(label, fn) {
    try { return fn(); } catch (e) {
      const msg = `${Game.time} ${label}: ${e && e.stack ? e.stack.split('\n').slice(0, 3).join(' | ') : e}`;
      console.log('[ERR] ' + msg); buf.push(msg);
    }
  },
  flush() { const out = buf.splice(0); return out; },
};
