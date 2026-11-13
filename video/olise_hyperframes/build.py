"""Builds the HyperFrames composition (index.html) + plan.json for the Olise video (Spanish)."""
import json, math, numpy as np, cv2
from scipy.ndimage import gaussian_filter1d

S = '/tmp/claude-0/-home-user-Fofana/adbce7f5-53e3-54dc-bd95-fa9317b2d1f9/scratchpad'
P = S + '/olise'
FPS = 30
SRC = 50.0
W = json.load(open(S + '/work/words.json'))
T = {k: {int(f): v for f, v in d.items()} for k, d in json.load(open(S + '/work/tracks.json')).items()}
DUR = 70.64
N = int(round(DUR * FPS))
w = lambda i: W[i]['start']
Y0MIN = 140
# measured TV graphics (source px): watermark top-right on both clips, score bug top-left on B
FORBID = {'A': [(1585, 0, 1890, 135)], 'B': [(1585, 0, 1890, 135), (0, 0, 590, 125)]}

# ---------- keeper B bbox from maroon blob (tracker drifts after the kick) ----------
def maroon_bb(clip, f, near):
    im = cv2.imread(f'{P}/assets/{clip}/{f:04d}.jpg').astype(int)
    B, G, R = im[..., 0], im[..., 1], im[..., 2]
    m = ((R > G + 35) & (R > B + 15) & (R < 230) & (G < 120)).astype(np.uint8)
    m[:300] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    best = min(range(1, n), key=lambda i: (np.hypot(cen[i][0] - near[0], cen[i][1] - near[1]) if st[i, 4] > 150 else 1e9))
    x, y, ww, hh, _ = st[best]
    return [int(x), int(y), int(ww), int(hh)], cen[best]
near = T['keeperB'][50]['bb'][0] + 20, T['keeperB'][50]['bb'][1] + 30
for f in range(50, 96):
    bb, c = maroon_bb('B', f, near); near = c
    x, y, ww, hh = bb
    T['keeperB'][f]['bb'] = [x - 14, y - 22, ww + 28, hh + 40]   # head above shirt + legs/boots below

# ---------- EDL ----------
# each: (t0, t1, clip, mode, a, speed_or_None, b, zoom, cam, tag)
segs = []
def play(t0, t1, clip, a, b, zoom, cam, tag=None, cut=True):
    segs.append(dict(t0=t0, t1=t1, clip=clip, mode='play', a=a, b=b, zoom=zoom, cam=cam, tag=tag, cut=cut))
def freeze(t0, t1, clip, f, zoom, cam, tag=None, cut=False, sfx=True):
    segs.append(dict(t0=t0, t1=t1, clip=clip, mode='freeze', a=f, b=f, zoom=zoom, cam=cam, tag=tag, cut=cut, fsfx=sfx))

