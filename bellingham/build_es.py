# Génère la composition HyperFrames (hf/index.html) : EDL calée sur words.json, caméra 9:16,
# étiquette du porteur, projecteur, sous-titres, bandeau de score, sons.
# Python ne fabrique aucune image de la vidéo : il écrit le HTML/GSAP que HyperFrames rend.
import json, os, re, math, shutil, subprocess
import numpy as np, cv2

B = '/home/user/Fofana/bellingham'
HF = f'{B}/hf'
SRC = {'a': '/tmp/claude-0/-home-user-Fofana/73e3ae01-f789-5811-8ac5-09dda17df3e8/scratchpad/src/a.mp4',
       'b': '/tmp/claude-0/-home-user-Fofana/73e3ae01-f789-5811-8ac5-09dda17df3e8/scratchpad/src/b.mp4'}
FPS_SRC = 50.0
OUT_W, OUT_H = 1080, 1920
Q = 1 / 30 / 4                      # décalage d'1/4 d'image

V = json.load(open(f'{B}/voice_user/words.json'))
DUR = round(V['duration'], 3)
words = V['words']
SEG = V['segments']
def word_time(seg, needle):
    i = sum(len(s.split()) for s in V['sentences'][:seg])
    for w in words[i:i + len(V['sentences'][seg].split())]:
        if needle.lower() in w['word'].lower(): return w['start']
    raise KeyError(needle)

# ---------------- EDL : groupe de segments de la voix -> plan ----------------
# (premier segment, clip, f0, f1, mode, caméra) ; chaque plan commence sur le premier mot de son groupe
EDL_ES = [
 (0,  'b', 790, 858, 'slow', [(790, 1050), (818, 1420), (858, 1450)]),
 (2,  'a', 0, 110, 'slow', [(0, 717), (40, 880), (60, 800), (75, 560), (110, 545)]),
 (5,  'a', 110, 200, 'slow', 'vini'),
 (6,  'b', 0, 45, 'slow', [(0, 1000), (45, 1000)]),
 (9,  'b', 16, 16, 'freeze', 'cuc'),
 (10, 'b', 16, 75, 'slow', [(16, 1000), (75, 1150)]),
 (12, 'b', 75, 110, 'slow', [(75, 1200), (110, 1250)]),
 (13, 'b', 95, 140, 'slow', [(95, 1300), (140, 1000)]),
 (15, 'b', 140, 180, 'slow', 'cuc'),
 (17, 'b', 180, 180, 'freeze', [(180, 1100)]),
 (19, 'b', 505, 596, 'slow', [(505, 900), (560, 900), (596, 700)]),
 (21, 'b', 340, 420, 'slow', [(340, 1150), (380, 1150), (420, 1190)]),
 (24, 'b', 420, 440, 'slow', [(420, 1190), (440, 1350)]),
 (25, 'b', 560, 628, 'slow', [(560, 1100), (592, 1500), (604, 1620), (628, 1750)]),
 (28, 'b', 436, 478, 'slow', [(436, 1300), (448, 1400), (478, 700)]),
 (30, 'b', 790, 816, 'slow', [(790, 1100), (816, 1450)]),
 (31, 'b', 815, 830, 'slow', [(815, 1480), (830, 1500)]),
 (32, 'b', 990, 1066, 'slow', [(990, 420), (1020, 800), (1050, 1550), (1066, 1620)]),
]
EDL = {}; SPAN = {}
for i, e in enumerate(EDL_ES):
    t0 = 0.0 if i == 0 else SEG[e[0]]['start']
    t1 = SEG[EDL_ES[i + 1][0]]['start'] if i + 1 < len(EDL_ES) else DUR
    EDL[i] = [e[1:]]; SPAN[i] = (t0, t1)

HJ = json.load(open(f'{B}/analysis/heads.json'))
HEAD = {int(f): v for f, v in HJ['cuc_hc'].items()}
HEADV = {int(f): [v[0], v[1] - 2] for f, v in HJ['vini_a'].items()}   # biais mesuré : -2 px

