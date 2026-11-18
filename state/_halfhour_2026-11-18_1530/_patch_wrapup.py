#!/usr/bin/env python3
from pathlib import Path
p = Path("/workspace/screeps/state/_halfhour_2026-11-18_1530/wrapup.py")
t = p.read_text()

repls = [
("_halfhour_2026-11-18_1500", "_halfhour_2026-11-18_1530"),
('PREV = ROOT / "state" / "_halfhour_2026-11-18_1430" / "history_backfill.json"',
 'PREV = ROOT / "state" / "_halfhour_2026-11-18_1500" / "history_backfill.json"'),
("TMIN, TMAX = 84335801, 84336500", "TMIN, TMAX = 84336201, 84336900"),
("GT_FIRST = 84336595", "GT_FIRST = 84336947"),
('PUB_BASES = "84335800..84336400"', 'PUB_BASES = "84336200..84336800"'),
("TICK_S_FIRST = 4.62228", "TICK_S_FIRST = 4.54663"),
('TICK_S_PRINTED = "4.622"', 'TICK_S_PRINTED = "4.547"'),
('NEW_ROWS = {"W46N8": 1513, "W47N8": 4797, "W45N8": 1639, "W45N7": 782, "W47N7": 1029}',
 'NEW_ROWS = {"W46N8": 846, "W47N8": 649, "W45N8": 457, "W45N7": 333, "W47N7": 506}'),
("INSERTED_FIRST = 9760", "INSERTED_FIRST = 2791"),
("INSERTED_JUST_PUBLISHED = 3030", "INSERTED_JUST_PUBLISHED = 2601"),
("ALREADY = 15738", "ALREADY = 20841"),
("RECON_ROWS = 25498", "RECON_ROWS = 23632"),
("TS_REALIGNED_FIRST = 0", "TS_REALIGNED_FIRST = 17657"),
]
for a, b in repls:
    if a not in t:
        raise SystemExit("missing repl source: " + a)
    t = t.replace(a, b)

old_rem = """        rem_overlap = fill(c, 84335801, 84336200)
        rem_new = fill(c, 84336201, 84336500)
        rem_prev = fill(c, 84335801, 84336100)
        rem_prefill = fill(c, 84335801, 84335900)
        rem_just_window = fill(c, 84336401, 84336500)
        rem_just_published = fill(c, 84336501, 84336600)
        rem_prev_just = fill(c, 84336101, 84336200)
        rem_inwindow_404 = fill(c, 84336401, 84336500)"""
new_rem = """        rem_overlap_prev_window = fill(c, 84335801, 84336200)
        rem_new_prev_window = fill(c, 84336201, 84336500)
        rem_overlap = fill(c, 84336201, 84336600)
        rem_new = fill(c, 84336601, 84336900)
        rem_prev = fill(c, 84336201, 84336500)
        rem_prefill = fill(c, 84336101, 84336800)
        rem_just_window = fill(c, 84336801, 84336900)
        rem_just_published = fill(c, 84336901, 84337000)
        rem_prev_just = fill(c, 84336501, 84336600)
        rem_inwindow_404 = fill(c, 84336401, 84336500)
        rem_patrol_w47n7_367 = fill(c, 84336701, 84336800)
        freeze_1523 = fill(c, 84336791, 84336809)
        freeze_1523_pub = fill(c, 84336791, 84336800)
        freeze_1523_tail = fill(c, 84336801, 84336809)"""
if old_rem not in t:
    raise SystemExit("rem block not found")
t = t.replace(old_rem, new_rem)

old_prefill_ticks = '"hourly_patrol_prefill_ticks": [84335801, 84335900], "per_room": per_room,'
new_prefill_ticks = '"hourly_patrol_prefill_ticks": [84336101, 84336800], "per_room": per_room,'
if old_prefill_ticks not in t:
    raise SystemExit("prefill ticks not found")
t = t.replace(old_prefill_ticks, new_prefill_ticks)

