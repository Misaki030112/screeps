#!/usr/bin/env python3
from __future__ import annotations
import json, os, sys, subprocess
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path("/workspace/screeps")
DIR = ROOT / "state" / "_halfhour_2026-11-24_1200"
ROOMS = ("W46N8", "W47N8", "W45N8", "W45N7", "W47N7")
HK = ZoneInfo("Asia/Hong_Kong")
os.chdir(ROOT)
sys.path.insert(0, "tools")
import db

# Leftover official-404 holes still worth checking (plus any new ones later).
# Last delivered 3h patrol: ~20:44 _patrol_2026-11-23_2028 USER_LOG
# finished_at 20:43:58 (already delivered; do not re-tell that patrol or
# the earlier ~17:46 _patrol_2026-11-23_1728 USER_LOG, the ~14:44
# _patrol_2026-11-23_1427 USER_LOG, the ~11:46
# _patrol_2026-11-23_1129 USER_LOG, the ~08:34 0821 USER_LOG, or the
# 12h reviews _review12h_2026-11-23_20 ~20:40 and
# _review12h_2026-11-23_08 ~08:30).
# Quiet 22:00 half-hour _halfhour_2026-11-23_2200 wrapped 22:14:03
# official-filled 84441801..84442500 (published_bases 84441800..84442400
# at game.time=84442567; first pass --minutes 40, 34/35 200,
# missing_chunks=1 W45N7@84441900, still 404 after confirm 22:07:48
# gt=84442594 / retry2 22:08:29 gt=84442603 / late 22:09:00 gt=84442610
# / postjp 22:11:55 gt=84442651 inserted=0; not mere publish lag).
# tick_s_in_use later_raw 4.28346 (live-anchor-best).
# Standard --minutes 40 this 2230 pass. Retry leftover official 404s if
# still in/near this window; do not relabel already-recorded leftovers
# as NEW.
# NOT YET TOLD after quiet 2200 (and still-untold from quiet 2130/2100):
#   leftover official 404 W45N7@84441900 (first recorded as a first-pass
#   in-window 404 in quiet 2130; hole 84441901..84442000; listener 0/100;
#   still 404 through 2200 confirm/retry2/late/postjp);
#   盒子休眠 21:43:28-22:01:34 (from quiet 2200);
#   盒子休眠 21:21:51-21:28:39 (from quiet 2130);
#   盒子休眠 20:56:44-21:01:46 (from quiet 2100).
# Already told in the 20:44 2028 USER_LOG (finished_at 20:43:58):
#   leftover official 404s W47N7@84440900 (first recorded as a first-pass
#   in-window 404 in quiet 2030; also 404 in the 2028 patrol --minutes 210
#   first pass at gt=84441217; hole 84440901..84441000; listener 0/100),
#   W45N8@84439200, W45N8@84439300, W45N8@84439500 (from quiet 1830;
#   holes 84439201..84439300 / 84439301..84439400 / 84439501..84439600;
#   listener 27/100 on W45N8@84439200, 0/100 on the other two),
#   W47N7@84438700 (from quiet 1730 JP; hole 84438701..84438800;
#   listener 0/100);
#   盒子休眠 18:16:12-18:35:22, 18:52:46-18:58:58, 19:21:55-19:34:51,
#   and 20:14:37-20:28:31;
#   监听短中断 20:01:56.
# Already told in the 17:46 1728 USER_LOG: W45N8@84437100, W47N7@84436400,
# W47N8@84435500, W45N7@84435400, W45N7@84434800, W47N7@84434000, and older
# (1427/1129/0821 leftovers), plus freezes through 17:23:38-17:27:43.
# Retry leftovers if still in/near this official window; do not label them
# as NEW. Fold only newer freezes / short WS / leftover 404s than the
# already-told 2028 set plus the still-untold 2100/2130 items. Do not
# manually restart a healthy listener.

