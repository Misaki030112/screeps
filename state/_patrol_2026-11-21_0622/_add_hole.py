from pathlib import Path
p = Path('/workspace/screeps/state/_patrol_2026-11-21_0622/exact2h.py')
t = p.read_text()
needle = "        (84385301, 84385400, 'W47N8@84385300'),"
insert = needle + "\n        (84385901, 84386000, 'W47N8@84385900'),"
if '84385901' in t:
    print('already present')
elif needle not in t:
    raise SystemExit('anchor missing')
else:
    p.write_text(t.replace(needle, insert, 1))
    print('added')
