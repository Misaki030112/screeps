from pathlib import Path

p = Path("/workspace/screeps/state/_halfhour_2026-11-21_2230/wrapup_write.py")
t = p.read_text()

t = t.replace("WIN_TMIN, WIN_TMAX = 84400901, 84401600", "WIN_TMIN, WIN_TMAX = 84401301, 84402000")
t = t.replace("JUST_BASE = 84401500", "JUST_BASE = 84402000")
t = t.replace("PUBLISHED_BASES = [84400900, 84401500]", "PUBLISHED_BASES = [84401300, 84401900]")
t = t.replace("GT_FIRST = 84401604", "GT_FIRST = 84402070")
t = t.replace("INSERTED_FIRST = 13246", "INSERTED_FIRST = 243")
t = t.replace("TS_REALIGNED_FIRST = 10149", "TS_REALIGNED_FIRST = 12847")
t = t.replace("CREEP_ROWS_FIRST = 23278", "CREEP_ROWS_FIRST = 25461")
t = t.replace("ALREADY_IN_DB = 10032", "ALREADY_IN_DB = 25218")
t = t.replace(
    'jp = json.loads((DIR / "just_published_84401500.json").read_text())',
    'jp = json.loads((DIR / "just_published_84402000.json").read_text())',
)

old_gaps = """GAPS = [
    ("gap_2142_2201", 84401311, 84401589),  # NEW box freeze 21:42:29-22:01:09; not yet told
    ("gap_2049_2104", 84400561, 84400789),  # already told in _patrol_2026-11-21_2119
    ("gap_1952_2002", 84399771, 84399919),  # already told in _patrol_2026-11-21_2020
    ("gap_2021_shortws", 84400171, 84400189),  # already told in _patrol_2026-11-21_2020; aged out of this window start 84400901
]"""
new_gaps = """GAPS = [
    ("gap_2214_2226", 84401751, 84401939),  # NEW box freeze 22:14:12-22:26:30; not yet told unless 2226 patrol delivers
    ("gap_2142_2201", 84401311, 84401589),  # box freeze 21:42:29-22:01:09; still not delivered by a finished patrol as of this backfill
    ("gap_2049_2104", 84400561, 84400789),  # already told in _patrol_2026-11-21_2119
    ("gap_1952_2002", 84399771, 84399919),  # already told in _patrol_2026-11-21_2020
    ("gap_2021_shortws", 84400171, 84400189),  # already told in _patrol_2026-11-21_2020; aged out of this window start 84401301
]"""
if old_gaps not in t:
    raise SystemExit("GAPS block not found")
t = t.replace(old_gaps, new_gaps)

t = t.replace("aged out of window start 84400901", "aged out of window start 84401301")

old_fp = '''    "first_pass": {
        "gets_200": 32,
        "gets_total": 35,
        "missing_chunks": ["W47N8@84401500", "W45N8@84401500", "W47N7@84401500"],
        "reconstructed": [84400901, 84401600],
        "creep_rows": CREEP_ROWS_FIRST,
        "already_in_db": ALREADY_IN_DB,
        "inserted": inserted_first,
        "ts_realigned": TS_REALIGNED_FIRST,
        "tick_s_printed": 4.388,
        "overlap_compared": None,
        "overlap_match": None,
        "overlap_differ": None,
        "overlap_note": "First-pass output did not print an overlap compared/match/differ summary this run. Backfill does not overwrite existing rows.",
    },'''
new_fp = '''    "first_pass": {
        "gets_200": 35,
        "gets_total": 35,
        "missing_chunks": [],
        "reconstructed": [84401301, 84402000],
        "creep_rows": CREEP_ROWS_FIRST,
        "already_in_db": ALREADY_IN_DB,
        "inserted": inserted_first,
        "ts_realigned": TS_REALIGNED_FIRST,
        "tick_s_printed": 4.327,
        "overlap_compared": None,
        "overlap_match": None,
        "overlap_differ": None,
        "overlap_note": "First-pass output did not print an overlap compared/match/differ summary this run. Backfill does not overwrite existing rows. Concurrent 1h patrol already official-filled 84401201..84402000 (just-published 84401900 at 22:34:58 gt=84402045, inserted 2817) before this first pass.",
    },'''
if old_fp not in t:
    raise SystemExit("first_pass block not found")
t = t.replace(old_fp, new_fp)