# ---------------- zones interdites (mesurées) ----------------
WM_Y0 = 898            # filigrane « X.com/marfawe » : lignes 902-938 sur toute la largeur -> bas du cadre <= 898
LIVE = (1565, 1830, 110)   # bandeau gris « LIVE » : x 1565-1830, y 52-110
BUG_A = (60, 620, 105)     # score télé clip a : x 60-620, y 48-104 (et « GOAL »)

def clamp_crop(clip, cx, cy, h):
    h = min(h, WM_Y0)
    for _ in range(3):
        w = h * 9 / 16
        x0 = min(max(cx - w / 2, 0), 1920 - w)
        ymin = 0
        if x0 < LIVE[1] and x0 + w > LIVE[0]: ymin = max(ymin, LIVE[2])
        if clip == 'a' and x0 < BUG_A[1] and x0 + w > BUG_A[0]: ymin = max(ymin, BUG_A[2])
        h = min(h, WM_Y0 - ymin)
    w = h * 9 / 16
    x0 = min(max(cx - w / 2, 0), 1920 - w)
    y0 = min(max(cy - h / 2, ymin), WM_Y0 - h)
    return x0, y0, h

def gauss_smooth(arr, sigma=10):
    if len(arr) < 3: return arr
    r = int(3 * sigma); k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    p = np.pad(arr, (r, r), mode='edge'); return np.convolve(p, k, 'valid')

def interp_keys(keys, f):
    ks = sorted(keys)
    if f <= ks[0][0]: return ks[0][1]
    for a, b in zip(ks, ks[1:]):
        if a[0] <= f <= b[0]: return a[1] + (b[1] - a[1]) * (f - a[0]) / max(1, b[0] - a[0])
    return ks[-1][1]

# ---------------- planification des images ----------------
images = []     # dicts: clip, f, t0, t1, crop(x0,y0,h), shot
shots = []      # dicts: t0, t1, clip, mode, frames
for k in sorted(SPAN):
    t0, t1 = SPAN[k]
    subs = EDL[k]
    # durées des sous-plans
    fixed = [s[5] if len(s) > 5 else None for s in subs]
    rest = (t1 - t0) - sum(x for x in fixed if x)
    nfree = sum(1 for x in fixed if not x)
    tt = t0
    for s, fx in zip(subs, fixed):
        clip, f0, f1, mode, cam = s[:5]
        d = fx if fx else rest / nfree
        ta, tb = tt, tt + d; tt = tb
        if mode == 'freeze': speed = 0
        elif mode == 'x1': speed = 1.0
        else: speed = min(0.7, max(0.25, (f1 - f0) / (FPS_SRC * d)))
        frames = []
        if speed == 0: frames = [(f0, ta, tb)]
        else:
            f = f0
            while f <= f1:
                a = ta + (f - f0) / (FPS_SRC * speed)
                if a >= tb - 1e-6: break
                b = ta + (f + 1 - f0) / (FPS_SRC * speed)
                frames.append([f, a, min(b, tb)]); f += 1
            frames[-1][2] = tb            # dernière image tenue jusqu'à la fin du plan
        # caméra
        fs = [fr[0] for fr in frames]
        if cam == 'cuc':
            cx = np.array([HEAD[f][0] for f in fs]); hcrop = 760
        elif cam == 'vini':
            cx = np.array([HEADV[f][0] for f in fs]); hcrop = 760
        else:
            cx = np.array([interp_keys(cam, f) for f in fs], float); hcrop = 898
        cx = gauss_smooth(cx, 10)
        shot = dict(sent=k, t0=ta, t1=tb, clip=clip, mode=mode, speed=speed, f0=f0, f1=f1)
        shots.append(shot)
        for (f, a, b), x in zip(frames, cx):
            x0, y0, h = clamp_crop(clip, x, 0 if hcrop == 898 else 560, hcrop)
            images.append(dict(clip=clip, f=f, t0=a, t1=b, crop=(x0, y0, h), shot=len(shots) - 1))

