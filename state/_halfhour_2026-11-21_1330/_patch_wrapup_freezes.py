#!/usr/bin/env python3
from pathlib import Path
p = Path("/workspace/screeps/state/_halfhour_2026-11-21_1330/wrapup_write.py")
src = p.read_text()

def rep(old, new, label):
    global src
    n = src.count(old)
    if n != 1:
        raise SystemExit(f"{label}: found {n} occurrences, expected 1\n---OLD---\n{old[:400]}")
    src = src.replace(old, new)
    print("ok", label)

old_new_freeze = '''new_box_freeze = {
    "from": "2026-11-21 12:48:14",
    "to": "2026-11-21 12:57:17",
    "sec": 534,
    "stats": "84393831..84393969",
    "span": 139,
    "last_stats": "84393830 at 12:48:02",
    "next_stats": "84393970 at 12:57:57",
    "listener_restart": "12:57:20",
    "listener_pid": 1876378,
    "listener_started": "12:57:29",
    "official_fill": {r: (gaps.get("gap_1248_1257") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_missing("gap_1248_1257"),
    "told": False,
    "told_by": None,
    "first_recorded_by": "13:00 half-hour backfill",
    "note": (
        "NEW this run, not yet told. Box freeze 12:48:14-12:57:17 (534s); STATS 84393831..84393969 (139t). "
        "last_stats 84393830 at 12:48:02, next 84393970 at 12:57:57. Listener auto-restart 12:57:20, python 1876378 started 12:57:29, parent=4035476. "
        "This backfill official-filled all five 139/139 (published chunk 84393800 covering 84393831..84393900, plus just-published 84393900 covering the unpublished tail 84393901..84393969). "
        "Sits in official window start 84393201 and just-published 84393900. Next 1h patrol should tell this freeze together with the still-untold 12:30 freeze."
    ),
}'''

new_new_freeze = '''new_box_freeze = {
    "from": "2026-11-21 13:09:46",
    "to": "2026-11-21 13:21:14",
    "sec": 680,
    "stats": "84394131..84394299",
    "span": 169,
    "last_stats": "84394130 at 13:09:20",
    "next_stats": "84394300 at 13:21:31",
    "listener_restart": "13:21:17",
    "listener_pid": 1883231,
    "listener_started": "13:21:26",
    "official_fill": {r: (gaps.get("gap_1309_1321") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_missing("gap_1309_1321"),
    "told": False,
    "told_by": None,
    "first_recorded_by": "13:30 half-hour backfill",
    "note": (
        "NEW this run, not yet told. Box freeze 13:09:46-13:21:14 (680s); STATS 84394131..84394299 (169t). "
        "last_stats 84394130 at 13:09:20, next 84394300 at 13:21:31. Listener auto-restart 13:21:17, python 1883231 started 13:21:26, parent=4035476. "
        "This backfill official-filled all five 169/169 (chunks 84394100 and 84394200 cover the whole 169t inside official window start 84393701). "
        "Next 1h patrol should tell this freeze together with the still-untold 12:48 and 12:30 freezes."
    ),
}'''
rep(old_new_freeze, new_new_freeze, "new_box_freeze")

old_prior_1230 = '''prior_untold_freeze_1230 = {
    "from": "2026-11-21 12:30:42",
    "to": "2026-11-21 12:35:35",
    "sec": 283,
    "stats": "84393581..84393659",
    "span": 79,
    "last_stats": "84393580 at 12:30:15",
    "next_stats": "84393660 at 12:36:02",
    "listener_restart": "12:35:38",
    "listener_pid": 1869380,
    "listener_started": "12:35:48",
    "official_fill": {r: (gaps.get("gap_1230_1235") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_missing("gap_1230_1235"),
    "told": False,
    "told_by": None,
    "first_recorded_by": "12:30 half-hour backfill",
    "note": (
        "Still not yet told (first recorded by the 12:30 half-hour backfill). Box freeze 12:30:42-12:35:35 (283s); STATS 84393581..84393659 (79t). "
        "Official-filled all five 79/79 at the 12:30 run; still in official window start 84393201. "
        "Next 1h patrol should tell this freeze together with the newer 12:48 freeze. Do not treat as already told."
    ),
}'''
new_priors = '''prior_untold_freeze_1248 = {
    "from": "2026-11-21 12:48:14",
    "to": "2026-11-21 12:57:17",
    "sec": 534,
    "stats": "84393831..84393969",
    "span": 139,
    "last_stats": "84393830 at 12:48:02",
    "next_stats": "84393970 at 12:57:57",
    "listener_restart": "12:57:20",
    "listener_pid": 1876378,
    "listener_started": "12:57:29",
    "official_fill": {r: (gaps.get("gap_1248_1257") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_missing("gap_1248_1257"),
    "told": False,
    "told_by": None,
    "first_recorded_by": "13:00 half-hour backfill",
    "note": (
        "Still not yet told (first recorded by the 13:00 half-hour backfill). Box freeze 12:48:14-12:57:17 (534s); STATS 84393831..84393969 (139t). "
        "Official-filled all five 139/139 at the 13:00 run; still in official window start 84393701. "
        "Next 1h patrol should tell this freeze together with the newer 13:09 freeze and the still-untold 12:30 freeze. Do not treat as already told."
    ),
}

prior_untold_freeze_1230 = {
    "from": "2026-11-21 12:30:42",
    "to": "2026-11-21 12:35:35",
    "sec": 283,
    "stats": "84393581..84393659",
    "span": 79,
    "last_stats": "84393580 at 12:30:15",
    "next_stats": "84393660 at 12:36:02",
    "listener_restart": "12:35:38",
    "listener_pid": 1869380,
    "listener_started": "12:35:48",
    "official_fill": {r: (gaps.get("gap_1230_1235") or {}).get(r, {}).get("fill") for r in ROOMS},
    "official_fill_missing": fill_missing("gap_1230_1235"),
    "told": False,
    "told_by": None,
    "first_recorded_by": "12:30 half-hour backfill",
    "note": (
        "Still not yet told (first recorded by the 12:30 half-hour backfill). Box freeze 12:30:42-12:35:35 (283s); STATS 84393581..84393659 (79t). "
        "Official-filled all five 79/79 at the 12:30 run; ages out of official window start 84393701. "
        "Next 1h patrol should still tell this freeze together with 13:09 and 12:48. Do not treat as already told."
    ),
}'''
rep(old_prior_1230, new_priors, "prior_untolds")
p.write_text(src)
print("wrote freeze objects", p.stat().st_size)
