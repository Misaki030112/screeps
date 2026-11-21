from pathlib import Path
import re

src = Path("/workspace/screeps/state/_halfhour_2026-11-21_1730")
dst = Path("/workspace/screeps/state/_halfhour_2026-11-21_1800")
dst.mkdir(parents=True, exist_ok=True)

text = (src / "tick_s_check.py").read_text()
text = text.replace("_halfhour_2026-11-21_1730", "_halfhour_2026-11-21_1800")

w46_new = """W46 = {
    84397500: 1795252627120,
    84397600: 1795253057610,
    84397700: 1795253492945,
    84397800: 1795253918171,
    84397900: 1795254339046,
    84398000: 1795254768719,
    84398100: 1795255197043,
}"""
min_new = """MIN_ALL = {
    84397500: 1795252627120,  # W46N8
    84397600: 1795253057610,  # W46N8
    84397700: 1795253492945,  # W46N8
    84397800: 1795253918171,  # W46N8
    84397900: 1795254337575,  # W45N7
    84398000: 1795254768719,  # W46N8
    84398100: 1795255196185,  # W45N7
}"""

text = re.sub(r"W46 = \{.*?\}", w46_new, text, count=1, flags=re.S)
text = re.sub(r"MIN_ALL = \{.*?\}", min_new, text, count=1, flags=re.S)
text = text.replace("TMIN, TMAX = 84397101, 84397800", "TMIN, TMAX = 84397501, 84398200")
text = text.replace(
    "TICK_S_FIRST = (MIN_ALL[84397200] - MIN_ALL[84397100]) / 1000.0 / 100  # script printed 4.189, exact 4.18908",
    "TICK_S_FIRST = (MIN_ALL[84397600] - MIN_ALL[84397500]) / 1000.0 / 100  # script printed 4.305, exact 4.3049",
)
text = text.replace("GT_FIRST = 84397873", "GT_FIRST = 84398214")
text = text.replace(
    "TS_REALIGNED_FIRST = 0  # first-pass realign moved 0 (inserted=0, already_in_db=25644, missing_chunks=1 W45N7@84397400)",
    "TS_REALIGNED_FIRST = 1355  # first-pass realign moved 1355 (inserted=8278, already_in_db=16757, missing_chunks=0)",
)
text = text.replace(
    "PREV_LATER_MEAN = 4.23884  # 17:00 half-hour tick_s_in_use (first)",
    "PREV_LATER_MEAN = 4.18908  # 17:30 half-hour tick_s_in_use (first)",
)
text = text.replace("printed 4.357", "printed 4.305")
text = text.replace("inserted=11674, already_in_db=14523, missing_chunks=1", "inserted=8278, already_in_db=16757, missing_chunks=0")
(dst / "tick_s_check.py").write_text(text)
print("tick_s_check written", "1730" in text, "TMIN", "84397501" in text, "bases", "MIN_ALL[84397600]" in text)

conf = (src / "backfill_confirm.py").read_text()
conf = conf.replace("_halfhour_2026-11-21_1730", "_halfhour_2026-11-21_1800")
old_in = 'IN_WINDOW = [("W45N7", 84397400)]  # first pass 34/35 official GETs 200, missing_chunks=1 W45N7@84397400. Window 84397101..84397800 (published_bases 84397100..84397700 at game.time=84397873). Already-told leftover official 404s age out of window start 84397101 and are not retried.'
new_in = 'IN_WINDOW = []  # first pass 35/35 official GETs 200, missing_chunks=0. Window 84397501..84398200 (published_bases 84397500..84398100 at game.time=84398214). Already-told leftover official 404 W45N7@84397400 aged out of window start 84397501 and is not retried.'
if old_in not in conf:
    print("WARN: IN_WINDOW old string not found exactly")
    # fallback: regex replace the assignment
    conf2, n = re.subn(r"IN_WINDOW = \[.*?\][^\n]*", new_in, conf, count=1, flags=re.S)
    print("regex replacements", n)
    conf = conf2
else:
    conf = conf.replace(old_in, new_in)
conf = conf.replace("TICK_S = 4.189", "TICK_S = 4.305")
(dst / "backfill_confirm.py").write_text(conf)
print("confirm written, IN_WINDOW empty?", "IN_WINDOW = []" in conf)

jp = (src / "backfill_just_published.py").read_text()
jp = jp.replace("_halfhour_2026-11-21_1730", "_halfhour_2026-11-21_1800")
jp = jp.replace("JUST_BASE = 84397800", "JUST_BASE = 84398200")
jp = jp.replace("base 84397800 once game.time is safely past 84397940", "base 84398200 once game.time is safely past 84398340")
(dst / "backfill_just_published.py").write_text(jp)
print("just_published written", "JUST_BASE = 84398200" in jp, "WAIT+140", "WAIT_UNTIL_GT = JUST_BASE + 140" in jp)

(dst / "history_backfill_first_attempt_err.txt").write_text("")
print("done")
