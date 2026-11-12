#!/usr/bin/env python3
"""Génère le projet HyperFrames (index.html + assets) pour la vidéo Arda Güler.
Usage: python3 -I build.py <scratch>"""
import json, math, os, sys, shutil
import numpy as np

S = sys.argv[1]
P = f'{S}/proj'            # frames + words.json
H = f'{S}/guler'           # projet HyperFrames
AN = f'{S}/an'
FPS = 30
OW, OH = 1080, 1920
SRC_FPS = 50

words = json.load(open(f'{P}/words.json'))
VO_DUR = 70.50

def wt(text, sent, nth=0):
    c = [w for w in words if w['sent'] == sent and w['text'].strip('.,!?').lower() == text.lower()]
    return c[nth]['start']

def J(name):
    return {int(k): v for k, v in json.load(open(f'{AN}/{name}.json')).items() if v}

trkB = J('trk_B'); trkA = J('trk_A')
silA = J('sil_A'); silB = J('sil_B')
gkB1 = J('gk_B1'); gkC1 = J('gk_C1'); gkC = J('gk_C'); gkB4 = J('gk_B4')

# ---------------------------------------------------------------- overlays (coords source 1920x1080)
WATERMARK = (1575, 0, 1900, 135)     # toutes les sources
TVBUG = (75, 0, 565, 118)            # clip A uniquement

# ---------------------------------------------------------------- EDL
# map: [(T, srcframe)...] interpolation linéaire, cam: dict, spot: (target, t_on, t_off), label: bool
T = {}
T['s4'] = 9.55; T['s5'] = 13.39; T['s5b'] = wt('et', 4); T['s6'] = 20.21; T['s7'] = 24.37
T['s7b'] = wt('vers', 6); T['s8'] = 30.77; T['s8b'] = wt('convaincu', 7); T['s9'] = 37.99
T['s10'] = 41.65; T['envoie'] = wt('envoie', 9); T['s11'] = 45.53; T['s11b'] = wt('qui', 10)
T['s12'] = 53.05; T['s12b'] = wt('mais', 11); T['s13'] = 60.95; T['s14'] = 64.11; T['s15'] = 67.49

