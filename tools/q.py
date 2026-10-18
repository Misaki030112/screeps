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
def q(expr, timeout=40):
    check(expr)
    tag = 'QQ' + str(time.time()).replace('.', '')
    wrapped = f"(function(){{try{{return ({expr});}}catch(e){{return 'ERR '+e.stack}}}})()"
    api.req('user/console', {'expression': f"'{tag}'+JSON.stringify({{t:Game.time,v:{wrapped}}})", 'shard': api.SHARD})
    end = time.time() + min(timeout, 25)
    while time.time() < end:
        for line in _tail().splitlines():
            if tag in line and "'" + tag not in line:
                try:
                    m = json.loads(line.split(tag, 1)[1]); m['tag'] = tag; return m
                except ValueError: end = 0; break
        time.sleep(1.5)
    tag = str(time.time())  # fallback: Memory._q via user/memory (rate-limited)
    api.req('user/console', {'expression': f"Memory._q={{tag:'{tag}',t:Game.time,v:{wrapped}}}", 'shard': api.SHARD})
    end = time.time() + timeout
    while time.time() < end:
        try:
            m = api.memory('_q')
            if isinstance(m, dict) and m.get('tag') == tag: return m
        except Exception: pass
        time.sleep(2)
    raise SystemExit('timeout')
if __name__ == '__main__': print(json.dumps(q(sys.argv[1]), separators=(',', ':')))