old_rem_keys = '''        "remainder_overlap_84335801_84336200": rem_overlap,
        "remainder_new_84336201_84336500": rem_new,
        "remainder_prev_filled_84335801_84336100": rem_prev,
        "remainder_patrol_prefilled_84335801_84335900": rem_prefill,
        "remainder_window_last_chunk_84336401_84336500": rem_just_window,
        "remainder_just_published_84336501_84336600": rem_just_published,
        "remainder_prev_just_published_84336101_84336200": rem_prev_just,'''
new_rem_keys = '''        "remainder_overlap_84336201_84336600": rem_overlap,
        "remainder_new_84336601_84336900": rem_new,
        "remainder_prev_filled_84336201_84336500": rem_prev,
        "remainder_patrol_prefilled_84336101_84336800": rem_prefill,
        "remainder_window_last_chunk_84336801_84336900": rem_just_window,
        "remainder_just_published_84336901_84337000": rem_just_published,
        "remainder_prev_just_published_84336501_84336600": rem_prev_just,
        "remainder_patrol_recovered_w47n7_84336701_84336800": rem_patrol_w47n7_367,
        "remainder_overlap_prev_84335801_84336200": rem_overlap_prev_window,
        "remainder_new_prev_84336201_84336500": rem_new_prev_window,'''
if old_rem_keys not in t:
    raise SystemExit("rem keys not found")
t = t.replace(old_rem_keys, new_rem_keys)

old_corr = '''    tick_s_corr_txt = (
        f"later-mean-robust {later:.5f} already inside the 45s gate vs first-pass rows, "
        f"no corrective realign (nfix={nfix_corr} at game.time={tsr.get('gt_realign')}, still_over_45s_vs_later={vs_later_after.get('over45')})"
    )'''
new_corr = '''    tick_s_corr_txt = (
        f"later-mean-robust {later:.5f} was over the 45s gate vs first-pass rows (tick_s=4.54663 printed 4.547, ~101.3s at tmin); "
        f"applied corrective later-mean-robust realign of {nfix_corr} rows at game.time={tsr.get('gt_realign')}, still_over_45s_vs_later={vs_later_after.get('over45')}"
    )'''
if old_corr not in t:
    raise SystemExit("tick_s_corr_txt not found")
t = t.replace(old_corr, new_corr)

old_tsn = '''    ts_realign_note = (
        f"First pass (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}, live anchor game.time={GT_FIRST}) "
        f"moved {TS_REALIGNED_FIRST} rows, ts_realigned_first={TS_REALIGNED_FIRST}. "
        f"later-mean-robust {later:.5f} (delta first-robust -0.01245 s/tick, ~9.9s at tmin); "
        f"already inside the 45s gate, no corrective realign (nfix={nfix_corr}) at game.time={tsr.get('gt_realign')}; "
        f"still_over_45s_vs_later={vs_later_after.get('over45')}; vs_later over45={vs_later_after.get('over45')} "
        f"mean_off~{(vs_later_after.get('mean_off') or 0):.2f}s; skipped_cross_chunk=0. "
        f"in-use later-mean-robust {tick_s_in_use:.5f} (corrective_applied=False)."
    )'''
new_tsn = '''    ts_realign_note = (
        f"First pass (tick_s={TICK_S_FIRST} printed {TICK_S_PRINTED}, live anchor game.time={GT_FIRST}) "
        f"moved {TS_REALIGNED_FIRST} rows, ts_realigned_first={TS_REALIGNED_FIRST}. "
        f"later-mean-robust {later:.5f} (delta first-robust -0.13575 s/tick, ~101.3s at tmin) was over the 45s gate; "
        f"applied corrective later-mean-robust realign of {nfix_corr} rows at game.time={tsr.get('gt_realign')}; "
        f"still_over_45s_vs_later={vs_later_after.get('over45')}; vs_later over45={vs_later_after.get('over45')} "
        f"mean_off~{(vs_later_after.get('mean_off') or 0):.2f}s; skipped_cross_chunk=0. "
        f"in-use later-mean-robust {tick_s_in_use:.5f} (corrective_applied=True)."
    )'''