ZW, ZR, ZC = 1.55, 1.16, 1.2
play(0, w(17), 'A', 590, 590 + 0.4 * SRC * w(17), ZR, 'oliseR', 'oliseR')               # S1 hook
play(w(17), w(43), 'A', 0, 78, ZW, 'keeperA', 'keeperA')                                  # S2
freeze(w(43), w(49), 'A', 78, ZW, 'keeperA', 'keeperA')                                   # S3
freeze(w(49), w(62), 'A', 78, 1.3, ('fixed', 1150, 470), 'keeperA', cut=True, sfx=False)  # S4a free space / Barella zone
freeze(w(62), w(72), 'A', 78, 1.25, ('fixed', 470, 640), 'keeperA', cut=True, sfx=False)  # S4b clear to the side
t_k = w(72) + 15 / SRC / 0.25
play(w(72), t_k, 'B', 50, 65, ZW, 'keeperB', 'keeperB')                                   # S5a
play(t_k, w(87), 'B', 65, 151, 1.4, ('keys', {65: (640, 520), 85: (760, 500), 110: (900, 480), 151: (1040, 460)}), None, cut=False)
play(w(87), w(96), 'A', 150, 215, ZW, ('keys', {150: (900, 420), 180: (950, 410), 215: (1160, 410)}))   # S6
t7 = w(96) + 35 / SRC / 0.35
play(w(96), t7, 'A', 215, 250, ZW, ('keys', {215: (1160, 410), 235: (1230, 410), 250: (1260, 380)}))    # S7a
freeze(t7, w(115), 'A', 250, ZW, 'oliseW', 'oliseW')                                      # S7b
t8 = w(115) + 60 / SRC / 0.5
play(w(115), t8, 'A', 420, 480, ZR, ('keys', {420: (560, 560), 450: (640, 550), 480: (740, 540)}))      # S8a reverse (Olise hidden by Barella)
play(t8, w(131), 'A', 250, 290, ZW, 'oliseW', 'oliseW')                                   # S8b
freeze(w(131), w(139), 'A', 290, ZW, 'oliseW', 'oliseW')                                  # S9
play(w(139), w(156), 'A', 500, 590, ZR, ('keys', {500: (900, 560), 540: (1050, 560), 590: (1000, 560)}))  # S10 (keeper spotlight)
t11 = w(156) + 25 / SRC / 0.25
play(w(156), t11, 'A', 590, 615, ZR, 'oliseR', 'oliseR')                                  # S11
freeze(t11, w(166), 'A', 615, ZR, 'oliseR', 'oliseR')
t12 = w(166) + 25 / SRC / 0.25
play(w(166), t12, 'A', 615, 640, ZR, 'oliseR', 'oliseR', cut=False)                       # S12
freeze(t12, w(182), 'A', 640, ZR, 'oliseR', 'oliseR')
t13 = w(182) + 15 / SRC / 0.25
play(w(182), t13, 'A', 290, 305, ZW, 'oliseW', 'oliseW')                                  # S13
freeze(t13, w(194), 'A', 305, ZW, 'oliseW', 'oliseW')
play(w(194), w(206), 'A', 640, 681, ZR, 'oliseR', 'oliseR')                               # S14 (shot on "remata")
play(w(206), w(215), 'A', 681, 759, ZR, ('keys', {681: (1000, 560), 700: (1000, 580), 720: (960, 600), 740: (820, 610), 759: (720, 610)}), None, cut=False)  # S15
play(w(215), DUR, 'B', 640, 640 + (DUR - w(215)) * SRC, 1.16, ('keys', {640: (1010, 470), 660: (1090, 470), 680: (1060, 470), 700: (1050, 470)}))  # S16 celebration
for i, s in enumerate(segs):
    if i: assert abs(s['t0'] - segs[i - 1]['t1']) < 1e-6
assert abs(segs[-1]['t1'] - DUR) < 1e-6

# tag visibility windows (source frames, inclusive)
TAGWIN = {'keeperA': (0, 80), 'keeperB': (50, 63), 'oliseW': (250, 312), 'oliseR': (590, 680)}
NAMES = {'keeperA': ('Gianluigi Donnarumma', 'italy'), 'keeperB': ('Gianluigi Donnarumma', 'italy'),
         'oliseW': ('Michael Olise', 'france'), 'oliseR': ('Michael Olise', 'france')}

# spotlights: (t0, t1, track)
SPOTS = [(w(3), 3.3, 'oliseR'), (w(20), 9.4, 'keeperA'), (w(74), 23.9, 'keeperB'), (w(111), w(115) - 0.08, 'oliseW'),
         (w(131), w(139) - 0.1, 'oliseW'), (w(146), w(156) - 0.15, 'keeperR'), (w(161), w(166) - 0.1, 'oliseR'),
         (w(190), w(194) - 0.1, 'oliseW')]

def seg_at(t):
    for s in segs:
        if s['t0'] <= t < s['t1']: return s
    return segs[-1]
