# Génère index.html (composition HyperFrames) à partir de l'EDL, des suivis et de words.json.
# Python sert uniquement à calculer les positions ; le montage et le rendu sont faits par HyperFrames.
import json, math, numpy as np
from scipy.ndimage import gaussian_filter1d

OUT_FPS = 30
W, H = 1080, 1920
DUR = 96.60
SRC = {'A': dict(fps=30, w=720, h=960, n=1801), 'B': dict(fps=25, w=572, h=626, n=321)}
for s in SRC.values():
    s['s0'] = H / s['h']                      # échelle de base (hauteur pleine)
T = json.load(open('analysis/tracks.json'))
WORDS = json.load(open('analysis/words.json'))

def wt(word, after=0.0):
    for w in WORDS:
        if w['s'] >= after - 0.01 and w['w'].strip('.,').lower() == word.lower():
            return w['s']
    raise KeyError(word)

NAMES = {'salah': ('Mohamed Salah', 'liverpool'), 'trent': ('Trent Alexander-Arnold', 'liverpool')}

# EDL : (début, fin, source, entrée, sortie|None=arrêt, options)
#   entrée/sortie en IMAGES source. follow = suivi pour la caméra ; tag = (suivi, joueur, image début, image fin exclue)
#   spot = (suivi, instant de début dans la vidéo finale, instant de fin) ; z = zoom de base
SP1=('rice1', wt('Rice', 18.4), 23.96); SP2=('rice2', wt('Rice', 29.0), 37.72); SP4=('rice4', 52.92, 59.78)
EDL = [
 (0.00, 6.26, 'A', 1200, 1338, dict(z=1.0, follow='trent', fx=360, kick=[1296])),
 (6.26, 11.10, 'A', 108, 252, dict(z=1.3, follow='salah1', tag=[('salah1', 'salah', 180, 253)])),
 (11.10, 14.02, 'A', 383, 468, dict(z=1.3, follow='salah2', tag=[('salah2', 'salah', 383, 469)])),
 (14.02, 18.46, 'B', 0, 85, dict(z=1.0, fx=300, follow='salahB', tag=[('salahB', 'salah', 75, 86)])),
 (18.46, 20.58, 'A', 540, None, dict(z=1.0, follow='rice1', freeze=True, tag=[('salah5', 'salah', 540, 541)],
      spot=SP1)),
 (20.58, 23.96, 'A', 540, 618, dict(z=1.0, follow='rice1', tag=[('salah5', 'salah', 540, 619)], spot=SP1)),
 (23.96, 29.04, 'A', 660, 732, dict(z=1.3, follow='salah3', tag=[('salah3', 'salah', 662, 733)])),
 (29.04, 31.00, 'A', 732, None, dict(z=1.0, follow='rice2', freeze=True, tag=[('salah3', 'salah', 732, 733)],
      spot=SP2)),
 (31.00, 37.72, 'A', 732, 789, dict(z=1.0, follow='rice2', tag=[('salah3', 'salah', 732, 790)], spot=SP2)),
 (37.72, 45.02, 'A', 468, 636, dict(z=1.0, follow='saliba', tag=[('salah5', 'salah', 468, 637)],
      spot=('saliba', wt('Saliba', 37.7), 45.02))),
 (45.02, 48.28, 'A', 797, 816, dict(z=1.0, follow='rice3', tag=[('salah4', 'salah', 797, 817)],
      spot=('rice3', wt('Rice', 45.0), 48.28))),
 (48.28, 52.92, 'B', 165, 215, dict(z=1.0, follow='riceB', tag=[('salahB', 'salah', 165, 216)], spot=('riceB', 48.28, 52.92))),
 (52.92, 54.76, 'A', 894, None, dict(z=1.3, follow='rice4', freeze=True, spot=SP4)),
 (54.76, 59.78, 'A', 894, 927, dict(z=1.3, follow='rice4', spot=SP4)),
 (59.78, 64.88, 'A', 797, 828, dict(z=1.0, follow='rice3', tag=[('salah4', 'salah', 797, 829)], spot=('rice3', 59.78, 64.88))),
 (64.88, 70.52, 'B', 75, 165, dict(z=1.0, follow='riceB', tag=[('salahB', 'salah', 75, 166)], spot=('riceB', wt('Rice', 64.8), 70.52))),
 (70.52, 76.04, 'A', 1132, 1167, dict(z=1.0, follow='salahC', kick=[1142])),
 (76.04, 81.76, 'B', 190, 228, dict(z=1.0, follow='salahB', tag=[('salahB', 'salah', 190, 228)])),
 (81.76, 83.86, 'A', 820, 837, dict(z=1.3, follow='salah4', tag=[('salah4', 'salah', 820, 829)], kick=[829])),
 (83.86, 89.42, 'A', 1200, 1262, dict(z=1.0, fx=360, follow='trent')),
 (89.42, DUR, 'A', 1262, 1350, dict(z=1.0, fx=360, follow='trent', kick=[1296])),
]

