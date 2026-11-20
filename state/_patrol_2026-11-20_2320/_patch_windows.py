from pathlib import Path

p = Path("/workspace/screeps/state/_patrol_2026-11-20_2320/exact2h.py")
t = p.read_text()
old = "BF_LO, BF_HI = 84380801, 84381500"
new = "BF_LO, BF_HI = 84381701, 84382400"
if old not in t:
    if new in t:
        print("exact2h BF already patched")
    else:
        raise SystemExit("exact2h BF_LO block not found")
else:
    t = t.replace(old, new)
    p.write_text(t)
    print("exact2h BF patched")
for i, l in enumerate(p.read_text().splitlines(), 1):
    if "BF_LO" in l or "LAST_TIP" in l:
        print(f"  exact2h {i}:{l}")

p = Path("/workspace/screeps/state/_patrol_2026-11-20_2320/official_retry.py")
t = p.read_text()
old = '''# first-pass 40-min backfill this hour: will be updated after backfill if new 404s appear
IN_WINDOW = [
    ("W47N7", 84380900),  # leftover official 404 from 22:11 half-hour; hole 84380901..84381000; still 404 after confirm/retry2
]
# leftover already-told, retry once in case it published (aged out of this hour window start 84380691)
LEFTOVER = [
    ("W47N8", 84380300),  # already told by 21:23 1h patrol; hole 84380301..84380400
]
TICK_S = 4.176  # this hour first-pass official history (40-min 84380801..84381500)
'''
new = '''# first-pass 40-min backfill this hour (published_bases 84381700..84382300, reconstructed 84381701..84382400, missing_chunks=2)
IN_WINDOW = [
    ("W47N8", 84382100),  # NEW official 404 this backfill; hole 84382101..84382200 (listener already has 100/100)
    ("W47N7", 84382300),  # NEW official 404 this backfill; hole 84382301..84382400 (0/100, overlaps new freeze tail)
]
# leftover already-told, retry once in case it published (aged out of this hour window start 84381541)
LEFTOVER = [
    ("W47N7", 84380900),  # already told by 22:23 1h patrol; hole 84380901..84381000
]
TICK_S = 4.263  # this hour first-pass official history (40-min 84381701..84382400)
'''
if old not in t:
    if "84382100" in t and "TICK_S = 4.263" in t:
        print("official_retry already patched")
    else:
        raise SystemExit("official_retry header block not found")
else:
    t = t.replace(old, new)
    t = t.replace("jp_base = 84381500", "jp_base = 84382400")
    t = t.replace("LAST_TIP, TIP_GUESS = 84380690, 84381500", "LAST_TIP, TIP_GUESS = 84381540, 84382400")
    p.write_text(t)
    print("official_retry patched")
for i, l in enumerate(p.read_text().splitlines(), 1):
    if any(s in l for s in ("IN_WINDOW", "LEFTOVER", "TICK_S", "jp_base", "LAST_TIP", "OUTDIR", "84382100", "84382300", "84380900")):
        print(f"  retry {i}:{l}")