def src_frame(s, t):
    if s['mode'] == 'freeze': return s['a']
    sp = (s['b'] - s['a']) / ((s['t1'] - s['t0']) * SRC)
    return int(min(s['b'], math.floor(s['a'] + (t - s['t0']) * sp * SRC + 1e-6)))

def body_center(tr, f):
    d = T[tr].get(f)
    if d is None:
        ks = sorted(T[tr]); f = min(ks, key=lambda k: abs(k - f)); d = T[tr][f]
    x, y, ww, hh = d['bb']
    return x + ww / 2, y + hh / 2, d

# ---------- per output frame ----------
frames = []
for i in range(N):
    t = i / FPS
    s = seg_at(t); f = src_frame(s, t)
    frames.append(dict(i=i, t=t, seg=segs.index(s), clip=s['clip'], f=f))

# camera targets per segment (smoothed within segment)
for si, s in enumerate(segs):
    idx = [fr['i'] for fr in frames if fr['seg'] == si]
    if not idx: continue
    cx = []; cy = []
    for i in idx:
        f = frames[i]['f']; cam = s['cam']; ch = 1080 / s['zoom']
        if isinstance(cam, str):
            hx, hy = (T[cam].get(f) or T[cam][min(T[cam], key=lambda k: abs(k - f))])['head']
            cx.append(hx); cy.append(hy + 0.17 * ch)
        elif cam[0] == 'fixed':
            cx.append(cam[1]); cy.append(cam[2])
        else:
            ks = sorted(cam[1]); cx.append(np.interp(f, ks, [cam[1][k][0] for k in ks])); cy.append(np.interp(f, ks, [cam[1][k][1] for k in ks]))
    cx = np.array(cx, float); cy = np.array(cy, float)
    if s['mode'] == 'play' and len(idx) > 3:
        sig = min(10, len(idx) / 3)
        cx = gaussian_filter1d(cx, sig, mode='nearest'); cy = gaussian_filter1d(cy, sig, mode='nearest')
    for k, i in enumerate(idx):
        frames[i]['cx'] = float(cx[k]); frames[i]['cy'] = float(cy[k]); frames[i]['z'] = s['zoom']

# spotlight geometry: constant radius (source px) = max needed over the spot
spot_frames = {}
for (a, b, tr) in SPOTS:
    ids = [fr['i'] for fr in frames if a <= fr['t'] < b]
    rs = []; cs = []
    for i in ids:
        x, y, d = body_center(tr, frames[i]['f'])
        bx, by, bw, bh = d['bb']
        rs.append(0.5 * math.hypot(bw, bh) + 12); cs.append((x, y))
    R = max(rs)
    cxs = gaussian_filter1d(np.array([c[0] for c in cs]), 2, mode='nearest'); cys = gaussian_filter1d(np.array([c[1] for c in cs]), 2, mode='nearest')
    for k, i in enumerate(ids):
        tt = frames[i]['t']
        e_in = min(1, (tt - a) / 0.25); e_out = min(1, (b - tt) / 0.25)
        op = max(0, min(e_in, e_out))
        zin = 0.5 - 0.5 * math.cos(math.pi * min(1, (tt - a) / 0.7))
        zz = min(zin, e_out)
        spot_frames[i] = dict(sx=float(cxs[k]), sy=float(cys[k]), R=R, op=op, zf=zz, tr=tr)

