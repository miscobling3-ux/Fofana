#!/usr/bin/env python3
"""Generates the HyperFrames composition (index.html) for the Fermín López goal video.
Python only computes the edit decision list / camera / overlay positions; the video itself
is composed and rendered by HyperFrames."""
import json, math, os, shutil, sys
import numpy as np

W = os.path.dirname(os.path.abspath(__file__)) + '/work'
P = os.path.dirname(os.path.abspath(__file__)) + '/fermin'
FPS = 30
SRC_FPS = 50
words = json.load(open(f'{W}/words.json'))
ball = json.load(open(f'{W}/ball.json'))
T = 89.12  # voice duration

CW, CH = 403.0, 716.0   # base 9:16 crop in source pixels
S_BASE = 1080.0 / CW

# ---------------------------------------------------------------- EDL
# clip, v0, v1, s0, s1, top, cam keyframes [(src_t, cx)] or 'ball'
GOALCAM=[(10.6,650),(10.9,900),(11.2,900),(11.5,1550),(11.8,1450),(12.1,1450),(12.4,1445),(12.7,1365),(13.0,1377),(13.2,1380)]
EDL = [
 dict(id='hook',  clip='B', v0=0.00,  v1=4.25,  s0=8.95,  s1=10.65, top=172, cam=[(8.95,330),(9.5,300),(9.75,420),(9.95,600),(10.65,650)]),
 dict(id='goal1', clip='B', v0=4.25,  v1=7.20,  s0=10.65, s1=13.20, top=172, cam=GOALCAM),
 dict(id='build', clip='A', v0=7.20,  v1=10.70, s0=0.00,  s1=3.50,  top=110, cam=[(0,600),(0.7,760),(1.4,720),(2.1,900),(2.8,780),(3.5,700)]),
 dict(id='high1', clip='B', v0=10.70, v1=16.70, s0=0.50,  s1=3.50,  top=110, cam=[(0.5,930),(1,900),(2,900),(3,1000),(3.5,1030)]),
 dict(id='frz1',  clip='B', v0=16.70, v1=18.00, s0=3.50,  s1=3.50,  top=110, cam=[(3.5,1030)], freeze=True),
 dict(id='high2', clip='B', v0=18.00, v1=23.60, s0=3.50,  s1=5.00,  top=110, cam=[(3.5,1030),(4,1050),(5,1100)]),
 dict(id='wide2', clip='A', v0=23.60, v1=29.90, s0=1.50,  s1=3.10,  top=110, cam=[(1.5,720),(2.1,900),(2.8,780),(3.1,740)]),
 dict(id='frz2',  clip='B', v0=29.90, v1=31.40, s0=5.00,  s1=5.00,  top=110, cam=[(5.0,1100)], freeze=True),
 dict(id='high3', clip='B', v0=31.40, v1=37.90, s0=5.00,  s1=6.25,  top=110, cam=[(5.0,1100),(5.8,1050),(6.25,1100)]),
 dict(id='frzF',  clip='B', v0=37.90, v1=39.30, s0=6.64,  s1=6.64,  top=80,  cam=[(6.64,760)], freeze=True),
 dict(id='pass',  clip='B', v0=39.30, v1=44.80, s0=6.66,  s1=7.70,  top=172, cam=[(6.66,760),(7.0,900),(7.3,1250),(7.7,1500)]),
 dict(id='inter', clip='B', v0=44.80, v1=52.50, s0=7.70,  s1=9.70,  top=172, cam=[(7.7,1500),(8.0,1250),(8.4,1000),(8.8,700),(9.2,450),(9.5,330),(9.7,300)]),
 dict(id='wide3', clip='A', v0=52.50, v1=54.20, s0=6.10,  s1=6.50,  top=110, cam=[(6.1,760),(6.5,762)]),
 dict(id='frzA',  clip='A', v0=54.20, v1=58.90, s0=6.50,  s1=6.50,  top=110, cam=[(6.5,762)], freeze=True),
 dict(id='close2',clip='B', v0=58.90, v1=63.30, s0=8.60,  s1=9.70,  top=172, cam=[(8.6,850),(8.8,700),(9.2,450),(9.5,330),(9.7,300)]),
 dict(id='frzB',  clip='B', v0=63.30, v1=66.80, s0=9.70,  s1=9.70,  top=172, cam=[(9.7,300)], freeze=True),
 dict(id='roof',  clip='B', v0=66.80, v1=74.10, s0=19.00, s1=20.75, top=172, cam=[(19.0,1325),(19.6,1270),(20.2,1230),(20.75,1150)]),
 dict(id='frzC',  clip='B', v0=74.10, v1=76.80, s0=9.55,  s1=9.55,  top=172, cam=[(9.55,320)], freeze=True),
 dict(id='shot',  clip='B', v0=76.80, v1=81.50, s0=9.55,  s1=10.60, top=172, cam=[(9.55,300),(9.75,420),(9.95,600),(10.6,650)]),
 dict(id='goal2', clip='B', v0=81.50, v1=84.70, s0=11.35, s1=12.85, top=172, cam=GOALCAM),
 dict(id='celeb', clip='A', v0=84.70, v1=T,     s0=9.60,  s1=9.60 + (T - 84.70), top=172, cam=[(9.6,845),(10.4,770),(11.1,1075),(11.6,1075),(12.1,1500),(13.0,1450),(13.6,1440),(14.1,1500)]),
]

