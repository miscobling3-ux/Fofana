#!/usr/bin/env python3
"""Build data + index.html for the HyperFrames goal-analysis composition (analysis/data only)."""
import json, math, os, shutil, re
import numpy as np

SC = '/tmp/claude-0/-home-user-Fofana/663162a9-9ff1-508a-a745-47f437945801/scratchpad'
P = f'{SC}/hfgoal'
FPS = 30
SRC_FPS = 60
VOICE_DUR = 66.272653
NOUT = int(math.floor(VOICE_DUR * FPS))  # 1988 frames
DUR = NOUT / FPS

# ---------------- overlays (source px, with margin) ----------------
OVERLAYS = [
    (84, 30, 318, 180),     # TV score bug
    (1598, 44, 1834, 120),  # LIVE bar
    (1724, 864, 1856, 968), # green box
    (752, 880, 1096, 936),  # watermark url
    (1562, 992, 1860, 1044) # hashtag
]

# ---------------- tracks ----------------
def ld(name):
    d = json.load(open(f'{SC}/ann/trk_{name}.json'))
    return {int(k): tuple(v) for k, v in d.items()}

def smooth_track(tr, sigma=1.5):
    ks = sorted(tr)
    xs = np.array([tr[k][0] for k in ks]); ys = np.array([tr[k][1] for k in ks])
    # median filter 5 then gaussian
    def med(a):
        b = a.copy()
        for i in range(len(a)):
            b[i] = np.median(a[max(0, i-2):i+3])
        return b
    xs, ys = med(xs), med(ys)
    r = int(3*sigma); w = np.exp(-0.5*(np.arange(-r, r+1)/sigma)**2); w /= w.sum()
    def g(a):
        pad = np.pad(a, r, mode='edge'); return np.convolve(pad, w, 'valid')
    xs, ys = g(xs), g(ys)
    return {k: (float(x), float(y)) for k, x, y in zip(ks, xs, ys)}

def keys_track(keys):
    ks = sorted(keys)
    out = {}
    for a, b in zip(ks[:-1], ks[1:]):
        for f in range(a, b+1):
            u = (f-a)/(b-a)
            out[f] = (keys[a][0]*(1-u)+keys[b][0]*u, keys[a][1]*(1-u)+keys[b][1]*u)
    return out

DIO1 = smooth_track(ld('dio1'))
MBA = smooth_track(ld('mba'))
DIO2 = smooth_track(ld('dio2'))
BEL1 = smooth_track(ld('bel1'))
BEL_LO = keys_track({520: (1098, 385), 528: (1095, 392), 536: (1110, 397), 544: (1110, 392), 552: (1135, 382),
                     560: (1150, 372), 568: (1160, 377), 576: (1190, 377), 584: (1225, 337), 592: (1215, 347),
                     600: (1285, 337), 604: (1300, 342)})
BEL_CU = keys_track({879: (1200, 292), 894: (1162, 245), 909: (1088, 253), 924: (1064, 268), 939: (1061, 286),
                     954: (938, 241), 969: (921, 271), 984: (867, 248), 999: (871, 244), 1014: (908, 297),
                     1029: (951, 320), 1044: (1033, 335), 1059: (1114, 345), 1074: (1211, 353), 1085: (1217, 361)})
GUL = keys_track({712: (116, 516), 716: (156, 512), 720: (200, 504), 724: (240, 500),
                  728: (284, 498), 731: (324, 496)})

import sys
sys.path.insert(0, SC)
from track import head_sil
GUL = smooth_track({f: head_sil('B', f, x, y, 280, maxshift=25) for f, (x, y) in GUL.items()}, sigma=1.0)