if old_tsn not in t:
    raise SystemExit("ts_realign_note not found")
t = t.replace(old_tsn, new_tsn)

old_gtn = '''    game_time_note = (
        "Listener restarted at 15:04:12 after the box freeze 14:43:48–15:04:09 (~1213s); pid 403238 under run_listener.sh 4035476. "
        "This run did not restart the listener, war_cmd, or pulse. "
        "live.json was fresh at pre-check (stats.t and cpu flowing; objects empty because the peacetime single-slot rotation was on W47N8, not home). "
        "Segment 90 buffers were pulled after the 15:04 reconnect (creep_cpu and path_arrivals already through the tip at pre-check). "
        "The 14:30 half-hour backfill had already official-backfilled 84335401..84336100 "
        "(just-published then recovered all five rooms @84336100 / 84336101..84336200), "
        "and the 14:17 hourly patrol official-backfilled through 84335900 (overlap with this window). "
        "Leftover official 404s W47N7@84334700, W47N8@84334600, W45N8@84333500, W47N8@84333300, W47N8@84332600, W47N7@84332600, W47N8@84332700, W45N8@84332200, W47N7@84331000, W47N7@84330300, W45N8@84328100 and W45N7@84328300 remain outside this window. "
        "In-window official hole W46N8@84336400 still 404 after confirm/retry2/just-published, treated as official hole, not told. Listener is on the peacetime single-slot rotation."
    )'''
new_gtn = '''    game_time_note = (
        "Listener was already running (pid 413974, started 15:23:10 after the 15:23:01 restart by the 15:22 hourly patrol, under run_listener.sh 4035476). "
        "This run did not restart the listener, war_cmd, or pulse. "
        "live.json was fresh at pre-check (stats.t and cpu flowing; objects empty because the peacetime single-slot rotation was on W47N8, not home). "
        "Segment 90 buffers were pulled after the 15:23 reconnect (creep_cpu and path_arrivals already through the tip at pre-check). "
        "The 15:00 half-hour backfill had already official-backfilled 84335801..84336500 "
        "(just-published then recovered all five rooms @84336500 / 84336501..84336600), "
        "and the 15:22 hourly patrol official-backfilled through 84336800 (overlap with this window; W47N7@84336700 was 404 there and is 200 on this pass). "
        "Leftover official 404s W47N7@84334700, W47N8@84334600, W45N8@84333500, W47N8@84333300, W47N8@84332600, W47N7@84332600, W47N8@84332700, W45N8@84332200, W47N7@84331000, W47N7@84330300, W45N8@84328100 and W45N7@84328300 remain outside this window. "
        "In-window official hole W46N8@84336400 still 404 after confirm/retry2/just-published, treated as official hole, not told. Listener is on the peacetime single-slot rotation. "
        "No new box freeze after 15:04:09. Room_stats gap 84336791..84336809 (19) is the 15:23 listener restart, not a box pause."
    )'''
if old_gtn not in t:
    raise SystemExit("game_time_note not found")
t = t.replace(old_gtn, new_gtn)

