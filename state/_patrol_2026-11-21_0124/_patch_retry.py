from pathlib import Path
p = Path("/workspace/screeps/state/_patrol_2026-11-21_0124/official_retry.py")
t = p.read_text()
old = '''# first-pass 40-min backfill this hour (published_bases 84382500..84383100, reconstructed 84382501..84383200, missing_chunks=3)
IN_WINDOW = [
    ("W45N8", 84382600),  # still official 404 after 00:00 backfill confirm/retry2 and this 40m first pass; hole 84382601..84382700 (0/100)
    ("W45N7", 84382700),  # still official 404 after 00:00 backfill confirm/retry2 and this 40m first pass; hole 84382701..84382800 (0/100)
    ("W46N8", 84382900),  # still official 404 after 00:00 just-published retry and this 40m first pass; hole 84382901..84383000 (listener 67/100, missing 84382901..84382933)
]
# leftover already-told, retry once in case it published (aged out of this hour window start 84382501)
LEFTOVER = [
    ("W47N7", 84380900),  # already told leftover; hole 84380901..84381000
]
TICK_S = 4.178  # this hour first-pass official history (40-min 84382501..84383200)
'''
new = '''# first-pass 40-min backfill this hour (published_bases 84383400..84384000, reconstructed 84383401..84384100, missing_chunks=2)
IN_WINDOW = [
    ("W45N7", 84383500),  # still official 404 after 01:03 confirm / 01:05 retry2 and this 40m first pass; hole 84383501..84383600 (0/100)
    ("W45N7", 84383900),  # first-pass 404 this 40m; hole 84383901..84384000
]
# leftover already-told, retry once in case it published (aged out of this hour window start 84383401)
LEFTOVER = [
    ("W45N8", 84382600),  # already told leftover; hole 84382601..84382700
    ("W45N7", 84382700),  # already told leftover; hole 84382701..84382800
    ("W46N8", 84382900),  # already told leftover; hole 84382901..84383000 (listener 67/100, missing first 33t)
]
TICK_S = 4.172  # this hour first-pass official history (40-min 84383401..84384100)
'''
if old not in t:
    raise SystemExit("IN_WINDOW block not found")
t = t.replace(old, new)
t = t.replace("jp_base = 84382400", "jp_base = 84384100")
t = t.replace("LAST_TIP, TIP_GUESS = 84381540, 84382400", "LAST_TIP, TIP_GUESS = 84383290, 84384100")
t = t.replace("hour_cov_through_80600", "hour_cov_through_tip_guess")
t = t.replace("room_stats gaps since 84379900", "room_stats gaps since 84383100")
t = t.replace("tick>=84379900", "tick>=84383100")
p.write_text(t)
print("official_retry patched ok")