SEG = [
 dict(n='hook-frappe', clip='B', map=[(0, 441), (1.77, 485)], cam=dict(m='follow', tr='headB', dy=330, h=1000, side='left')),
 dict(n='but-haut', clip='B', map=[(1.77, 85), (5.71, 164)], cam=dict(m='static', cx=1030, cy=540, h=1080)),
 dict(n='coup-franc-loin', clip='A', map=[(5.71, 190), (T['s4'], 280)], cam=dict(m='pan', k=[(190, 560, 600, 900), (232, 600, 590, 900), (280, 1290, 470, 900)])),
 dict(n='trois-joueurs', clip='A', map=[(T['s4'], 99), (T['s5'], 150)], cam=dict(m='pan', k=[(99, 1360, 650, 900), (128, 1360, 650, 900), (141, 430, 585, 900), (150, 430, 585, 900)])),
 dict(n='mur', clip='A', map=[(T['s5'], 1), (T['s5b'], 98)], cam=dict(m='pan', k=[(1, 600, 608, 940), (98, 900, 608, 940)])),
 dict(n='gardien-haut', clip='B', map=[(T['s5b'], 1), (T['s6'], 20)], cam=dict(m='static', cx=960, cy=640, h=880), spot=('gkB1', wt('surprendre', 4), T['s6'])),
 dict(n='guler-ensuite', clip='A', map=[(T['s6'], 150), (T['s6'] + 3.0, 186), (T['s7'], 186)], cam=dict(m='follow', tr='headA', dy=470, h=945, side='down'), spot=('silA', wt('arda', 5), T['s7']), freeze_from=186),
 dict(n='main-levee', clip='B', map=[(T['s7'], 320), (T['s7'] + 1.03, 345), (T['s7'] + 2.23, 345), (T['s7b'], 395)], cam=dict(m='follow', tr='headB', dy=280, h=760, side='left'), freeze_from=345),
 dict(n='surface', clip='C', map=[(T['s7b'], 1), (T['s8'], 24)], cam=dict(m='pan', k=[(1, 760, 560, 1000), (24, 1150, 560, 1000)])),
 dict(n='gardien-trompe', clip='B', map=[(T['s8'], 20), (T['s8b'], 45)], cam=dict(m='static', cx=960, cy=700, h=820), spot=('gkB1', wt('trompe', 7), T['s8b'])),
 dict(n='guler-prepare', clip='B', map=[(T['s8b'], 250), (T['s9'], 330)], cam=dict(m='follow', tr='headB', dy=300, h=780, side='left')),
 dict(n='course', clip='B', map=[(T['s9'], 400), (T['s10'], 455)], cam=dict(m='follow', tr='headB', dy=330, h=1080, side='left'), spot=('silB', wt('arda', 8), T['s10']), label=True),
 dict(n='frappe', clip='B', map=[(T['s10'], 455), (T['envoie'], 471), (T['envoie'] + 1.16, 500)], cam=dict(m='follow', tr='headB', dy=330, h=1000, side='left'), label=True),
 dict(n='ballon-mur', clip='B', map=[(T['envoie'] + 1.16, 501), (T['s11'], 560)], cam=dict(m='pan', k=[(501, 1000, 540, 1080), (560, 1000, 540, 1080)])),
 dict(n='trajectoire', clip='C', map=[(T['s11'], 221), (T['s11b'], 321)], cam=dict(m='pan', k=[(221, 900, 540, 1080), (290, 1000, 540, 1080), (321, 1150, 560, 1000)])),
 dict(n='gardien-surpris', clip='B', map=[(T['s11b'], 603), (T['s12'], 626)], cam=dict(m='gk', tr='gkB4', h=900), spot=('gkB4', wt('gardien', 10), None)),
 dict(n='gardien-croit', clip='C', map=[(T['s12'], 50), (T['s12b'], 99)], cam=dict(m='gk', tr='gkC1', h=1000), spot=('gkC1', None, None)),
 dict(n='trop-tard', clip='C', map=[(T['s12b'], 321), (T['s13'], 384)], cam=dict(m='gk', tr='gkC', h=900), spot=('gkC', None, None)),
 dict(n='effort', clip='B', map=[(T['s13'], 626), (T['s14'], 666)], cam=dict(m='gk', tr='gkB4', h=900), spot=('gkB4', None, T['s14'])),
 dict(n='filets', clip='B', map=[(T['s14'], 97), (T['s15'], 151)], cam=dict(m='static', cx=1030, cy=540, h=1080)),
 dict(n='reaction', clip='C', map=[(T['s15'], 170), (T['s15'] + 1.0, 219)], cam=dict(m='static', cx=1000, cy=600, h=960)),
 dict(n='celebration', clip='C', map=[(T['s15'] + 1.0, 471), (VO_DUR, 571)], cam=dict(m='static', cx=1300, cy=600, h=960)),
]
LABEL_END_FRAME = 471          # contact du pied (mesuré image par image, clip B)
KICK_T = None

def tracks(name, k):
    if name == 'headB':
        d = trkB
    elif name == 'headA':
        d = trkA
    else:
        raise KeyError(name)
    ks = sorted(d); k2 = min(max(k, ks[0]), ks[-1])
    return d[k2][0], d[k2][1]

def boxes(name):
    return {'gkB1': gkB1, 'gkC1': gkC1, 'gkC': gkC, 'gkB4': gkB4, 'silA': silA, 'silB': silB}[name]

def box_at(name, k):
    d = boxes(name); ks = sorted(d)
    k2 = min(ks, key=lambda q: abs(q - k))
    return d[k2]

def gk_box_padded(b):
    x0, y0, x1, y1 = b; w, h = x1 - x0, y1 - y0
    return (x0 - 0.12 * w - 14, y0 - 0.28 * h - 14, x1 + 0.12 * w + 14, y1 + 0.10 * h + 10)