# ---------------- extraction des images utilisées (JPEG 95) ----------------
os.makedirs(f'{HF}/frames', exist_ok=True)
need = {}
for im in images: need.setdefault(im['clip'], set()).add(im['f'])
for clip, fset in need.items():
    cap = cv2.VideoCapture(SRC[clip]); f = 0; mx = max(fset)
    while f <= mx:
        ok, fr = cap.read()
        if not ok: break
        p = f'{HF}/frames/{clip}{f:04d}.jpg'
        if f in fset and not os.path.exists(p): cv2.imwrite(p, fr, [cv2.IMWRITE_JPEG_QUALITY, 95])
        f += 1

def out_xy(im, x, y):
    x0, y0, h = im['crop']; s = OUT_H / h
    return (x - x0) * s, (y - y0) * s, s

# ---------------- étiquette (Cucurella, plan large) ----------------
TAGS = [('Vinícius Júnior', 'logo_rma.png', 'a', 78, 201, HEADV), ('Marc Cucurella', 'logo_rma.png', 'b', 145, 199, HEAD)]
tag_events = []
for name, logo, clip, fa, fc, HH in TAGS:
    seq = [im for im in images if im['clip'] == clip and fa <= im['f'] < fc and im['f'] in HH]
    # une étiquette par suite continue d'images (elle disparaît à la coupe ou à l'image de la passe)
    runs = []
    for im in seq:
        if runs and images.index(im) == images.index(runs[-1][-1]) + 1: runs[-1].append(im)
        else: runs.append([im])
    for run in runs:
        if run[0]['t1'] - run[0]['t0'] == 0: continue
        pts = []
        for im in run:
            hx, hy = HH[im['f']]; x, y, s_ = out_xy(im, hx, hy); pts.append((im['t0'], x, y))
        tag_events.append(dict(name=name, logo=logo, t0=run[0]['t0'], t1=run[-1]['t1'], pts=pts))

# ---------------- projecteur ----------------
SPOTS = []
def spot_from_boxes(sent, needle, boxes_by_frame, zoom):
    k = sent; ta = max(SPAN[k][0], word_time(EDL_ES[k][0], needle) - 0.5); tb = SPAN[k][1]
    seq = [im for im in images if shots[im['shot']]['sent'] == k and im['t1'] > ta]
    pts = []; rad = 0
    for im in seq:
        x0b, y0b, x1b, y1b = boxes_by_frame(im['f'])
        cx, cy = (x0b + x1b) / 2, (y0b + y1b) / 2
        X, Y, s = out_xy(im, cx, cy)
        r = math.hypot((x1b - x0b) / 2, (y1b - y0b) / 2) * s
        rad = max(rad, r); pts.append([max(im['t0'], ta), X, Y])
    # lissage léger du centre
    xs = gauss_smooth(np.array([p[1] for p in pts]), 2); ys = gauss_smooth(np.array([p[2] for p in pts]), 2)
    for p, x, y in zip(pts, xs, ys): p[1], p[2] = float(x), float(y)
    SPOTS.append(dict(t0=ta, t1=tb, pts=pts, r=rad + 24, zoom=zoom))

def cuc_box(f):
    hx, hy = HEAD[f]; return (hx - 48, hy - 8, hx + 48, hy + 108)
spot_from_boxes(4, 'cucurella', cuc_box, True)

# ---------------- sous-titres (texte du script, un mot à la fois) ----------------
subs = []
for w in words:
    t = re.sub(r"^[«\"(]+|[,.;:!?»\")]+$", '', w['word']).lower()
    if not t: continue
    subs.append((w['start'], w['end'], t))
for i in range(len(subs)):              # durée minimale (aucune durée nulle)
    a, b, t = subs[i]; nxt = subs[i + 1][0] if i + 1 < len(subs) else DUR
    if b - a < 0.08:
        a = min(a, nxt - 0.08); b = a + 0.08
        if i > 0 and subs[i - 1][1] > a: subs[i - 1] = (subs[i - 1][0], a, subs[i - 1][2])
    subs[i] = (a, b, t)