# spotlights: segment id, v0, v1, centres [(src_t,x,y)], radius (src px)
SPOT = [
 dict(seg='frzA', v0=54.25, v1=58.90, pts=[(6.5, 762, 652)], r=70, name='Fermín'),
 dict(seg='roof', v0=69.30, v1=74.10, pts=[(19.0,1325,705),(19.6,1270,709),(20.2,1230,712),(20.75,1150,705)], r=185, name='portero'),
]
# ball-carrier labels: seg, v0, v1, head-top points [(src_t, x, y)], name
LABELS = [
 dict(seg='frzF', v0=38.20, v1=39.30, pts=[(6.64, 743, 157)], name='Fermín López'),
 dict(seg='frzA', v0=54.25, v1=58.90, pts=[(6.5, 760, 613)], name='Fermín López'),
]
# ball contacts (source time) -> kick sound
CONTACTS = {'B': [9.78], 'A': [6.56]}

def seg_src_time(seg, t):
    if seg.get('freeze') or seg['s1'] == seg['s0']:
        return seg['s0']
    return seg['s0'] + (t - seg['v0']) * (seg['s1'] - seg['s0']) / (seg['v1'] - seg['v0'])

def src_index(clip, st):
    n = 854 if clip == 'A' else 1248
    return min(n, max(1, int(math.floor(st * SRC_FPS + 0.25)) + 1))

def interp(pts, st):
    xs = [p[0] for p in pts]
    if st <= xs[0]: return pts[0][1:]
    if st >= xs[-1]: return pts[-1][1:]
    for a, b in zip(pts[:-1], pts[1:]):
        if a[0] <= st <= b[0]:
            u = (st - a[0]) / (b[0] - a[0])
            return tuple(a[i] + u * (b[i] - a[i]) for i in range(1, len(a)))

def ball_cam(seg, frames):
    key = 'f' + seg['clip']
    xs = []
    for (t, st) in frames:
        o = ball[key][src_index(seg['clip'], st) - 1]
        xs.append(o[0] if o else np.nan)
    xs = np.array(xs, float)
    # median-filter outliers, then fill gaps
    med = np.array([np.nanmedian(xs[max(0, i - 6):i + 7]) for i in range(len(xs))])
    bad = np.isnan(xs) | (np.abs(xs - med) > 180)
    xs[bad] = np.nan
    idx = np.arange(len(xs))
    good = ~np.isnan(xs)
    if good.sum() == 0: return np.full(len(xs), 960.0)
    return np.interp(idx, idx[good], xs[good])