# apply punch zoom + spotlight zoom, clamp windows
cut_times = [s['t0'] for s in segs[1:] if s['cut']]
for fr in frames:
    z = fr['z']; cx, cy = fr['cx'], fr['cy']
    for ct in cut_times:
        if 0 <= fr['t'] - ct < 0.1: z *= 1 + 0.07 * (1 - (fr['t'] - ct) / 0.1)
    sp = spot_frames.get(fr['i'])
    if sp:
        k = sp['zf']; z *= 1 + 0.22 * k
        cx = cx + (sp['sx'] - cx) * 0.6 * k; cy = cy + (sp['sy'] - cy) * 0.6 * k
    ch = min(1080, 1080 / z); cw = ch * 9 / 16
    x0 = min(max(cx - cw / 2, 0), 1920 - cw); y0 = min(max(cy - ch / 2, 0), 1080 - ch)
    for (fx0, fy0, fx1, fy1) in FORBID[fr['clip']]:
        if x0 < fx1 and x0 + cw > fx0 and y0 < fy1:
            y0 = fy1 + 4
            if y0 + ch > 1080: ch = 1080 - y0; cw = ch * 9 / 16; x0 = min(max(cx - cw / 2, 0), 1920 - cw)
    # spotlight must not push a tagged player out: if spot player differs from tag player keep tag head inside
    fr.update(x0=x0, y0=y0, ch=ch, s=1920 / ch)

# tags
for fr in frames:
    s = segs[fr['seg']]; tr = s['tag']; fr['tag'] = None
    if tr and TAGWIN[tr][0] <= fr['f'] <= TAGWIN[tr][1] and fr['f'] in T[tr]:
        hx, hy = T[tr][fr['f']]['head']
        X = (hx - fr['x0']) * fr['s']; Y = (hy - fr['y0']) * fr['s']
        bounce = 5 * abs(math.sin(2 * math.pi * 1.4 * fr['t']))
        if 60 <= X <= 1020 and 330 <= Y <= 1880:
            fr['tag'] = dict(tr=tr, X=X, Y=Y - 6 - bounce, head=(X, Y))
for i, fr in enumerate(frames):
    sp = spot_frames.get(i)
    if sp:
        fr['spot'] = dict(X=(sp['sx'] - fr['x0']) * fr['s'], Y=(sp['sy'] - fr['y0']) * fr['s'], R=sp['R'] * fr['s'], op=sp['op'], tr=sp['tr'])
    else:
        fr['spot'] = None

# tag appearance events (pop sfx + pop animation)
tag_on = []
for i, fr in enumerate(frames):
    prev = frames[i - 1]['tag'] if i else None
    if fr['tag'] and (not prev or prev['tr'] != fr['tag']['tr'] or frames[i - 1]['seg'] != fr['seg'] and segs[fr['seg']]['cut']):
        tag_on.append(i)

# ---------- audio events ----------
sfx = []
WH = [166, 174, 168, 3115]; KICK = [2112, 2108, 2099]
DURS = {166: .7586, 174: .9937, 168: .8369, 3115: .5496, 1492: 1.3333, 3005: .1578, 2112: 1.4116, 2108: .9153, 2099: 1.5422}
for k, ct in enumerate(cut_times): sfx.append((ct - 0.12, WH[k % 4], 0.32))
for s in segs:
    if s['mode'] == 'freeze' and s.get('fsfx'): sfx.append((s['t0'], 1492, 0.42))
for i in tag_on: sfx.append((frames[i]['t'], 3005, 0.5))
sfx.append((w(17), 3005, 0.5))  # score banner pop
sfx.append((w(215), 3005, 0.55))  # score flip
def out_time_of(seg_i, src_f):
    s = segs[seg_i]; sp = (s['b'] - s['a']) / ((s['t1'] - s['t0']) * SRC)
    return s['t0'] + (src_f - s['a']) / (sp * SRC)
kicks = [out_time_of(0, 681), out_time_of(segs.index([s for s in segs if s['clip'] == 'B' and s['a'] == 50][0]), 64), w(206)]
for k, kt in enumerate(kicks): sfx.append((kt, KICK[k % 3], 0.6))
sfx = sorted((max(0, t), i, v) for t, i, v in sfx)