KNOWN_HOLES = [
    ("W47N7", 84452600),  # NOT YET TOLD; first recorded as a first-pass in-window official 404 in quiet 1030 at gt=84452986; other four rooms already 200 on 84452600; still 404 through confirm 10:35:42 / retry2 10:36:38 / late 10:37:28 / postjp 10:39:06 gt=84453076 official inserted=0; listener also 0/100 ticks 84452601..84452700; 376 ticks past chunk close 84452700 at postjp, not mere publish lag; retry if in/near window; do not relabel NEW until next 3h patrol tells it
    ("W46N8", 84450800),  # already told in ~08:31 0820 USER_LOG; leftover from quiet 0830; still 404 through 1030 postjp official inserted=0; listener 38/100 ticks 84450801..84450838; aged out of 1030 window start 84452201; retry if in/near window; do not relabel NEW
    ("W46N8", 84450500),  # already told in ~08:31 0820 USER_LOG; leftover from quiet 0730 JP; still 404 through 1030 postjp official inserted=0; listener 0/100; aged out of 1030 window start 84452201; retry if in/near window; do not relabel NEW
    ("W46N8", 84448500),  # NOT YET TOLD; first recorded as a first-pass in-window official 404 in quiet 0530; still 404 through confirm 05:37:24 / retry2 05:38:14 / late 05:38:59 / postjp 05:43:37 gt=84448959 official inserted=0 for this room; listener 50/100 ticks 84448501..84448550; 359 ticks past chunk close 84448600 at postjp, not mere publish lag, because the other four rooms on 84448500 already succeeded at the first pass; retry if in/near window; do not relabel NEW until next 3h patrol tells it
    ("W45N8", 84448600),  # NOT YET TOLD; first recorded as a first-pass in-window official 404 in quiet 0530; still 404 through confirm/retry2/late/postjp official inserted=0 for this room; listener 12/100 ticks 84448689..84448700; 259 ticks past chunk close 84448700 at postjp, not mere publish lag, because the other four rooms on 84448600 already succeeded at the first pass; retry if in/near window; do not relabel NEW until next 3h patrol tells it
    ("W47N8", 84448400),  # NOT YET TOLD; first recorded as a just-published official 404 in quiet 0500; still 404 through JP GET 05:13:21 gt=84448541 / retry 05:17:51 gt=84448600 / retry2 05:25:07 gt=84448700 official inserted=0 for this room; listener also 0/100 ticks 84448401..84448500; 200 ticks past the base / 200 past chunk close 84448500 at retry2, not mere publish lag, because the other four rooms on 84448400 already succeeded at +141; outside TMAX=84448400 of the 0500 window; retry if in/near window; do not relabel NEW until next 3h patrol tells it
    ("W47N8", 84447700),  # NOT YET TOLD; first recorded as a first-pass in-window official 404 in quiet 0430; still 404 through confirm 04:39:32 / retry2 04:40:18 / late 04:40:59 / postjp 04:45:08 gt=84448151 official inserted=0 for this room; listener also 0/100 ticks 84447701..84447800; 351 ticks past chunk close 84447800 at postjp, not mere publish lag, because the other four rooms on 84447700 already succeeded at the first pass; retry if in/near window; do not relabel NEW until next 3h patrol tells it
    ("W45N8", 84447400),  # NOT YET TOLD from quiet 0400; still 404 through 0430 confirm/retry2/late/postjp official inserted=0; listener also 0/100 ticks 84447401..84447500; still in 0430 window start 84447301; other four rooms already succeeded at 0400 first pass; do not relabel NEW until next 3h patrol tells it; first recorded as a first-pass in-window official 404 in quiet 0400; still 404 through confirm 04:06:59 / retry2 04:07:42 / late 04:08:20 / postjp 04:11:04 gt=84447680 official inserted=0 for this room; listener also 0/100 ticks 84447401..84447500; 180 ticks past chunk close 84447500 at postjp, not mere publish lag, because the other four rooms on 84447400 already succeeded at the first pass; retry if in/near window; do not relabel NEW until next 3h patrol tells it
    ("W47N7", 84446600),  # NOT YET TOLD; first recorded as a first-pass in-window official 404 in quiet 0300; still 404 through confirm 03:03:03 / retry2 03:03:56 / late 03:04:40 / postjp 03:12:08 gt=84446859 official inserted=0 for this room; listener also 0/100 ticks 84446601..84446700; 159 ticks past chunk close 84446700 at postjp, not mere publish lag, because the other four rooms on 84446600 already succeeded at first pass or confirm; retry if in/near window; do not relabel NEW until next 3h patrol tells it
    ("W46N8", 84445500),  # already told in ~02:34 0221 USER_LOG; first recorded as just-published official 404 in quiet 0130; still 404 through JP GET 01:45:20 gt=84445641 / retry 01:49:33 gt=84445700 / retry2 01:56:36 gt=84445800 official inserted=0; listener already 100/100 ticks 84445501..84445600 rows=963, no trajectory hole; 300 ticks past the base / 200 past chunk close 84445600 at retry2, not mere publish lag, because the other four rooms on 84445500 already succeeded at +141; outside TMAX=84445500 of the 0130 window; retry if in/near window; do not relabel NEW until next 3h patrol tells it
    ("W47N8", 84445100),  # already told in ~02:34 0221 USER_LOG; first recorded as just-published official 404 in quiet 0100; still 404 through JP GET 01:16:59 gt=84445242 / retry 01:21:18 gt=84445300 / retry2 01:28:14 gt=84445400 official inserted=0; listener 3/100 ticks 84445101..84445103; 300 ticks past the base / 200 past chunk close 84445200 at retry2, not mere publish lag, because the other four rooms on 84445100 already succeeded at +140; outside TMAX=84445100 of the 0100 window; retry if in/near window; do not relabel NEW until next 3h patrol tells it
    ("W45N7", 84444900),  # already told in ~02:34 0221 USER_LOG; first recorded as a first-pass in-window official 404 in quiet 0100; still 404 through late 01:09:39 / postjp 01:21:51 official inserted=0; listener also 0/100 ticks 84444901..84445000; 311 ticks past chunk close 84445000 at postjp, not mere publish lag, because the other four rooms on 84444900 already succeeded at the first pass; retry if in/near window; do not relabel NEW until next 3h patrol tells it
    ("W46N8", 84444500),  # already told in ~02:34 0221 USER_LOG; from quiet 0030; still 404 through 0100 late/postjp official inserted=0; listener also 0/100 ticks 84444501..84444600; still in 0100 window start 84444401; other four rooms already succeeded at 0030 first pass; retry if in/near window; do not relabel NEW until next 3h patrol tells it
    ("W46N8", 84444200),  # already told in ~02:34 0221 USER_LOG; first recorded as just-published official 404 in quiet 0000; still 404 through 0100 postjp; listener also 0/100 ticks 84444201..84444300; aged out of 0100 window start 84444401; retry if in/near window; do not relabel NEW until next 3h patrol tells it
    ("W47N8", 84443800),  # already told in ~02:34 0221 USER_LOG; first recorded as just-published official 404 in quiet 2330; still 404 through 0100 postjp; listener already 100/100 84443801..84443900; aged out of 0100 window start 84444401; retry if in/near window; do not relabel NEW until next 3h patrol tells it
    ("W47N7", 84443300),  # already told in 23:33 2321 patrol; first recorded as first-pass in-window 404 in quiet 2300; still 404 through 2330 confirm/retry2/late/postjp (not mere publish lag); retry if in/near window; do not relabel NEW
    ("W45N7", 84441900),  # already told in 23:33 2321 patrol; first recorded as first-pass in-window 404 in quiet 2130; still 404 through 2330 near-window retry; retry if in/near window; do not relabel NEW
    ("W47N7", 84440900),  # already told in 20:44 2028 patrol (also mentioned in 23:33 2321); first recorded as first-pass in-window 404 in quiet 2030; still 404 through 2330 near-window retry; retry if in/near window; do not relabel NEW
    ("W45N8", 84439200),  # already told in 20:44 2028 patrol; leftover from quiet 1830 first-pass; still 404 through 2030 postjp; retry if in/near window; do not relabel NEW
    ("W45N8", 84439300),  # already told in 20:44 2028 patrol; leftover from quiet 1830 first-pass; still 404 through 2030 postjp; retry if in/near window; do not relabel NEW
    ("W45N8", 84439500),  # already told in 20:44 2028 patrol; leftover from quiet 1830 first-pass; still 404 through 2030 postjp; retry if in/near window; do not relabel NEW
    ("W47N7", 84438700),  # already told in 20:44 2028 patrol; leftover from quiet 1730 JP; still 404 through 2030 postjp; retry if in/near window; do not relabel NEW
    ("W45N8", 84437100),  # already told in 17:46 1728 patrol; leftover from quiet 1600; retry if in/near window; do not relabel NEW
    ("W47N7", 84436400),  # already told in 17:46 1728 patrol; leftover from quiet 1500; retry if in/near window; do not relabel NEW
    ("W45N7", 84435400),  # already told in 17:46 1728 / 14:44 1427 patrol; retry if in/near window; do not relabel NEW
    ("W47N8", 84435500),  # already told in 17:46 1728 / 14:44 1427 patrol; leftover from quiet 1400; retry if in/near window; do not relabel NEW
    ("W45N7", 84434800),  # already told in 14:44 1427 patrol; retry if in/near window; do not relabel NEW
    ("W47N7", 84434000),  # already told in 14:44 1427 patrol; retry if in/near window; do not relabel NEW
    ("W47N8", 84433300),  # already told in 11:46 1129 patrol; retry if in/near window; do not label NEW
    ("W45N8", 84433100),  # already told in 11:46 1129 patrol; retry if in/near window; do not label NEW
    ("W45N8", 84432300),  # already told in 11:46 1129 patrol; retry if in/near window; do not label NEW
    ("W45N7", 84432500),  # already told in 11:46 1129 patrol; retry if in/near window; do not label NEW
    ("W47N7", 84432800),  # already told in 11:46 1129 patrol; retry if in/near window; do not label NEW
    ("W47N8", 84432000),  # already told in 11:46 1129 patrol; retry if in/near window; do not label NEW
    ("W47N8", 84431000),  # already told in 11:46 1129 patrol; retry if in/near window; do not label NEW
    ("W47N7", 84430800),  # already told in 08:34 0821 patrol (and 11:46); retry if in/near window; do not label NEW
    ("W47N7", 84430700),  # already told in 08:34 0821 patrol (and 11:46); retry if in/near window; do not label NEW
    ("W46N8", 84430500),  # already told in 08:34 0821 patrol (and 11:46); retry if in/near window; do not label NEW
    ("W47N8", 84429900),  # already told in 08:34 0821 patrol; retry if in/near window; do not label NEW
    ("W47N7", 84429300),  # already told in 08:34 0821 patrol; retry if in/near window; do not label NEW
    ("W45N7", 84428300),  # already told in 08:34 0821 patrol (and 05:40 0516); retry if in/near window; do not label NEW
    ("W45N8", 84426200),  # already told in 05:40 0516 patrol; retry if in/near window; do not label NEW
    ("W45N8", 84425500),  # already told in 02:43 patrol; retry if in/near window; do not label NEW
    ("W45N8", 84425800),  # already told in 02:43 patrol; retry if in/near window; do not label NEW
    ("W45N8", 84422100),  # already-told leftover in 22:37 patrol; retry if in/near window
    ("W45N8", 84422400),  # already-told leftover in 22:37 patrol; retry if in/near window
    ("W45N7", 84419000),  # already-told leftover; aged out of 84420301
    ("W45N7", 84419300),  # already-told leftover; aged out of 84420301
    ("W45N8", 84419600),  # already-told leftover; aged out of 84420301
    ("W46N8", 84418900),  # already told in 18:38 patrol; aged out of 19:00 window
    ("W47N8", 84418900),
    ("W45N8", 84418900),
    ("W45N7", 84418900),
    ("W47N7", 84418900),
    ("W47N8", 84400100),
    ("W45N7", 84400300),
    ("W45N7", 84400400),
    ("W45N7", 84403700),
    ("W45N7", 84403800),
    ("W45N8", 84406400),
    ("W46N8", 84406600),
    ("W46N8", 84406700),
    ("W46N8", 84407000),
    ("W45N8", 84407700),
    ("W47N7", 84407900),
    ("W46N8", 84408300),
    ("W47N8", 84408300),
    ("W47N8", 84409800),
    ("W45N7", 84411500),
    ("W47N7", 84412400),
    ("W46N8", 84413700),
    ("W46N8", 84414700),
    ("W45N8", 84415500),
]