def trk(name, f, key):
    fr = T[name]['frames']; ks = sorted(int(k) for k in fr)
    f = min(max(f, ks[0]), ks[-1])
    if str(f) in fr: return fr[str(f)][key]
    i = np.searchsorted(ks, f); a, b = ks[i - 1], ks[i]
    return fr[str(a)][key] + (fr[str(b)][key] - fr[str(a)][key]) * (f - a) / (b - a)

def smooth_track(name):
    fr = T[name]['frames']; ks = sorted(int(k) for k in fr)
    out = {}
    for key, sig in (('cx', 1.5), ('cy', 1.5), ('hx', 1.2), ('hy', 1.2), ('w', 4), ('h', 4)):
        v = gaussian_filter1d(np.array([fr[str(k)][key] for k in ks], float), sig, mode='nearest')
        for k, x in zip(ks, v): out.setdefault(k, {})[key] = float(x)
    T[name]['s'] = out
for n in T: smooth_track(n)
def st(name, f, key):
    s = T[name]['s']; ks = sorted(s); f = min(max(f, ks[0]), ks[-1])
    return s[f][key]

# ---- échantillonnage image par image de la sortie ----
frames = []  # par image de sortie
for si, (t0, t1, src, fin, fout, o) in enumerate(EDL):
    n0, n1 = round(t0 * OUT_FPS), round(t1 * OUT_FPS)
    for n in range(n0, n1):
        t = n / OUT_FPS
        if fout is None: sf = fin
        else: sf = fin + (fout - fin) * (t - t0) / (t1 - t0); sf = min(int(math.floor(sf + 1e-6)), fout)
        frames.append(dict(n=n, t=t, shot=si, src=src, sf=sf, o=o, t0=t0))

# caméra : centre suivant le joueur, gaussienne sigma = 10 images
for si in range(len(EDL)):
    fl = [f for f in frames if f['shot'] == si]; o = EDL[si][5]; src = EDL[si][2]
    if o.get('follow'):
        cx = np.array([st(o['follow'], f['sf'], 'cx') for f in fl]); cy = np.array([st(o['follow'], f['sf'], 'cy') for f in fl])
        if 'fx' in o and o['follow'] in ('trent',):
            # avant que le joueur n'apparaisse dans le plan : centre fixe
            ks = sorted(T[o['follow']]['s']);
            m = np.array([f['sf'] < ks[0] for f in fl]); cx[m] = o['fx']; cy[m] = SRC[src]['h'] / 2
        if o.get('spot') and o.get('tag'):
            # spotlight + porteur étiqueté : la caméra cadre les deux joueurs
            tn = o['tag'][0][0]
            cx = (cx + np.array([st(tn, f['sf'], 'cx') for f in fl])) / 2
            cy = (cy + np.array([st(tn, f['sf'], 'cy') for f in fl])) / 2
        if not o.get('freeze'):
            cx = gaussian_filter1d(cx, 10, mode='nearest'); cy = gaussian_filter1d(cy, 10, mode='nearest')
    else:
        cx = np.full(len(fl), o.get('fx', SRC[src]['w'] / 2)); cy = np.full(len(fl), SRC[src]['h'] / 2)
    for f, a, b in zip(fl, cx, cy): f['cx'], f['cy'] = float(a), float(b)

