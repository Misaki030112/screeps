#!/usr/bin/env python3
"""Confirm leftover official-history 404s and in-window 404s; insert if a later GET returns 200."""
from __future__ import annotations
import json, sys, time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "/workspace/screeps/tools")
import history_backfill as hb
import db, api

ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
# First pass at game.time=84375643; published_bases 84374900..84375500,
# reconstructed 84374901..84375600 (700). inserted=3400, already_in_db=21481, reconstructed=24881,
# ts_realigned_first_pass=6594 (first-interval tick_s=4.21402 script printed 4.214).
# tick_s_in_use overwritten from tick_s_realign.json after tick_s_check.
# First pass 34 of 35 official GETs 200, missing_chunks=1 W45N8@84375300.
# Leftover official 404s W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 and older aged out of this window start 84374901 and are not retried.
# 15:00 half-hour official already through 84375300 / reconstructed through 84375200
# (just-published 84375200 was written then at 15:10:58 gt=84375341).
# Concurrent 1h patrol _patrol_2026-11-20_1526 is running; do not write its folder.
# NEW box freeze 15:15:12-15:26:38 STATS 84375391..84375569 sits inside this window.
IN_WINDOW = [("W47N8", 84395100)]  # first pass 34/35 official GETs 200, missing_chunks=1 W47N8@84395100. In-window first-pass official 404: W47N8@84395100 (not yet told; retried here). Already-told leftover official 404 W46N8@84394300 (told by the delivered 13:32 1h patrol t508s3575; listener 79/100 84394301..84394379, hole 21 ticks 84394380..84394400) ages out of window start 84394501 and is not retried here. Already-told leftover official 404s W45N8@84392600, W46N8@84390800, W47N7@84390900, W46N8@84390400, W45N7@84388500, W45N8@84386600 and older also age out of window start 84394501 and are not retried here.