# carriers in clip B: list of (f_from, f_to_inclusive_last_frame_shown, name, track, ph)
# the label disappears at the exact frame of the pass/shot (f_to is the contact frame -> hidden from it)
CARRIERS_B = [
    (0, 40, 'Yan Diomande', DIO1, 32),
    (41, 69, 'Kylian Mbappé', MBA, 34),
    (70, 93, 'Yan Diomande', DIO2, 34),
    (94, 340, 'Jude Bellingham', BEL1, 36),
    (520, 600, 'Jude Bellingham', BEL_LO, 320),
    (879, 1085, 'Jude Bellingham', BEL_CU, 620),
    (712, 729, 'Arda Güler', GUL, 280),
]

def carrier_at(clip, f):
    if clip != 'B':
        return None
    for a, b, name, tr, ph in CARRIERS_B:
        if a <= f < b and f in tr:
            return name, tr[f], ph
    return None

# ---------------- EDL ----------------
# (out_t0, out_t1, clip, f_in, f_out or None(freeze), camkeys {f:(cx,cy)}, h, kind)
def lin(*pairs):
    return {f: xy for f, xy in pairs}

def head_keys(tr, f0, f1, dy, step=1):
    return {f: (tr[f][0], tr[f][1] + dy) for f in range(f0, f1+1, step) if f in tr}

SHOTS = []
def shot(t0, t1, clip, fin, fout, cam, h, cut=True):
    SHOTS.append(dict(t0=t0, t1=t1, clip=clip, fin=fin, fout=fout, cam=cam, h=h, cut=cut))

# 1 hook: Güler shot (low angle)
shot(0.00, 3.40, 'B', 690, 779, lin((690, (250, 560)), (729, (330, 560)), (745, (620, 560)), (760, (1080, 540)), (779, (1230, 540))), 680)
# 2 context: live wide
shot(3.40, 6.64, 'A', 0, 194, lin((0, (880, 560)), (60, (700, 530)), (120, (760, 560)), (194, (600, 500))), 704)
# 3 Diomande has the ball
hk = head_keys(DIO1, 0, 40, 40)
shot(6.64, 7.84, 'B', 0, 18, hk, 600)
shot(7.84, 8.86, 'B', 18, None, hk, 600, cut=False)
# 4 recorte / pass
shot(8.86, 9.86, 'B', 18, 33, hk, 600, cut=False)
shot(9.86, 10.46, 'B', 33, None, hk, 600, cut=False)
cam4 = dict(head_keys(DIO1, 33, 40, 40)); cam4.update({52: (760, 560)}); cam4.update(head_keys(MBA, 62, 69, 40))
shot(10.46, 12.64, 'B', 33, 65, cam4, 600, cut=False)
# 5 Mbappe back to goal (freeze)
shot(12.64, 15.56, 'B', 65, None, cam4, 600, cut=False)
# 6 return + pass to Bellingham
cam6 = dict(head_keys(MBA, 65, 69, 40)); cam6.update(head_keys(DIO2, 85, 95, 40)); cam6.update({125: (560, 610)}); cam6.update(head_keys(BEL1, 150, 162, 40))
shot(15.56, 20.78, 'B', 65, 162, cam6, 640, cut=False)
# 7 Bellingham controls, faces defender
shot(20.78, 24.54, 'B', 162, 240, head_keys(BEL1, 162, 240, 50), 640, cut=False)
# 8-9 close-up dribble
cu = {f: (BEL_CU[f][0], BEL_CU[f][1]) for f in range(879, 1086)}
shot(24.54, 28.76, 'B', 879, 1005, cu, 760)
shot(28.76, 33.34, 'B', 1005, 1074, cu, 760, cut=False)
# 10 second defender (high cam)
shot(33.34, 37.94, 'B', 240, 324, head_keys(BEL1, 240, 340, 60), 704)
# 11 freeze wide: Diomande free
cam11 = lin((324, (560, 520)), (336, (600, 520)))
shot(37.94, 38.74, 'B', 324, 336, cam11, 704)
shot(38.74, 41.60, 'B', 336, None, cam11, 704, cut=False)
# 12 low angle: Bellingham crosses
lo = {f: (BEL_LO[f][0] - 40, BEL_LO[f][1] + 240) for f in range(520, 605)}
lo.update({606: (1150, 580), 612: (950, 610), 616: (860, 610)})
shot(41.60, 43.60, 'B', 520, 556, lo, 704)
shot(43.60, 44.20, 'B', 556, None, lo, 704, cut=False)
shot(44.20, 46.10, 'B', 556, 600, lo, 704, cut=False)
shot(46.10, 47.30, 'B', 600, None, lo, 704, cut=False)
shot(47.30, 48.36, 'B', 600, 616, lo, 704, cut=False)
# 13 deflection, ball across the line, reaches Güler
cam13 = lin((616, (860, 610)), (628, (730, 560)), (640, (670, 500)), (664, (630, 470)), (688, (630, 480)), (700, (600, 520)), (712, (380, 580)), (726, (300, 640)))
shot(48.36, 52.53, 'B', 616, 700, cam13, 860, cut=False)
shot(52.53, 54.26, 'B', 700, 726, cam13, 860, cut=False)
shot(54.26, 56.32, 'B', 726, None, cam13, 860, cut=False)
# 14 the shot
cam14 = lin((726, (300, 640)), (729, (330, 580)), (746, (640, 560)), (762, (1080, 540)), (779, (1230, 540)))
shot(56.32, 57.62, 'B', 726, 746, cam14, 860, cut=False)
shot(57.62, 59.20, 'B', 746, 779, cam14, 860, cut=False)
# 15 other angle
shot(59.20, 63.10, 'B', 1158, 1314, lin((1158, (980, 560)), (1220, (880, 540)), (1314, (760, 500))), 760)
# 16 celebration
shot(63.10, DUR, 'A', 564, 754, lin((564, (930, 440)), (610, (960, 440)), (650, (860, 440)), (690, (1000, 440)), (730, (900, 440)), (754, (860, 440))), 880)