def ease(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)

# zoom : base, spotlight +22 %, petit punch +7 % à chaque coupe
for f in frames:
    o = f['o']; z = o.get('z', 1.0)
    sp = o.get('spot')
    if sp:
        z *= 1 + 0.22 * ease((f['t'] - sp[1]) / 1.0) if f['t'] >= sp[1] else 1
    z *= 1 + 0.07 * max(0.0, 1 - (f['t'] - f['t0']) / 0.1)
    f['z'] = z

# le cercle du spotlight doit rester entièrement dans le cadre : on contraint le centre caméra
def _clamp_spot():
    for si in range(len(EDL)):
        o = EDL[si][5]; sp = o.get('spot')
        if not sp: continue
        fl = [f for f in frames if f['shot'] == si]; src = EDL[si][2]
        for _ in range(2):
            for f in fl:
                S = SRC[src]['s0'] * f['z']; n = sp[0]
                sx, sy = st(n, f['sf'], 'cx'), st(n, f['sf'], 'cy')
                r = 0.62 * math.hypot(st(n, f['sf'], 'w'), st(n, f['sf'], 'h')) * S + 24
                mx = max(0, (W / 2 - r - 14) / S); my = max(0, (H / 2 - r - 200) / S)
                f['cx'] = min(max(f['cx'], sx - mx), sx + mx); f['cy'] = min(max(f['cy'], sy - my), sy + my)
            if not o.get('freeze'):
                a = gaussian_filter1d(np.array([f['cx'] for f in fl]), 4, mode='nearest'); b = gaussian_filter1d(np.array([f['cy'] for f in fl]), 4, mode='nearest')
                for f, x, y in zip(fl, a, b): f['cx'], f['cy'] = float(x), float(y)
_clamp_spot()

def cam(f):
    s = SRC[f['src']]; S = s['s0'] * f['z']
    vw, vh = W / S, H / S
    cx = min(max(f['cx'], vw / 2), s['w'] - vw / 2); cy = min(max(f['cy'], vh / 2), s['h'] - vh / 2)
    return S, cx, cy
def to_stage(f, x, y):
    S, cx, cy = cam(f); return (x - cx) * S + W / 2, (y - cy) * S + H / 2

# vérifie que le zoom du spotlight ne sort pas un joueur étiqueté du cadre ; sinon pas de zoom sur ce plan
for si in range(len(EDL)):
    o = EDL[si][5]
    if not o.get('spot') or not o.get('tag'): continue
    fl = [f for f in frames if f['shot'] == si]; bad = False
    for f in fl:
        for (tn, who, a, b) in o['tag']:
            if a <= f['sf'] < b or (o.get('freeze') and f['sf'] == a):
                x, y = to_stage(f, st(tn, f['sf'], 'hx'), st(tn, f['sf'], 'hy'))
                if not (90 < x < W - 90 and 260 < y < H - 120): bad = True
    if bad:
        print('spot sans zoom sur plan', si)
        for f in fl:
            f['z'] = o.get('z', 1.0) * (1 + 0.07 * max(0.0, 1 - (f['t'] - f['t0']) / 0.1))

# ---- éléments ----
html_imgs = []; sets = []
# images source : un <img class="clip"> par image source (groupes d'images de sortie consécutives)
runs = []
for f in frames:
    if runs and runs[-1]['src'] == f['src'] and runs[-1]['sf'] == f['sf'] and runs[-1]['shot'] == f['shot']:
        runs[-1]['n1'] = f['n'] + 1
    else:
        runs.append(dict(src=f['src'], sf=f['sf'], shot=f['shot'], n0=f['n'], n1=f['n'] + 1))
for r in runs:
    s = SRC[r['src']]; st0 = r['n0'] / OUT_FPS - 0.25 / OUT_FPS; d = (r['n1'] - r['n0']) / OUT_FPS
    st0 = max(0, st0)
    html_imgs.append((r['src'], f'<img id="im{len(html_imgs)}" class="clip src" src="frames/{r["src"]}/{r["sf"]:04d}.jpg" data-start="{st0:.4f}" data-duration="{d:.4f}" style="width:{s["w"]}px;height:{s["h"]}px">'))

