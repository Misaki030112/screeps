#!/usr/bin/env python3
from pathlib import Path
ROOT = Path("/workspace/screeps")
OUT = ROOT / "state/_review12h_2026-11-23_20"

def load(name: str) -> str:
    return (OUT / name).read_text()

roadmap_block = load("block_roadmap.md")
rcl7_block = load("block_rcl7.md")
strategy_new = load("block_strategy.md")
model_block = load("block_model.md")
model_w47_block = load("block_model_w47.md")
mineral_block = load("block_mineral.md")

roadmap = ROOT / "ROADMAP.md"
rt = roadmap.read_text()
unique_rm = "2026-11-23 20:3x Asia/Hong_Kong 12h strategic review: plan holds; home 92.6%"
if unique_rm in rt:
    raise SystemExit("ROADMAP already has 20:3x")
mark = "**Safe mode: NEVER auto-activate** — alert Misaki.\n\n"
if mark not in rt:
    raise SystemExit("ROADMAP marker missing")
roadmap.write_text(rt.replace(mark, mark + roadmap_block, 1))
print("patched ROADMAP")

rcl7 = ROOT / "docs/RCL7.md"
r7 = rcl7.read_text()
if "2026-11-23 20:3x Asia/Hong_Kong — 12h strategic review (plan holds; home 92.56%" in r7:
    raise SystemExit("RCL7 already has 20:3x")
mark7 = "# Home W46N8 RCL7 readiness (strategy review 2026-10-19 18:4x UTC+8)\n\n"
if mark7 not in r7:
    raise SystemExit("RCL7 marker missing")
rcl7.write_text(r7.replace(mark7, mark7 + rcl7_block, 1))
print("patched RCL7")

st = ROOT / "docs/STRATEGY.md"
s = st.read_text()
old_h = "## Current state (2026-11-23 ~08:2x Asia/Hong_Kong · 12h review)\n"
if "## Current state (2026-11-23 ~20:3x Asia/Hong_Kong · 12h review)" in s:
    raise SystemExit("STRATEGY already has 20:3x")
if old_h not in s:
    raise SystemExit("STRATEGY old heading missing")
st.write_text(s.replace(old_h, strategy_new, 1))
print("patched STRATEGY")

model = ROOT / "docs/MODEL.md"
mt = model.read_text()
if "## 2026-11-23 20:3x — 12h actuals (plan holds)" in mt:
    raise SystemExit("MODEL already has 20:3x")
markm = (
    "## Actuals (DB, default 6 h)\n"
    "upgrade rate (room_stats progress), pickups per source (positive store deltas within 2 tiles of the source, normalised by tick coverage — a lower bound), deliveries (hub vs controller container), per-role idle/repaths/CPU (creep_cpu), planned vs actual path length (path_arrivals), hauler cycle median, share of hauling traffic on ideal-route tiles ± 1.\n\n"
)
if markm not in mt:
    raise SystemExit("MODEL marker missing")
model.write_text(mt.replace(markm, markm + model_block, 1))
print("patched MODEL")

mw = ROOT / "docs/MODEL_W47N8.md"
mwt = mw.read_text()
if "2026-11-23 20:3x — keep=2, no 40k touch this window (max 34839)" in mwt:
    raise SystemExit("MODEL_W47 already has 20:3x")
markw = "reserve7 (2 CLAIM) is spawned and paid by home.\n\n"
if markw not in mwt:
    raise SystemExit("MODEL_W47 marker missing")
mw.write_text(mwt.replace(markw, markw + model_w47_block, 1))
print("patched MODEL_W47N8")

mn = ROOT / "docs/MINERAL_DEFENSE_ROADMAP.md"
mtxt = mn.read_text()
mark_old = "## 2026-11-23 08:2x — home KO stockpile grew 58851→63861; 15k reaction floor is pausing at the tip; boost still waits on the 20k energy skip; industry / market stay off\n"
if "2026-11-23 20:3x — home KO stockpile grew 63861→69001" in mtxt:
    raise SystemExit("MINERAL already has 20:3x")
if mark_old not in mtxt:
    raise SystemExit("MINERAL marker missing")
mn.write_text(mtxt.replace(mark_old, mineral_block + mark_old, 1))
print("patched MINERAL_DEFENSE_ROADMAP")
