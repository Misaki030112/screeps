// Compact stats line to the console every N ticks; picked up by the websocket listener (tools/listener.py).
module.exports = { run(every = 10) {
  if (Game.time % every) return;
  const s = Memory.stats || {};
  console.log('STATS ' + JSON.stringify({ t: Game.time, cpu: +(s.cpu || 0).toFixed(2), b: Game.cpu.bucket, gcl: s.gcl, rooms: s.rooms, creeps: s.creeps, nerr: (s.errors || []).length }));
} };