def fmt(v): return f'{v:.2f}'
# caméra par image
prev_src = None
for f in frames:
    S, cx, cy = cam(f); x = W / 2 - cx * S; y = H / 2 - cy * S
    lay = '#layA' if f['src'] == 'A' else '#layB'
    sets.append(f'[{fmt(f["t"])},"{lay}",{fmt(x)},{fmt(y)},{S:.4f}]')

# étiquettes porteur (flèche + nom + logo), image par image
tag_sets = {k: [] for k in NAMES}; tag_on = {k: [] for k in NAMES}
for f in frames:
    o = f['o']; shown = set()
    for (tn, who, a, b) in o.get('tag', []):
        if a <= f['sf'] < b or (o.get('freeze') and f['sf'] == a):
            hx, hy = st(tn, f['sf'], 'hx'), st(tn, f['sf'], 'hy')
            x, y = to_stage(f, hx, hy)
            if not (24 < x < W - 24 and 280 < y < H): continue
            bounce = 5 * abs(math.sin(2 * math.pi * 1.4 * f['t']))
            half = 200; dx = min(max(0.0, 16 + half - x), 0.0) if False else 0.0
            if x - half < 16: dx = 16 + half - x
            if x + half > W - 16: dx = W - 16 - half - x
            tag_sets[who].append(f'[{fmt(f["t"])},{fmt(x)},{fmt(y - bounce)},{fmt(dx)}]'); shown.add(who)
    for who in NAMES: tag_on[who].append((f['n'], (f['shot'] if who in shown else None)))

def intervals(lst):
    out = []; cur = None
    prev = None
    for n, on in lst:
        if cur is not None and on != prev: out.append((cur, n)); cur = None
        if on is not None and cur is None: cur = n
        prev = on
    if cur is not None: out.append((cur, lst[-1][0] + 1))
    return out

# spotlight
spot_sets = []; spot_iv = []
spots = {}
for si, (t0, t1, src, fin, fout, o) in enumerate(EDL):
    if o.get('spot'): spots.setdefault((o['spot'][0], o['spot'][1], o['spot'][2]), []).append(si)
for (name, ts, te), shots in spots.items():
    fl = [f for f in frames if f['shot'] in shots and ts <= f['t'] < te]
    if not fl: continue
    pts = []; R = 0
    for f in fl:
        S = cam(f)[0]; x, y = to_stage(f, st(name, f['sf'], 'cx'), st(name, f['sf'], 'cy'))
        r = 0.62 * math.hypot(st(name, f['sf'], 'w'), st(name, f['sf'], 'h')) * S + 24
        R = max(R, r); pts.append((f['t'], x, y))
    xs = gaussian_filter1d(np.array([p[1] for p in pts]), 1.5, mode='nearest'); ys = gaussian_filter1d(np.array([p[2] for p in pts]), 1.5, mode='nearest')
    R = min(R, 330)
    spot_iv.append((fl[0]['t'], fl[-1]['t'] + 1 / OUT_FPS, R))
    for (t, _, _), x, y in zip(pts, xs, ys): spot_sets.append(f'[{fmt(t)},{fmt(x)},{fmt(y)},{R:.1f}]')

# sous-titres : un mot à la fois
subs = []
for i, w in enumerate(WORDS):
    s = w['s']; e = WORDS[i + 1]['s'] if i + 1 < len(WORDS) and WORDS[i + 1]['s'] - w['e'] < 0.35 else w['e'] + 0.12
    txt = w['w'].strip('.,;').lower()
    if i == len(WORDS) - 1: e = DUR
    subs.append(f'<div id="w{i}" class="clip sub" data-start="{s:.3f}" data-duration="{max(0.06, e - s):.3f}">{txt}</div>')