# Spotlights: (t0, t1, track, ph, rscale, name)
SPOTS = [
    (6.64, 8.86, DIO1, 32, 0.95, 0.5, True, 0),
    (12.64, 15.56, MBA, 34, 0.95, 0.5, True, 0),
    (20.78, 22.90, BEL1, 36, 1.75, 0.62, True, 0.15),
]

# ---------------- helpers ----------------
def interp_keys(keys, f):
    ks = sorted(keys)
    if f <= ks[0]: return keys[ks[0]]
    if f >= ks[-1]: return keys[ks[-1]]
    import bisect
    i = bisect.bisect_right(ks, f)
    a, b = ks[i-1], ks[i]
    u = (f-a)/(b-a)
    return (keys[a][0]*(1-u)+keys[b][0]*u, keys[a][1]*(1-u)+keys[b][1]*u)

def window_ok(x0, y0, x1, y1):
    for ax0, ay0, ax1, ay1 in OVERLAYS:
        if x0 < ax1 and x1 > ax0 and y0 < ay1 and y1 > ay0:
            return False
    return 0 <= x0 and x1 <= 1920 and 0 <= y0 and y1 <= 1080

def solve_window(cx, cy, h):
    """Return a crop window (x0,y0,h) near (cx,cy) avoiding overlays; shrink h if needed."""
    hh = h
    while hh >= 300:
        w = hh*9/16
        best = None
        for dy in sorted(range(-400, 401, 4), key=abs):
            for dx in (0, 8, -8, 16, -16, 32, -32, 64, -64):
                x0 = min(max(cx - w/2 + dx, 0), 1920 - w); y0 = min(max(cy - hh/2 + dy, 0), 1080 - hh)
                if window_ok(x0, y0, x0+w, y0+hh):
                    best = (x0, y0, hh); break
            if best: break
        if best: return best
        hh -= 8
    raise RuntimeError('no window')

