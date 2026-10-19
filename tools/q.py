#!/usr/bin/env python3
"""Live console query: python3 tools/q.py '<js expr returning JSON-able>' -> evaluated in game.
Result comes back through the console stream (metrics/console.log, written by tools/listener.py), so it costs no
GET user/memory quota (1440/day; exhausted 2026-10-18 14:09 by q.py polling -> HTTP 429 for ~6h).
Falls back to Memory._q + user/memory only if the console line never shows up (listener down) or fails to parse."""
import sys, os, json, time
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'scripts')); import api
LOG = os.path.join(ROOT, 'metrics', 'console.log')
def _tail(n=262144):
    try:
        with open(LOG, 'rb') as f:
            f.seek(0, 2); s = f.tell(); f.seek(max(0, s - n)); return f.read().decode('utf-8', 'ignore')
    except OSError: return ''
def check(expr):
    # syntax-check locally before sending (17:00: four 'SyntaxError: Unexpected token )' notify mails from malformed exprs)
    import subprocess
    r = subprocess.run(['node', '-e', 'new Function("return (" + process.argv[1] + ");")', expr], capture_output=True, text=True)
    if r.returncode: raise SystemExit('q.py: expression has a syntax error, not sent:\n' + next((l for l in r.stderr.splitlines() if 'Error' in l), r.stderr.strip()[-200:]))
    # require() names are the flat dist/ names (src/managers/walls.js -> 'managers.walls'). Patrols kept guessing 'managers_walls' /
    # 'roles_queen' -> 'Unknown module' console errors logged as runtime error events (2room eval 10-20 03:1x). Check locally.
    import re, glob
    known = {os.path.relpath(f, os.path.join(ROOT, 'src'))[:-3].replace(os.sep, '.') for f in glob.glob(os.path.join(ROOT, 'src', '**', '*.js'), recursive=True)}
    bad = [m for m in re.findall(r"require\(\s*['\"]([^'\"]+)['\"]\s*\)", expr) if m not in known and not m.startswith('./')]
    if bad:
        hint = {b: next((k for k in sorted(known) if k.replace('.', '_') == b.replace('.', '_').replace('/', '_')), None) for b in bad}
        raise SystemExit('q.py: unknown module ' + ', '.join(f"'{b}'" + (f" (did you mean '{h}'?)" if h else '') for b, h in hint.items()) + ' - names are dotted src paths, e.g. managers.walls, rooms.w47n8.roles; not sent')
# Server cap on console expressions: 1001 chars accepted, 1024 refused with {'error': 'expression size is too large'}
# (probed 2026-10-20 02:4x). q.py used to ignore that reply and wait ~65 s for a line that never comes, which patrols read as
# a stalled listener (02:18 restart). Now the full wrapped expression is size-checked locally and any console error is raised.
MAX_EXPR = 1000
def send(expression):
    if len(expression) > MAX_EXPR:
        raise SystemExit(f'q.py: expression too large ({len(expression)} chars after wrapping, server max ~{MAX_EXPR}); '
                         f'not sent. Split it into smaller queries.')
    r = api.req('user/console', {'expression': expression, 'shard': api.SHARD})
    if isinstance(r, dict) and r.get('error'): raise SystemExit('q.py: console refused the expression: ' + str(r['error']))
    return r
def q(expr, timeout=40):
    check(expr)
    tag = 'QQ' + str(time.time()).replace('.', '')
    wrapped = f"(function(){{try{{return ({expr});}}catch(e){{return 'ERR '+e.stack}}}})()"
    send(f"'{tag}'+JSON.stringify({{t:Game.time,v:{wrapped}}})")
    end = time.time() + min(timeout, 25)
    while time.time() < end:
        for line in _tail().splitlines():
            if tag in line and "'" + tag not in line:
                try:
                    m = json.loads(line.split(tag, 1)[1]); m['tag'] = tag; return m
                except ValueError: end = 0; break
        time.sleep(1.5)
    tag = str(time.time())  # fallback: Memory._q via user/memory (rate-limited)
    send(f"Memory._q={{tag:'{tag}',t:Game.time,v:{wrapped}}}")
    end = time.time() + timeout
    while time.time() < end:
        try:
            m = api.memory('_q')
            if isinstance(m, dict) and m.get('tag') == tag: return m
        except Exception: pass
        time.sleep(2)
    raise SystemExit('timeout')
if __name__ == '__main__':
    # `q.py --help` used to send the JS expression `--help` -> 'help is not defined' console error events (3 patrols, 10-20 03:2x-03:4x)
    if len(sys.argv) != 2 or sys.argv[1].startswith('-'): raise SystemExit(__doc__.strip() + "\nusage: tools/q.py '<js expr>' (nothing sent)")
    print(json.dumps(q(sys.argv[1]), separators=(',', ':')))