t = t.replace(
    '''    "confirm": {
        "at": confirm_j.get("confirm_at") or confirm_j.get("at"),
        "skipped": False,''',
    '''    "confirm": {
        "at": confirm_j.get("confirm_at") or confirm_j.get("at"),
        "skipped": True,''',
)

old_jp = '''    "just_published": {
        "base": JUST_BASE,
        "included_in_first_pass": True,
        "first_pass_at": "2026-11-21 22:03:03 Asia/Hong_Kong",
        "first_pass_game_time": GT_FIRST,
        "first_pass_all_five_200": False,
        "first_pass_200": ["W46N8@84401500", "W45N7@84401500"],
        "first_pass_404": ["W47N8@84401500", "W45N8@84401500", "W47N7@84401500"],'''
new_jp = '''    "just_published": {
        "base": JUST_BASE,
        "included_in_first_pass": False,
        "first_pass_at": "2026-11-21 22:36:25 Asia/Hong_Kong",
        "first_pass_game_time": GT_FIRST,
        "first_pass_all_five_200": True,
        "first_pass_200": ["W46N8@84401900", "W47N8@84401900", "W45N8@84401900", "W45N7@84401900", "W47N7@84401900"],
        "first_pass_404": [],'''
if old_jp not in t:
    raise SystemExit("just_published block not found")
t = t.replace(old_jp, new_jp)

old_rst = '''        "restarts_before_this_run": [
            {"at": "22:01:12", "why": "box freeze 21:42:29-22:01:09", "python_started": "22:01:21", "pid": 2104047},
        ],'''
new_rst = '''        "restarts_before_this_run": [
            {"at": "22:01:12", "why": "box freeze 21:42:29-22:01:09", "python_started": "22:01:21", "pid": 2104047},
            {"at": "22:26:33", "why": "box freeze 22:14:12-22:26:30", "python_started": "22:26:42", "pid": 2110888},
        ],'''
if old_rst not in t:
    raise SystemExit("restarts block not found")
t = t.replace(old_rst, new_rst)

t = t.replace(
    '    "new_untold_box_freezes": ["21:42:29-22:01:09"],',
    '    "new_untold_box_freezes": ["22:14:12-22:26:30", "21:42:29-22:01:09"],',
)
t = t.replace(
    '    "concurrent_1h_patrol": "none during this run; next 1h patrol is due around 22:19; fold NEW 盒子休眠 21:42:29-22:01:09 into that patrol",',
    '    "concurrent_1h_patrol": "_patrol_2026-11-21_2226 running during this backfill; do not write its folder. It already recorded both freezes in freeze_clock. If that patrol delivers, treat both as already told afterwards; otherwise fold into the next 1h patrol after 2226.",',
)

old_fill = '''gap2142 = gaps["gap_2142_2201"]
gap2049 = gaps["gap_2049_2104"]
gap1952 = gaps["gap_1952_2002"]
gap2021 = gaps["gap_2021_shortws"]
fill2142 = ", ".join(f"{r} {gap2142[r]['fill']}" for r in ROOMS)
fill2049 = ", ".join(f"{r} {gap2049[r]['fill']}" for r in ROOMS)
fill1952 = ", ".join(f"{r} {gap1952[r]['fill']}" for r in ROOMS)
fill2021 = ", ".join(f"{r} {gap2021[r]['fill']}" for r in ROOMS)
'''
new_fill = '''gap2214 = gaps["gap_2214_2226"]
gap2142 = gaps["gap_2142_2201"]
gap2049 = gaps["gap_2049_2104"]
gap1952 = gaps["gap_1952_2002"]
gap2021 = gaps["gap_2021_shortws"]
fill2214 = ", ".join(f"{r} {gap2214[r]['fill']}" for r in ROOMS)
fill2142 = ", ".join(f"{r} {gap2142[r]['fill']}" for r in ROOMS)
fill2049 = ", ".join(f"{r} {gap2049[r]['fill']}" for r in ROOMS)
fill1952 = ", ".join(f"{r} {gap1952[r]['fill']}" for r in ROOMS)
fill2021 = ", ".join(f"{r} {gap2021[r]['fill']}" for r in ROOMS)
'''
if old_fill not in t:
    raise SystemExit("fill helpers not found")
t = t.replace(old_fill, new_fill)