for i in range(len(subs) - 1):          # chaque mot reste jusqu'au suivant (pas de trou)
    if subs[i + 1][0] - subs[i][1] < 0.35: subs[i] = (subs[i][0], subs[i + 1][0], subs[i][2])

# ---------------- sons ----------------
sfx = []
cut_times = [s['t0'] for s in shots[1:]]
for i, t in enumerate(cut_times):
    sfx.append((f'whoosh{i % 4 + 1}.wav', max(0, t - 0.12), 0.35, 0.55))
for s in shots:
    if s['mode'] == 'freeze': sfx.append(('freeze.wav', s['t0'], 0.6, 0.6))
for te in tag_events: sfx.append(('pop.wav', te['t0'], 0.15, 0.6))
T_SCORE_IN = SEG[2]['start']; T_FLIP = word_time(33, 'fondo')
sfx.append(('pop.wav', T_SCORE_IN, 0.15, 0.6))
kick_n = 0
for (clip, fc) in [('b', 448), ('b', 820)]:
    for im in images:
        if im['clip'] == clip and im['f'] == fc:
            # une frappe par plan qui montre l'image du contact
            if any(abs(im['t0'] - x[1]) < 0.05 for x in sfx if x[0].startswith('kick')): continue
            sfx.append((f'kick{kick_n % 3 + 1}.wav', im['t0'], 0.3, 0.9)); kick_n += 1
VOL = json.load(open(f'{B}/mix.json')) if os.path.exists(f'{B}/mix.json') else {'voice': 1.0, 'sfx': 1.0}

# ---------------- HTML ----------------
def fx(v): return f'{v:.3f}'
L = []
L.append(f'''<!doctype html>
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={OUT_W}, height={OUT_H}" />
<script src="assets/gsap.min.js"></script>
<style>
@font-face {{ font-family: Poppins; font-weight: 500; src: url(assets/fonts/poppins-latin-500-normal.woff2) format('woff2'); }}
@font-face {{ font-family: Poppins; font-weight: 800; src: url(assets/fonts/poppins-latin-800-normal.woff2) format('woff2'); }}
@font-face {{ font-family: Montserrat; font-weight: 800; src: url(assets/fonts/montserrat-latin-800-normal.woff2) format('woff2'); }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: {OUT_W}px; height: {OUT_H}px; overflow: hidden; background: #000; }}
#root {{ position: relative; width: {OUT_W}px; height: {OUT_H}px; overflow: hidden; background: #000; }}
#punch, #zoom, #imgs {{ position: absolute; inset: 0; transform-origin: 50% 50%; }}
#imgs img {{ position: absolute; max-width: none; }}
#dark {{ position: absolute; inset: 0; opacity: 0; background: rgba(0,0,0,.58);
  -webkit-backdrop-filter: blur(5px); backdrop-filter: blur(5px);
  -webkit-mask-image: radial-gradient(circle var(--r) at var(--x) var(--y), transparent 99%, #000 100%);
  mask-image: radial-gradient(circle var(--r) at var(--x) var(--y), transparent 99%, #000 100%); }}
#ring {{ position: absolute; left: 0; top: 0; opacity: 0; border: 5px solid #fff; border-radius: 50%;
  box-shadow: 0 0 14px rgba(255,255,255,.55), inset 0 0 10px rgba(255,255,255,.35); }}
.tag {{ position: absolute; left: 0; top: 0; width: 0; height: 0; }}
.tag .inner {{ position: absolute; left: 0; bottom: 0; transform-origin: 50% 100%; }}
.tag .box {{ position: absolute; left: -300px; width: 600px; bottom: 4px; display: flex; flex-direction: column-reverse; align-items: center; gap: 8px; }}
.tag .arrow {{ width: 64px; height: 86px; filter: drop-shadow(0 3px 4px rgba(0,0,0,.5)); }}
.tag .name {{ font-family: Montserrat; font-weight: 800; font-size: 38px; color: #fff; background: rgba(12,14,20,.86);
  padding: 6px 18px 8px; border-radius: 14px; white-space: nowrap; line-height: 1.1; }}
.tag .logo {{ width: 84px; height: 84px; border-radius: 50%; background: #fff; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 3px 8px rgba(0,0,0,.45); }}
.tag .logo img {{ height: 66px; }}
#scorewrap {{ position: absolute; top: 150px; left: 0; right: 0; display: flex; justify-content: center; }}
#score {{ position: relative; display: flex; align-items: center; gap: 0;
  font-family: Poppins; font-weight: 800; font-size: 44px; color: #fff; opacity: 0; filter: drop-shadow(0 4px 10px rgba(0,0,0,.5)); }}
#score .team {{ background: rgba(12,14,20,.9); padding: 10px 22px; }}
#score .team.l {{ border-radius: 16px 0 0 16px; }} #score .team.r {{ border-radius: 0 16px 16px 0; }}
#score .res {{ background: #e3171e; padding: 10px 20px; display: flex; gap: 14px; perspective: 400px; }}
#score .dig {{ position: relative; display: inline-block; width: 30px; height: 56px; }}
#score .dig span {{ position: absolute; left: 0; top: 0; width: 30px; text-align: center; backface-visibility: hidden; }}
#score .min {{ margin-left: 14px; font-size: 34px; background: rgba(12,14,20,.9); padding: 12px 16px; border-radius: 14px; }}
.sub {{ position: absolute; left: 0; right: 0; top: 1600px; text-align: center; font-family: Poppins; font-weight: 500; font-size: 46px;
  color: #fff; text-shadow: 0 2px 4px rgba(0,0,0,.85); line-height: 1; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{fx(DUR)}" data-width="{OUT_W}" data-height="{OUT_H}">
<div id="punch"><div id="zoom">
<div id="imgs">''')
for n, im in enumerate(images):
    x0, y0, h = im['crop']; s = OUT_H / h
    st = f"left:{-x0 * s:.1f}px;top:{-y0 * s:.1f}px;width:{1920 * s:.1f}px;height:{1080 * s:.1f}px"
    L.append(f'<img id="img{n}" class="clip" src="frames/{im["clip"]}{im["f"]:04d}.jpg" data-start="{fx(im["t0"] + Q if n else 0)}" data-duration="{fx(im["t1"] - im["t0"])}" style="{st}" alt="">')
