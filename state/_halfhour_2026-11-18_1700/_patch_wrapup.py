#!/usr/bin/env python3
from pathlib import Path
p = Path("/workspace/screeps/state/_halfhour_2026-11-18_1700/wrapup.py")
t = p.read_text()
repls = [
    ('Write local status records for the 16:30 half-hour official-history backfill.',
     'Write local status records for the 17:00 half-hour official-history backfill.'),
    ('DIR = ROOT / "state" / "_halfhour_2026-11-18_1630"',
     'DIR = ROOT / "state" / "_halfhour_2026-11-18_1700"'),
    ("TMIN, TMAX = 84336901, 84337600", "TMIN, TMAX = 84337301, 84338000"),
    ('PUB_BASES = "84336900..84337500"', 'PUB_BASES = "84337300..84337900"'),
    ("GT_FIRST = 84337699", "GT_FIRST = 84338038"),
    ("TICK_S_FIRST = 4.90332", "TICK_S_FIRST = 4.68475"),
    ('TICK_S_PRINTED = "4.903"', 'TICK_S_PRINTED = "4.685"'),
    ("TICK_S_IN_USE = 4.65477", "TICK_S_IN_USE = 4.66119"),
    ("TS_REALIGNED_FIRST = 459", "TS_REALIGNED_FIRST = 0"),
    ("NFIX_CORR = 20265", "NFIX_CORR = 60"),
    ("GT_CORR = 84337723", "GT_CORR = 84338062"),
    ("RECON_ROWS = 23947", "RECON_ROWS = 23593"),
    ("ALREADY = 23947", "ALREADY = 13586"),
    ("INSERTED_FIRST = 0", "INSERTED_FIRST = 10007"),
    ("INSERTED_JUST = 2597", "INSERTED_JUST = 3094"),
    ('PER_ROOM_LINE = "W46N8:700t/0new W47N8:600t/0new W45N8:700t/0new W45N7:700t/0new W47N7:700t/0new"',
     'PER_ROOM_LINE = "W46N8:700t/2860new W47N8:600t/3744new W45N8:700t/1114new W45N7:700t/1127new W47N7:700t/1162new"'),
    ("(same window; also missing W47N8@84337400; inserted=4844); ",
     "(overlap of this window; also missing W47N8@84337400; inserted=4844); "),
    ("16:00 backfill already wrote through 84337300 and just-published 84337300 (84337301..84337400) for all five rooms",
     "16:30 backfill already wrote through 84337600 and just-published 84337600 (84337601..84337700) for all five rooms"),
]
for a, b in repls:
    if a not in t:
        raise SystemExit(f"missing chunk A: {a[:80]!r}")
    t = t.replace(a, b)

a = '''confirm_summary = (
    "confirm inserted=0 leftover official 404s unchanged "
    "(first confirm SSL abort mid-aged leftovers at 16:35:36 game.time=84337732, reran 16:36:30); "
    "retry2 inserted=0 leftovers still 404; "
    "just-published 84337600 recovered all five rooms inserted=2597 (after this window); "'''
# after INSERTED_JUST replace, 2597 is already 3094 in this string if it was replaced globally...
# INSERTED_JUST = 2597 was replaced, but the string "inserted=2597" is different.
# Check both.
b = '''confirm_summary = (
    "confirm inserted=0 leftover official 404s unchanged "
    "(17:01:33 game.time=84338065, no SSL abort); "
    "retry2 inserted=0 leftovers still 404 (17:02:49 game.time=84338082, IN_WINDOW 14 targets); "
    "just-published 84338000 recovered all five rooms inserted=3094 (after this window); "'''
if a not in t:
    raise SystemExit("confirm_summary start not found")
t = t.replace(a, b)

a = '''tick_s_corr_txt = (
    f"later-mean-robust {TICK_S_IN_USE:.5f} was over the 45s gate vs first-pass rows "
    f"(tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}, ~198.3s at tmin); "
    f"applied corrective later-mean-robust realign of {NFIX_CORR} rows at game.time={GT_CORR}, "
    f"still_over_45s_vs_later={vs_later_after.get('over45', 0)}"
)'''
b = '''tick_s_corr_txt = (
    f"later-mean-robust {TICK_S_IN_USE:.5f} was over the 45s gate vs first-pass rows "
    f"(tick_s={TICK_S_FIRST:.5f} printed {TICK_S_PRINTED}, first-vs-later ~17.4s at tmin, 204 rows over45 vs later before corrective); "
    f"applied corrective later-mean-robust realign of {NFIX_CORR} rows at game.time={GT_CORR}, "
    f"still_over_45s_vs_later={vs_later_after.get('over45', 0)}"
)'''
if a not in t:
    raise SystemExit("tick_s_corr_txt not found")
t = t.replace(a, b)