# ---------------- per output frame ----------------
frames = []
for k in range(NOUT):
    t = k / FPS + 1e-6
    sh = next(s for s in SHOTS if s['t0'] <= t < s['t1'] + 1e-9)
    if sh['fout'] is None:
        fs = float(sh['fin'])
    else:
        speed = (sh['fout'] - sh['fin']) / (SRC_FPS * (sh['t1'] - sh['t0']))
        fs = sh['fin'] + (t - sh['t0']) * SRC_FPS * speed
    f = int(round(fs))
    if sh['fout'] is not None:
        f = min(f, sh['fout'])
    cx, cy = interp_keys(sh['cam'], fs)
    frames.append(dict(k=k, t=t, shot=SHOTS.index(sh), clip=sh['clip'], f=f, cx=cx, cy=cy, h=sh['h']))

# gaussian smoothing of camera centre within each continuous camera run (sigma = 10 frames), fixed during freezes
def gauss_smooth(vals, sigma=10):
    r = int(3*sigma); w = np.exp(-0.5*(np.arange(-r, r+1)/sigma)**2); w /= w.sum()
    pad = np.pad(np.array(vals, float), r, mode='edge'); return np.convolve(pad, w, 'valid')

runs = []
for i, s in enumerate(SHOTS):
    if s['cut'] or not runs: runs.append([i])
    else: runs[-1].append(i)
for run in runs:
    idx = [fr['k'] for fr in frames if fr['shot'] in run]
    xs = gauss_smooth([frames[i]['cx'] for i in idx]); ys = gauss_smooth([frames[i]['cy'] for i in idx])
    for j, i in enumerate(idx):
        sh = SHOTS[frames[i]['shot']]
        frames[i]['cx'], frames[i]['cy'] = float(xs[j]), float(ys[j])
    # freezes: hold camera of first frame of the freeze
    for i in idx:
        sh = SHOTS[frames[i]['shot']]
        if sh['fout'] is None:
            first = next(fr for fr in frames if fr['shot'] == frames[i]['shot'])
            frames[i]['cx'], frames[i]['cy'] = first['cx'], first['cy']

# spotlights: zoom +22% toward player, circle around full body
for fr in frames:
    fr['spot'] = None
    fr['zoom'] = 1.0
    for (t0, t1, tr, ph, rs, cyf, zm, dxf) in SPOTS:
        if t0 <= fr['t'] < t1:
            f = fr['f']
            hx, hy = tr.get(f, tr[min(tr, key=lambda q: abs(q - f))])
            # body extent: head top -> feet ~ ph ; circle centred on body middle; radius covers body + ball + margin
            scx, scy = hx + ph*dxf, hy + ph*cyf
            r = ph*rs
            u = (fr['t'] - t0)
            a_in = min(1, u/0.25); a_out = min(1, (t1 - fr['t'])/0.25)
            alpha = max(0, min(a_in, a_out))
            p = min(1, u/1.0); p = p*p*(3-2*p)
            fr['spot'] = dict(x=scx, y=scy, r=r, a=alpha)
            if not zm: p = 0
            fr['zoom'] = 1 + 0.22*p*alpha
            # move camera toward player proportional to zoom
            fr['cx'] = fr['cx']*(1-0.6*p*alpha) + scx*0.6*p*alpha
            fr['cy'] = fr['cy']*(1-0.6*p*alpha) + scy*0.6*p*alpha

# cut punch: +7% at each cut, falls back in 0.1 s
cut_times = [s['t0'] for s in SHOTS if s['cut'] and s['t0'] > 0]
for fr in frames:
    for ct in cut_times:
        if 0 <= fr['t'] - ct < 0.1:
            fr['zoom'] *= 1 + 0.07*(1 - (fr['t'] - ct)/0.1)

