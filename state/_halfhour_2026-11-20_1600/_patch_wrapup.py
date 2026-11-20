from pathlib import Path

p = Path("/workspace/screeps/state/_halfhour_2026-11-20_1600/wrapup.py")
s = p.read_text()

old_prior = '''        prior_gap_fill[room] = f"{int(pd)}/{PRIOR_SPAN}"
    tips = {'''
new_prior = '''        prior_gap_fill[room] = f"{int(pd)}/{PRIOR_SPAN}"
    d, mn, mx, n = c.execute(
        "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks WHERE room=%s AND tick BETWEEN %s AND %s",
        ("W46N8", 84376101, 84376200),
    ).fetchone()
    w46n8_404_live = {"distinct": int(d or 0), "rows": int(n or 0), "min": mn, "max": mx}
    tips = {'''
if old_prior not in s:
    raise SystemExit("prior_gap_fill/tips block not found")
s = s.replace(old_prior, new_prior)

old_note = '''w45n7_gap_note = "W45N7 shortfall is official empty-no-creep (84375818..84375843, 26t inside the STATS gap; also earlier empty 84375445 and 84375447..84375614 from the invader-core civilian withdrawal), not a 404."'''
new_note = '''w45n7_gap_note = (
    "W46N8 missing 84376101..84376109 (9t) because official 404 W46N8@84376100 still unfilled after "
    "just-published GET 16:13:28 gt=84376240, retry 16:14:13 gt=84376251 and retry2 16:14:56 gt=84376261 "
    "(44 live ticks 84376157..84376200 present; hole 84376101..84376156). "
    "W45N7 shortfall is official empty-no-creep (84375818..84375843, 26t inside the STATS gap; "
    "also earlier empty 84375445 and 84375447..84375614 from the invader-core civilian withdrawal), not a 404."
)'''
if old_note not in s:
    raise SystemExit("w45n7_gap_note not found")
s = s.replace(old_note, new_note)

old_404 = '''    "new_official_404": [],'''
new_404 = '''    "new_official_404": [
        {
            "chunk": "W46N8@84376100",
            "hole": "84376101..84376200",
            "live_ticks_present": "84376157..84376200 (44t)",
            "still_404_after": "just-published 16:13:28 gt=84376240, retry 16:14:13 gt=84376251 and retry2 16:14:56 gt=84376261",
            "db": w46n8_404_live,
            "told": False,
            "first_recorded_by": "30-min backfill _halfhour_2026-11-20_1600",
        }
    ],'''
if old_404 not in s:
    raise SystemExit("new_official_404 not found")
s = s.replace(old_404, new_404)

old_confirm = '''    + "confirm skipped (no in-window official 404s; first pass 35/35 200, missing_chunks=0). retry2 skipped. Leftover official 404 W45N8@84375300 and older already-told 404s aged out of window start 84375401 and were not retried." + NL'''
new_confirm = '''    + "confirm skipped (no in-window official 404s; first pass 35/35 200, missing_chunks=0). retry2 skipped. Just-published 84376100: W46N8 still 404 after 16:13:28 / 16:14:13 / 16:14:56 (gt=84376240/84376251/84376261); 44 live ticks 84376157..84376200 present, hole 84376101..84376156. Leftover official 404 W45N8@84375300 and older already-told 404s aged out of window start 84375401 and were not retried." + NL'''
if old_confirm not in s:
    raise SystemExit("confirm skipped line not found")
s = s.replace(old_confirm, new_confirm)

old_none = '''    + "Official 404 in this first-pass window after confirm+retry2: none. Official empty-no-creep: W45N7 195t. W46N8/W47N8/W45N8/W47N7 700/700; W45N7 505/700 (195 empty)." + NL'''
new_none = '''    + "Official 404 in this first-pass window after confirm+retry2: none. Official empty-no-creep: W45N7 195t. W46N8/W47N8/W45N8/W47N7 700/700; W45N7 505/700 (195 empty). NEW leftover official 404 on just-published 84376100: W46N8 still 404 after 16:13:28/16:14:13/16:14:56; 44 live ticks 84376157..84376200 present, hole 56t 84376101..84376156." + NL'''
if old_none not in s:
    raise SystemExit("Official 404 none line not found")
s = s.replace(old_none, new_none)

old_none2 = '''    + "No new leftover official 404 in this window. Already-told leftover official 404 W45N8@84375300 (hole 84375301..84375400) aged out of window start 84375401 and was not retried (still unfilled; already told by the 15:29 1h patrol). Older already-told leftovers W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 also aged out and were not retried." + NL'''
new_none2 = '''    + "NEW leftover official 404 W46N8@84376100 (just-published; hole 84376101..84376200, 44 live ticks 84376157..84376200 present, still 404 after 16:13:28/16:14:13/16:14:56); told=false, first recorded by this 16:00 half-hour, left to 1h patrol. Already-told leftover official 404 W45N8@84375300 (hole 84375301..84375400) aged out of window start 84375401 and was not retried (still unfilled; already told by the 15:29 1h patrol). Older already-told leftovers W45N7@84373700, W47N8@84373800, W45N7@84373300, W47N7@84373200, W46N8@84371600 also aged out and were not retried." + NL'''
if old_none2 not in s:
    raise SystemExit("No new leftover line not found")
s = s.replace(old_none2, new_none2)

p.write_text(s)
print("patched wrapup.py", p.stat().st_size)
