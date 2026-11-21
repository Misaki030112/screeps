#!/usr/bin/env python3
from pathlib import Path

p = Path("/workspace/screeps/state/_patrol_2026-11-21_1423/exact2h.py")
t = p.read_text()
old = "BF_LO, BF_HI = 84393601, 84394300  # PATCH after backfill"
new = "BF_LO, BF_HI = 84394401, 84395100  # this hour first-pass official window"
if old in t:
    p.write_text(t.replace(old, new))
    print("exact2h BF patched")
elif "BF_LO, BF_HI = 84394401, 84395100" in t:
    print("exact2h BF already patched")
else:
    print("WARN exact2h BF not found")
    for i, ln in enumerate(t.splitlines(), 1):
        if "BF_LO" in ln:
            print(i, ln)

p = Path("/workspace/screeps/state/_patrol_2026-11-21_1423/_probe.py")
t = p.read_text()
if "BF_LO, BF_HI = 84393601, 84394300" in t:
    p.write_text(t.replace("BF_LO, BF_HI = 84393601, 84394300", "BF_LO, BF_HI = 84394401, 84395100"))
    print("probe BF patched")
else:
    print("probe BF lines:")
    for i, ln in enumerate(t.splitlines(), 1):
        if "BF_LO" in ln or "LAST_TIP" in ln:
            print(i, ln)

p = Path("/workspace/screeps/state/_patrol_2026-11-21_1423/freeze_clock.py")
t = p.read_text()
reps = [
    ('"""Console silences and listener restarts since last patrol (~11:28)."""',
     '"""Console silences and listener restarts since last patrol (~13:32)."""'),
    ("CUT = datetime(2026, 11, 21, 11, 20, 43, tzinfo=HK)",
     "CUT = datetime(2026, 11, 21, 13, 21, 14, tzinfo=HK)"),
    ("if t >= datetime(2026, 11, 21, 11, 0, tzinfo=HK):",
     "if t >= datetime(2026, 11, 21, 13, 0, tzinfo=HK):"),
    ('print(f"console lines after 11:00 in tail: {len(times)}")',
     'print(f"console lines after 13:00 in tail: {len(times)}")'),
    ('print("=== console silences >=60s after 11:20 ===")',
     'print("=== console silences >=60s after 13:21 ===")'),
    ('print("=== listener.out interesting lines after 11:00 ===")',
     'print("=== listener.out interesting lines after 13:00 ===")'),
    ('if re.search(r"2026-11-21 (11|12):|start|restart|subscribe|rot|yield|slot|freeze|hibern", line, re.I):',
     'if re.search(r"2026-11-21 (13|14):|start|restart|subscribe|rot|yield|slot|freeze|hibern", line, re.I):'),
    ('if line.startswith("2026-11-21 ") and line[11:13] < "11":',
     'if line.startswith("2026-11-21 ") and line[11:13] < "13":'),
    ('print("=== box_pauses after 11:12 ===")',
     'print("=== box_pauses after 13:21 ===")'),
    ("if to >= CUT or fr >= datetime(2026, 11, 21, 11, 12, tzinfo=HK):",
     "if to >= CUT or fr >= datetime(2026, 11, 21, 13, 21, tzinfo=HK):"),
]
for a, b in reps:
    if a not in t:
        print("WARN missing freeze snippet:", a[:90])
    else:
        t = t.replace(a, b)
p.write_text(t)
print("freeze_clock written")

