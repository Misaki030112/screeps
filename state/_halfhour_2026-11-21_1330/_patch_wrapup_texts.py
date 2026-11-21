#!/usr/bin/env python3
from pathlib import Path
p = Path("/workspace/screeps/state/_halfhour_2026-11-21_1330/wrapup_write.py")
src = p.read_text()

def rep(old, new, label):
    global src
    n = src.count(old)
    if n != 1:
        raise SystemExit(f"{label}: found {n} occurrences, expected 1\n---OLD start---\n{old[:200]}")
    src = src.replace(old, new)
    print("ok", label)

old_wrap = '''wrap_body = f"""---- wrap {now_s} ----
confirm at {confirm_at} game.time={confirm_gt} still_404={confirm_still} inserted={inserted_confirm} recovered={confirm_rec} skipped={confirm_skipped}; retry2 at {retry2_at} game.time={retry2_gt} still_404={retry2_still} inserted={inserted_retry2} recovered={retry2_rec} skipped={retry2_skipped}. First pass 35/35 official GETs 200, missing_chunks=0. Confirm 13:01:19 and retry2 13:01:32 both skipped, no targets. Already-told leftover official 404s W45N8@84392600 / W46N8@84390800 / W47N7@84390900 / W46N8@84390400 and older aged out of window start {WIN_TMIN} and were not retried. Just-published {JUST_BASE} at {jp.get('at')} gt={jp.get('game_time')} all_five_200={jp_all_five} script={script_sum} actual={actual_sum}. Coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404} (W45N7 178 empty-no-creep 84393411, 84393413..84393580 after invader-core evac, plus 84393793..84393798 and 84393817..84393819, not a 404). inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} just_actual={actual_sum} total={inserted_total}. tick_s_printed=4.272 first={tick_s_first:.5f} in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=0 corrective={corrective}. Listener pid=1876378 started=12:57:29 parent=4035476 slot={slot} rot={rot_s} yield={'absent' if yield_absent else 'present'} restarted_this_run=false. Peacetime single-slot 5:5:1:1. This run did not restart the listener or war_cmd/pulse.
NEW-this-window not yet told: box freeze 12:48:14-12:57:17 (534s; STATS 84393831..84393969, 139t; official-filled all five 139/139; listener auto-restart 12:57:20, python 1876378 started 12:57:29). Still not yet told from the 12:30 backfill and still in window: box freeze 12:30:42-12:35:35 (283s; STATS 84393581..84393659, 79t; official-filled all five 79/79; listener auto-restart 12:35:38, python 1869380 started 12:35:48). Already told by the 12:26 1h patrol t508s3573 and still in window: short listener WS gaps 12:10:56-12:10:59 (29t official-filled all five 29/29) and 12:18:13-12:18:17 (29t; W45N7 21/29 empty-no-creep 84393411..84393419 after evac, not a 404). Already-told leftover official 404 W45N8@84392600 and older leftovers W46N8@84390800 / W47N7@84390900 / W46N8@84390400 / W45N7@84388500 / W45N8@84386600, plus already-told freeze 11:49:12-11:57:31 and freezes through 11:19:06-11:20:43 and short WS gap 11:12:51-11:12:54, age out of window start {WIN_TMIN}. Fold the new freeze 12:48:14-12:57:17 and the still-untold 12:30:42-12:35:35; do not re-tell already-told freezes through 11:49:12-11:57:31 or leftover official 404 W45N8@84392600.
"""'''

