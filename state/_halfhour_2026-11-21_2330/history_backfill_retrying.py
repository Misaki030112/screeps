#!/usr/bin/env python3
"""Run repo history_backfill.py with SSL/URLError retries. Does not modify the repo tool."""
from __future__ import annotations
import ssl
import sys
import time
import urllib.error

sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb

_orig = hb.history_get


def history_get_retry(room, base):
    last = None
    for attempt in range(5):
        try:
            return _orig(room, base)
        except (urllib.error.URLError, ssl.SSLError, TimeoutError, OSError) as e:
            last = e
            print(f"  transient {room}@{base} attempt {attempt+1}: {e!r}", flush=True)
            time.sleep(5 * (attempt + 1))
    raise last


hb.history_get = history_get_retry
hb.GAP_S = 1.2

if __name__ == "__main__":
    sys.exit(hb.main())
