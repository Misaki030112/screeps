from pathlib import Path

# Restore 1530 pre.txt / pre_raw.txt from the original 15:31 stdout (drop the trailing "wrote ..." line)
src1530 = Path("/workspace/screeps/state/_halfhour_2026-11-20_1530/pre_run_stdout.txt").read_text()
lines = src1530.splitlines()
if lines and lines[-1].startswith("wrote "):
    lines = lines[:-1]
nl = chr(10)
text = nl.join(lines) + nl
p = Path("/workspace/screeps/state/_halfhour_2026-11-20_1530")
(p / "pre.txt").write_text(text)
(p / "pre_raw.txt").write_text(text)
print("restored 1530 pre.txt bytes", len(text), "starts", text[:40].replace(nl, " | "), "ends", text[-80:].replace(nl, " | "))

# Fix 1600 pre_check DIR
chk = Path("/workspace/screeps/state/_halfhour_2026-11-20_1600/pre_check.py")
s = chk.read_text().replace(
    'DIR = ROOT / "state" / "_halfhour_2026-11-20_1530"',
    'DIR = ROOT / "state" / "_halfhour_2026-11-20_1600"',
)
if "_halfhour_2026-11-20_1530" in s:
    raise SystemExit("still has 1530 path")
chk.write_text(s)
print("fixed pre_check DIR")

# Write 1600 pre.txt from this run's stdout
src1600 = Path("/workspace/screeps/state/_halfhour_2026-11-20_1600/pre_run_stdout.txt").read_text()
lines = src1600.splitlines()
if lines and lines[-1].startswith("wrote "):
    lines = lines[:-1]
text = nl.join(lines) + nl
d = Path("/workspace/screeps/state/_halfhour_2026-11-20_1600")
(d / "pre.txt").write_text(text)
(d / "pre_raw.txt").write_text(text)
print("wrote 1600 pre.txt bytes", len(text))