# final windows
for fr in frames:
    h = fr['h'] / fr['zoom']
    x0, y0, hh = solve_window(fr['cx'], fr['cy'], h)
    if fr['spot']:
        # keep circle fully inside frame: shift window if needed
        s = fr['spot']; w = hh*9/16
        x0 = min(max(x0, s['x'] + s['r'] + 6 - w), s['x'] - s['r'] - 6) if 2*s['r'] + 12 < w else x0
        y0 = min(max(y0, s['y'] + s['r'] + 6 - hh), s['y'] - s['r'] - 6) if 2*s['r'] + 12 < hh else y0
        if not window_ok(x0, y0, x0 + w, y0 + hh):
            x0, y0, hh = solve_window(x0 + w/2, y0 + hh/2, hh)
    fr['x0'], fr['y0'], fr['ch'] = x0, y0, hh
    fr['scale'] = 1920.0 / hh

# labels
for fr in frames:
    c = carrier_at(fr['clip'], fr['f'])
    fr['tag'] = None
    if c:
        name, (hx, hy), ph = c
        ox = (hx - fr['x0'])*fr['scale']; oy = (hy - fr['y0'])*fr['scale']
        if 30 < ox < 1050 and 260 < oy < 1900:
            fr['tag'] = dict(n=name, x=round(ox, 1), y=round(oy, 1))

# automatic head-top refinement on the source frame (non-grass pixels under the estimate)
from track import img as _img, grass as _grass
def measure_head(clip, f, hx, hy, sc):
    im = _img(clip, f)
    y0 = int(hy - 30/sc); y1 = int(hy + 60/sc)
    bw = max(2, int(round(6/sc)))
    win = im[max(0, int(hy-40/sc)):int(hy+120/sc), max(0, int(hx-40/sc)):int(hx+40/sc)+1]
    if win.size == 0 or _grass(win).mean() <= 0.35: return None
    band = im[max(0, y0):y1, max(0, int(hx)-bw):int(hx)+bw+1]
    rows = (~_grass(band)).mean(1) > 0.35
    for i in range(len(rows)-2):
        if rows[i] and rows[i+1] and rows[i+2]:
            ty = max(0, y0) + i
            # horizontal centre of the head: non-grass columns in the 4 src px below the top, within +-14 output px
            wx = max(2, int(round(14/sc)))
            strip = im[ty:ty+max(3, int(round(10/sc))), max(0, int(hx)-wx):int(hx)+wx+1]
            cols = np.nonzero((~_grass(strip)).mean(0) > 0.3)[0]
            nx = hx if len(cols) == 0 else max(0, int(hx)-wx) + cols.mean()
            return ty, nx
    return None
runs_t = []
for fr in frames:
    if fr['tag']:
        sc = fr['scale']
        hx = fr['x0'] + fr['tag']['x']/sc; hy = fr['y0'] + fr['tag']['y']/sc
        m = measure_head(fr['clip'], fr['f'], hx, hy, sc)
        fr['tag']['corr'] = None if m is None else (m[0] - hy)*sc
        fr['tag']['corrx'] = None if m is None else (m[1] - hx)*sc
        if runs_t and runs_t[-1][-1]['k'] == fr['k']-1 and runs_t[-1][-1]['tag']['n'] == fr['tag']['n']:
            runs_t[-1].append(fr)
        else:
            runs_t.append([fr])
for run in runs_t:
    c = np.array([np.nan if r['tag']['corr'] is None else r['tag']['corr'] for r in run], float)
    if np.all(np.isnan(c)): continue
    idx = np.arange(len(c)); good = ~np.isnan(c)
    c = np.interp(idx, idx[good], c[good])
    cm = c.copy()
    for i in range(len(c)): cm[i] = np.median(c[max(0, i-2):i+3])
    cx_ = np.array([np.nan if r['tag']['corrx'] is None else r['tag']['corrx'] for r in run], float)
    cx_ = np.interp(idx, idx[~np.isnan(cx_)], cx_[~np.isnan(cx_)]) if (~np.isnan(cx_)).any() else np.zeros(len(run))
    cxm = cx_.copy()
    for i in range(len(cx_)): cxm[i] = np.median(cx_[max(0, i-2):i+3])
    for r, d, dx in zip(run, cm, cxm):
        r['tag']['y'] = round(r['tag']['y'] + float(d), 1)
        r['tag']['x'] = round(r['tag']['x'] + float(np.clip(dx, -20, 20)), 1)

