#!/usr/bin/env python3
from pathlib import Path

D = Path("/workspace/screeps/state/_patrol_2026-11-20_1923")

# --- exact2h ---
p = D / "exact2h.py"
t = p.read_text()
repls = [
    (
        "LAST_TIP = 84377350  # previous 1h patrol analysis tip (17:30:44)",
        "LAST_TIP = 84378090  # previous 1h patrol analysis tip (18:22:59)",
    ),
    (
        "BF_LO, BF_HI = 84377301, 84378000",
        "BF_LO, BF_HI = 84378201, 84378900",
    ),
]
for old, new in repls:
    if old not in t:
        raise SystemExit(f"exact2h missing block: {old!r}")
    t = t.replace(old, new)
p.write_text(t)
print("exact2h patched")

# --- official_retry ---
p = D / "official_retry.py"
t = p.read_text()
repls = [
    (
        '    ("W46N8", 84377600),  # first-pass 404 this hour; first recorded by 18:00 half-hour, still untold\n',
        "",
    ),
    (
        '''LEFTOVER = [
    ("W47N8", 84377100),  # already told by 17:40 1h patrol; aged out of hour window start 84377351
    ("W45N7", 84376800),  # already told; aged out
]
TICK_S = 4.074  # 18:00 half-hour first-pass in-use (this hour first-pass 4.227 is freeze-inflated)
OUTDIR = "/workspace/screeps/state/_patrol_2026-11-20_1819"
''',
        '''LEFTOVER = [
    ("W47N7", 84378000),  # already told by 18:31 1h patrol; hole 84378001..84378100 overlaps first 10t of hour window start 84378091
    ("W46N8", 84377600),  # already told by 18:31; aged out of hour window start 84378091
]
TICK_S = 4.244  # this hour first-pass official history (40-min 84378201..84378900)
OUTDIR = "/workspace/screeps/state/_patrol_2026-11-20_1923"
''',
    ),
    ("jp_base = 84377300", "jp_base = 84378900"),
    ("LAST_TIP, TIP_GUESS = 84376450, 84377300", "LAST_TIP, TIP_GUESS = 84378090, 84378900"),
    (
        'print("=== hour-window coverage LAST_TIP+1..84377300 ===", flush=True)',
        'print("=== hour-window coverage LAST_TIP+1..84378900 ===", flush=True)',
    ),
    ('results["hour_cov_through_77300"] = cov', 'results["hour_cov_through_78900"] = cov'),
    (
        'print("=== room_stats gaps since 84375600 ===", flush=True)',
        'print("=== room_stats gaps since 84378000 ===", flush=True)',
    ),
    (
        '"SELECT tick, ts FROM room_stats WHERE room=\'W46N8\' AND tick>=84376440 ORDER BY tick"',
        '"SELECT tick, ts FROM room_stats WHERE room=\'W46N8\' AND tick>=84378000 ORDER BY tick"',
    ),
]
for old, new in repls:
    if old not in t:
        raise SystemExit(f"official_retry missing block:\n{old}")
    t = t.replace(old, new)

# comment fix
t = t.replace(
    "# first-pass 404s this run + leftover in-window official 404 from 16:15 backfill",
    "# first-pass 40-min backfill this hour: missing_chunks=0, no NEW official 404s",
)
p.write_text(t)
print("official_retry patched")

# verify
t2 = p.read_text()
assert "jp_base = 84378900" in t2
assert "OUTDIR = \"/workspace/screeps/state/_patrol_2026-11-20_1923\"" in t2
assert "LAST_TIP, TIP_GUESS = 84378090, 84378900" in t2
assert '("W47N7", 84378000)' in t2
assert "IN_WINDOW = [\n]" in t2 or "IN_WINDOW = []" in t2
print("official_retry verified")
print("--- IN_WINDOW/LEFTOVER/TICK/OUT/JP ---")
for i, line in enumerate(t2.splitlines(), 1):
    if any(k in line for k in ("IN_WINDOW", "LEFTOVER", "TICK_S", "OUTDIR", "jp_base", "LAST_TIP, TIP", "84377600", "84378000", "84376440", "84378000 ORDER")):
        print(f"{i}: {line}")