new_wrap = '''wrap_body = f"""---- wrap {now_s} ----
confirm at {confirm_at} game.time={confirm_gt} still_404={confirm_still} inserted={inserted_confirm} recovered={confirm_rec} skipped={confirm_skipped}; retry2 at {retry2_at} game.time={retry2_gt} still_404={retry2_still} inserted={inserted_retry2} recovered={retry2_rec} skipped={retry2_skipped}. First pass 34/35 official GETs 200, missing_chunks=1 W46N8@84394300. Confirm 13:33:07 and retry2 13:33:42 still 404; late retry 13:39:21 gt=84394550 also still 404, inserted=0. Already-told leftover official 404s W45N8@84392600 / W46N8@84390800 / W47N7@84390900 / W46N8@84390400 and older aged out of window start {WIN_TMIN} and were not retried. Just-published {JUST_BASE} at {jp.get('at')} gt={jp.get('game_time')} all_five_200={jp_all_five} script={script_sum} actual={actual_sum}. Coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404} (W45N7 9 empty-no-creep 84393793..84393798 and 84393817..84393819, not a 404; W46N8 leftover official 404 hole 84394380..84394400, listener 79/100 84394301..84394379). inserted_first={inserted_first} confirm={inserted_confirm} retry2={inserted_retry2} just_actual={actual_sum} total={inserted_total}. tick_s_printed=4.236 first={tick_s_first:.5f} in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) ts_realigned_first=0 corrective={corrective}. Listener pid=1883231 started=13:21:26 parent=4035476 slot={slot} rot={rot_s} yield={'absent' if yield_absent else 'present'} restarted_this_run=false. Peacetime single-slot 5:5:1:1. This run did not restart the listener or war_cmd/pulse.
NEW-this-window not yet told: box freeze 13:09:46-13:21:14 (680s; STATS 84394131..84394299, 169t; official-filled all five 169/169; listener auto-restart 13:21:17, python 1883231 started 13:21:26). NEW leftover official 404 W46N8@84394300 not yet told (confirm+retry2+late_retry still 404; listener 79/100 84394301..84394379; hole 21 ticks 84394380..84394400). Still not yet told from the 13:00 backfill and still in window: box freeze 12:48:14-12:57:17 (534s; STATS 84393831..84393969, 139t; official-filled all five 139/139; listener auto-restart 12:57:20, python 1876378 started 12:57:29). Still not yet told from the 12:30 backfill but ages out of window start {WIN_TMIN}: box freeze 12:30:42-12:35:35 (283s; STATS 84393581..84393659, 79t; official-filled all five 79/79; listener auto-restart 12:35:38, python 1869380 started 12:35:48). Already told by the 12:26 1h patrol t508s3573 and now age out of window start {WIN_TMIN}: short listener WS gaps 12:10:56-12:10:59 and 12:18:13-12:18:17, leftover official 404 W45N8@84392600 and older leftovers W46N8@84390800 / W47N7@84390900 / W46N8@84390400 / W45N7@84388500 / W45N8@84386600, already-told freeze 11:49:12-11:57:31 and freezes through 11:19:06-11:20:43 and short WS gap 11:12:51-11:12:54. Fold the new freeze 13:09:46-13:21:14, the still-untold 12:48:14-12:57:17 and 12:30:42-12:35:35, and the new leftover official 404 W46N8@84394300; do not re-tell already-told freezes through 11:49:12-11:57:31 or leftover official 404 W45N8@84392600.
"""'''
rep(old_wrap, new_wrap, "wrap_body")

old_verify = '''verify = f"""{now_s}
first pass 35/35 official GETs 200 missing_chunks=0 reconstructed 84393201..84393900 (700); confirm skipped no targets inserted={inserted_confirm}; retry2 skipped no targets inserted={inserted_retry2}
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
{win_lines}
just-published {JUST_BASE} ticks 84393901..84394000 actual_inserted={actual_sum} script={script_sum} all_five_200={jp_all_five}
{chr(10).join(jp_lines)}
no in-window official 404 this run; already-told leftover official 404 W45N8@84392600 {hole926_d}/100 (listener 84392664..84392692, 29; hole 71) aged out of window start 84393201, not retried (already told by 12:26 1h patrol). Already-told leftovers W46N8@84390800 / W47N7@84390900 / W46N8@84390400 / W45N7@84388500 / W45N8@84386600 also aged out, not retried
gap_1248_1257 STATS 84393831..84393969 (139) NEW this run, not yet told (box freeze 12:48:14-12:57:17, 534s); last_stats 84393830 at 12:48:02, next 84393970 at 12:57:57; listener auto-restart 12:57:20, python 1876378 started 12:57:29; official-filled all five 139/139; published 84393831..84393900 plus just-published tail 84393901..84393969
{gap_lines("gap_1248_1257")}
gap_1230_1235 STATS 84393581..84393659 (79) still not yet told (recorded by 12:30 half-hour backfill; box freeze 12:30:42-12:35:35, 283s); official-filled all five 79/79; still in official window start 84393201
{gap_lines("gap_1230_1235")}
gap_1218 STATS 84393391..84393419 (29) already-told by 12:26 patrol (short listener WS ping/pong 12:18:13, restart 12:18:17, not a box freeze); four rooms 29/29; W45N7 21/29 missing 84393411..84393419 official empty-no-creep after evac, not a 404; still in official window start 84393201
{gap_lines("gap_1218")}
gap_1210 STATS 84393291..84393319 (29) already-told by 12:26 patrol (short listener WS ping/pong 12:10:56, restart 12:10:59, not a box freeze); official-filled all five 29/29; still in official window start 84393201
{gap_lines("gap_1210")}
gap_1149_1157 STATS 84393001..84393129 (129) already-told by 12:26 patrol (box freeze 11:49:12-11:57:31, 494s); official-filled all five 129/129; ages out of official window start 84393201
{gap_lines("gap_1149_1157")}
NEW box freeze 12:48:14-12:57:17 not yet told (official-filled all five 139/139). Still-untold 12:30:42-12:35:35 also not yet told (official-filled all five 79/79). Do not re-tell already-told freeze 11:49:12-11:57:31, short WS gaps 12:10/12:18/11:12, or leftover official 404 W45N8@84392600 and older leftovers.
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.272 corrective={corrective} ts_realigned_first=0
tips room_stats={tips.get("room_stats")} creep_cpu={tips.get("creep_cpu")} path_arrivals={tips.get("path_arrivals")}
listener pid=1876378 started=12:57:29 parent=4035476 slot={slot} rot={rot_s} yield={"absent" if yield_absent else "present"} restarted_this_run=false
ok_quiet=True
"""'''