# Previously recorded STATS gaps. Already told through the delivered ~11:46
# patrol _patrol_2026-11-23_1129 USER_LOG (finished_at 11:46:33):
# freeze_1122_1128 (11:22:21-11:28:28, STATS 84433481..84433589),
# freeze_1049_1050 (10:49:06-10:50:33, STATS 84433011..84433049),
# freeze_1008_1036 (10:08:51-10:36:08, STATS 84432441..84432839),
# freeze_0928_0935 (09:28:39-09:35:07, STATS 84431871..84431979),
# freeze_0854_0905 (08:54:25-09:05:57, STATS 84431391..84431559),
# plus the earlier already-told set from the ~08:34 0821 patrol
# (freeze_0818_0822 through freeze_0548_0606) and earlier patrols.
# Still-untold from the quiet 1200 half-hour:
# freeze_1151_1200 (11:51:57-12:00:55, STATS 84433911..84434049).
# Still-untold from the quiet 1230 half-hour:
# shortws_1234 (12:34:21, STATS 84434421..84434519).
# Still-untold from the quiet 1300 half-hour:
# freeze_1252_1256 (12:52:15-12:56:55, STATS 84434761..84434839).
# Fold only newer freezes / short WS than the already-told 11:46 1129
# patrol set plus those still-untold 1200/1230/1300 items.
# Do not restart the listener.