def gauss(x, sigma=10):
    if len(x) < 3: return x
    k = np.arange(-3 * sigma, 3 * sigma + 1)
    g = np.exp(-k ** 2 / (2 * sigma ** 2)); g /= g.sum()
    pad = np.pad(x, (3 * sigma, 3 * sigma), mode='edge')
    return np.convolve(pad, g, mode='valid')

NF = int(round(T * FPS))
frame_seg = []
for k in range(NF):
    t = k / FPS
    seg = next(s for s in EDL if s['v0'] - 1e-9 <= t < s['v1'] + 1e-9)
    frame_seg.append(seg)

# camera per output frame
cam = [None] * NF
for seg in EDL:
    ks = [k for k in range(NF) if frame_seg[k] is seg]
    frames = [(k / FPS, seg_src_time(seg, k / FPS)) for k in ks]
    if seg['cam'] == 'ball':
        cx = ball_cam(seg, frames)
    else:
        cx = np.array([interp(seg['cam'], st)[0] for _, st in frames])
    if not seg.get('freeze'):
        cx = gauss(cx, 10)
    xmin = 0 if seg['top'] >= 172 else 320
    for i, k in enumerate(ks):
        x0 = min(max(cx[i] - CW / 2, xmin), 1920 - CW)
        cam[k] = dict(x0=x0, y0=seg['top'])

def spot_at(t):
    for sp in SPOT:
        if sp['v0'] <= t < sp['v1']:
            return sp
    return None

# zoom: cut punch (+7 %, back in 0.1 s), freeze push-in, spotlight +22 % toward subject
view = []
for k in range(NF):
    t = k / FPS; seg = frame_seg[k]; c = cam[k]
    z = 1.0; fx, fy = c['x0'] + CW / 2, c['y0'] + CH / 2
    dt = t - seg['v0']
    if dt < 0.1 and seg is not EDL[0]:
        z *= 1.07 - 0.07 * (dt / 0.1)
    sp = spot_at(t)
    st = seg_src_time(seg, t)
    if sp:
        u = min(1, (t - sp['v0']) / max(0.8, (sp['v1'] - sp['v0']) * 0.7))
        u = u * u * (3 - 2 * u)
        z *= 1 + 0.22 * u
        px, py = interp(sp['pts'], st)
        fx = fx + (px - fx) * u; fy = fy + (py - fy) * u
    elif seg.get('freeze'):
        z *= 1 + 0.05 * dt / (seg['v1'] - seg['v0'])
    w, h = CW / z, CH / z
    x0 = min(max(fx - w / 2, c['x0']), c['x0'] + CW - w)
    y0 = min(max(fy - h / 2, c['y0']), c['y0'] + CH - h)
    view.append(dict(x0=x0, y0=y0, s=1080.0 / w))

def to_out(k, x, y):
    v = view[k]
    return (x - v['x0']) * v['s'], (y - v['y0']) * v['s']

# ---------------------------------------------------------------- images
os.makedirs(f'{P}/assets/frames', exist_ok=True)
imgs = []  # (clip, idx, start_frame, nframes)
for k in range(NF):
    seg = frame_seg[k]
    idx = src_index(seg['clip'], seg_src_time(seg, k / FPS))
    if imgs and imgs[-1][0] == seg['clip'] and imgs[-1][1] == idx and imgs[-1][2] + imgs[-1][3] == k:
        imgs[-1][3] += 1
    else:
        imgs.append([seg['clip'], idx, k, 1])
used = set((c, i) for c, i, _, _ in imgs)
for c, i in used:
    dst = f'{P}/assets/frames/{c}{i:05d}.jpg'
    if not os.path.exists(dst):
        shutil.copy(f'{W}/f{c}/{i:05d}.jpg', dst)

# ---------------------------------------------------------------- html
H = []
add = H.append
Q = 0.25 / FPS  # quarter-frame offset
def ts(x): return f'{max(0.0, x):.4f}'