# ---------------------------------------------------------------- output frames
NF = int(round(VO_DUR * FPS))
frames = []   # per output frame dict
for i in range(NF):
    t = i / FPS
    seg = None
    for si, sg in enumerate(SEG):
        if sg['map'][0][0] - 1e-9 <= t < sg['map'][-1][0] - 1e-9 or (si == len(SEG) - 1 and t >= sg['map'][0][0]):
            seg = si; break
    sg = SEG[seg]; m = sg['map']
    for a, b in zip(m, m[1:]):
        if a[0] - 1e-9 <= t <= b[0] + 1e-9:
            u = (t - a[0]) / (b[0] - a[0]) if b[0] > a[0] else 0
            kf = a[1] + u * (b[1] - a[1]); break
    k = int(math.floor(kf + 1e-6))
    k = max(min(k, max(p[1] for p in m)), min(p[1] for p in m))
    frames.append(dict(i=i, t=t, seg=seg, clip=sg['clip'], k=k))

# ---------------------------------------------------------------- camera
def gauss_smooth(vals, sigma):
    vals = np.array(vals, float); n = len(vals)
    if n < 3: return vals
    r = int(3 * sigma); xs = np.arange(-r, r + 1); w = np.exp(-xs ** 2 / (2 * sigma ** 2))
    out = np.empty(n)
    for j in range(n):
        idx = np.clip(j + xs, 0, n - 1); out[j] = (vals[idx] * w).sum() / w.sum()
    return out

def interp_keys(keys, k):
    if k <= keys[0][0]: return keys[0][1:]
    for a, b in zip(keys, keys[1:]):
        if a[0] <= k <= b[0]:
            u = (k - a[0]) / (b[0] - a[0]); u = u * u * (3 - 2 * u)
            return tuple(a[j] + u * (b[j] - a[j]) for j in (1, 2, 3))
    return keys[-1][1:]

cam_by_seg = {}
for si, sg in enumerate(SEG):
    ks = sorted(set(p[1] for p in sg['map'])); kr = list(range(min(ks), max(ks) + 1))
    c = sg['cam']; cx, cy, hh = [], [], []
    for k in kr:
        if c['m'] == 'static':
            v = (c['cx'], c['cy'], c['h'])
        elif c['m'] == 'pan':
            v = interp_keys(c['k'], k)
        elif c['m'] == 'follow':
            x, y = tracks(c['tr'], k); v = (x + c.get('dx', 0), y + c['dy'], c['h'])
        elif c['m'] == 'gk':
            b = gk_box_padded(box_at(c['tr'], k)); v = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, c['h'])
        cx.append(v[0]); cy.append(v[1]); hh.append(v[2])
    if c['m'] in ('follow', 'gk'):
        cx = gauss_smooth(cx, 10); cy = gauss_smooth(cy, 10)
    cam_by_seg[si] = {k: (cx[j], cy[j], hh[j]) for j, k in enumerate(kr)}

def rect_hit(r, x0, y0, x1, y1):
    return x0 < r[2] and x1 > r[0] and y0 < r[3] and y1 > r[1]

def constrain(clip, cx, cy, h, side):
    h = min(h, 1080.0); w = h * 9 / 16
    cx = min(max(cx, w / 2), 1920 - w / 2); cy = min(max(cy, h / 2), 1080 - h / 2)
    for _ in range(4):
        x0, y0, x1, y1 = cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
        bad = [r for r in ([WATERMARK] + ([TVBUG] if clip == 'A' else [])) if rect_hit(r, x0, y0, x1, y1)]
        if not bad: break
        r = bad[0]
        if side == 'left' and r is WATERMARK:
            cx = r[0] - w / 2 - 2
        elif side == 'right' and r is TVBUG:
            cx = r[2] + w / 2 + 2
        else:
            need_top = r[3] + 2
            if need_top + h > 1080: h = 1080 - need_top; w = h * 9 / 16
            cy = need_top + h / 2
    return cx, cy, h