a = '''freeze_para = (
    "Listener restart 16:26:42 (box wake after freeze 16:20:37-16:26:39 (356s); "
    "run_listener.sh auto-restart / 16:26 hourly patrol, not this run; pid 440177) "
    "room_stats gap 84337531..84337619 (89); official-filled 89/89 of 89 of 89 all five "
    "(in-window published 84337531..84337600 all five 70/70 of 70 of 70; "
    "tail 84337601..84337619 all five 19/19 of 19 of 19 after just-published 84337600). "
    "This run did not restart the listener. "
    "Listener restart 16:02:35 (15:50:56-16:02:32 freeze (689s), not this run; pid 431060) "
    "room_stats gap 84337151..84337319 (169) remains in this window and stays official-filled "
    "169/169 of 169 of 169 all five. "
    "Listener restart 15:23:01 (15:22 hourly patrol, not this run) "
    "room_stats gap 84336791..84336809 (19) remains in this window and stays official-filled "
    "19/19 of 19 of 19 all five. "
    "Earlier 14:43:48-15:04:09 freeze / room_stats gap 84336301..84336569 is now outside this window."
)'''
b = '''freeze_para = (
    "Listener restart 16:57:13 (box wake after freeze 16:49:42-16:57:10 (447s); "
    "run_listener.sh auto-restart, not this run; pid 454066) "
    "room_stats gap 84337901..84338019 (119); official-filled 119/119 of 119 of 119 all five "
    "(in-window published 84337901..84338000 all five 100/100 of 100 of 100; "
    "tail 84338001..84338019 all five 19/19 of 19 of 19 after just-published 84338000). "
    "This run did not restart the listener. "
    "Listener restart 16:26:42 (16:20:37-16:26:39 freeze (356s), not this run; pid 440177) "
    "room_stats gap 84337531..84337619 (89) remains in this window and stays official-filled "
    "89/89 of 89 of 89 all five. "
    "Listener restart 16:02:35 (15:50:56-16:02:32 freeze (689s), not this run; pid 431060) "
    "room_stats gap 84337151..84337319 (169) is now only partly in this window "
    "(in-window tail 84337301..84337319 all five 19/19 of 19 of 19) and stays official-filled "
    "169/169 of 169 of 169 all five. "
    "Listener restart 15:23:01 (15:22 hourly patrol, not this run) "
    "room_stats gap 84336791..84336809 (19) is now outside this window."
)'''
if a not in t:
    raise SystemExit("freeze_para not found")
t = t.replace(a, b)

# payload just_published / confirm / retry2 / listener / box_freeze
pairs = [
    ('"base": 84337600,', '"base": 84338000,'),
    ('"oom_killed_at": ["16:39:26", "16:40:25"],', '"oom_killed_at": [],'),
    ('"oom_note": "first two just-published attempts were SIGKILL collateral of the concurrent 16:26 hourly patrol python (~13GB) OOM; slim retry then recovered all five",',
     '"oom_note": None,'),
    ('"recovered_at": "16:41:16",', '"recovered_at": "17:08:59",'),
    ('"recovered_game_time": 84337804,', '"recovered_game_time": 84338161,'),
    ('"ticks": "84337601..84337700",', '"ticks": "84338001..84338100",'),
    ('"at": "16:36:30",', '"at": "17:01:33",'),
    ('"game_time": 84337743,', '"game_time": 84338065,'),
    ('"ssl_abort_first": {"at": "16:35:36", "game_time": 84337732},',
     '"ssl_abort_first": None,'),
    ('"retry2": {"at": "16:37:56", "game_time": 84337762, "inserted": 0},',
     '"retry2": {"at": "17:02:49", "game_time": 84338082, "inserted": 0},'),
    ('"pid": 440177,', '"pid": 454066,'),
    ('"restart_at": "16:26:42",', '"restart_at": "16:57:13",'),
    ('"from": "2026-11-18 16:20:37",', '"from": "2026-11-18 16:49:42",'),
    ('"to": "2026-11-18 16:26:39",', '"to": "2026-11-18 16:57:10",'),
    ('"sec": 356,', '"sec": 447,'),
    ('"room_stats_gap": "84337531..84337619",', '"room_stats_gap": "84337901..84338019",'),
    ('"official_filled": "89/89 all five",', '"official_filled": "119/119 all five",'),
    ('_halfhour_backfill_retry2_1630.txt', '_halfhour_backfill_retry2_1700.txt'),
    ('"just-published first two attempts SIGKILL collateral of 16:26 patrol ~13GB python OOM at 16:39:26 and 16:40:25; slim retry recovered 16:41:16 game.time=84337804 base 84337600 all five rooms inserted=2597 (after this window).",',
     '"just-published 84338000 recovered 17:08:59 game.time=84338161 all five rooms inserted=3094 (after this window); W47N8@84337400 still 404.",'),
]
# The 2597 in verify line may have been changed if we did a global replace of INSERTED_JUST = 2597 only
for a, b in pairs:
    if a not in t:
        raise SystemExit(f"missing pair: {a[:100]!r}")
    t = t.replace(a, b)

p.write_text(t)
# leftover scan
for i, line in enumerate(t.splitlines(), 1):
    if any(s in line for s in ("1630", "84336901", "84337699", "4.903", "2597", "16:35:36", "16:41:16", "20265", "440177")):
        print(f"LEFTOVER {i}:{line}")
print("patched ok")