for n, (c, i, k0, nk) in enumerate(imgs):
    s = k0 / FPS - (Q if k0 else 0)
    d = nk / FPS + (Q if k0 else 0)
    add(f'<img class="clip src" src="assets/frames/{c}{i:05d}.jpg" data-start="{ts(s)}" data-duration="{d:.4f}" alt="" />')

# captions
caps = []
for j, w in enumerate(words):
    txt = w['w'].strip('.,;:¡!¿?').lower()
    s = w['s']
    e = words[j + 1]['s'] if j + 1 < len(words) else T
    if e - w['e'] > 0.35: e = w['e'] + 0.25
    caps.append(f'<div class="clip cap" data-start="{s:.3f}" data-duration="{max(0.05, e - s):.3f}">{txt}</div>')

# timeline JS
js = []
tl = js.append
for k in range(NF):
    v = view[k]
    tl(f'tl.set("#stage",{{x:{-v["x0"]*v["s"]:.2f},y:{-v["y0"]*v["s"]:.2f},scale:{v["s"]:.5f}}},{k/FPS:.4f});')

# spotlights
spot_html = []
for n, sp in enumerate(SPOT):
    R0 = sp['r'] * S_BASE
    sid = f'spot{n}'
    spot_html.append(f'<div id="{sid}" class="clip spotwrap" data-start="{sp["v0"]-0.01:.3f}" data-duration="{sp["v1"]-sp["v0"]+0.02:.3f}"><div class="shade" style="--cx:540px;--cy:960px;--rr:{R0:.1f}px"></div><div class="ringpos"><div class="ring" style="--r:{R0:.1f}px"></div></div></div>')
    tl(f'tl.fromTo("#{sid}",{{opacity:0}},{{opacity:1,duration:0.25,ease:"none"}},{sp["v0"]:.3f});')
    tl(f'tl.to("#{sid}",{{opacity:0,duration:0.25,ease:"none"}},{sp["v1"]-0.25:.3f});')
    k0 = int(math.ceil(sp['v0'] * FPS)); k1 = int(math.floor(sp['v1'] * FPS))
    for k in range(k0, min(k1 + 1, NF)):
        st = seg_src_time(frame_seg[k], k / FPS)
        px, py = interp(sp['pts'], st)
        ox, oy = to_out(k, px, py)
        sc = view[k]['s'] / S_BASE
        tl(f'tl.set("#{sid} .shade",{{"--cx":"{ox:.1f}px","--cy":"{oy:.1f}px","--rr":"{R0*sc:.1f}px"}},{k/FPS:.4f});')
        tl(f'tl.set("#{sid} .ringpos",{{x:{ox:.1f},y:{oy:.1f},scale:{sc:.4f}}},{k/FPS:.4f});')

# labels
lab_html = []
for n, lb in enumerate(LABELS):
    lid = f'lab{n}'
    lab_html.append(f'<div id="{lid}w" class="clip labwrap" data-start="{lb["v0"]:.3f}" data-duration="{lb["v1"]-lb["v0"]:.3f}"><div id="{lid}" class="lab"><div class="inner"><div class="name">{lb["name"]}</div><svg class="arrow" viewBox="0 0 64 86" width="64" height="86"><path d="M18 2 H46 V44 H62 L32 84 L2 44 H18 Z" fill="#ff1f1f" stroke="#2a0000" stroke-width="3" stroke-linejoin="round"/></svg></div></div></div>')
    tl(f'tl.fromTo("#{lid} .inner",{{scale:0.2,opacity:0}},{{scale:1,opacity:1,duration:0.12,ease:"back.out(2)"}},{lb["v0"]:.3f});')
    k0 = int(math.ceil(lb['v0'] * FPS)); k1 = int(math.ceil(lb['v1'] * FPS))
    for k in range(k0, min(k1, NF)):
        t = k / FPS
        st = seg_src_time(frame_seg[k], t)
        hx, hy = interp(lb['pts'], st)
        ox, oy = to_out(k, hx, hy)
        bounce = 5 * abs(math.sin(2 * math.pi * 1.4 * (t - lb['v0'])))
        tl(f'tl.set("#{lid}",{{x:{ox:.1f},y:{oy - bounce:.1f}}},{t:.4f});')

