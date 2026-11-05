"""Peacetime room slot for tools/listener.py.

The official Screeps websocket allows 2 room subscriptions per user. With 3,
the server answers 'subscribe limit reached' and every room loses ticks
(measured 2026-10-17: 2 rooms 10/10, 3 rooms 7-8/10). Ops used to pin W46N8
and rotate a second slot (W47N8 600s / W45N8 300s / W45N7 150s).

A separate Grok bot (Screeps指挥官) needs that second slot. Peacetime ops
therefore holds exactly one room and rotates it:

    W46N8 : W47N8 : W45N8 : W45N7  =  5 : 5 : 1 : 1   (wall clock)

UNIT_S = 120s, so the holds are 600, 600, 120, 120 (cycle 1440s). Creep
motion is slow; Misaki accepted the sparser samples.

Wartime, when that bot is live-commanding a local campaign: ops holds zero
room subscriptions. Touch metrics/listener_yield_rooms; the listener drops
its room within about 5s and keeps console + cpu (those are not room slots).
The commander subscribes the battle rooms, both official slots if the fight
needs two. Handback: commander unsubscribes, then remove the yield file.
Ops resumes this schedule. See docs/COMMANDER.md.
"""
SHARD = 'shard3'
HOME = 'W46N8'
WATCH = 'W45N8'  # watch events + creep trail; not copied as the live.json room
TRAIL = ('W47N8', 'W45N7')  # creep trail only (creep_ticks), not mixed into live.json
UNIT_S = 120
# Order is the rotation order. Weights are the wall-clock ratio, not tick counts.
WEIGHTS = (('W46N8', 5), ('W47N8', 5), ('W45N8', 1), ('W45N7', 1))
ROT = tuple((room, weight * UNIT_S) for room, weight in WEIGHTS)
PEACETIME_SLOTS = 1
WARTIME_OPS_SLOTS = 0
# Presence of this file under metrics/ means ops holds no room subscription.
YIELD_FILE = 'listener_yield_rooms'

def duty():
    """room -> share of one cycle (sums to 1)."""
    total = sum(w for _, w in WEIGHTS)
    return {room: w / total for room, w in WEIGHTS}

def cycle_s():
    return sum(hold for _, hold in ROT)

def room_at(elapsed_s):
    """The one room that owns the peacetime slot at this wall-clock offset.

    The boundary belongs to the next room: t=0 is W46N8, t=600 is W47N8.
    """
    if elapsed_s < 0:
        raise ValueError(elapsed_s)
    t = elapsed_s % cycle_s()
    acc = 0
    for room, hold in ROT:
        acc += hold
        if t < acc:
            return room
    return ROT[0][0]
