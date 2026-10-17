#!/usr/bin/env python3
"""Live console query: python3 tools/q.py '<js expr returning JSON-able>' -> evaluated in game, stored in Memory._q, read back."""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts')); import api
def q(expr, timeout=40):
    tag = str(time.time())
    api.req('user/console', {'expression': f"Memory._q={{tag:'{tag}',t:Game.time,v:(function(){{try{{return ({expr});}}catch(e){{return 'ERR '+e.stack}}}})()}}", 'shard': api.SHARD})
    end = time.time() + timeout
    while time.time() < end:
        try:
            m = api.memory('_q')
            if isinstance(m, dict) and m.get('tag') == tag: return m
        except Exception: pass
        time.sleep(2)
    raise SystemExit('timeout')
if __name__ == '__main__': print(json.dumps(q(sys.argv[1]), separators=(',', ':')))
