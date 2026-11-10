#!/usr/bin/env python3
"""Reconstruct official history + DB traces into energy-flow measurements."""
from __future__ import annotations
import json, sys, os
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timezone, timedelta

ROOT = Path('/workspace/screeps')
sys.path.insert(0, str(ROOT / 'tools'))
import db

CACHE = ROOT / 'state' / 'hist_cache'
OUT = ROOT / 'state' / '_energy_flow_numbers.json'
HKT = timezone(timedelta(hours=8))

W46 = {
    'srcA': (32, 11), 'srcA_cont': (31, 12), 'srcA_link': (30, 11),
    'srcB': (39, 33), 'srcB_cont': (38, 32),
    'ctl_cont': (30, 30), 'ctl_link': (30, 31),
    'hub_link': (37, 29), 'storage': (37, 31),
    'fillerA': (35, 24), 'cont_34_34': (34, 34), 'min_cont': (41, 24),
    'spawn1': (35, 28), 'spawn2': (30, 34),
    'up_spots': {(30, 30), (31, 30), (29, 30), (31, 31), (29, 31)},
    'drop': (31, 29),
}
W47 = {
    'srcA': (27, 11), 'srcA_cont': (26, 11), 'srcA_link': (26, 12),
    'srcB': (11, 44), 'srcB_cont': (11, 43),
    'ctl_cont': (13, 26), 'ctl_link': (13, 25),
    'hub_cont': (33, 33), 'hub_link': (33, 34),
    'storage': (35, 32),  # from model stores key
    'up_spots': {(12, 25), (12, 26), (14, 26), (14, 27)},
}

def apply_update(state, upd):
    if not isinstance(upd, dict):
        return
    for oid, o in upd.items():
        if o is None:
            state.pop(oid, None)
        elif not isinstance(o, dict):
            continue
        elif oid in state:
            state[oid].update(o)
        else:
            state[oid] = dict(o)

def iter_chunks(room):
    files = sorted(CACHE.glob(f'{room}_*.json'), key=lambda p: int(p.stem.split('_')[1]))
    return files

def reconstruct(room):
    """Yield (hist_tick, state) for end-of-tick snapshots. hist_tick is official key."""
    state = {}
    for f in iter_chunks(room):
        j = json.loads(f.read_text())
        ticks = {}
        for k, v in (j.get('ticks') or {}).items():
            try:
                ticks[int(k)] = v
            except Exception:
                continue
        for t in sorted(ticks):
            upd = ticks[t]
            if upd is not None:
                apply_update(state, upd)
            # shallow copy of interest only would be cheaper; copy refs is ok if we extract immediately
            yield t, state

def energy_of(o):
    if not o:
        return None
    typ = o.get('type')
    if typ in ('source',):
        return o.get('energy')
    if typ in ('energy',):
        return o.get('energy') or 0
    st = o.get('store')
    if isinstance(st, dict):
        return st.get('energy') or 0
    return None

def index_by_pos(state, types=None):
    out = {}
    for o in state.values():
        if not isinstance(o, dict) or o.get('x') is None:
            continue
        typ = o.get('type')
        if types and typ not in types:
            continue
        out[(typ, o['x'], o['y'])] = o
    return out

def harvest_from_source(series):
    """series: list (tick, energy, ttr). Return harvested e, ticks, waste (left at regen)."""
    harvested = 0
    waste = 0
    n = 0
    prev = None
    for t, e, ttr in series:
        if e is None:
            prev = None
            continue
        n += 1
        if prev is not None:
            pe, pttr = prev
            if e < pe:
                harvested += pe - e
            elif e > pe + 50:
                # regen: leftover wasted = pe if ttr was low / energy jumped toward 3000
                waste += pe  # energy left unharvested at regen
                # new pile starts at e (usually 3000)
        prev = (e, ttr)
    return harvested, waste, n

