#!/bin/sh
# Run every tests/*.js and tests/*_test.py; print failures; exit 1 if any fail.
cd "$(dirname "$0")/.." || exit 2
fail=0
for f in tests/*.js; do timeout 60 node "$f" >/dev/null 2>&1 || { echo "FAIL $f"; fail=1; }; done
for f in tests/*_test.py; do [ -e "$f" ] || continue; timeout 60 .venv/bin/python "$f" >/dev/null 2>&1 || { echo "FAIL $f"; fail=1; }; done
[ $fail = 0 ] && echo "all tests pass"
exit $fail