# closed-loop fixes measured on the previous render (frame k -> shift in output px)
_fix = json.load(open(f'{SC}/tag_fix.json')) if os.path.exists(f'{SC}/tag_fix.json') else {}
for fr in frames:
    if fr['tag'] and str(fr['k']) in _fix:
        fr['tag']['y'] = round(fr['tag']['y'] + _fix[str(fr['k'])], 1)

# label start (pop) times
prev = None; pops = []
for fr in frames:
    n = fr['tag']['n'] if fr['tag'] else None
    if n and n != prev:
        pops.append(fr['t'])
        fr['tag']['pop'] = 1
    if fr['tag']:
        # time since this label appeared
        fr['tag']['since'] = round(fr['t'] - pops[-1], 3)
    prev = n

# ---------------- images (clips) ----------------
fdir = f'{P}/assets/frames'
os.makedirs(fdir, exist_ok=True)
import glob
def srcpath(clip, f):
    for d in sorted(glob.glob(f'{SC}/frames/{clip}_*')):
        p = f'{d}/f{f:05d}.jpg'
        if os.path.exists(p): return p
    raise FileNotFoundError((clip, f))
segs = []
for fr in frames:
    key = (fr['clip'], fr['f'])
    if segs and segs[-1]['key'] == key and segs[-1]['k1'] == fr['k']:
        segs[-1]['k1'] = fr['k'] + 1
    else:
        segs.append(dict(key=key, k0=fr['k'], k1=fr['k'] + 1))
used = set(s['key'] for s in segs)
for clip, f in used:
    dst = f'{fdir}/{clip}{f:05d}.jpg'
    if not os.path.exists(dst): shutil.copy(srcpath(clip, f), dst)
for fn in os.listdir(fdir):
    m = re.match(r'([AB])(\d{5})\.jpg', fn)
    if m and (m.group(1), int(m.group(2))) not in used: os.remove(f'{fdir}/{fn}')

# ---------------- words / subtitles ----------------
words = json.load(open(f'{SC}/work/transcript_words.json'))
fix = {'Moriño': 'Mourinho', 'Guler': 'Güler', 'Guler.': 'Güler.'}
subs = []
for i, w in enumerate(words):
    txt = fix.get(w['text'], w['text'])
    txt = re.sub(r'[¿?¡!.,;:]', '', txt).lower()
    nxt = words[i+1]['start'] if i+1 < len(words) else w['end'] + 0.4
    subs.append(dict(s=w['start'], e=min(nxt, w['end'] + 0.35), w=txt))
json.dump([dict(text=fix.get(w['text'], w['text']), start=w['start'], end=w['end']) for w in words],
          open(f'{P}/words.json', 'w'), ensure_ascii=False, indent=0)

# ---------------- sfx events ----------------
def out_time_of(clip, f, shots_idx=None):
    """first output time where source frame f of clip appears (moving shots only)."""
    for s in SHOTS:
        if s['clip'] == clip and s['fout'] is not None and s['fin'] <= f <= s['fout']:
            speed = (s['fout'] - s['fin'])/(SRC_FPS*(s['t1'] - s['t0']))
            return s['t0'] + (f - s['fin'])/(SRC_FPS*speed)
    return None
sfx = []
whoosh = ['w1', 'w2', 'w3', 'w4']
for i, ct in enumerate(cut_times):
    sfx.append((max(0, ct - 0.12), whoosh[i % 4]))
for s in SHOTS:
    if s['fout'] is None:
        sfx.append((s['t0'], 'freeze'))