def main():
    report = {}
    # ---- W46N8 structure time series ----
    keys = W46
    want_types = {'source','container','link','storage','spawn','energy','creep','extension','tower','terminal'}
    series = defaultdict(list)  # name -> list of (tick, energy)
    dropped = []  # (tick, x, y, amt)
    creeps = []  # (tick, name, x, y, e, spawning, role)
    ext_sum = []  # (tick, energyAvailable-like, cap)
    n_ticks = 0
    tmin = tmax = None
    srcA_s = []
    srcB_s = []
    # link send detect
    link_e = defaultdict(list)

    last_extract = None
    for t, state in reconstruct('W46N8'):
        n_ticks += 1
        tmin = t if tmin is None else min(tmin, t)
        tmax = t if tmax is None else max(tmax, t)
        by = index_by_pos(state, want_types)
        def e_at(typ, xy):
            o = by.get((typ, xy[0], xy[1]))
            return energy_of(o)
        rec = {
            'tick': t,
            'srcA': e_at('source', keys['srcA']),
            'srcB': e_at('source', keys['srcB']),
            'srcA_cont': e_at('container', keys['srcA_cont']),
            'srcB_cont': e_at('container', keys['srcB_cont']),
            'ctl_cont': e_at('container', keys['ctl_cont']),
            'ctl_link': e_at('link', keys['ctl_link']),
            'hub_link': e_at('link', keys['hub_link']),
            'srcA_link': e_at('link', keys['srcA_link']),
            'storage': e_at('storage', keys['storage']),
            'fillerA': e_at('container', keys['fillerA']),
            'spawn1': e_at('spawn', keys['spawn1']),
            'spawn2': e_at('spawn', keys['spawn2']),
        }
        # ttr
        sa = by.get(('source',)+keys['srcA']); sb = by.get(('source',)+keys['srcB'])
        rec['srcA_ttr'] = sa.get('ticksToRegeneration') if sa else None
        rec['srcB_ttr'] = sb.get('ticksToRegeneration') if sb else None
        # extensions sum
        e_ext = cap_ext = 0
        n_ext_empty = 0
        for typ,x,y in by:
            if typ == 'extension' or typ == 'spawn' or typ == 'tower':
                o = by[(typ,x,y)]
                ev = energy_of(o) or 0
                cap = o.get('storeCapacity') or (50 if typ=='extension' else 300 if typ=='spawn' else 1000)
                # spawn/tower storeCapacity may be in store
                if typ=='extension':
                    cap = 50
                    e_ext += ev; cap_ext += cap
                    if ev < 50: n_ext_empty += 1
                elif typ=='spawn':
                    cap = 300
                    e_ext += ev; cap_ext += cap
        rec['e_avail'] = e_ext
        rec['e_cap_extspawn'] = cap_ext
        rec['n_ext_emptyish'] = n_ext_empty
        # dropped energy
        drops = []
        for typ,x,y in by:
            if typ=='energy':
                amt = energy_of(by[(typ,x,y)]) or 0
                if amt:
                    drops.append((x,y,amt))
        rec['drops'] = sum(d[2] for d in drops)
        rec['drops_ctl'] = sum(d[2] for d in drops if abs(d[0]-30)<=2 and abs(d[1]-30)<=2)
        # creeps of interest
        ups = []
        feeders = []
        for typ,x,y in by:
            if typ!='creep': continue
            o = by[(typ,x,y)]
            name = o.get('name') or ''
            e = energy_of(o) or 0
            sp = o.get('spawning') not in (None, False, 0)
            role = ''.join(ch for ch in name if ch.isalpha()) or '?'
            if role == 'upgrader':
                ups.append({'name':name,'x':x,'y':y,'e':e,'sp':sp})
            if role in ('queen','hauler','rhauler'):
                feeders.append({'name':name,'role':role,'x':x,'y':y,'e':e})
        rec['ups'] = ups
        rec['feeders'] = feeders
        rec['nUp_live'] = sum(1 for u in ups if not u['sp'])
        rec['nUp_spawn'] = sum(1 for u in ups if u['sp'])
        rec['up_e'] = sum(u['e'] for u in ups if not u['sp'])
        rec['up_empty'] = sum(1 for u in ups if not u['sp'] and u['e']==0)
        rec['up_on_spot'] = sum(1 for u in ups if not u['sp'] and (u['x'],u['y']) in keys['up_spots'])
        rec['battery'] = (rec['ctl_cont'] or 0) + (rec['ctl_link'] or 0)
        series['_rows'].append(rec)

    rows = series['_rows']
    print(f'W46N8 official ticks {tmin}..{tmax} n={n_ticks} rows={len(rows)}')

    def window(t0, t1):
        return [r for r in rows if t0 <= r['tick'] <= t1]

    def harvest(rows, key_e, key_ttr):
        harvested=waste=n=0
        prev=None
        for r in rows:
            e, ttr = r.get(key_e), r.get(key_ttr)
            if e is None:
                prev=None; continue
            n += 1
            if prev is not None:
                pe = prev
                if e < pe:
                    harvested += pe-e
                elif e > pe + 50:
                    waste += pe
            prev = e
        ticks = (rows[-1]['tick']-rows[0]['tick']+1) if rows else 0
        return harvested, waste, n, ticks

    def mean(xs):
        xs=[x for x in xs if x is not None]
        return sum(xs)/len(xs) if xs else None

    def rate(delta, ticks):
        return delta/ticks if ticks else None

    def summarize(rows, label):
        if not rows:
            return {'label':label,'n':0}
        t0,t1 = rows[0]['tick'], rows[-1]['tick']
        ticks = t1-t0+1
        # coverage holes inside window (missing official ticks)
        present = {r['tick'] for r in rows}
        missing = [t for t in range(t0,t1+1) if t not in present]
        ha, wa, na, _ = harvest(rows,'srcA','srcA_ttr')
        hb, wb, nb, _ = harvest(rows,'srcB','srcB_ttr')
        # storage delta
        s0 = next((r['storage'] for r in rows if r['storage'] is not None), None)
        s1 = next((r['storage'] for r in reversed(rows) if r['storage'] is not None), None)
        # battery
        bat = [r['battery'] for r in rows]
        ctlc = [r['ctl_cont'] for r in rows]
        ctll = [r['ctl_link'] for r in rows]
        # nUp
        nup = Counter(r['nUp_live'] for r in rows)
        empty_frac = sum(r['up_empty'] for r in rows)/max(1,sum(r['nUp_live'] for r in rows))
        # hungry: live upgrader with e<=14 and battery==0
        hungry_ticks = 0
        hung_up = 0
        live_up = 0
        for r in rows:
            bat0 = r['battery']==0
            for u in r['ups']:
                if u['sp']: continue
                live_up += 1
                if u['e']<=14 and bat0:
                    hung_up += 1
            if r['nUp_live'] and r['up_empty']==r['nUp_live'] and bat0:
                hungry_ticks += 1
        # link throughput: srcA_link and hub_link downward drops >=400 with ctl_link rise
        srcA_sent = hub_sent = 0
        prev=None
        for r in rows:
            if prev:
                for k, acc in (('srcA_link','a'),('hub_link','h')):
                    pe, ce = prev[k], r[k]
                    if pe is not None and ce is not None and pe-ce >= 50:
                        if acc=='a': srcA_sent += pe-ce
                        else: hub_sent += pe-ce
            prev=r
        # pipeline inventory averages
        inv = {
            'srcA_cont': mean([r['srcA_cont'] for r in rows]),
            'srcB_cont': mean([r['srcB_cont'] for r in rows]),
            'ctl_cont': mean(ctlc),
            'ctl_link': mean(ctll),
            'hub_link': mean([r['hub_link'] for r in rows]),
            'srcA_link': mean([r['srcA_link'] for r in rows]),
            'storage': mean([r['storage'] for r in rows]),
            'fillerA': mean([r['fillerA'] for r in rows]),
            'up_carry': mean([r['up_e'] for r in rows]),
            'drops': mean([r['drops'] for r in rows]),
            'e_avail': mean([r['e_avail'] for r in rows]),
        }
        return {
            'label': label, 't0': t0, 't1': t1, 'span': ticks, 'samples': len(rows),
            'missing_ticks': len(missing),
            'harvest_A': ha, 'harvest_B': hb,
            'harvest_A_et': ha/ticks if ticks else None,
            'harvest_B_et': hb/ticks if ticks else None,
            'waste_A': wa, 'waste_B': wb,
            'storage0': s0, 'storage1': s1,
            'storage_d_et': ((s1-s0)/ticks) if (s0 is not None and s1 is not None and ticks) else None,
            'bat_mean': mean(bat), 'bat_min': min(bat) if bat else None, 'bat_max': max(bat) if bat else None,
            'ctl_cont_mean': mean(ctlc), 'ctl_cont_min': min(x for x in ctlc if x is not None) if any(x is not None for x in ctlc) else None,
            'ctl_link_mean': mean(ctll), 'ctl_link_min': min(x for x in ctll if x is not None) if any(x is not None for x in ctll) else None,
            'nUp_hist': dict(nup),
            'empty_frac_among_live': empty_frac,
            'hungry_up_frac': hung_up/live_up if live_up else None,
            'all_empty_and_bat0_ticks': hungry_ticks,
            'srcA_link_sent': srcA_sent, 'srcA_link_et': srcA_sent/ticks if ticks else None,
            'hub_link_sent': hub_sent, 'hub_link_et': hub_sent/ticks if ticks else None,
            'inv': inv,
        }

    # windows
    # last ~2h of official: tmax-1600, last 6h all
    windows = {
        'all': summarize(rows, 'all_cached'),
        'last2h': summarize(window(tmax-1600, tmax), 'last2h'),
        'last6hish': summarize(rows, 'all_cached'),
        # 3rd upgrader 84184827 life
        'u84827': summarize(window(84184829, 84185207), 'upgrader84184827_life'),
        # cluster at controller start
        'cluster_1800': summarize(window(84184878, 84184920), '3rd_at_29_31'),
        # 3 live at spots end
        'cluster_1820': summarize(window(84185170, 84185210), '3rd_arrives_31_30'),
        # screenshot send ~18:29, 84185280-84185320
        'shot_1829': summarize(window(84185240, 84185399), 'screenshot_window'),
        # nUp=3 long stretch
        'nup3_18h': summarize(window(84184880, 84185207), 'nUp3_stretch'),
        # nUp=2 healthy after recycle
        'nup2_after': summarize(window(84185210, 84185245), 'nUp2_after_recycle'),
        # 3rd spawn 84185246
        'u85246': summarize(window(84185246, 84185399), 'upgrader84185246_era'),
    }
    report['W46'] = {'tmin': tmin, 'tmax': tmax, 'n': n_ticks, 'windows': windows}

    # detailed tick dump for screenshot + 84827 arrival
    def dump_ticks(t0,t1):
        out=[]
        for r in window(t0,t1):
            out.append({
                't': r['tick'],
                'stor': r['storage'], 'ctl': r['ctl_cont'], 'clink': r['ctl_link'],
                'hub': r['hub_link'], 'alink': r['srcA_link'],
                'aC': r['srcA_cont'], 'bC': r['srcB_cont'],
                'srcA': r['srcA'], 'srcB': r['srcB'],
                'eAv': r['e_avail'], 'drops': r['drops'],
                'nUp': r['nUp_live'], 'nSp': r['nUp_spawn'],
                'up_empty': r['up_empty'], 'up_e': r['up_e'], 'bat': r['battery'],
                'ups': r['ups'],
                'feeders': [f for f in r['feeders'] if abs(f['x']-30)<=8 and abs(f['y']-30)<=8 or f['role']=='queen'],
            })
        return out
    report['W46_ticks_84827_start'] = dump_ticks(84184870, 84184920)
    report['W46_ticks_84827_end'] = dump_ticks(84185170, 84185210)
    report['W46_ticks_shot'] = dump_ticks(84185240, 84185399)

    # ---- W47 ----
    rows47=[]
    tmin47=tmax47=None
    for t, state in reconstruct('W47N8'):
        tmin47 = t if tmin47 is None else min(tmin47, t)
        tmax47 = t if tmax47 is None else max(tmax47, t)
        by = index_by_pos(state, want_types)
        def e_at(typ, xy):
            o = by.get((typ, xy[0], xy[1]))
            return energy_of(o)
        k=W47
        rec={
            'tick':t,
            'srcA': e_at('source', k['srcA']),
            'srcB': e_at('source', k['srcB']),
            'srcA_cont': e_at('container', k['srcA_cont']),
            'srcB_cont': e_at('container', k['srcB_cont']),
            'ctl_cont': e_at('container', k['ctl_cont']),
            'ctl_link': e_at('link', k['ctl_link']),
            'hub_cont': e_at('container', k['hub_cont']),
            'hub_link': e_at('link', k['hub_link']),
            'srcA_link': e_at('link', k['srcA_link']),
            'storage': e_at('storage', k['storage']),
        }
        sa=by.get(('source',)+k['srcA']); sb=by.get(('source',)+k['srcB'])
        rec['srcA_ttr']=sa.get('ticksToRegeneration') if sa else None
        rec['srcB_ttr']=sb.get('ticksToRegeneration') if sb else None
        # storage might be at a slightly different tile; search
        if rec['storage'] is None:
            for typ,x,y in by:
                if typ=='storage':
                    rec['storage']=energy_of(by[(typ,x,y)])
                    rec['stor_xy']=(x,y)
                    break
        ups=[]
        for typ,x,y in by:
            if typ!='creep': continue
            o=by[(typ,x,y)]; name=o.get('name') or ''
            role=''.join(ch for ch in name if ch.isalpha()) or '?'
            if role in ('w8upgrader','upgrader') or name.startswith('w8upgrader') or 'upgrader' in name:
                if name.startswith('w8upgrader') or role=='w8upgrader':
                    ups.append({'name':name,'x':x,'y':y,'e':energy_of(o) or 0,'sp':o.get('spawning') not in (None,False,0)})
        rec['ups']=ups
        rec['nUp_live']=sum(1 for u in ups if not u['sp'])
        rec['nUp_spawn']=sum(1 for u in ups if u['sp'])
        rec['up_empty']=sum(1 for u in ups if not u['sp'] and u['e']==0)
        rec['up_e']=sum(u['e'] for u in ups if not u['sp'])
        rec['battery']=(rec['ctl_cont'] or 0)+(rec['ctl_link'] or 0)
        rows47.append(rec)

    def summarize47(rows, label):
        if not rows: return {'label':label,'n':0}
        t0,t1=rows[0]['tick'],rows[-1]['tick']; ticks=t1-t0+1
        ha,wa,na,_=harvest(rows,'srcA','srcA_ttr')
        hb,wb,nb,_=harvest(rows,'srcB','srcB_ttr')
        s0=next((r['storage'] for r in rows if r['storage'] is not None), None)
        s1=next((r['storage'] for r in reversed(rows) if r['storage'] is not None), None)
        bat=[r['battery'] for r in rows]
        # link sent
        srcA_sent=hub_sent=0; prev=None
        for r in rows:
            if prev:
                for k,acc in (('srcA_link','a'),('hub_link','h')):
                    pe,ce=prev.get(k),r.get(k)
                    if pe is not None and ce is not None and pe-ce>=50:
                        if acc=='a': srcA_sent += pe-ce
                        else: hub_sent += pe-ce
            prev=r
        return {
            'label':label,'t0':t0,'t1':t1,'span':ticks,'samples':len(rows),
            'harvest_A':ha,'harvest_B':hb,
            'harvest_A_et':ha/ticks if ticks else None,
            'harvest_B_et':hb/ticks if ticks else None,
            'waste_A':wa,'waste_B':wb,
            'storage0':s0,'storage1':s1,
            'storage_d_et':((s1-s0)/ticks) if (s0 is not None and s1 is not None and ticks) else None,
            'bat_mean':mean(bat),'bat_min':min(bat) if bat else None,'bat_max':max(bat) if bat else None,
            'ctl_cont_mean':mean([r['ctl_cont'] for r in rows]),
            'ctl_link_mean':mean([r['ctl_link'] for r in rows]),
            'srcA_cont_mean':mean([r['srcA_cont'] for r in rows]),
            'srcB_cont_mean':mean([r['srcB_cont'] for r in rows]),
            'srcA_link_mean':mean([r['srcA_link'] for r in rows]),
            'hub_link_mean':mean([r['hub_link'] for r in rows]),
            'hub_cont_mean':mean([r['hub_cont'] for r in rows]),
            'nUp_hist':dict(Counter(r['nUp_live'] for r in rows)),
            'empty_frac': sum(r['up_empty'] for r in rows)/max(1,sum(r['nUp_live'] for r in rows)),
            'srcA_link_sent':srcA_sent,'srcA_link_et':srcA_sent/ticks if ticks else None,
            'hub_link_sent':hub_sent,'hub_link_et':hub_sent/ticks if ticks else None,
        }
    report['W47']={'tmin':tmin47,'tmax':tmax47,'n':len(rows47),
                   'windows':{
                       'all':summarize47(rows47,'all'),
                       'last2h':summarize47([r for r in rows47 if r['tick']>= (tmax47 or 0)-1600],'last2h'),
                   }}

    # remotes source harvest
    remotes={}
    for room in ('W45N8','W45N7','W47N7'):
        srcs=defaultdict(list)  # (x,y)->[(t,e,ttr)]
        conts=defaultdict(list)
        t0=t1=None; n=0; n404_skip=0
        files=iter_chunks(room)
        state={}
        for f in files:
            j=json.loads(f.read_text())
            ticks={}
            for k,v in (j.get('ticks') or {}).items():
                try: ticks[int(k)]=v
                except: continue
            for t in sorted(ticks):
                if ticks[t] is not None:
                    apply_update(state, ticks[t])
                n+=1
                t0=t if t0 is None else min(t0,t); t1=t if t1 is None else max(t1,t)
                for o in state.values():
                    if not isinstance(o,dict): continue
                    if o.get('type')=='source' and o.get('x') is not None:
                        srcs[(o['x'],o['y'])].append((t,o.get('energy'),o.get('ticksToRegeneration')))
                    if o.get('type')=='container' and o.get('x') is not None:
                        conts[(o['x'],o['y'])].append((t, (o.get('store') or {}).get('energy') or 0))
        def hv(series):
            harvested=waste=0; prev=None
            for t,e,ttr in series:
                if e is None:
                    prev=None; continue
                if prev is not None:
                    if e<prev: harvested += prev-e
                    elif e>prev+50: waste += prev
                prev=e
            return harvested, waste, len(series)
        ticks = (t1-t0+1) if t0 is not None else 0
        remotes[room]={
            't0':t0,'t1':t1,'span':ticks,'samples':n,
            'sources':{f'{x},{y}': {'harvest':hv(s)[0],'waste':hv(s)[1],'n':hv(s)[2],
                                    'et': (hv(s)[0]/ticks if ticks else None)}
                       for (x,y),s in srcs.items()},
            'conts_mean':{f'{x},{y}': (sum(e for _,e in s)/len(s) if s else None) for (x,y),s in conts.items()},
        }
    report['remotes']=remotes

    # print human summary
    def fmt(w):
        if not w or not w.get('span'):
            return str(w)
        return (f"{w['label']} t{w['t0']}..{w['t1']} span={w['span']} n={w['samples']} miss={w.get('missing_ticks')}\n"
                f"  harvest A={w.get('harvest_A_et')} B={w.get('harvest_B_et')} wasteA={w.get('waste_A')} wasteB={w.get('waste_B')}\n"
                f"  stor {w.get('storage0')}->{w.get('storage1')} d={w.get('storage_d_et')}\n"
                f"  bat mean/min/max={w.get('bat_mean')}/{w.get('bat_min')}/{w.get('bat_max')} "
                f"ctl={w.get('ctl_cont_mean')} link={w.get('ctl_link_mean')}\n"
                f"  nUp={w.get('nUp_hist')} empty_frac={w.get('empty_frac_among_live') or w.get('empty_frac')} "
                f"hungry={w.get('hungry_up_frac')} all_empty_bat0={w.get('all_empty_and_bat0_ticks')}\n"
                f"  link sent srcA={w.get('srcA_link_et')} hub={w.get('hub_link_et')}\n"
                f"  inv={w.get('inv')}")
    print('\n===== W46 windows =====')
    for k,w in windows.items():
        print(fmt(w))
        print()
    print('===== W47 windows =====')
    for k,w in report['W47']['windows'].items():
        print(fmt(w)); print()
    print('===== remotes =====')
    print(json.dumps(remotes, indent=2, default=str))

    OUT.write_text(json.dumps(report, indent=2, default=str))
    print('wrote', OUT, 'bytes', OUT.stat().st_size)

if __name__=='__main__':
    main()