L.append('</div>')
L.append('<div id="dark"></div><div id="ring"></div>')
for i, te in enumerate(tag_events):
    L.append(f'''<div class="tag clip" id="tag{i}" data-start="{fx(te['t0'] + Q)}" data-duration="{fx(te['t1'] - te['t0'])}"><div class="inner"><div class="box">
<svg class="arrow" viewBox="0 0 64 86"><path d="M20 3 H44 V44 H60 L32 83 L4 44 H20 Z" fill="#ff1f1f" stroke="#3a0000" stroke-width="3" stroke-linejoin="round"/></svg>
<div class="name">{te['name']}</div><div class="logo"><img src="assets/{te['logo']}" alt=""></div></div></div></div>''')
L.append('</div></div>')
L.append(f'''<div id="scorewrap" class="clip" data-start="{fx(T_SCORE_IN)}" data-duration="{fx(DUR - T_SCORE_IN)}"><div id="score">
<div class="team l">AEK</div><div class="res"><span class="dig"><span>1</span></span><span>–</span><span class="dig"><span id="d0">0</span><span id="d1">1</span></span></div><div class="team r">RMA</div><div class="min">32'</div></div></div>''')
for i, (a, b, t) in enumerate(subs):
    L.append(f'<div id="w{i}" class="sub clip" data-start="{fx(a + Q)}" data-duration="{fx(b - a)}">{t}</div>')
L.append(f'<audio class="clip" id="voice" src="voice_es.wav" data-start="0" data-duration="{fx(DUR)}" data-volume="{VOL["voice"]:.3f}"></audio>')
for i, (f, t, d, v) in enumerate(sorted(sfx, key=lambda x: x[1])):
    L.append(f'<audio class="clip" id="sfx{i}" src="sfx/{f}" data-start="{fx(t)}" data-duration="{fx(d)}" data-volume="{v * VOL["sfx"]:.3f}"></audio>')