for pt in pops:
    sfx.append((pt, 'pop'))
sfx.append((3.50, 'pop'))
for s in SHOTS:  # kicks on contact frames shown in moving shots
    for cf in (40, 69, 93, 600, 729):
        if s['clip'] == 'B' and s['fout'] is not None and s['fin'] <= cf < s['fout']:
            speed = (s['fout'] - s['fin'])/(SRC_FPS*(s['t1'] - s['t0']))
            sfx.append((s['t0'] + (cf - s['fin'])/(SRC_FPS*speed), 'kick' if cf != 729 else 'shot'))
sfx.sort()
# dedupe pops too close
clean = []
for t, n in sfx:
    if clean and n == clean[-1][1] and t - clean[-1][0] < 0.2: continue
    clean.append((round(t, 3), n))
sfx = clean

data = dict(fps=FPS, n=NOUT, dur=DUR,
            fr=[[round(f['x0'], 2), round(f['y0'], 2), round(f['scale'], 5),
                 (None if not f['spot'] else [round((f['spot']['x'] - f['x0'])*f['scale'], 1), round((f['spot']['y'] - f['y0'])*f['scale'], 1), round(f['spot']['r']*f['scale'], 1), round(f['spot']['a'], 3)]),
                 (None if not f['tag'] else [f['tag']['n'], f['tag']['x'], f['tag']['y'], f['tag']['since']])] for f in frames],
            subs=subs, banner=dict(t=3.50, flip=61.74))
json.dump(data, open(f'{SC}/data_debug.json', 'w'))
json.dump(dict(shots=SHOTS, sfx=sfx, cut_times=cut_times), open(f'{SC}/edl_debug.json', 'w'), default=str)
json.dump([dict(k=f['k'], clip=f['clip'], f=f['f'], x0=f['x0'], y0=f['y0'], ch=f['ch'], tag=f['tag'], spot=f['spot']) for f in frames], open(f'{SC}/frames_debug.json', 'w'))

# ---------------- HTML ----------------
imgs = []
for i, s in enumerate(segs):
    clip, f = s['key']
    st = s['k0']/FPS - 1/(4*FPS)
    st = max(0.0, st)
    du = (s['k1'] - s['k0'])/FPS
    imgs.append(f'<img id="i{i}" class="clip src" src="assets/frames/{clip}{f:05d}.jpg" data-start="{st:.5f}" data-duration="{du:.5f}" data-track-index="1" alt="">')

aud = [f'<audio id="voice" src="assets/voice.wav" data-start="0" data-duration="{DUR:.3f}" data-volume="0.96" data-track-index="10"></audio>']
SFXLEN = dict(w1=0.42, w2=0.42, w3=0.42, w4=0.42, freeze=0.7, pop=0.16, kick=0.25, shot=0.45)
SFXVOL = dict(w1=0.26, w2=0.26, w3=0.26, w4=0.26, freeze=0.34, pop=0.24, kick=0.36, shot=0.45)
for i, (t, n) in enumerate(sfx):
    d = min(SFXLEN[n], DUR - t)
    if d <= 0.02: continue
    aud.append(f'<audio id="sfx{i}" src="assets/sfx/{n}.wav" data-start="{t:.3f}" data-duration="{d:.3f}" data-volume="{SFXVOL[n]}" data-track-index="{11 + i % 6}"></audio>')

html = open(f'{SC}/template.html').read()
html = html.replace('%%DUR%%', f'{DUR:.4f}').replace('%%IMGS%%', '\n'.join(imgs)).replace('%%AUDIO%%', '\n'.join(aud))
html = html.replace('%%DATA%%', json.dumps(data, ensure_ascii=False, separators=(',', ':')))
open(f'{P}/index.html', 'w').write(html)
print('frames', NOUT, 'dur', DUR, 'imgs', len(segs), 'unique', len(used), 'sfx', len(sfx), 'pops', len(pops))