# sons
aud = ['<audio class="clip" src="assets/voice.wav" data-start="0" data-duration="96.52" data-volume="0.78"></audio>']
k = 0
for si, (t0, *_r) in enumerate(EDL[1:], 1):
    nm = 'whoosh' if k % 2 == 0 else 'whoosh2'; k += 1
    aud.append(f'<audio class="clip" src="sfx/{nm}.wav" data-start="{max(0, t0 - 0.12):.3f}" data-duration="{0.38 if nm == "whoosh" else 0.28}" data-volume="0.24"></audio>')
for si, (t0, t1, src, fin, fout, o) in enumerate(EDL):
    if o.get('freeze'):
        aud.append(f'<audio class="clip" src="sfx/freeze.wav" data-start="{t0:.3f}" data-duration="0.45" data-volume="0.28"></audio>')
    for kf in o.get('kick', []):
        for f in frames:
            if f['shot'] == si and f['sf'] >= kf:
                aud.append(f'<audio class="clip" src="sfx/kick.wav" data-start="{f["t"]:.3f}" data-duration="0.25" data-volume="0.36"></audio>'); break
pops = []
for who in NAMES:
    for a, b in intervals(tag_on[who]):
        pops.append(a / OUT_FPS)
for a, b, R in spot_iv: pops.append(a)
for p in sorted(set(round(p, 3) for p in pops)):
    aud.append(f'<audio class="clip" src="sfx/pop.wav" data-start="{p:.3f}" data-duration="0.09" data-volume="0.24"></audio>')

tag_iv = {who: [(a / OUT_FPS, b / OUT_FPS) for a, b in intervals(tag_on[who])] for who in NAMES}
json.dump(dict(tag_iv=tag_iv, spot_iv=spot_iv, frames=[dict(t=f['t'], src=f['src'], sf=f['sf'], shot=f['shot'], cam=cam(f)) for f in frames], tags={w: tag_sets[w] for w in NAMES}, spots=spot_sets),
          open('analysis/plan.json', 'w'))

def tag_html(who):
    name, club = NAMES[who]
    return f'''<div class="tag" id="tag_{who}"><div class="tag-in">
  <div class="nl"><div class="logo"><img src="assets/logos/{club}.png"></div>
  <div class="name">{name}</div></div>
  <svg class="arrow" width="64" height="86" viewBox="0 0 64 86"><path d="M20 2 H44 V44 H62 L32 84 L2 44 H20 Z" fill="#ff1f1f" stroke="#3a0000" stroke-width="3" stroke-linejoin="round"/></svg>
</div></div>'''

