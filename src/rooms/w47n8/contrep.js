// W47N8 builder container repair hysteresis (11-11 15:xx). All 5 containers decay around 50%, so the old "<50% -> urgent" line
// re-picked the closest container under the line every 15-tick rescan and once the current one crossed 50% -> builders flipped
// targets mid-repair and walked across the room (w8builder84200485 -> 37,44 then 6ac12233 while 37,44 still sat at 49.96%).
// Enter: a container picked while < IN. Hold: keep it (no rescan, no switch because another container crossed IN) until > OUT.
// Only a crash-level job (< CRASH, container or road) on another object pre-empts the hold.
const IN = 0.5, OUT = 0.6, CRASH = 0.1;
const isCont = s => !!s && s.structureType === STRUCTURE_CONTAINER;
// still holding? clears the flag once the target is gone / not a container / above OUT
function held(mem, rep) {
  const h = !!mem.rjc && isCont(rep) && rep.hits <= rep.hitsMax * OUT;
  if (!h) delete mem.rjc;
  return h;
}
// after a (re)pick: arm the hold when the pick is a container under the entry line
function mark(mem, rep) { if (isCont(rep) && rep.hits < rep.hitsMax * IN) mem.rjc = 1; else delete mem.rjc; }
module.exports = { IN, OUT, CRASH, held, mark };