# spotlight geometry (source coords) per segment: center per frame (smoothed), constant radius
spot_geo = {}
for si, sg in enumerate(SEG):
    if 'spot' not in sg: continue
    name = sg['spot'][0]; ks = sorted(cam_by_seg[si]); cs, rs = [], []
    for k in ks:
        b = box_at(name, k)
        if name.startswith('gk'): b = gk_box_padded(b)
        else: b = (b[0] - 18, b[1] - 18, b[2] + 18, b[3] + 18)
        cs.append(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)); rs.append(math.hypot(b[2] - b[0], b[3] - b[1]) / 2)
    sx = gauss_smooth([c[0] for c in cs], 2); sy = gauss_smooth([c[1] for c in cs], 2)
    # rayon constant = le plus grand nécessaire, recalculé avec le centre lissé
    R = 0
    for j, k in enumerate(ks):
        b = box_at(name, k)
        if name.startswith('gk'): b = gk_box_padded(b)
        else: b = (b[0] - 18, b[1] - 18, b[2] + 18, b[3] + 18)
        for px, py in ((b[0], b[1]), (b[2], b[1]), (b[0], b[3]), (b[2], b[3])):
            R = max(R, math.hypot(px - sx[j], py - sy[j]))
    spot_geo[si] = ({k: (sx[j], sy[j]) for j, k in enumerate(ks)}, R)

# spotlight timing windows (a single spotlight may span several consecutive segments)
spot_windows = []   # (t_on, t_off, [seg idx])
cur = None
for si, sg in enumerate(SEG):
    if 'spot' in sg:
        on = sg['spot'][1] if sg['spot'][1] is not None else sg['map'][0][0]
        off = sg['spot'][2] if sg['spot'][2] is not None else sg['map'][-1][0]
        if cur and sg['spot'][1] is None:
            cur[1] = off; cur[2].append(si)
        else:
            cur = [on, off, [si]]; spot_windows.append(cur)
        if sg['spot'][2] is not None: cur = None
    else:
        cur = None

def spot_alpha(t):
    for on, off, segs in spot_windows:
        if on - 1e-9 <= t <= off + 1e-9:
            return min(1, (t - on) / 0.25, (off - t) / 0.25), on, off
    return 0, None, None

cut_times = [sg['map'][0][0] for sg in SEG[1:]]

for f in frames:
    si = f['seg']; sg = SEG[si]; c = sg['cam']
    cx, cy, h = cam_by_seg[si][f['k']]
    a, on, off = spot_alpha(f['t']); f['spot'] = 0
    if a > 0 and si in spot_geo:
        (cmap, R) = spot_geo[si]; scx, scy = cmap[f['k']]
        prog = min(1, max(0, (f['t'] - on) / 1.2)); prog = prog * prog * (3 - 2 * prog)
        ease_out = min(1, max(0, (off - f['t']) / 0.25))
        zmax = max(1.0, min(1.22, 520.0 / (R * OH / h)))
        z = 1 + (zmax - 1) * prog * ease_out
        h = h / z; cx = cx + (scx - cx) * 0.6 * prog * ease_out; cy = cy + (scy - cy) * 0.6 * prog * ease_out
        f['spot'] = a; f['spot_src'] = (scx, scy, R)
    # punch +7 % à chaque coupe (retombe en 0,1 s)
    for ct in [0.0] + cut_times:
        if 0 <= f['t'] - ct < 0.1:
            h = h / (1 + 0.07 * (1 - (f['t'] - ct) / 0.1))
    cx, cy, h = constrain(f['clip'], cx, cy, h, c.get('side', 'down'))
    f['cam'] = (cx, cy, h)

# ---------------------------------------------------------------- label (porteur du ballon)
def to_out(f, x, y):
    cx, cy, h = f['cam']; s = OH / h; w = h * 9 / 16
    return (x - (cx - w / 2)) * s, (y - (cy - h / 2)) * s

label_on = []
for f in frames:
    sg = SEG[f['seg']]
    show = sg.get('label', False) and f['clip'] == 'B' and f['k'] < LABEL_END_FRAME and f['k'] in trkB
    if f['seg'] == 0 and f['k'] < LABEL_END_FRAME: show = True   # accroche : course d'élan
    f['label'] = show
    if show:
        hx, hy = trkB[f['k']][:2]; X, Y = to_out(f, hx, hy)
        bounce = 5 * abs(math.sin(2 * math.pi * 1.4 * f['t']))
        f['lab'] = (X, Y + 2 - bounce)       # pointe de la flèche

# ---------------------------------------------------------------- write project
os.makedirs(f'{H}/assets/frames', exist_ok=True)
used = sorted(set((f['clip'], f['k']) for f in frames))
for clip, k in used:
    dst = f'{H}/assets/frames/{clip}{k:04d}.jpg'
    if not os.path.exists(dst):
        os.link(f'{P}/frames/{clip}/{k:04d}.jpg', dst)