# score banner
SC0 = 81.5
fl = next(w for w in words if w['w'].startswith('red'))['s']
tl(f'tl.fromTo("#score",{{y:-40,opacity:0}},{{y:0,opacity:1,duration:0.2,ease:"back.out(2)"}},{SC0:.3f});')
tl(f'tl.to("#bar-score-old",{{rotationX:90,duration:0.12,ease:"power1.in"}},{fl:.3f});')
tl(f'tl.fromTo("#bar-score-new",{{rotationX:-90}},{{rotationX:0,duration:0.14,ease:"power1.out"}},{fl+0.12:.3f});')

# audio
aud = ['<audio id="voice" class="clip" src="assets/audio/voice_lim.wav" data-start="0" data-duration="%.3f" data-volume="0.708"></audio>' % T]
sfx = []
cuts = [s['v0'] for s in EDL[1:]]
for n, c in enumerate(cuts):
    f = 'sfx_whoosh1.wav' if n % 2 == 0 else 'sfx_whoosh2.wav'
    d = 0.35 if n % 2 == 0 else 0.30
    sfx.append((c - 0.12, f, d, 0.22))
for s in EDL:
    if s.get('freeze'): sfx.append((s['v0'], 'sfx_freeze.wav', 0.5, 0.25))
for lb in LABELS: sfx.append((lb['v0'], 'sfx_pop.wav', 0.09, 0.3))
sfx.append((SC0, 'sfx_pop.wav', 0.09, 0.3))
for s in EDL:
    if s.get('freeze'): continue
    for ct in CONTACTS[s['clip']]:
        lo, hi = sorted((s['s0'], s['s1']))
        if lo <= ct <= hi:
            v = s['v0'] + (ct - s['s0']) * (s['v1'] - s['v0']) / (s['s1'] - s['s0'])
            sfx.append((v, 'sfx_kick.wav', 0.25, 0.45))
for n, (t0, f, d, vol) in enumerate(sorted(sfx)):
    aud.append(f'<audio id="sfx{n}" class="clip" src="assets/audio/{f}" data-start="{max(0,t0):.3f}" data-duration="{d}" data-volume="{vol*0.708:.3f}"></audio>')

CSS = open(os.path.dirname(os.path.abspath(__file__)) + '/style.css').read()
html = f'''<!doctype html>
<html lang="es" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="assets/gsap.min.js"></script>
<style>
{CSS}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{T:.3f}" data-width="1080" data-height="1920">
  <div id="viewport"><div id="stage">
{chr(10).join(H)}
  </div></div>
{chr(10).join(spot_html)}
{chr(10).join(lab_html)}
  <div id="score" class="clip" data-start="{SC0-0.01:.3f}" data-duration="{T-SC0+0.01:.3f}">
    <span class="team">ATLÉTICO</span><span class="box"><span>1</span><span class="dash">–</span><span class="flip"><span id="bar-score-old">0</span><span id="bar-score-new">1</span></span></span><span class="team">BARÇA</span><span class="min">45'</span>
  </div>
{chr(10).join(caps)}
{chr(10).join(aud)}
</div>
<script>
window.__timelines = window.__timelines || {{}};
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
window.__timelines["main"] = tl;
tl.seek(0);
</script>
</body>
</html>
'''
open(f'{P}/index.html', 'w').write(html)
json.dump(dict(view=view, segs=[s['id'] for s in frame_seg]), open(f'{W}/view.json', 'w'))
print('frames used', len(used), 'img clips', len(imgs), 'NF', NF, 'size', len(html) // 1024, 'KB')