new_verify = '''verify = f"""{now_s}
first pass 34/35 official GETs 200 missing_chunks=1 W46N8@84394300 reconstructed 84393701..84394400 (700); confirm still 404 inserted={inserted_confirm}; retry2 still 404 inserted={inserted_retry2}; late retry 13:39:21 gt=84394550 still 404 inserted=0
coverage official_recovered={cov_rec}/{cov_exp} empty_no_creep={empty_n} official_404={off404}
{win_lines}
just-published {JUST_BASE} ticks 84394401..84394500 actual_inserted={actual_sum} script={script_sum} all_five_200={jp_all_five}
{chr(10).join(jp_lines)}
NEW leftover official 404 W46N8@84394300 {hole943_d}/100 (listener 84394301..84394379, 79; hole 21 ticks 84394380..84394400) not yet told; confirm+retry2+late_retry still 404. Already-told leftover official 404 W45N8@84392600 {hole926_d}/100 (listener 84392664..84392692, 29; hole 71) aged out of window start 84393701, not retried (already told by 12:26 1h patrol). Already-told leftovers W46N8@84390800 / W47N7@84390900 / W46N8@84390400 / W45N7@84388500 / W45N8@84386600 also aged out, not retried
gap_1309_1321 STATS 84394131..84394299 (169) NEW this run, not yet told (box freeze 13:09:46-13:21:14, 680s); last_stats 84394130 at 13:09:20, next 84394300 at 13:21:31; listener auto-restart 13:21:17, python 1883231 started 13:21:26; official-filled all five 169/169; whole gap sits in official window start 84393701 (chunks 84394100 and 84394200)
{gap_lines("gap_1309_1321")}
gap_1248_1257 STATS 84393831..84393969 (139) still not yet told (recorded by 13:00 half-hour backfill; box freeze 12:48:14-12:57:17, 534s); official-filled all five 139/139; still in official window start 84393701
{gap_lines("gap_1248_1257")}
gap_1230_1235 STATS 84393581..84393659 (79) still not yet told (recorded by 12:30 half-hour backfill; box freeze 12:30:42-12:35:35, 283s); official-filled all five 79/79; ages out of official window start 84393701
{gap_lines("gap_1230_1235")}
gap_1218 STATS 84393391..84393419 (29) already-told by 12:26 patrol (short listener WS ping/pong 12:18:13, restart 12:18:17, not a box freeze); four rooms 29/29; W45N7 21/29 missing 84393411..84393419 official empty-no-creep after evac, not a 404; ages out of official window start 84393701
{gap_lines("gap_1218")}
gap_1210 STATS 84393291..84393319 (29) already-told by 12:26 patrol (short listener WS ping/pong 12:10:56, restart 12:10:59, not a box freeze); official-filled all five 29/29; ages out of official window start 84393701
{gap_lines("gap_1210")}
gap_1149_1157 STATS 84393001..84393129 (129) already-told by 12:26 patrol (box freeze 11:49:12-11:57:31, 494s); official-filled all five 129/129; ages out of official window start 84393701
{gap_lines("gap_1149_1157")}
NEW box freeze 13:09:46-13:21:14 not yet told (official-filled all five 169/169). NEW leftover official 404 W46N8@84394300 not yet told (listener 79/100, hole 21). Still-untold 12:48:14-12:57:17 also not yet told (official-filled all five 139/139). Still-untold 12:30:42-12:35:35 also not yet told (official-filled all five 79/79; ages out of this official window). Do not re-tell already-told freeze 11:49:12-11:57:31, short WS gaps 12:10/12:18/11:12, or leftover official 404 W45N8@84392600 and older leftovers.
tick_s_in_use={tick_s_in_use:.5f} ({tick_s_in_use_name}) first={tick_s_first:.5f} printed=4.236 corrective={corrective} ts_realigned_first=0
tips room_stats={tips.get("room_stats")} creep_cpu={tips.get("creep_cpu")} path_arrivals={tips.get("path_arrivals")}
listener pid=1883231 started=13:21:26 parent=4035476 slot={slot} rot={rot_s} yield={"absent" if yield_absent else "present"} restarted_this_run=false
ok_quiet=True
"""'''
rep(old_verify, new_verify, "verify")

p.write_text(src)
print("wrote wrap/verify", p.stat().st_size)