# img clips: group consecutive output frames showing the same source image
imgs = []
for f in frames:
    key = (f['clip'], f['k'])
    if imgs and imgs[-1]['key'] == key and imgs[-1]['last'] == f['i'] - 1:
        imgs[-1]['last'] = f['i']
    else:
        imgs.append(dict(key=key, first=f['i'], last=f['i']))

Q = 1 / FPS / 4
def tstart(i): return max(0.0, i / FPS - Q) if i > 0 else 0.0

html = []
A = html.append
A('<!doctype html>\n<html lang="fr" data-resolution="portrait">\n<head>\n<meta charset="UTF-8" />\n<meta name="viewport" content="width=1080, height=1920" />')
A('<script src="assets/gsap.min.js"></script>')
A('''<style>
@font-face{font-family:"Poppins";font-weight:500;src:url(assets/fonts/poppins-500.woff2) format("woff2")}
@font-face{font-family:"Poppins";font-weight:800;src:url(assets/fonts/poppins-800.woff2) format("woff2")}
@font-face{font-family:"Montserrat";font-weight:800;src:url(assets/fonts/montserrat-800.woff2) format("woff2")}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#000}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#000}
#stage{position:absolute;left:0;top:0;width:1920px;height:1080px;transform-origin:0 0}
#stage img.clip{position:absolute;left:0;top:0;width:1920px;height:1080px;display:block}
#spot{position:absolute;inset:0;z-index:5;opacity:0;--sx:540px;--sy:960px;--sr:300px;
 background:rgba(0,0,0,.58);backdrop-filter:blur(5px);-webkit-backdrop-filter:blur(5px);
 -webkit-mask-image:radial-gradient(circle var(--sr) at var(--sx) var(--sy),transparent 99.4%,#000 100%);
 mask-image:radial-gradient(circle var(--sr) at var(--sx) var(--sy),transparent 99.4%,#000 100%)}
#ring{position:absolute;z-index:6;left:0;top:0;width:2px;height:2px;border-radius:50%;opacity:0;
 border:5px solid #fff;box-shadow:0 0 14px rgba(255,255,255,.55),inset 0 0 10px rgba(255,255,255,.25)}
#label{position:absolute;z-index:8;left:0;top:0;width:0;height:0;opacity:0}
#label .inner{position:absolute;left:0;top:0;transform-origin:0 0}
#label .stack{position:absolute;left:-200px;bottom:0;width:400px;display:flex;flex-direction:column;align-items:center;gap:8px}
#label .logo{width:84px;height:84px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;box-shadow:0 3px 8px rgba(0,0,0,.45)}
#label .logo img{width:62px;height:62px;object-fit:contain}
#label .name{font-family:"Montserrat";font-weight:800;font-size:38px;color:#fff;background:rgba(14,14,18,.86);padding:6px 18px 8px;border-radius:14px;white-space:nowrap;box-shadow:0 3px 8px rgba(0,0,0,.4)}
#label svg{display:block;filter:drop-shadow(0 3px 3px rgba(0,0,0,.5))}
.word{position:absolute;z-index:20;left:0;width:1080px;top:1600px;text-align:center;font-family:"Poppins";font-weight:500;font-size:46px;line-height:1.15;color:#fff;text-transform:lowercase;text-shadow:0 2px 4px rgba(0,0,0,.85)}
#score{position:absolute;z-index:15;top:120px;left:50%;transform:translateX(-50%);display:flex;align-items:stretch;height:74px;border-radius:12px;overflow:hidden;box-shadow:0 6px 18px rgba(0,0,0,.5);font-family:"Poppins";font-weight:800;opacity:0}
#score .team{background:#fff;color:#111;font-size:36px;display:flex;align-items:center;gap:10px;padding:0 18px}
#score .team img{width:44px;height:44px;object-fit:contain}
#score .box{background:#e10600;color:#fff;font-size:42px;display:flex;align-items:center;padding:0 16px;min-width:150px;justify-content:center;perspective:300px}
#score .digit{display:inline-block;width:30px;text-align:center}
#score .min{background:#111;color:#fff;font-size:30px;display:flex;align-items:center;padding:0 16px}
</style>\n</head>\n<body>''')
A(f'<div id="root" data-composition-id="main" data-start="0" data-duration="{VO_DUR:.3f}" data-width="1080" data-height="1920">')
A('<div id="stage">')
for n, im in enumerate(imgs):
    clip, k = im['key']; st = tstart(im['first']); en = (im['last'] + 1) / FPS
    if im['last'] == NF - 1: en = VO_DUR
    A(f'<img class="clip" src="assets/frames/{clip}{k:04d}.jpg" data-start="{st:.4f}" data-duration="{en - st:.4f}" alt="" />')