p = Path("/workspace/screeps/state/_patrol_2026-11-21_1423/official_retry.py")
t = p.read_text()
start = t.find("IN_WINDOW = [")
end = t.find("TICK_S = ")
comment = t.rfind("# first-pass", 0, start) if start >= 0 else -1
print("official markers", comment, start, end)
if start >= 0 and end >= 0:
    if comment < 0:
        comment = start
    new_block = (
        "# first-pass 40-min backfill this hour missing_chunks=0 "
        "(published_bases 84394400..84395000, reconstructed 84394401..84395100).\n"
        "# No first-pass official 404s this hour. W46N8@84394300 is an already-told leftover "
        "whose hole 84394380..84394400 sits in the hour window.\n"
        "IN_WINDOW = [\n"
        '    ("W46N8", 84394300),  # already told by 13:32 1h patrol; listener 79/100 84394301..84394379; hole 21: 84394380..84394400\n'
        "]\n"
        "# leftover already-told official 404s, retry once in case they published\n"
        "LEFTOVER = [\n"
        '    ("W45N8", 84392600),  # already told; aged out of this window start 84394401\n'
        '    ("W46N8", 84390400),\n'
        '    ("W46N8", 84390800),\n'
        '    ("W47N7", 84390900),\n'
        '    ("W45N7", 84388500),\n'
        '    ("W45N8", 84386600),\n'
        '    ("W46N8", 84386400),\n'
        '    ("W47N8", 84385900),\n'
        '    ("W47N8", 84385300),\n'
        '    ("W45N7", 84383500),\n'
        '    ("W45N7", 84383900),\n'
        '    ("W45N8", 84382600),\n'
        '    ("W45N7", 84382700),\n'
        '    ("W46N8", 84382900),\n'
        "]\n"
        "TICK_S = 4.239  # first-pass official history (40-min 84394401..84395100)\n"
    )
    # convert escaped newlines written as literal backslash-n? We used \n in the heredoc?
    # This file is a quoted heredoc so \n in the python source becomes 
 in the string? 
    # In the shell heredoc 'ENDPY', backslash is literal. So I used \n which will be the two chars  n in the python source, and the python string will become real newlines if I use a normal string... wait.
    # I used "..." with \n. In the heredoc raw file, that's 
 (backslash + n) inside the python string, which IS a newline escape in Python. Good if the file contains 
 (one backslash).
    # In this shell command I wrote \n because... this is already inside a TS template? No, this is a shell command string in TS with backticks. Then the shell sees cat << 'ENDPY'. The TS template is the command. In the TS template, \ becomes  in the command sent to shell. Then heredoc 'ENDPY' is literal, so the python file gets 
 which Python interprets as newline. Good.
    t = t[:comment] + new_block + t[end + t[end:].find("\n") + 1:]
t = t.replace("    jp_base = 84393400  # next chunk after first-pass published_bases 84392700..84393300",
              "    jp_base = 84395100  # next chunk after first-pass published_bases 84394400..84395000")
t = t.replace("        LAST_TIP, TIP_GUESS = 84392640, 84393400",
              "        LAST_TIP, TIP_GUESS = 84394330, 84395100")
t = t.replace('        print("=== room_stats gaps since 84391000 ===", flush=True)',
              '        print("=== room_stats gaps since 84394300 ===", flush=True)')
t = t.replace(
    '            "SELECT tick, ts FROM room_stats WHERE room=\'W46N8\' AND tick>=84391800 ORDER BY tick"',
    '            "SELECT tick, ts FROM room_stats WHERE room=\'W46N8\' AND tick>=84394300 ORDER BY tick"',
)
p.write_text(t)
print("official_retry written")

# verify key lines
for path in [
    "/workspace/screeps/state/_patrol_2026-11-21_1423/exact2h.py",
    "/workspace/screeps/state/_patrol_2026-11-21_1423/official_retry.py",
    "/workspace/screeps/state/_patrol_2026-11-21_1423/freeze_clock.py",
    "/workspace/screeps/state/_patrol_2026-11-21_1423/_probe.py",
]:
    txt = Path(path).read_text()
    print("---", Path(path).name, "---")
    for i, ln in enumerate(txt.splitlines(), 1):
        if any(k in ln for k in ("LAST_TIP", "BF_LO", "TICK_S =", "jp_base", "CUT =", "IN_WINDOW", "84394300", "84395100", "tick>=8439")):
            if i <= 40 or "jp_base" in ln or "LAST_TIP, TIP" in ln or "tick>=" in ln or "CUT" in ln:
                print(f"  {i}: {ln}")