KNOWN_STATS_GAPS = [
    ("shortws_2021_stats", 84400171, 84400189),
    ("freeze_2049_stats", 84400561, 84400789),
    ("freeze_2142_stats", 84401311, 84401589),
    ("freeze_2214_stats", 84401751, 84401939),
    ("freeze_2249_stats", 84402241, 84402409),
    ("freeze_2320_stats", 84402681, 84402749),
    ("freeze_2353_stats", 84403151, 84403209),
    ("freeze_0011_stats", 84403391, 84403549),
    ("freeze_0050_stats", 84403921, 84404079),
    ("freeze_0118_stats", 84404311, 84404369),
    ("freeze_0150_stats", 84404761, 84404919),
    ("freeze_0213_stats", 84405081, 84405269),
    ("freeze_0244_stats", 84405501, 84405799),
    ("freeze_0347_stats", 84406431, 84406719),
    ("freeze_0418_stats", 84406881, 84406949),
    ("freeze_0441_stats", 84407211, 84407499),
    ("freeze_0517_stats", 84407741, 84407849),
    ("shortws_0525_stats", 84407871, 84407899),
    ("freeze_0552_stats", 84408271, 84408449),
    ("freeze_0621_stats", 84408691, 84408779),
    ("freeze_0650_stats", 84409111, 84409299),
    ("freeze_0720_stats", 84409551, 84409649),
    ("freeze_0744_stats", 84409901, 84410189),
    ("freeze_0851_stats", 84410881, 84411039),
    ("freeze_0914_stats", 84411221, 84411299),
    ("freeze_0941_stats", 84411621, 84411889),
    ("freeze_1016_stats", 84412131, 84412219),
    ("freeze_1045_stats", 84412541, 84412859),
    ("freeze_1145_stats", 84413411, 84413649),
    ("shortws_1214_stats", 84413821, 84413849),
    ("freeze_1220_stats", 84413921, 84413969),
    ("freeze_1251_stats", 84414371, 84414559),
    ("freeze_1316_stats", 84414731, 84414879),
    ("freeze_1348_stats", 84415191, 84415339),
    ("freeze_1415_stats", 84415571, 84415649),
    ("freeze_1447_stats", 84416041, 84416249),
    ("shortws_1602_stats", 84417111, 84417129),
    ("freeze_1615_stats", 84417291, 84417409),
    ("freeze_1644_stats", 84417731, 84417949),
    ("freeze_1712_stats", 84418131, 84418279),
    ("freeze_1741_stats", 84418531, 84418879),  # already told in 18:38 patrol
    ("shortws_1912_stats", 84419821, 84419849),  # already told in 19:36 patrol
    ("freeze_1943_stats", 84420281, 84420519),  # already told in 20:27 patrol
    ("freeze_2049_2059_stats", 84421221, 84421389),  # already told in 21:27 patrol
    ("freeze_2145_2204_stats", 84422041, 84422319),  # already told in 22:37 patrol
    ("freeze_2243_2305_stats", 84422871, 84423199),  # already told in 23:31 patrol
    ("freeze_2352_2359_stats", 84423801, 84423969),  # already told in 02:43 patrol
    ("freeze_0023_0033_stats", 84424291, 84424449),  # already told in 02:43 patrol
    ("freeze_0051_0057_stats", 84424691, 84424799),  # already told in 02:43 patrol
    ("freeze_0115_0127_stats", 84425041, 84425219),  # already told in 02:43 patrol
    ("freeze_0146_0201_stats", 84425481, 84425709),  # already told in 02:43 patrol
    ("freeze_0219_0228_stats", 84425951, 84426089),  # already told in 02:43 patrol
    ("freeze_0251_0258_stats", 84426401, 84426519),  # already told in 05:40 0516 patrol
    ("freeze_0322_0329_stats", 84426841, 84426959),  # already told in 05:40 0516 patrol
    ("freeze_0352_0358_stats", 84427261, 84427359),  # already told in 05:40 0516 patrol
    ("freeze_0420_0435_stats", 84427641, 84427859),  # already told in 05:40 0516 patrol
    ("freeze_0453_0458_stats", 84428081, 84428169),  # already told in 05:40 0516 patrol
    ("freeze_0516_0525_stats", 84428401, 84428539),  # already told in 05:40 0516 patrol
    ("freeze_0548_0606_stats", 84428841, 84429079),  # already told in 08:34 0821 patrol
    ("freeze_0623_0627_stats", 84429281, 84429349),  # already told in 08:34 0821 patrol
    ("freeze_0700_0706_stats", 84429761, 84429849),  # already told in 08:34 0821 patrol
    ("freeze_0738_0800_stats", 84430301, 84430629),  # already told in 08:34 0821 patrol
    ("freeze_0818_0822_stats", 84430871, 84430939),  # already told in 08:34 0821 patrol
    ("freeze_0854_0905_stats", 84431391, 84431559),  # already told in 11:46 1129 patrol
    ("freeze_0928_0935_stats", 84431871, 84431979),  # already told in 11:46 1129 patrol
    ("freeze_1008_1036_stats", 84432441, 84432839),  # already told in 11:46 1129 patrol
    ("freeze_1049_1050_stats", 84433011, 84433049),  # already told in 11:46 1129 patrol
    ("freeze_1122_1128_stats", 84433481, 84433589),  # already told in 11:46 1129 patrol
    ("freeze_1151_1200_stats", 84433911, 84434049),  # already told in 14:44 1427 patrol
    ("shortws_1234_stats", 84434421, 84434519),  # already told in 14:44 1427 patrol
    ("freeze_1252_1256_stats", 84434761, 84434839),  # already told in 14:44 1427 patrol
    ("freeze_1324_1327_stats", 84435221, 84435269),  # already told in 14:44 1427 patrol
    ("freeze_1350_1405_stats", 84435571, 84435809),  # already told in 14:44 1427 patrol
    ("freeze_1422_1427_stats", 84436041, 84436119),  # already told in 14:44 1427 patrol
    ("freeze_1450_1502_stats", 84436431, 84436619),  # already told in 17:46 1728 patrol
    ("freeze_1521_1531_stats", 84436871, 84437029),  # already told in 17:46 1728 patrol
    ("freeze_1549_1556_stats", 84437281, 84437379),  # already told in 17:46 1728 patrol
    ("freeze_1614_1629_stats", 84437621, 84437849),  # already told in 17:46 1728 patrol
    ("freeze_1652_1706_stats", 84438151, 84438369),  # already told in 17:46 1728 patrol
    ("freeze_1723_1727_stats", 84438601, 84438669),  # already told in 17:46 1728 patrol
    ("freeze_1816_1835_stats", 84439341, 84439619),  # already told in 20:44 2028 patrol; 盒子休眠 18:16:12-18:35:22; STATS 279t
    ("freeze_1852_1858_stats", 84439851, 84439959),  # already told in 20:44 2028 patrol; 盒子休眠 18:52:46-18:58:58; STATS 109t; official-filled all five 109/109
    ("freeze_1921_1934_stats", 84440261, 84440459),  # already told in 20:44 2028 patrol; 盒子休眠 19:21:55-19:34:51 (769s, STATS 199t; official-filled all five after 2028 patrol filled W47N7 84440302..84440494)
    ("shortws_2001_stats", 84440811, 84440839),  # already told in 20:44 2028 patrol; 监听短中断 20:01:56 (STATS 29t; official-filled all five 29/29 after JP 84440800)
    ("freeze_2014_2028_stats", 84441001, 84441209),  # already told in 20:44 2028 patrol; 盒子休眠 20:14:37-20:28:31 (834s, STATS 209t; official-filled all five 209/209); listener auto-restarted 20:28:34, python 3257911 started 20:28:44
    ("freeze_2056_2101_stats", 84441591, 84441679),  # already told in 23:33 2321 patrol; 盒子休眠 20:56:44-21:01:46 (292s, STATS 89t; official-filled all five 89/89); do not relabel NEW
    ("freeze_2121_2128_stats", 84441901, 84442049),  # already told in 23:33 2321 patrol; 盒子休眠 21:21:51-21:28:39 (400s, STATS 149t; official-filled W46N8/W47N8/W45N8/W47N7 149/149, W45N7 49/149 due to leftover official 404 W45N7@84441900); do not relabel NEW
    ("freeze_2143_2201_stats", 84442251, 84442509),  # already told in 23:33 2321 patrol; 盒子休眠 21:43:28-22:01:34 (1078s, STATS 259t; official-filled all five 259/259 after first pass plus JP 84442500); do not relabel NEW
    ("freeze_2223_2235_stats", 84442741, 84442989),  # already told in 23:33 2321 patrol; 盒子休眠 22:23:02-22:35:40 (747s, STATS 249t; official-filled all five 249/249 after 2230 first pass); do not relabel NEW
    ("freeze_2259_2305_stats", 84443221, 84443419),  # already told in 23:33 2321 patrol; 盒子休眠 22:59:15-23:05:47 (385s, STATS 199t; official-filled W46N8/W47N8/W45N8/W45N7 199/199; W47N7 99/199 missing 84443301..84443400 due to leftover official 404 W47N7@84443300); do not relabel NEW
    ("shortws_0034_stats", 84444571, 84444659),  # already told in ~02:34 0221 USER_LOG; from quiet 0030; 监听短中断 00:34:41; STATS gap 89t; official-filled W47N8/W45N8/W45N7/W47N7 89/89; W46N8 59/89 missing 84444571..84444600 due to leftover official 404 W46N8@84444500; do not relabel NEW
    ("shortws_0102_stats", 84444961, 84445069),  # already told in ~02:34 0221 USER_LOG; from quiet 0100; 监听短中断 01:02:38 (errors.log no STATS for 348s since ~00:56:50; then 01:04:10 ws error ping/pong timed out; no box_pauses row and no box-frozen line; listener auto-restarted 01:02:38 and 01:04:14, python 3379693 started 01:04:24, parent 4035476; STATS gap 109t; official-filled W46N8/W47N8/W45N8/W47N7 109/109; W45N7 69/109 missing 84444961..84445000 due to leftover official 404 W45N7@84444900); do not relabel NEW
    ("freeze_0203_0221_stats", 84445891, 84446159),  # already told in ~02:34 0221 USER_LOG; 盒子休眠 02:03:03-02:21:36 (1108s, STATS 269t; official-filled all five 269/269); listener auto-restarted 02:21:39, python 3411463 started 02:21:48, parent 4035476; do not relabel NEW
    ("shortws_0257_stats", 84446631, 84446659),  # NOT YET TOLD from quiet 0300; 监听短中断 02:57:18 (errors.log ws error ping/pong timed out; no box_pauses row and no box-frozen line; listener auto-restarted 02:57:21, python 3431965 started 02:57:31, parent 4035476; STATS gap 29t; official-filled W46N8/W47N8/W45N8/W45N7 29/29; W47N7 0/29 missing 84446631..84446659 due to leftover official 404 W47N7@84446600); do not relabel NEW
    ("freeze_0321_0331_stats", 84446991, 84447129),  # NOT YET TOLD from quiet 0330; 盒子休眠 03:21:51-03:31:05 (553s, STATS 139t; official-filled all five 139/139 after 0330 first pass plus JP 84447100); box_pauses row present; errors.log box frozen ~553s; listener auto-restarted 03:31:08, python 3445130 started 03:31:17, parent 4035476; do not relabel NEW
    ("freeze_0349_0401_stats", 84447381, 84447549),  # NOT YET TOLD from quiet 0400; 盒子休眠 03:49:23-04:01:11 (700s, STATS 169t; official-filled W46N8/W47N8/W45N7/W47N7 169/169, W45N8 69/169 missing 84447401..84447500 due to leftover official 404 W45N8@84447400); box_pauses row present; errors.log box frozen ~700s; listener auto-restarted 04:01:14, python 3455971 started 04:01:24, parent 4035476; do not relabel NEW
    ("freeze_0418_0432_stats", 84447781, 84447979),  # already told in ~08:31 0820 USER_LOG (was NOT YET TOLD from quiet 0430); 盒子休眠 04:18:52-04:32:23; do not relabel NEW
    ("freeze_0854_0905_today_stats", 84451621, 84451769),  # NOT YET TOLD from quiet 0900; 盒子休眠 08:54:41-09:05:01 (615s, official-filled all five 149/149; STATS 84451621..84451769); do not relabel NEW
    ("freeze_0923_0930_stats", 84452011, 84452129),  # NOT YET TOLD from quiet 0930; 盒子休眠 09:23:04-09:30:46 (462s, official-filled all five 119/119; STATS 84452011..84452129); do not relabel NEW
    ("freeze_0948_1000_stats", 84452371, 84452549),  # NOT YET TOLD from quiet 1000; 盒子休眠 09:48:37-10:00:27 (703s, official-filled all five 179/179; STATS 84452371..84452549); do not relabel NEW
    ("freeze_1018_1028_stats", 84452781, 84452939),  # NOT YET TOLD from quiet 1030; 盒子休眠 10:18:29-10:28:45 (610s, official-filled all five 159/159; STATS 84452781..84452939); do not relabel NEW
    ("freeze_1047_1100_stats", 84453181, 84453379),  # NOT YET TOLD from quiet 1100; 盒子休眠 10:47:01-11:00:07 (785s, official-filled all five 199/199; STATS 84453181..84453379); do not relabel NEW
]