A('</div>')
A('<div id="spot"></div><div id="ring"></div>')
A('''<div id="label"><div class="inner"><div class="stack">
<div class="logo"><img src="assets/tff.svg" alt="" /></div>
<div class="name">Arda Güler</div>
<svg width="64" height="86" viewBox="0 0 64 86"><path d="M20 3 H44 V44 H61 L32 83 L3 44 H20 Z" fill="#ff1f1f" stroke="#3a0000" stroke-width="3" stroke-linejoin="round"/></svg>
</div></div></div>''')
A('''<div id="score"><div class="team"><img src="assets/tff.svg" alt="" />TUR</div><div class="box"><span class="digit" id="d1">0</span><span>–</span><span class="digit">0</span></div><div class="team">BEL<img src="assets/rbfa.svg" alt="" /></div><div class="min">20'</div></div>''')
# sous-titres
for j, w in enumerate(words):
    st = w['start']; en = words[j + 1]['start'] if j + 1 < len(words) else VO_DUR
    if en - st < 0.05: en = st + 0.05
    txt = w['text'].strip('.,!?:;').lower()
    if not txt: continue
    A(f'<div class="word clip" data-start="{st:.3f}" data-duration="{en - st:.3f}">{txt}</div>')

# ---------------------------------------------------------------- audio
sfx = []
def add_sfx(fid, t, vol):
    dur = {166: 0.81, 174: 1.04, 168: 0.88, 3115: 0.60, 1492: 1.38, 3005: 0.21, 2112: 1.46, 2108: 0.97, 2099: 1.59}[fid]
    t = max(0.0, t); dur = min(dur, VO_DUR - t)
    if dur > 0.02: sfx.append((fid, t, dur, round(vol * 0.708, 3)))
cuts = [0.0] + cut_times
alt = [166, 174, 168, 3115]
for j, ct in enumerate(cut_times):
    add_sfx(alt[j % 4], ct - 0.12, 0.22)
# arrêts sur image
for si, sg in enumerate(SEG):
    if 'freeze_from' in sg:
        m = sg['map']
        for a, b in zip(m, m[1:]):
            if a[1] == b[1]: add_sfx(1492, a[0], 0.30)
# frappe : image du contact (clip B 471) — accroche et frappe principale
kick_times = []
for f in frames:
    if f['clip'] == 'B' and f['k'] == LABEL_END_FRAME and (not frames[f['i'] - 1]['k'] == LABEL_END_FRAME or f['i'] == 0):
        kick_times.append(f['t'])
kick_ids = [2112, 2108, 2099]
for j, kt in enumerate(kick_times):
    add_sfx(kick_ids[j % 3], kt, 0.55)
# pop étiquette
lab_starts = [f['t'] for f in frames if f['label'] and (f['i'] == 0 or not frames[f['i'] - 1]['label'])]
for t0 in lab_starts: add_sfx(3005, t0, 0.35)
SCORE_ON = T['s14']; SCORE_FLIP = wt('filets', 13)
add_sfx(3005, SCORE_ON, 0.35)

A(f'<audio id="voice" class="clip" src="assets/voice.wav" data-start="0" data-duration="{VO_DUR:.3f}" data-volume="0.708"></audio>')
for n, (fid, t, dur, vol) in enumerate(sfx):
    A(f'<audio id="sfx{n}" class="clip" src="assets/sfx/{fid}.mp3" data-start="{t:.3f}" data-duration="{dur:.3f}" data-volume="{vol}"></audio>')
A('</div>')