old_ins = '''    inserted_note = (
        f"This 15:00 first pass inserted {INSERTED_FIRST} new rows (already_in_db={ALREADY}, reconstructed={RECON_ROWS}). "
        "hourly_patrol_prefilled=true from 14:17 patrol official already through 84335900 (overlap); 14:30 backfill already wrote through 84336100 and just-published 84336100 (84336101..84336200) for all five rooms. "
        "The overlap 84335801..84336200 with the 14:30 window / just-published 84336100 / 14:17 patrol was already present. "
        "Newly published ticks 84336201..84336400 were official 200 on all five rooms in the first pass; 84336401..84336500 were official 200 on four rooms (W46N8@84336400 404). "
        "The in-window box-freeze gap 84336301..84336569 sits inside recovered chunks 84336300 (all five), 84336400 (four rooms; W46N8 official 404), plus just-published 84336500 (69-tick tail, all five). "
        f"Confirm at {confirm_at} game.time={confirm_gt} inserted={INSERTED_CONFIRM}; "
        "outside-window leftover official 404s unchanged; in-window W46N8@84336400 still 404. "
        f"retry2 at {retry2_at} game.time={retry2_gt} inserted={INSERTED_RETRY2}; leftovers and W46N8@84336400 still 404. "
        "Just-published at 15:12:42 game.time=84336673 base 84336500 recovered all five rooms inserted=3030 (after this window); W46N8@84336400 still 404. "
        f"Coverage official_recovered={recovered}/{expected} including {empty_no_creep} official empty-no-creep ticks (W45N7 5: 84335811..84335815); {official_404_missing} in-window official-404 ticks remain (W46N8@84336400). Official history recovered 3395 of 3500 room-ticks."
    )'''
new_ins = '''    inserted_note = (
        f"This 15:30 first pass inserted {INSERTED_FIRST} new rows (already_in_db={ALREADY}, reconstructed={RECON_ROWS}). "
        "hourly_patrol_prefilled=true from 15:22 patrol official already through 84336800 (overlap; W47N7@84336700 was 404 there and is 200 on this pass); 15:00 backfill already wrote through 84336500 and just-published 84336500 (84336501..84336600) for all five rooms. "
        "The overlap 84336201..84336600 with the 15:00 window / just-published 84336500, and 84336601..84336800 with the 15:22 patrol, was already largely present. "
        "Newly published ticks 84336801..84336900 were official 200 on all five rooms in the first pass; W47N7@84336700 (84336701..84336800) also 200 on this pass. W46N8@84336400 still 404. "
        "The still-in-window box-freeze gap 84336301..84336569 sits inside recovered chunks 84336300 (all five), 84336400 (four rooms; W46N8 official 404), plus previously just-published 84336500 (69-tick tail, all five). "
        f"Confirm at {confirm_at} game.time={confirm_gt} inserted={INSERTED_CONFIRM}; "
        "outside-window leftover official 404s unchanged; in-window W46N8@84336400 still 404. "
        f"retry2 at {retry2_at} game.time={retry2_gt} inserted={INSERTED_RETRY2}; leftovers and W46N8@84336400 still 404. "
        "Just-published at 15:38:55 game.time=84337006 base 84336900 recovered W46N8 and W45N7 inserted=1197; retry at 15:40:29 game.time=84337026 recovered W47N8, W45N8 and W47N7 inserted=1404; all five rooms 100/100, inserted=2601 (after this window); W46N8@84336400 still 404. "
        f"Coverage official_recovered={recovered}/{expected} including {empty_no_creep} official empty-no-creep ticks; {official_404_missing} in-window official-404 ticks remain (W46N8@84336400). Official history recovered 3400 of 3500 room-ticks."
    )'''
if old_ins not in t:
    raise SystemExit("inserted_note not found")
t = t.replace(old_ins, new_ins)

old_mcn = '''    missing_chunk_note = (
        f"First pass (game.time={GT_FIRST}) published_bases {PUB_BASES}, reconstructed {TMIN}..{TMAX} (700). 34 of 35 official GETs 200; missing_chunks=1 (W46N8@84336400). "
        f"Confirm at {confirm_at} game.time={confirm_gt} inserted={INSERTED_CONFIRM}; leftover official 404s unchanged; W46N8@84336400 still 404. "
        f"retry2 at {retry2_at} game.time={retry2_gt} inserted={INSERTED_RETRY2}; leftovers and W46N8@84336400 still 404. "
        "Just-published at 15:12:42 game.time=84336673 base 84336500 recovered all five rooms inserted=3030 (after this window); W46N8@84336400 still 404."
    )'''
