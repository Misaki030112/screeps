import json, re
from pathlib import Path

j = json.loads(Path('chunk_ts.json').read_text())
print('TICK_S_FIRST', j.get('TICK_S_FIRST'))
print('w46 keys', sorted(int(k) for k in j['w46']))

p = Path('backfill_confirm.py')
t = p.read_text()
t2, n = re.subn(r'TICK_S = [0-9.]*', 'TICK_S = %.5f' % j['TICK_S_FIRST'], t, count=1)
p.write_text(t2)
print('confirm TICK_S replacements', n)
for line in t2.splitlines():
    if line.startswith('TICK_S') or line.startswith('IN_WINDOW') or line.startswith('OUT'):
        print(' ', line)

w46 = {int(k): int(v) for k, v in j['w46'].items()}
min_all = {int(k): int(v) for k, v in j['min_all'].items()}

def dict_src(d):
    parts = ['{']
    for k in sorted(d):
        parts.append('    %d: %d,' % (k, d[k]))
    parts.append('}')
    return chr(10).join(parts)

new_consts = (
    'W46 = ' + dict_src(w46) + chr(10)
    + 'MIN_ALL = ' + dict_src(min_all) + chr(10)
    + 'TMIN, TMAX = 84421901, 84422600' + chr(10)
    + 'ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")' + chr(10)
    + 'TICK_S_FIRST = (MIN_ALL[84422000] - MIN_ALL[84421900]) / 1000.0 / 100  # script printed 4.189, exact %.5f' % j['TICK_S_FIRST'] + chr(10)
    + 'GT_FIRST = 84422636' + chr(10)
    + 'TS_REALIGNED_FIRST = 15440  # first-pass realign moved 15440 rows (inserted=3081 already_in_db=21946)' + chr(10)
    + 'PREV_LATER_MEAN = 4.16058  # tick_s_in_use from 22:00 halfhour' + chr(10)
)

pat = r'W46 = \{.*?' + chr(10) + r'PREV_LATER_MEAN = [0-9.]+\s*(?:#[^' + chr(10) + r']*)?' + chr(10)
p = Path('tick_s_check.py')
t = p.read_text()
t2, n = re.subn(pat, new_consts + chr(10), t, count=1, flags=re.S)
print('tick_s_check replacements', n)
if n == 1:
    p.write_text(t2)
    m = re.search(r'W46 = \{.*?' + r'PREV_LATER_MEAN = [^' + chr(10) + r']+' + chr(10), t2, flags=re.S)
    print('---- constants ----')
    print(m.group(0) if m else 'NOT FOUND AFTER WRITE')
else:
    print('FAILED')
    i = t.find('W46 =')
    print(t[i:i+800])