imgsA = '\n'.join(h for s, h in html_imgs if s == 'A'); imgsB = '\n'.join(h for s, h in html_imgs if s == 'B')
html = f'''<!doctype html>
<html lang="es" data-resolution="portrait">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=1080, height=1920">
<script src="assets/gsap.min.js"></script>
<style>
@font-face {{ font-family: Poppins; font-weight: 500; src: url(assets/fonts/Poppins-Medium.ttf); }}
@font-face {{ font-family: Poppins; font-weight: 800; src: url(assets/fonts/Poppins-ExtraBold.ttf); }}
@font-face {{ font-family: Montserrat; font-weight: 800; src: url(assets/fonts/Montserrat-ExtraBold.ttf); }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#000; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#000; }}
.layer {{ position:absolute; left:0; top:0; transform-origin:0 0; }}
#layA {{ width:720px; height:960px; }} #layB {{ width:572px; height:626px; }}
.src {{ position:absolute; left:0; top:0; }}
#spot {{ position:absolute; left:0; top:0; width:4400px; height:4400px; margin:-2200px 0 0 -2200px; opacity:0;
  background:rgba(0,0,0,.58); backdrop-filter:blur(5px); -webkit-backdrop-filter:blur(5px);
  -webkit-mask-image:radial-gradient(circle at 50% 50%, transparent var(--r), #000 calc(var(--r) + 1.5px));
          mask-image:radial-gradient(circle at 50% 50%, transparent var(--r), #000 calc(var(--r) + 1.5px)); --r:200px; z-index:5; }}
#ring {{ position:absolute; left:0; top:0; border-radius:50%; border:5px solid #fff; opacity:0; z-index:6;
  box-shadow:0 0 14px 3px rgba(255,255,255,.55), inset 0 0 10px rgba(255,255,255,.35); }}
.tag {{ position:absolute; left:0; top:0; z-index:8; opacity:0; }}
.tag-in {{ position:absolute; left:0; bottom:0; transform:translateX(-50%); display:flex; flex-direction:column; align-items:center; transform-origin:50% 100%; }}
.nl {{ display:flex; flex-direction:column; align-items:center; }}
.logo {{ width:84px; height:84px; border-radius:50%; background:#fff; display:flex; align-items:center; justify-content:center; box-shadow:0 3px 8px rgba(0,0,0,.5); margin-bottom:8px; }}
.logo img {{ height:62px; }}
.name {{ font-family:Montserrat; font-weight:800; font-size:38px; color:#fff; background:rgba(15,15,20,.86); padding:6px 20px 8px; border-radius:16px; white-space:nowrap; margin-bottom:6px; }}
.arrow {{ display:block; filter:drop-shadow(0 3px 3px rgba(0,0,0,.55)); }}
.sub {{ position:absolute; left:0; width:1080px; top:1600px; text-align:center; font-family:Poppins; font-weight:500; font-size:46px; line-height:1.15;
  color:#fff; text-shadow:0 2px 4px rgba(0,0,0,.85); z-index:20; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
<div class="layer" id="layA">
{imgsA}
</div>
<div class="layer" id="layB">
{imgsB}
</div>
<div id="spot"></div><div id="ring"></div>
{tag_html('salah')}
{tag_html('trent')}
{chr(10).join(subs)}
{chr(10).join(aud)}
</div>
<script>
const CAM=[{",".join(sets)}];
const SPOT=[{",".join(spot_sets)}];
const SPOTIV={json.dumps(spot_iv)};
const TAG={json.dumps({w: [] for w in NAMES})};
{chr(10).join(f'TAG["{w}"]=[{",".join(tag_sets[w])}];' for w in NAMES)}
const TAGIV={json.dumps(tag_iv)};
const tl = gsap.timeline({{ paused: true }});
let cur=null;
for (const [t,sel,x,y,s] of CAM) {{
  if (sel!==cur) {{ tl.set(sel==="#layA"?"#layB":"#layA",{{opacity:0}},t); tl.set(sel,{{opacity:1}},t); cur=sel; }}
  tl.set(sel,{{x:x,y:y,scale:s}},t);
}}
for (const [t,x,y,r] of SPOT) {{
  tl.set("#spot",{{x:x,y:y,"--r":r+"px"}},t);
  tl.set("#ring",{{x:x-r,y:y-r,width:2*r,height:2*r}},t);
}}
for (const [a,b,r] of SPOTIV) {{
  tl.fromTo(["#spot","#ring"],{{opacity:0}},{{opacity:1,duration:0.25,ease:"none"}},a);
  tl.to(["#spot","#ring"],{{opacity:0,duration:0.25,ease:"none"}},Math.max(a+0.25,b-0.25));
}}
for (const w in TAG) {{
  for (const [t,x,y,dx] of TAG[w]) {{ tl.set("#tag_"+w,{{x:x,y:y}},t); tl.set("#tag_"+w+" .nl",{{x:dx}},t); }}
  for (const [a,b] of TAGIV[w]) {{
    tl.set("#tag_"+w,{{opacity:1}},a);
    tl.fromTo("#tag_"+w+" .tag-in",{{scale:0.2}},{{scale:1,duration:0.12,ease:"back.out(2)"}},a);
    tl.set("#tag_"+w,{{opacity:0}},b);
  }}
}}
tl.set("#root",{{opacity:1}},{DUR});
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = tl;
tl.seek(0);
</script>
</body>
</html>
'''
import re as _re
_c=[0]
def _aid(m): _c[0]+=1; return f'<audio id="au{_c[0]}" '
html=_re.sub(r'<audio ', _aid, html)
import os
open(os.environ.get('HF_OUT','index.html'), 'w').write(html)
print('images:', len(html_imgs), 'frames:', len(frames), 'spots:', spot_iv, 'tags:', tag_iv)