# ---------- HTML ----------
q = 1 / (4 * FPS)
def ts(t): return f'{max(0, t - q):.4f}'
imgs = []
i = 0
while i < N:
    j = i
    while j + 1 < N and frames[j + 1]['clip'] == frames[i]['clip'] and frames[j + 1]['f'] == frames[i]['f']: j += 1
    st = max(0, i / FPS - q); en = (j + 1) / FPS - q if j + 1 < N else DUR
    imgs.append(f'<img class="clip src" src="assets/{frames[i]["clip"]}/{frames[i]["f"]:04d}.jpg" data-start="{st:.4f}" data-duration="{en - st:.4f}" alt="">')
    i = j + 1

camk = [[round(fr['t'], 4), round(-fr['x0'] * fr['s'], 2), round(-fr['y0'] * fr['s'], 2), round(fr['s'], 5)] for fr in frames]
tagk = [[round(fr['t'], 4), round(fr['tag']['X'], 1), round(fr['tag']['Y'], 1), fr['tag']['tr']] if fr['tag'] else [round(fr['t'], 4), None] for fr in frames]
spk = [[round(fr['t'], 4), round(fr['spot']['X'], 1), round(fr['spot']['Y'], 1), round(fr['spot']['R'], 1), round(fr['spot']['op'], 3)] if fr['spot'] else [round(fr['t'], 4), None] for fr in frames]
words = [[x['start'], x['end'], x['text'].lower().strip('.,;:!?¿¡')] for x in W]
for k in range(len(words) - 1): words[k][1] = words[k + 1][0]
words[-1][1] = DUR
popk = [round(frames[i]['t'], 4) for i in tag_on]

audio = [f'<audio id="vo" class="clip" src="assets/voice.wav" data-start="0" data-duration="{DUR}" data-volume="0.86"></audio>']
for k, (t, sid, v) in enumerate(sfx):
    d = min(DURS[sid], DUR - t)
    audio.append(f'<audio id="sfx{k}" class="clip" src="assets/sfx/{sid}.mp3" data-start="{t:.4f}" data-duration="{d:.4f}" data-volume="{round(v*0.62,3)}"></audio>')

