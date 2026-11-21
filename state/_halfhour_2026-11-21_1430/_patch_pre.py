#!/usr/bin/env python3
from pathlib import Path
p = Path("/workspace/screeps/state/_halfhour_2026-11-21_1430/pre_check.py")
t = p.read_text()
t = t.replace("_halfhour_2026-11-21_1400", "_halfhour_2026-11-21_1430")
old_start = t.find("PREV_END = ")
old_end = t.find("\nROOMS = ")
if old_start < 0 or old_end < 0:
    raise SystemExit(f"markers not found start={old_start} end={old_end}")
new = (
    "PREV_END = 84394900  # last 14:00 half-hour official first-pass 84394101..84394800 "
    "(700, published_bases 84394100..84394700 at game.time=84394837; first pass 34/35 official GETs 200, "
    "missing_chunks=1 W46N8@84394300) + confirm 14:02:14 gt=84394873, retry2 14:02:52 gt=84394882, "
    "and late retry 14:10:21 gt=84394985 still 404 inserted=0 + just-published 84394800 at 14:07:11 "
    "gt=84394941 (all_five_200=True; actual 2384 ticks 84394801..84394900; script 2386). Coverage "
    "official_recovered=3479/3500 empty_no_creep=0 official_404=21 (W46N8 leftover official 404 hole "
    "84394380..84394400, listener 79/100 84394301..84394379). Already told by the delivered 13:32 1h "
    "patrol t508s3575: leftover official 404 W46N8@84394300 (and W45N8@84392600 / W46N8@84390400 / "
    "W46N8@84390800 / W47N7@84390900 / W45N7@84388500 / W45N8@84386600 and older), box freezes "
    "12:30:42-12:35:35 / 12:48:14-12:57:17 / 13:09:46-13:21:14, short WS gaps 11:12 / 12:10 / 12:18, "
    "and older freezes through 11:49:12-11:57:31 and 11:19:06-11:20:43. The 14:00/14:14 backfill recorded "
    "NEW not-yet-told box freeze 13:49:01-13:56:56 (475s; STATS 84394681..84394809, 129t; official-filled "
    "all five 129/129; listener auto-restart 13:56:59, python 1901116 started 13:57:09) for the next 1h "
    "patrol; this 14:30 run must keep that as not-yet-told unless a newer patrol has already delivered it, "
    "and only fold newer freezes/404s/short gaps. This run must not restart the listener or war_cmd/pulse, "
    "and must not start a second listener. Measure any new STATS gap after PREV_END."
)
t = t[:old_start] + new + t[old_end:]
old_c = (
    "creep_ticks since tick {start_after} (after 13:30 half-hour official through 84394400 / just-published "
    "84394400 actual 1872; leftover W46N8@84394300 already told by 13:32 patrol; leftover W45N8@84392600 "
    "and older leftovers already told; already-told freezes 12:30:42-12:35:35 / 12:48:14-12:57:17 / "
    "13:09:46-13:21:14 and short WS gaps 11:12/12:10/12:18 told by 13:32 patrol; this run must not restart the listener):"
)
new_c = (
    "creep_ticks since tick {start_after} (after 14:00 half-hour official through 84394800 / just-published "
    "84394800 actual 2384; leftover W46N8@84394300 already told by 13:32 patrol; leftover W45N8@84392600 "
    "and older leftovers already told; already-told freezes through 13:09:46-13:21:14 and short WS gaps "
    "11:12/12:10/12:18 told by 13:32 patrol; not-yet-told freeze 13:49:01-13:56:56 recorded by 14:00 backfill; "
    "this run must not restart the listener):"
)
if old_c not in t:
    raise SystemExit("later comment not found")
t = t.replace(old_c, new_c)
p.write_text(t)
print("patched", p)
print("PREV_END ok", "PREV_END = 84394900" in t)
print("DIR 1430 only", "_halfhour_2026-11-21_1430" in t and "_halfhour_2026-11-21_1400" not in t)