# New 盒子休眠 / short WS after the quiet 2200 wrap (22:14:03) will be
# discovered as new_stats_*. Still-untold from quiet 2200/2130/2100 (do
# not relabel NEW): leftover official 404 W45N7@84441900; freeze_2143_2201;
# freeze_2121_2128; freeze_2056_2101.
# Already told in the ~20:44 2028 USER_LOG finished_at 20:43:58 (do not
# re-tell, do not relabel NEW): leftover official 404s W47N7@84440900,
# W45N8@84439200, W45N8@84439300, W45N8@84439500, W47N7@84438700;
# freeze_1816_1835, freeze_1852_1858, freeze_1921_1934, freeze_2014_2028;
# shortws_2001.
# Already told in the ~17:46 1728 USER_LOG finished_at 17:44:55:
# leftover official 404 W45N8@84437100, W47N7@84436400 and older;
# freezes through freeze_1723_1727.
# Last delivered patrol is ~20:44 2028 USER_LOG finished_at 20:43:58;
# do not re-tell already-told 2028/1728 leftovers/freezes. Do not
# manually restart a healthy listener.


def gaps(ticks):
    if not ticks:
        return []
    ticks = sorted(set(ticks))
    out = []
    expect = ticks[0]
    for t in ticks:
        if t > expect:
            out.append((expect, t - 1, t - expect))
        expect = t + 1
    return out