# ---------------------------------------------------------------- GSAP timeline
js = ['const tl=gsap.timeline({paused:true});', 'const st=document.getElementById("stage"),sp=document.getElementById("spot"),rg=document.getElementById("ring"),lb=document.getElementById("label"),li=document.querySelector("#label .inner");']
prev = {}
def setp(el, props, t):
    key = el
    if prev.get(key) == props: return
    prev[key] = props
    js.append(f'tl.set({el},{{{props}}},{t:.4f});')
for f in frames:
    t = max(0.0, f['t'] - Q) if f['i'] else 0.0
    cx, cy, h = f['cam']; s = OH / h; w = h * 9 / 16
    setp('st', f'x:{-(cx - w / 2) * s:.2f},y:{-(cy - h / 2) * s:.2f},scale:{s:.5f}', t)
    if f['spot'] > 0:
        scx, scy, R = f['spot_src']; X, Y = to_out(f, scx, scy); r = R * s
        setp('sp', f'opacity:{f["spot"]:.3f},"--sx":"{X:.1f}px","--sy":"{Y:.1f}px","--sr":"{r:.1f}px"', t)
        setp('rg', f'opacity:{f["spot"]:.3f},x:{X - r - 2.5:.1f},y:{Y - r - 2.5:.1f},width:{2 * r + 5:.1f},height:{2 * r + 5:.1f}', t)
    else:
        setp('sp', 'opacity:0', t); setp('rg', 'opacity:0', t)
    if f['label']:
        X, Y = f['lab']
        # pop 0,12 s
        t0 = max(s0 for s0 in lab_starts if s0 <= f['t'] + 1e-9)
        sc = min(1.0, (f['t'] - t0) / 0.12 + 0.35)
        setp('lb', f'opacity:1,x:{X:.1f},y:{Y:.1f}', t)
        setp('li', f'scale:{sc:.3f}', t)
    else:
        setp('lb', 'opacity:0', t)
js.append(f'tl.set("#score",{{opacity:0,scale:0.4}},0);')
js.append(f'tl.to("#score",{{opacity:1,scale:1,duration:0.12,ease:"back.out(2)"}},{SCORE_ON:.3f});')
js.append(f'tl.to("#d1",{{rotationX:90,duration:0.12,ease:"power1.in"}},{SCORE_FLIP:.3f});')
js.append(f'tl.call(()=>{{}},[],{SCORE_FLIP + 0.12:.3f});')
js.append(f'tl.set("#d1",{{textContent:"1"}},{SCORE_FLIP + 0.12:.3f});')
js.append(f'tl.to("#d1",{{rotationX:0,duration:0.14,ease:"power1.out"}},{SCORE_FLIP + 0.12:.3f});')
js.append('window.__timelines=window.__timelines||{};window.__timelines["main"]=tl;tl.seek(0);')
A('<script>\n' + '\n'.join(js) + '\n</script>')
A('</body>\n</html>')
open(f'{H}/index.html', 'w').write('\n'.join(html))

# dump plan for verification
plan = [dict(i=f['i'], t=round(f['t'], 4), clip=f['clip'], k=f['k'], seg=SEG[f['seg']]['n'], cam=[round(v, 2) for v in f['cam']],
             label=f.get('lab') if f['label'] else None, spot=(list(to_out(f, *f['spot_src'][:2])) + [f['spot_src'][2] * OH / f['cam'][2]]) if f['spot'] > 0 else None,
             spot_a=f['spot']) for f in frames]
json.dump(dict(frames=plan, segs=[dict(n=s['n'], t0=s['map'][0][0], t1=s['map'][-1][0]) for s in SEG], sfx=sfx, kick=kick_times,
               score=(SCORE_ON, SCORE_FLIP), spots=[(a, b) for a, b, _ in spot_windows]), open(f'{S}/an/plan.json', 'w'))
print('frames', NF, 'imgs', len(imgs), 'sfx', len(sfx), 'kick', kick_times, 'spots', [(round(a, 2), round(b, 2)) for a, b, _ in spot_windows])
for si, sg in enumerate(SEG):
    print(f"{si:2d} {sg['n']:16s} {sg['map'][0][0]:6.2f}-{sg['map'][-1][0]:6.2f} {sg['clip']} {sg['map'][0][1]}-{sg['map'][-1][1]}")
