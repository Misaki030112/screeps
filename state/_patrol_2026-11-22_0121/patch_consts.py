#!/usr/bin/env python3
from pathlib import Path

p = Path('/workspace/screeps/state/_patrol_2026-11-22_0121/backfill_just_published.py')
t = p.read_text()
if 'JUST_BASE = 84404100' in t:
    t = t.replace('JUST_BASE = 84404100', 'JUST_BASE = 84404300')
    p.write_text(t)
    print('updated JUST_BASE')
else:
    for line in t.splitlines():
        if 'JUST_BASE' in line:
            print('JP:', line)

p = Path('/workspace/screeps/state/_patrol_2026-11-22_0121/exact2h.py')
t = p.read_text()
t = t.replace(
    'LAST_TIP = 84402790  # previous 1h patrol analysis tip (23:35 later 84402870 live 84402869)',
    'LAST_TIP = 84403680  # previous 1h patrol analysis tip (00:35 later 84403680 / 84403710 live)',
)
t = t.replace(
    'BF_LO, BF_HI = 84402801, 84403500  # first-pass official window this hour, missing_chunks=0',
    'BF_LO, BF_HI = 84403601, 84404300  # first-pass official window this hour, missing_chunks=2',
)
t = t.replace(
    '/workspace/screeps/state/_patrol_2026-11-21_1722/exact2h_copy.txt',
    '/workspace/screeps/state/_patrol_2026-11-22_0121/exact2h_copy.txt',
)
if 'W45N7@84403700' not in t:
    needle = "        (84386401, 84386500, 'W46N8@84386400'),"
    add = needle + "\n        (84403701, 84403800, 'W45N7@84403700')," + "\n        (84403801, 84403900, 'W45N7@84403800')," + "\n        (84400301, 84400400, 'W45N7@84400300')," + "\n        (84400401, 84400500, 'W45N7@84400400')," + "\n        (84400101, 84400200, 'W47N8@84400100'),"
    if needle in t:
        t = t.replace(needle, add)
        print('added leftover holes')
    else:
        print('needle not found')
p.write_text(t)
for line in t.splitlines():
    if 'LAST_TIP' in line or 'BF_LO' in line or 'exact2h_copy' in line:
        print(line)

sh = Path('/workspace/screeps/state/_patrol_2026-11-22_0121/_run_analysis.sh')
s = sh.read_text()
s = s.replace('\\${name}', '${name}')
s = s.replace('\\u0024{name}', '${name}')
sh.write_text(s)
print('analysis name lines:')
for line in s.splitlines():
    if 'name' in line:
        print(repr(line))