# Mark start/end of wrap narrative by unique first and last lines, replace the whole wrap= block body via unique anchors
start = '    f"confirm at {confirm_at} gt={confirm_gt} recovered W47N8@84401500, W45N8@84401500, W47N7@84401500 inserted={inserted_confirm}; still_404 none. "'
end = '    f"No concurrent 1h patrol during this run. Fold only the NEW 盒子休眠 21:42:29-22:01:09 into the next 1h patrol; do not re-tell earlier already-told items.\\n"'
if start not in t or end not in t:
    raise SystemExit(f"wrap anchors missing start={start in t} end={end in t}")
new_wrap = r'''    f"confirm at {confirm_at} skipped no targets inserted={inserted_confirm}; still_404 none. "
    f"retry2 at {retry2_at} skipped no targets inserted={inserted_retry2}. "
    f"late retry skipped no targets inserted={inserted_late}. "
    f"First pass 35/35 official GETs 200, missing_chunks=0. "
    f"Leftover official 404s W45N7@84400400, W45N7@84400300, and W47N8@84400100 aged out of window start 84401301 and were not retried (already told in the delivered 21:31 / 20:34 1h patrols; do not re-tell). "
    f"Just-published 84402000 was not in first pass (first pass ended at published 84401900 / reconstructed 84401301..84402000 at 2026-11-21 22:36:25 Asia/Hong_Kong gt={GT_FIRST}, all five 200); GET at {jp.get('at')} gt={jp.get('game_time')} all_five_200={not jp.get('still_404')} script={script_sum} actual={actual_sum}; "
    f"W46N8 script {script_by['W46N8']} vs actual {actual_by['W46N8']}, W47N8 script {script_by['W47N8']} vs actual {actual_by['W47N8']}, W45N8 script {script_by['W45N8']} vs actual {actual_by['W45N8']}, W45N7 script {script_by['W45N7']} vs actual {actual_by['W45N7']}, W47N7 script {script_by['W47N7']} vs actual {actual_by['W47N7']}. "
    f"Coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}. "
    f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} just_actual={actual_sum} total={inserted_total}. "
    f"tick_s_in_use={tick_s_in_use:.5f} ({tick_s_name}) first={tick_s_first:.5f} ts_realigned_first={TS_REALIGNED_FIRST} corrective={corrective_nfix}. "
    f"NEW not yet told — fold into the next 1h patrol after the delivered 21:31 _patrol_2026-11-21_2119, unless the concurrent _patrol_2026-11-21_2226 already delivers this set: "
    f"盒子休眠 22:14:12-22:26:30 (737s, already healed; STATS 84401751..84401939, 189t; official-filled {fill2214}; listener auto-restart 22:26:33, python 2110888 started 22:26:42); "
    f"and still-untold 盒子休眠 21:42:29-22:01:09 (1115s, already healed; STATS 84401311..84401589, 279t; official-filled {fill2142}; listener auto-restart 22:01:12, python 2104047 started 22:01:21). "
    f"No new leftover official 404 and no new short WS this run. "
    f"Concurrent 1h patrol _patrol_2026-11-21_2226 is running (do not write its folder); it already official-filled 84401201..84402000 (just-published 84401900 at 22:34:58 gt=84402045 inserted=2817) and recorded both freezes in freeze_clock. If that patrol delivers, treat both freezes as already told afterwards. "
    f"_patrol_2026-11-21_2119 USER_LOG already includes (treat as already told; do not re-tell): "
    f"盒子休眠 20:49:04-21:04:03 (895s; official-filled {fill2049}); "
    f"监听短中断 21:13:29 ping/pong; "
    f"leftover official 404 W45N7@84400300 (listener {w45n7_84400300['distinct']}/100; hole {w45n7_84400300['hole_ticks']} ticks 84400301..84400400; aged out of this official window start 84401301) and W45N7@84400400 (listener {w45n7_84400400['distinct']}/100 {w45n7_84400400['min']}..{w45n7_84400400['max']}; hole {w45n7_84400400['hole_ticks']} ticks {hole_range_txt(w45n7_84400400)}; aged out of window start 84401301). "
    f"_patrol_2026-11-21_2020 USER_LOG finished 20:35:40 already includes (treat as already told; do not re-tell): "
    f"盒子休眠 19:52:19-20:02:21 (599s; official-filled {fill1952}; aged around/out of this window); "
    f"监听短中断 20:21:38 (STATS 84400171..84400189; official/listener fill {fill2021}; aged out of this official window start 84401301); "
    f"leftover official 404 W45N8@84399500, W45N7@84399800, and W47N8@84400100 (this run still 404 at W47N8@84400100; listener {w47n8_84400100['distinct']}/100; hole {w47n8_84400100['hole_ticks']} ticks 84400101..84400200; aged out of window start 84401301 and was not retried). "
    f"Already told by earlier delivered 1h patrols and not re-told: 盒子休眠 19:10:45-19:18:45, 18:47:50-18:58:17, leftover official 404 all five @84399100, W45N8@84399300, and older freezes/404s. "
    f"Fold only the NEW 盒子休眠 22:14:12-22:26:30 and the still-untold 21:42:29-22:01:09 into the next 1h patrol if 2226 does not deliver them; do not re-tell earlier already-told items.\n"'''
