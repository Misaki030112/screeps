// How many defenders a threat is worth. Pure. Used by the remote FSM and by owned-room guards.
// A max RCL7 body (19 RA + 25 MOVE + 6 HEAL, 190 dmg / 72 heal) beats one small Invader,
// including a boosted small melee and a 3-RA small ranged. Numbers go up only when one body
// cannot both kill and out-heal the wave.
//   0  nothing to fight (caller treats an open THREAT with an empty list as 1)
//   1  solo, including boosted solo and a single small ranged (3 RA)
//   2  two creeps, or any healer
//   3  three creeps, a ranged-heavy body (>=6 RA, bigger than a small Invader), or a boosted pair
//   4  four or more creeps, or an invader core that still has creep support
const MAX = 4;
function judge(list, mission) {
  const last = list || [];
  const n = last.length;
  if (!n) return mission === 'core' ? 1 : 0;
  const heal = last.some(i => i.heal);
  const ra = i => (i.ra != null ? i.ra : (i.ranged3 ? 3 : 0));
  const heavy = last.some(i => ra(i) >= 6);
  const boosted = last.some(i => i.boosted);
  let w = 1;
  if (n >= 2 || heal) w = 2;
  if (n >= 3 || heavy || (boosted && n >= 2)) w = 3;
  if (n >= 4 || (mission === 'core' && n >= 1)) w = 4;
  return Math.max(1, Math.min(MAX, w));
}
// Where a carrier should put energy while a fight is on.
// Spawn/extensions first until the max body can start (spawnShort). Towers are next, ahead of
// anything that is not a spawn structure. Once the spawn pile is full, towers come first.
function fillRank(alert, spawnShort, type) {
  const ext = type === 'spawn' || type === 'extension';
  const tower = type === 'tower';
  if (!alert) return ext ? 0 : tower ? 2 : 1;
  if (spawnShort && ext) return 0;
  if (tower) return 1;
  if (ext) return 2;
  return 3;
}
module.exports = { judge, fillRank, MAX };