new_mcn = '''    missing_chunk_note = (
        f"First pass (game.time={GT_FIRST}) published_bases {PUB_BASES}, reconstructed {TMIN}..{TMAX} (700). 34 of 35 official GETs 200; missing_chunks=1 (W46N8@84336400). "
        f"Confirm at {confirm_at} game.time={confirm_gt} inserted={INSERTED_CONFIRM}; leftover official 404s unchanged; W46N8@84336400 still 404. "
        f"retry2 at {retry2_at} game.time={retry2_gt} inserted={INSERTED_RETRY2}; leftovers and W46N8@84336400 still 404. "
        "Just-published at 15:38:55 game.time=84337006 and retry 15:40:29 game.time=84337026 base 84336900 recovered all five rooms inserted=2601 (after this window); W46N8@84336400 still 404."
    )'''
if old_mcn not in t:
    raise SystemExit("missing_chunk_note not found")
t = t.replace(old_mcn, new_mcn)

pairs = [
('just-published at 15:12:42 game.time=84336673 base 84336500 recovered all five rooms inserted=3030 (after this window); ',
 'just-published at 15:38:55/15:40:29 game.time=84337006/84337026 base 84336900 recovered all five rooms inserted=2601 (after this window); '),
('hourly_patrol_prefilled=true from 14:17 patrol official already through 84335900 (overlap); 14:30 backfill already wrote through 84336100 and just-published 84336100 (84336101..84336200) for all five rooms; ',
 'hourly_patrol_prefilled=true from 15:22 patrol official already through 84336800 (overlap; W47N7@84336700 was 404 there and is 200 on this pass); 15:00 backfill already wrote through 84336500 and just-published 84336500 (84336501..84336600) for all five rooms; '),
('just-published at 15:12:42 game.time=84336673 recovered all five rooms @84336500 inserted=3030 (after this window); ',
 'just-published at 15:38:55/15:40:29 game.time=84337006/84337026 recovered all five rooms @84336900 inserted=2601 (after this window); '),
('just-published 84336500 recovered all five rooms inserted=3030 (after this window); ',
 'just-published 84336900 recovered all five rooms inserted=2601 (after this window); '),
]
for a, b in pairs:
    if a not in t:
        raise SystemExit("missing text pair: " + a[:80])
    t = t.replace(a, b)

old_jp = '''        "just_published_at": "2026-11-18 15:12:42 Asia/Hong_Kong", "just_published_game_time": 84336673,
        "just_published_retry_at": None, "just_published_retry_game_time": None,'''
new_jp = '''        "just_published_at": "2026-11-18 15:38:55 Asia/Hong_Kong", "just_published_game_time": 84337006,
        "just_published_retry_at": "2026-11-18 15:40:29 Asia/Hong_Kong", "just_published_retry_game_time": 84337026,'''
if old_jp not in t:
    raise SystemExit("just_published_at not found")
t = t.replace(old_jp, new_jp)

old_rec = '"just_published_recovered": ["W46N8@84336500", "W47N8@84336500", "W45N8@84336500", "W45N7@84336500", "W47N7@84336500"],'
new_rec = '"just_published_recovered": ["W46N8@84336900", "W47N8@84336900", "W45N8@84336900", "W45N7@84336900", "W47N7@84336900"],'
if old_rec not in t:
    raise SystemExit("just_published_recovered not found")
t = t.replace(old_rec, new_rec)

old_fp = '''    prev_now = (ROOT / "state" / "_halfhour_2026-11-18_1430" / "history_backfill_now.txt").read_text()
    marker = "In-window box freeze 13:54:32"
    freeze_para = prev_now[prev_now.index(marker):]
    kept = []
    for ln in freeze_para.splitlines():
        if ln.startswith("listener single_slot"):
            break
        kept.append(ln)
    freeze_para = nl.join(kept).rstrip()
    def fill_txt(d):
        parts = [str(d[r]["distinct"]) for r in ROOMS]
        span = d[ROOMS[0]]["span"]
        return f"{'/'.join(parts)} of {span} of {span}"
    new_freeze = (
        f"In-window box freeze 14:43:48–15:04:09 (~1213s) room_stats gap 84336301..84336569; "
        f"official-filled {fill_txt(freeze_1443)} (W46N8 169/269 missing official 404 84336401..84336500; other four rooms 269/269); "
        f"in-window 84336301..84336400 all five {fill_txt(freeze_1443_pre)}; just-published tail 84336501..84336569 all five {fill_txt(freeze_1443_tail)}; "
        "W46N8@84336400 still 404 after confirm/retry2/just-published (0/100), treated as official hole, not told. "
        "listener resumed after the 15:04:12 restart (pid 403238, this run did not restart it)."
    )
    # keep the previous 13:54 paragraph as prior history
    rest = freeze_para.replace("In-window box freeze 13:54:32", "Prior box freeze 13:54:32", 1)
    freeze_para = new_freeze + nl + rest'''
