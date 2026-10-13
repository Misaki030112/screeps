"""Continuous time-series store for creep telemetry (box side, zero in-game CPU for positions).
SQLite metrics/ts.sqlite (WAL, append-only):
  pos(tick, room, name, x, y, hits, e)            every tick a room update arrives over the websocket (per creep)
  cpu(tick, name, cpu, acts, work, rp, st, tgt)   in-game 5-tick windows from memory segment 90 (cpu in 0.01 ms units)
  arr(tick, name, role, tgt, plan, actual)        path arrivals: planned length vs actual ticks
  deploys(tick, ts, commit, note)                 every upload (scripts/deploy.py) -> before/after comparisons
Retention (prune()): full resolution 7 days; older pos rows downsampled to every 10th tick, kept 60 days."""
import sqlite3, os, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, 'metrics', 'ts.sqlite')
SCHEMA = """
CREATE TABLE IF NOT EXISTS pos(tick INT, room TEXT, name TEXT, x INT, y INT, hits INT, e INT, ts INT);
CREATE INDEX IF NOT EXISTS pos_t ON pos(tick); CREATE INDEX IF NOT EXISTS pos_n ON pos(name, tick);
CREATE TABLE IF NOT EXISTS cpu(tick INT, name TEXT, cpu INT, acts INT, work INT, rp INT, st INT, tgt TEXT, PRIMARY KEY(tick, name)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS arr(tick INT, name TEXT, role TEXT, tgt TEXT, plan INT, actual INT, PRIMARY KEY(tick, name, tgt)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS deploys(tick INT, ts INT, gitcommit TEXT, note TEXT);
"""
def connect():
    c = sqlite3.connect(DB, timeout=10); c.execute('PRAGMA journal_mode=WAL'); c.execute('PRAGMA synchronous=NORMAL'); c.executescript(SCHEMA); return c
def prune(c, now_ts=None):
    now = now_ts or int(time.time()); d7, d60 = now - 7 * 86400, now - 60 * 86400
    c.execute('DELETE FROM pos WHERE ts < ?', (d60,))
    c.execute('DELETE FROM pos WHERE ts < ? AND tick % 10 != 0', (d7,))
    c.commit()