def main():
    now = datetime.now(HK).strftime("%Y-%m-%d %H:%M:%S Asia/Hong_Kong")
    print(f"pre_run {now}")
    live = json.loads((ROOT / "metrics/live.json").read_text())
    stats = live.get("stats") if isinstance(live.get("stats"), dict) else {}
    print(f"live.updated {live.get('updated')} stats.t {stats.get('t')} roomSlot {live.get('roomSlot')} cpu {live.get('cpu')} gameTime {live.get('gameTime')}")

    rot = json.loads((ROOT / "metrics/listener_rot.json").read_text())
    yield_p = ROOT / "metrics/listener_yield_rooms"
    print(f"listener_rot {rot} yield_absent={not yield_p.exists()}")

    out = subprocess.check_output(["ps", "-o", "pid,ppid,lstart,etime,stat,cmd", "-C", "python"], text=True)
    n_listeners = 0
    for line in out.splitlines():
        if "tools/listener.py" in line:
            n_listeners += 1
            print("listener_ps", line.strip())
    print(f"listener_count {n_listeners}")

    with db.connect() as c:
        rows = c.execute(
            "SELECT tick FROM room_stats WHERE tick >= (SELECT max(tick)-2000 FROM room_stats) ORDER BY tick"
        ).fetchall()
        ticks = [r[0] for r in rows]
        print(f"room_stats n {len(ticks)} min {ticks[0] if ticks else None} max {ticks[-1] if ticks else None}")
        gs = gaps(ticks)
        print("room_stats gaps (start,end,len) len>=11:")
        big = []
        for g in gs:
            if g[2] >= 11:
                print(f"  {g}")
                big.append(g)
        print("room_stats all gaps count", len(gs), "len>=11", len(big))
        print("room_stats all gaps (start,end,len):")
        for g in gs:
            print(f"  {g}")

        for table in ("creep_cpu", "path_arrivals", "room_stats"):
            row = c.execute(f"SELECT min(tick), max(tick), count(*) FROM {table}").fetchone()
            print(f"{table} all min={row[0]} max={row[1]} n={row[2]}")
            print(f"  tip {row[1]}")

        tip = ticks[-1] if ticks else 0
        t0 = (tip // 100) * 100 - 1000 + 1
        print(f"creep_ticks per room recent {t0}.. now")
        for room in ROOMS:
            r = c.execute(
                "SELECT min(tick), max(tick), count(*), count(DISTINCT tick) FROM creep_ticks "
                "WHERE room=%s AND tick>=%s",
                (room, t0),
            ).fetchone()
            print(f"  {room} min={r[0]} max={r[1]} rows={r[2]} distinct={r[3]}")

        for room, base in KNOWN_HOLES:
            r = c.execute(
                "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks "
                "WHERE room=%s AND tick BETWEEN %s AND %s",
                (room, base + 1, base + 100),
            ).fetchone()
            print(f"{room}@{base} hole distinct={r[0]} rows={r[3]} range={r[1]}..{r[2]}")

        gap_specs = list(KNOWN_STATS_GAPS)
        known_spans = {(a, b) for _, a, b in KNOWN_STATS_GAPS}
        for a, b, ln in big:
            if (a, b) not in known_spans:
                gap_specs.append((f"new_stats_{a}_{b}", a, b))

        for label, a, b in gap_specs:
            r = c.execute(
                "SELECT min(tick), max(tick), count(DISTINCT tick) FROM room_stats WHERE tick BETWEEN %s AND %s",
                (a, b),
            ).fetchone()
            print(f"room_stats {label} {a}..{b} min={r[0]} max={r[1]} distinct={r[2]}")
            for room in ROOMS:
                d, mn, mx, n = c.execute(
                    "SELECT count(DISTINCT tick), min(tick), max(tick), count(*) FROM creep_ticks "
                    "WHERE room=%s AND tick BETWEEN %s AND %s",
                    (room, a, b),
                ).fetchone()
                span = b - a + 1
                print(f"  {room} fill={int(d or 0)}/{span} rows={n} range={mn}..{mx}")

    pauses = []
    with open(ROOT / "metrics/box_pauses.jsonl") as f:
        for line in f:
            line = line.strip()
            if line:
                pauses.append(json.loads(line))
    print("box_pauses last 8:")
    for p in pauses[-8:]:
        print(f"  {p}")

    outp = (ROOT / "metrics/listener.out").read_text().splitlines()
    today = [ln for ln in outp if (ln.startswith("2026-11-22") or ln.startswith("2026-11-23") or ln.startswith("2026-11-24")) and "restart" in ln]
    print("listener.out recent restarts last 8:")
    for ln in today[-8:]:
        print(f"  {ln}")

    errp = ROOT / "metrics/errors.log"
    if errp.exists():
        lines = errp.read_text().splitlines()
        recent = [ln for ln in lines if ln.startswith("2026-11-22 ") or ln.startswith("2026-11-23 ") or ln.startswith("2026-11-24 ")]
        print("errors.log since 00:00 last 16:")
        for ln in recent[-16:]:
            print(f"  {ln}")


if __name__ == "__main__":
    main()