new_fp = '''    prev_now = (ROOT / "state" / "_halfhour_2026-11-18_1500" / "history_backfill_now.txt").read_text()
    marker = "In-window box freeze 14:43:48"
    freeze_para = prev_now[prev_now.index(marker):]
    kept = []
    for ln in freeze_para.splitlines():
        if ln.startswith("listener single_slot"):
            break
        kept.append(ln)
    freeze_para = nl.join(kept).rstrip()
    def fill_txt(d):
        parts = [str(d[r]["distinct"]) for r in ROOMS]
        span = d[ROOMS[0]]["span"]
        return f"{'/'.join(parts)} of {span} of {span}"
    new_gap = (
        f"Listener restart 15:23:01 (15:22 hourly patrol, not this run; pid 413974) room_stats gap 84336791..84336809 (19); "
        f"official-filled {fill_txt(freeze_1523)} (in-window 84336791..84336800 all five {fill_txt(freeze_1523_pub)}; tail 84336801..84336809 all five {fill_txt(freeze_1523_tail)} after this first pass / just-published overlap). "
        "W47N7@84336700 was 404 at the 15:22 patrol first pass and 200 on this pass. No new box freeze after 15:04:09. "
        "listener already running after the 15:23:01 restart (pid 413974, this run did not restart it)."
    )
    # 14:43 freeze remains in this window
    freeze_para = new_gap + nl + freeze_para'''
if old_fp not in t:
    raise SystemExit("freeze_para block not found")
t = t.replace(old_fp, new_fp)

old_pay1 = '''        "freeze_1354_win": freeze_1354_win,
        "freeze_1354_tail": freeze_1354_tail,
    }'''
new_pay1 = '''        "freeze_1354_win": freeze_1354_win,
        "freeze_1354_tail": freeze_1354_tail,
        "freeze_1523_fill": freeze_1523,
        "freeze_1523_pub": freeze_1523_pub,
        "freeze_1523_tail": freeze_1523_tail,
    }'''
if old_pay1 not in t:
    raise SystemExit("payload freeze end not found")
t = t.replace(old_pay1, new_pay1)

old_pay2 = '''    payload["freeze_1354_fill"] = freeze_1354
    payload["freeze_1354_win"] = freeze_1354_win
    payload["freeze_1354_tail"] = freeze_1354_tail'''
new_pay2 = '''    payload["freeze_1354_fill"] = freeze_1354
    payload["freeze_1354_win"] = freeze_1354_win
    payload["freeze_1354_tail"] = freeze_1354_tail
    payload["freeze_1523_fill"] = freeze_1523
    payload["freeze_1523_pub"] = freeze_1523_pub
    payload["freeze_1523_tail"] = freeze_1523_tail'''
if old_pay2 not in t:
    raise SystemExit("payload freeze assign not found")
t = t.replace(old_pay2, new_pay2)

t = t.replace("_halfhour_backfill_retry2_1500.txt", "_halfhour_backfill_retry2_1530.txt")

p.write_text(t)
import ast
ast.parse(t)
print("wrapup.py patched, syntax ok")
print("DIR check", "_halfhour_2026-11-18_1530" in t and "TMIN, TMAX = 84336201, 84336900" in t)