i0 = t.index(start)
i1 = t.index(end) + len(end)
t = t[:i0] + new_wrap + t[i1:]

start2 = '    f"window {WIN_TMIN}..{WIN_TMAX} first_pass 32/35 missing_chunks=3 W47N8@84401500,W45N8@84401500,W47N7@84401500 recovered on confirm\\n"'
end2 = '    f"NEW 盒子休眠 21:42:29-22:01:09 (1115s; STATS 84401311..84401589 279t; official-filled {fill2142}; listener auto-restart 22:01:12 pid=2104047 started=22:01:21) not yet told — fold into next 1h patrol\\n"'
if start2 not in t or end2 not in t:
    raise SystemExit(f"verify anchors missing start={start2 in t} end={end2 in t}")
new_ver = r'''    f"window {WIN_TMIN}..{WIN_TMAX} first_pass 35/35 missing_chunks=0\n"
    f"db_window {json.dumps(window_db)}\n"
    f"just_published 84402000 not in first pass; GET all_five_200={not jp.get('still_404')} script={script_sum} actual={actual_sum} by_actual={json.dumps(actual_by)} by_script={json.dumps(script_by)}\n"
    f"confirm skipped no targets inserted={inserted_confirm}; retry2 skipped; late skipped\n"
    f"coverage official_recovered={cov['official_recovered']}/{cov['expected']} empty_no_creep={cov['empty_no_creep']} official_404={cov['official_404_missing']}\n"
    f"inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} late={inserted_late} just_actual={actual_sum} total={inserted_total}\n"
    f"tick_s_in_use={tick_s_in_use:.5f} ({tick_s_name}) first={tick_s_first:.5f} ts_realigned_first={TS_REALIGNED_FIRST} corrective={corrective_nfix}\n"
    f"NEW leftover official 404 / short WS: none\n"
    f"NEW 盒子休眠 22:14:12-22:26:30 (737s; STATS 84401751..84401939 189t; official-filled {fill2214}; listener auto-restart 22:26:33 pid=2110888 started=22:26:42) not yet told — fold into next 1h patrol unless concurrent _patrol_2026-11-21_2226 delivers\n"
    f"still-untold 盒子休眠 21:42:29-22:01:09 (1115s; STATS 84401311..84401589 279t; official-filled {fill2142}; listener auto-restart 22:01:12 pid=2104047 started=22:01:21) — same: fold unless 2226 delivers\n"'''
# The old verify also had db_window / just_published / confirm / coverage / inserted / tick_s / NEW leftover lines between start2 and end2.
# start2 is the window line; end2 is the NEW freeze line. The db_window line is after start2, so we need to include those in the replacement. Good.

j0 = t.index(start2)
j1 = t.index(end2) + len(end2)
t = t[:j0] + new_ver + t[j1:]

t = t.replace(
    "f\"ok_quiet=True new_official_404_untold=[] new_box_freeze_untold=['21:42:29-22:01:09'] new_short_ws_untold=[]\\n\"",
    "f\"ok_quiet=True new_official_404_untold=[] new_box_freeze_untold=['22:14:12-22:26:30', '21:42:29-22:01:09'] new_short_ws_untold=[]\\n\"",
)

# leftover old numbers
left = []
for i, line in enumerate(t.splitlines(), 1):
    if any(s in line for s in ("84400901", "32/35", "84401500", "84401604", "13246", "22:03:03")):
        left.append(f"{i}: {line}")
print("remaining old constants:")
print("\n".join(left) if left else "(none)")
p.write_text(t)
print("wrote wrapup_write.py", len(t))