L.append('</div>')

# ---------------- timeline GSAP ----------------
J = []
J.append('const tl = gsap.timeline({ paused: true });')
J.append('gsap.set("#d1",{rotationX:-90,opacity:0}); tl.set("#punch",{scale:1},0); tl.set("#zoom",{scale:1},0);')
for s in shots[1:]:
    J.append(f'tl.fromTo("#punch",{{scale:1.07}},{{scale:1,duration:0.1,ease:"power2.out"}},{fx(s["t0"])});')
for i, te in enumerate(tag_events):
    J.append(f'tl.fromTo("#tag{i} .inner",{{scale:0}},{{scale:1,duration:0.12,ease:"back.out(2)"}},{fx(te["t0"])});')
    period = 1 / (2 * 1.4)
    J.append(f'tl.fromTo("#tag{i} .box",{{y:0}},{{y:-5,duration:{period:.4f},ease:"sine.out",yoyo:true,repeat:{int((te["t1"] - te["t0"]) / period) + 1}}},{fx(te["t0"])});')
    for t, x, y in te['pts']:
        J.append(f'tl.set("#tag{i}",{{x:{x:.1f},y:{y:.1f}}},{fx(t)});')
for sp in SPOTS:
    t0, t1 = sp['t0'], sp['t1']; r = sp['r']
    J.append(f'tl.set("#dark",{{"--r":"{r:.1f}px"}},{fx(t0)});')
    J.append(f'tl.set("#ring",{{width:{2 * r:.1f},height:{2 * r:.1f}}},{fx(t0)});')
    for t, x, y in sp['pts']:
        J.append(f'tl.set("#dark",{{"--x":"{x:.1f}px","--y":"{y:.1f}px"}},{fx(t)});')
        J.append(f'tl.set("#ring",{{x:{x - r:.1f},y:{y - r:.1f}}},{fx(t)});')
    J.append(f'tl.fromTo(["#dark","#ring"],{{opacity:0}},{{opacity:1,duration:0.25}},{fx(t0)});')
    J.append(f'tl.to(["#dark","#ring"],{{opacity:0,duration:0.25}},{fx(t1 - 0.25)});')
    if sp['zoom']:
        x, y = sp['pts'][0][1], sp['pts'][0][2]
        J.append(f'tl.set("#zoom",{{transformOrigin:"{x:.1f}px {y:.1f}px"}},{fx(t0)});')
        J.append(f'tl.fromTo("#zoom",{{scale:1}},{{scale:1.22,duration:{min(1.2, t1 - t0 - 0.3):.2f},ease:"power2.inOut"}},{fx(t0)});')
        J.append(f'tl.set("#zoom",{{scale:1}},{fx(t1)});')
J.append(f'tl.fromTo("#score",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.12,ease:"back.out(2)"}},{fx(T_SCORE_IN)});')
J.append(f'tl.to("#d0",{{rotationX:90,opacity:0,duration:0.15,ease:"power1.in"}},{fx(T_FLIP)});')
J.append(f'tl.to("#d1",{{rotationX:0,opacity:1,duration:0.15,ease:"power1.out"}},{fx(T_FLIP + 0.15)});')
J.append('window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl; tl.seek(0);')
L.append('<script>\n' + '\n'.join(J) + '\n</script>\n</body>\n</html>')
open(f'{HF}/index.html', 'w').write('\n'.join(L))
json.dump(dict(shots=shots, images=[dict(im, crop=list(im['crop'])) for im in images], tags=tag_events, spots=SPOTS,
               subs=subs, sfx=sfx, t_score=T_SCORE_IN, t_flip=T_FLIP, duration=DUR), open(f'{B}/analysis/plan.json', 'w'), indent=0)
print('images', len(images), 'shots', len(shots), 'subs', len(subs), 'sfx', len(sfx), 'dur', DUR)
for s in shots: print(f"P{s['sent']:2d} {s['t0']:6.2f}-{s['t1']:6.2f} {s['clip']}{s['f0']}-{s['f1']} {s['mode']} v={s['speed']:.2f}")