html = f'''<!doctype html>
<html lang="es" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="assets/gsap.min.js"></script>
<style>
@font-face {{ font-family: 'Poppins'; font-weight: 500; src: url(assets/fonts/poppins-500.woff2) format('woff2'); }}
@font-face {{ font-family: 'Poppins'; font-weight: 800; src: url(assets/fonts/poppins-800.woff2) format('woff2'); }}
@font-face {{ font-family: 'Montserrat'; font-weight: 800; src: url(assets/fonts/montserrat-800.woff2) format('woff2'); }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: #000; }}
#root {{ position: relative; width: 1080px; height: 1920px; overflow: hidden; background: #000; }}
#cam {{ position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; transform-origin: 0 0; }}
#cam img.src {{ position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; inset: auto; }}
#spot {{ position: absolute; inset: 0; width: 1080px; height: 1920px; opacity: 0; z-index: 5;
  background: rgba(0,0,0,.58); -webkit-backdrop-filter: blur(5px); backdrop-filter: blur(5px);
  --x: 540px; --y: 900px; --r: 200px;
  -webkit-mask-image: radial-gradient(circle var(--r) at var(--x) var(--y), transparent 0, transparent calc(var(--r) - 1px), #000 var(--r));
  mask-image: radial-gradient(circle var(--r) at var(--x) var(--y), transparent 0, transparent calc(var(--r) - 1px), #000 var(--r)); }}
#ring {{ position: absolute; left: 0; top: 0; width: 400px; height: 400px; border-radius: 50%; border: 5px solid #fff; z-index: 6; opacity: 0;
  box-shadow: 0 0 14px rgba(255,255,255,.55), inset 0 0 10px rgba(255,255,255,.25); }}
#tagw {{ position: absolute; left: 0; top: 0; width: 0; height: 0; z-index: 8; opacity: 0; }}
.tag {{ position: absolute; left: 0; bottom: 0; transform: translateX(-50%); display: flex; flex-direction: column; align-items: center; transform-origin: 50% 100%; }}
.tag .logo {{ width: 84px; height: 84px; border-radius: 50%; background: #fff; display: flex; align-items: center; justify-content: center; box-shadow: 0 3px 8px rgba(0,0,0,.5); overflow: hidden; }}
.tag .logo img {{ max-width: 62px; max-height: 66px; }}
.tag .logo.fr img {{ max-width: 84px; max-height: 84px; width: 84px; height: 84px; object-fit: cover; border-radius: 50%; }}
.tag .name {{ margin-top: 8px; font-family: 'Montserrat'; font-weight: 800; font-size: 38px; color: #fff; white-space: nowrap; background: rgba(12,12,16,.88); padding: 6px 18px 8px; border-radius: 14px; line-height: 1.1; }}
.tag svg {{ margin-top: 8px; display: block; filter: drop-shadow(0 3px 3px rgba(0,0,0,.45)); }}
#banner {{ position: absolute; top: 150px; left: 50%; transform: translateX(-50%); z-index: 9; display: flex; align-items: center; gap: 0; opacity: 0;
  font-family: 'Poppins'; font-weight: 800; font-size: 44px; color: #fff; filter: drop-shadow(0 4px 10px rgba(0,0,0,.6)); }}
#banner .team {{ background: #111; padding: 10px 22px; }}
#banner .score {{ background: #e3121b; padding: 10px 22px; display: flex; align-items: center; gap: 12px; perspective: 400px; }}
#banner .digit {{ display: inline-block; min-width: 30px; text-align: center; position: relative; }}
#banner .min {{ background: #fff; color: #111; padding: 10px 16px; font-size: 36px; }}
#sub {{ position: absolute; left: 0; width: 1080px; top: 1600px; text-align: center; z-index: 20; font-family: 'Poppins'; font-weight: 500; font-size: 46px; color: #fff;
  text-shadow: 0 2px 4px rgba(0,0,0,.85); line-height: 1.15; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{DUR}" data-width="1080" data-height="1920">
  <div id="cam">
    {chr(10).join(imgs)}
  </div>
  <div id="spot"></div>
  <div id="ring"></div>
  <div id="tagw">
    <div class="tag" id="tag-italy" style="opacity:0"><div class="logo"><img src="assets/logos/italy.svg" alt=""></div><div class="name">Gianluigi Donnarumma</div>
      <svg width="64" height="86" viewBox="0 0 64 86"><path d="M20 2 H44 V46 H62 L32 84 L2 46 H20 Z" fill="#ff1f1f" stroke="#3a0000" stroke-width="3" stroke-linejoin="round"/></svg></div>
    <div class="tag" id="tag-france" style="opacity:0"><div class="logo fr"><img src="assets/logos/france.png" alt=""></div><div class="name">Michael Olise</div>
      <svg width="64" height="86" viewBox="0 0 64 86"><path d="M20 2 H44 V46 H62 L32 84 L2 46 H20 Z" fill="#ff1f1f" stroke="#3a0000" stroke-width="3" stroke-linejoin="round"/></svg></div>
  </div>
  <div id="banner"><span class="team">ITA</span><span class="score"><span class="digit" id="d1">0</span><span>–</span><span class="digit" id="d2">0</span></span><span class="team">FRA</span><span class="min">10'</span></div>
  <div id="sub"></div>
  {chr(10).join(audio)}
</div>
<script>
const CAM = {json.dumps(camk)};
const TAG = {json.dumps(tagk)};
const SPOT = {json.dumps(spk)};
const WORDS = {json.dumps(words, ensure_ascii=False)};
const POPS = {json.dumps(popk)};
const Q = {q};
const tl = gsap.timeline({{ paused: true }});
const at = t => Math.max(0, t - Q);
const cam = document.getElementById('cam'), tagw = document.getElementById('tagw'), spot = document.getElementById('spot'), ring = document.getElementById('ring');
const tags = {{ italy: document.getElementById('tag-italy'), france: document.getElementById('tag-france') }};
const which = tr => tr.startsWith('keeper') ? 'italy' : 'france';
gsap.set(cam, {{ transformOrigin: '0 0' }});
let lastTag = null, lastSpot = false;
for (let k = 0; k < CAM.length; k++) {{
  const [t, x, y, s] = CAM[k];
  tl.set(cam, {{ x, y, scale: s }}, at(t));
  const g = TAG[k];
  if (g[1] === null) {{ if (lastTag !== null) {{ tl.set(tagw, {{ opacity: 0 }}, at(t)); lastTag = null; }} }}
  else {{
    const w = which(g[3]);
    if (lastTag !== w) {{ tl.set(tags.italy, {{ opacity: w === 'italy' ? 1 : 0 }}, at(t)); tl.set(tags.france, {{ opacity: w === 'france' ? 1 : 0 }}, at(t)); }}
    tl.set(tagw, {{ opacity: 1, x: g[1], y: g[2] }}, at(t)); lastTag = w;
  }}
  const p = SPOT[k];
  if (p[1] === null) {{ if (lastSpot) {{ tl.set([spot, ring], {{ opacity: 0 }}, at(t)); lastSpot = false; }} }}
  else {{
    tl.set(spot, {{ opacity: p[4], '--x': p[1] + 'px', '--y': p[2] + 'px', '--r': p[3] + 'px' }}, at(t));
    tl.set(ring, {{ opacity: p[4], x: p[1] - p[3], y: p[2] - p[3], width: 2 * p[3], height: 2 * p[3] }}, at(t));
    lastSpot = true;
  }}
}}
// pop-in of the carrier label (0.12 s)
for (const t of POPS) {{
  for (const el of [tags.italy, tags.france]) tl.fromTo(el, {{ scale: 0.2 }}, {{ scale: 1, duration: 0.12, ease: 'back.out(2.2)', immediateRender: false }}, at(t));
}}
// subtitles: one word at a time
const sub = document.getElementById('sub');
for (const [a, b, txt] of WORDS) {{ tl.set(sub, {{ textContent: txt }}, at(a)); }}
tl.set(sub, {{ textContent: '' }}, 0);
tl.set(sub, {{ textContent: WORDS[0][2] }}, at(WORDS[0][0]));
// score banner: pops in on the context, digit flips on "gol"
const banner = document.getElementById('banner');
tl.fromTo(banner, {{ opacity: 0, scale: 0.6 }}, {{ opacity: 1, scale: 1, duration: 0.12, ease: 'back.out(2)', immediateRender: false }}, at({w(17)}));
const d2 = document.getElementById('d2');
tl.to(d2, {{ rotationX: 90, duration: 0.12, ease: 'power2.in' }}, at({w(215)}));
tl.set(d2, {{ textContent: '1' }}, at({w(215)}) + 0.12);
tl.fromTo(d2, {{ rotationX: -90 }}, {{ rotationX: 0, duration: 0.14, ease: 'power2.out', immediateRender: false }}, at({w(215)}) + 0.12);
tl.set({{}}, {{}}, {DUR});
window.__timelines = window.__timelines || {{}};
window.__timelines['main'] = tl;
tl.seek(0);
</script>
</body>
</html>
'''
open(P + '/index.html', 'w').write(html)
json.dump(dict(frames=frames, segs=segs, sfx=sfx, tag_on=tag_on, spots=SPOTS, kicks=kicks), open(S + '/work/plan.json', 'w'), default=float)
print('frames', N, 'imgs', len(imgs), 'segs', len(segs), 'sfx', len(sfx), 'tag_on', [round(frames[i]['t'], 2) for i in tag_on], 'kicks', [round(k, 2) for k in kicks])
