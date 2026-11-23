from pathlib import Path
line = Path('/workspace/screeps/state/_patrol_2026-11-24_0522/iterations_line.txt').read_text().strip()
log = Path('/workspace/screeps/state/iterations.log')
cur = log.read_text()
key = line[:40]
if key in cur[-12000:]:
    print('already present')
else:
    if not cur.endswith(chr(10)):
        cur += chr(10)
    log.write_text(cur + line + chr(10))
    print('appended', len(line))
