from pathlib import Path
p = Path("/workspace/screeps/state/_halfhour_2026-11-23_0600/wrapup_write.py")
t = p.read_text()

def sub(old, new, label):
    global t
    if old not in t:
        raise SystemExit(f"NOT FOUND: {label}")
    t = t.replace(old, new, 1)
    print("ok", label)

# add 0548 to verify gaps line
sub(
    '        + f"gaps 0516={{ { {r: gaps[\'gap_0516_0525\'][r][\'fill\'] for r in ROOMS} } }} ',
    '        + f"gaps 0548={{ { {r: gaps[\'gap_0548_0606\'][r][\'fill\'] for r in ROOMS} } }} 0516={{ { {r: gaps[\'gap_0516_0525\'][r][\'fill\'] for r in ROOMS} } }} ',
    "verify gaps 0548",
)

sub(
'''        + f"NEW 盒子休眠 this run: none. The 05:16:36-05:25:46 freeze (545s; STATS 84428401..84428539 official-filled {fill0516}; listener auto-restart 05:25:49, python 2883580 started 05:25:59, parent 4035476) was already told in the ~05:38 _patrol_2026-11-23_0516 USER_LOG finished_at 05:40:08; do not re-tell. Already-told 盒子休眠 04:53:04-04:58:42 (332s; STATS 84428081..84428169 official-filled {fill0453}; listener auto-restart 04:58:45, python 2872869 started 04:58:54, parent 4035476) and 04:20:59-04:35:45 (878s; STATS 84427641..84427859 official-filled {fill0420}; listener auto-restart 04:35:48, python 2862906 started 04:35:58, parent 4035476) and 03:52:38-03:58:50 (371s; STATS 84427261..84427359 official-filled {fill0352}; listener auto-restart 03:58:53, python 2850693 started 03:59:02, parent 4035476) and 03:22:33-03:29:51 (432s; STATS 84426841..84426959 official-filled {fill0322}; listener auto-restart 03:29:55, python 2838073 started 03:30:04, parent 4035476) and 02:51:37-02:58:39 (421s; STATS 84426401..84426519 official-filled {fill0251}; listener auto-restart 02:58:42, python 2822854 started 02:58:52, parent 4035476) were already told in the same 0516 USER_LOG; do not re-tell. Leftover official 404 W45N7@84428300 (first-pass 404 this window; still 404 after confirm/retry2/late/postjp; hole 100 ticks 84428301..84428400; listener {w45n7_84428300['distinct']}/100) already told in the 0516 USER_LOG; do not re-tell. Leftover official 404 W45N8@84426200 (previously still-untold from 03:00; aged out of window start 84427901, not retried this pass; hole 100 ticks 84426201..84426300; listener {w45n8_84426200['distinct']}/100) already told in the 0516 USER_LOG; do not re-tell. Leftover official 404 W45N8@84425500 and W45N8@84425800 (aged out, not retried this pass) already told in the 02:43 patrol USER_LOG and mentioned as already-told in the 0516 USER_LOG; do not re-tell. NEW leftover official 404 none this run beyond the 0516 USER_LOG (first pass 34/35 200, missing_chunks=1 W45N7@84428300, still 404 after confirm 05:36:48 / retry2 05:37:34 / late 05:41:15 / postjp 05:41:26). NEW 监听短中断 none. ''',
'''        + f"NEW 盒子休眠 this run: 05:48:18-06:06:20 Asia/Hong_Kong (1075s, box_pauses row; STATS 84428841..84429079, 239t; official-filled {fill0548}; listener auto-restart 06:06:23, python 2899745 started 06:06:33, parent 4035476) — NOT YET TOLD; fold into the next 3h patrol. Already-told 盒子休眠 05:16:36-05:25:46 (545s; STATS 84428401..84428539 official-filled {fill0516}; listener auto-restart 05:25:49, python 2883580 started 05:25:59, parent 4035476) was already told in the ~05:38 _patrol_2026-11-23_0516 USER_LOG finished_at 05:40:08; do not re-tell. Already-told 盒子休眠 04:53:04-04:58:42 (332s; STATS 84428081..84428169 official-filled {fill0453}; listener auto-restart 04:58:45, python 2872869 started 04:58:54, parent 4035476) and 04:20:59-04:35:45 (878s; STATS 84427641..84427859 official-filled {fill0420}; listener auto-restart 04:35:48, python 2862906 started 04:35:58, parent 4035476) and 03:52:38-03:58:50 (371s; STATS 84427261..84427359 official-filled {fill0352}; listener auto-restart 03:58:53, python 2850693 started 03:59:02, parent 4035476) and 03:22:33-03:29:51 (432s; STATS 84426841..84426959 official-filled {fill0322}; listener auto-restart 03:29:55, python 2838073 started 03:30:04, parent 4035476) and 02:51:37-02:58:39 (421s; STATS 84426401..84426519 official-filled {fill0251}; listener auto-restart 02:58:42, python 2822854 started 02:58:52, parent 4035476) were already told in the same 0516 USER_LOG; do not re-tell. Leftover official 404 W45N7@84428300 (not a first-pass 404 this window; near window start 84428401 so retried on confirm/retry2/late/postjp; still 404; hole 100 ticks 84428301..84428400; listener {w45n7_84428300['distinct']}/100) already told in the 0516 USER_LOG; do not re-tell. Leftover official 404 W45N8@84426200 (previously still-untold from 03:00; aged out of window start 84428401, not retried this pass; hole 100 ticks 84426201..84426300; listener {w45n8_84426200['distinct']}/100) already told in the 0516 USER_LOG; do not re-tell. Leftover official 404 W45N8@84425500 and W45N8@84425800 (aged out, not retried this pass) already told in the 02:43 patrol USER_LOG and mentioned as already-told in the 0516 USER_LOG; do not re-tell. NEW leftover official 404 none this run (first pass 35/35 200, missing_chunks=0). NEW 监听短中断 none. ''',
    "verify NEW freeze/404 prose",
)

sub(
    'new_box_freeze_untold=[] still_untold_freeze_from_0500=[]',
    'new_box_freeze_untold=[05:48:18-06:06:20] still_untold_freeze_from_0500=[]',
    "verify baseline new_box_freeze_untold",
)

sub(
    'first_pass_source=this_halfhour_0530 concurrent_patrol=_patrol_2026-11-23_0516_finished_at_05:40:08_USER_LOG_~05:38',
    'first_pass_source=this_halfhour_0600 concurrent_patrol=none_this_run last=_patrol_2026-11-23_0516_finished_at_05:40:08_USER_LOG_~05:38',
    "verify first_pass_source",
)

sub(
    '        "new_box_freeze_untold": [],\n',
    '        "new_box_freeze_untold": ["05:48:18-06:06:20"],\n',
    "snap new_box_freeze_untold",
)

sub(
    '        "concurrent_patrol": "_patrol_2026-11-23_0516_finished_at_05:40:08_USER_LOG_~05:38",\n',
    '        "concurrent_patrol": "none_this_run; last=_patrol_2026-11-23_0516_finished_at_05:40:08_USER_LOG_~05:38",\n',
    "snap concurrent_patrol",
)

sub(
    '        "first_pass_realign": "moved 1304 rows ts_realigned_first=1304 with first=4.22793; tick_s_check live-anchor-best first 4.22793 (first over45=0, later over45=20364, all_mean over45=18969), no corrective",\n',
    '        "first_pass_realign": "moved 14041 rows ts_realigned_first=14041 with first=4.32606; tick_s_check live-anchor-best prev_later 4.38831 (first over45=0, later over45=17169, all_mean over45=14973), no corrective",\n',
    "snap first_pass_realign",
)

p.write_text(t)
print("wrote wrapup")
needles = [
    "NEW 盒子休眠 this run: none.",
    "new_box_freeze_untold=[]",
    "first_pass_source=this_halfhour_0530",
    "missing_chunks=1 W45N7@84428300",
    "moved 1304 rows",
    "new_box_freeze_untold=[05:48:18-06:06:20]",
    'new_box_freeze_untold": ["05:48:18-06:06:20"]',
    "first_pass_source=this_halfhour_0600",
    "gaps 0548=",
]
for n in needles:
    print(("STILL" if n in t else "gone "), n)
