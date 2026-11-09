#!/usr/bin/env python3
"""Build the HyperFrames composition (index.html + data.js + frames) for the Giuliano goal analysis.
All analysis data (tracks, events) was measured on the 50 fps sources."""
import json, os, math, shutil, cv2, numpy as np

S = os.path.dirname(os.path.abspath(__file__)) + '/..'
W = S + '/work'
P = S + '/gol'
FPS = 30
DUR = 77.6
N = int(round(DUR * FPS))
BAND_Y0, BAND_Y1 = 176, 899           # TV scoreboard ends y=170, watermark starts y=905
BAND_H = BAND_Y1 - BAND_Y0             # 723
SRCDIR = {'A': W + '/fa', 'B': W + '/fb'}

# ---------------------------------------------------------------- tracks (head top, source px)
def load(n):
    return {int(k): tuple(v) for k, v in json.load(open(f'{W}/{n}.json')).items()}
def lin(kf):
    kf = sorted(kf); d = {}
    for (f0, x0, y0), (f1, x1, y1) in zip(kf, kf[1:]):
        for f in range(f0, f1 + 1):
            w = (f - f0) / (f1 - f0); d[f] = (x0 + w * (x1 - x0), y0 + w * (y1 - y0))
    return d
TR = {
    'lee': ('A', load('tLee')),
    'alv': ('A', {**{192: (369, 632)}, **load('tAlv')}),
    'giu': ('A', load('tGiu')),
    'llo': ('A', {1: (621, 304)}),
    'giuB': ('B', lin([(875, 1640, 640), (880, 1588, 625), (886, 1500, 625), (890, 1456, 625), (894, 1463, 632),
                      (898, 1419, 632), (902, 1404, 640), (906, 1390, 625), (910, 1397, 632), (916, 1390, 632),
                      (922, 1353, 618), (935, 1320, 620)])),
}
PLAYER = {'lee': ('Kang-in Lee', 'atm'), 'alv': ('Julián Álvarez', 'atm'), 'giu': ('Giuliano Simeone', 'atm'),
          'giuB': ('Giuliano Simeone', 'atm'), 'llo': ('Marcos Llorente', 'atm')}

# ---------------------------------------------------------------- EDL: (t0, t1, clip, f0, f1)
SEG = [
    (0.00, 4.35, 'B', 1030, 1150),    # hook: behind-the-net replay, keeper beaten
    (4.35, 7.32, 'A', 440, 500),      # hook: wide, pass -> first-time shot -> net
    (7.32, 11.14, 'A', 554, 744),     # celebration x1
    (11.14, 13.11, 'A', 1, 1),        # freeze: Llorente
    (13.11, 17.32, 'A', 1, 84),       # Llorente's ball in behind to Lee
    (17.32, 25.66, 'A', 84, 192),     # Lee carries on the counter
    (25.66, 31.56, 'A', 192, 192),    # freeze: Lee looks up, Álvarez runs in behind
    (31.56, 35.87, 'A', 160, 202),    # trivela (contact f202 on "trivela")
    (35.87, 37.48, 'A', 202, 285),    # ball flight to Álvarez
    (37.48, 42.06, 'A', 285, 360),    # Álvarez controls, faces his defender
    (42.06, 51.30, 'A', 360, 360),    # freeze: everyone expected a pass
    (51.30, 57.12, 'A', 360, 420),    # Álvarez takes the defender on
    (57.12, 65.04, 'A', 420, 420),    # freeze: head up, Giuliano alone
    (65.04, 65.95, 'A', 420, 428),    # the pass (contact f428 on "envía")
    (65.95, 68.58, 'A', 428, 450),
    (68.58, 70.97, 'B', 860, 899),    # other angle: first-time finish (contact f899 on "rematar")
    (70.97, 72.58, 'B', 899, 935),
    (72.58, 74.86, 'A', 440, 456),    # wide: no control needed (contact f456 on "para")
    (74.86, 77.60, 'A', 456, 525),    # into the net
]
FREEZE_T = [s[0] for s in SEG if s[3] == s[4]]
CUTS = [s[0] for s in SEG[1:] if not any(abs(s[0] - p[1]) < 1e-6 and p[2] == s[2] and p[4] == s[3] for p in SEG)]
CONTACTS = [('A', 202), ('A', 428), ('B', 899), ('A', 456)]

def src_at(t):
    for s in SEG:
        if s[0] - 1e-9 <= t < s[1] or (s is SEG[-1] and t <= s[1]):
            t0, t1, c, f0, f1 = s
            f = f0 if f0 == f1 else int(round(f0 + (t - t0) / (t1 - t0) * (f1 - f0)))
            return SEG.index(s), c, f
    raise ValueError(t)

# ---------------------------------------------------------------- camera keyframes per segment (t, cx, cy, z)
def head(tr, f):
    d = TR[tr][1]
    if f in d: return d[f]
    return d[min(d, key=lambda q: abs(q - f))]

def cam_target(i, c, f, t):
    """returns cx, cy, z in source coords"""
    if i == 0:   # behind the net: keeper + ball
        return (np.interp(f, [1030, 1100, 1150], [930, 1000, 1080]), 640, 1.0)
    if i == 1:
        if f <= 446: x, y = head('alv', 428) if f >= 428 else (540, 640); return (np.interp(f, [440, 446], [700, 760]), 600, 1.0)
        return (np.interp(f, [446, 456, 470, 500], [760, 760, 600, 520]), np.interp(f, [446, 470, 500], [560, 520, 520]), 1.0)
    if i == 2:   # celebration faces
        x = np.interp(f, [554, 580, 610, 640, 668, 680, 690, 715, 744], [900, 1250, 1270, 1373, 1212, 1100, 1050, 909, 909])
        y = np.interp(f, [554, 640, 668, 680, 744], [560, 560, 560, 600, 640])
        return (x, y, 1.0)
    if i == 3:
        x, y = head('llo', 1); return (x, y + 120, 1.25)
    if i == 4:
        # follow the ball from Llorente to Lee
        bx = np.interp(f, [1, 20, 45, 84], [600, 500, 360, 375]); return (bx, 400, 1.25)
    if i in (5,):
        x, y = head('lee', f); return (x, y + 110, 1.25)
    if i == 6:   # freeze f192: Lee, then both Lee and Álvarez
        lx, ly = head('lee', 192); ax, ay = head('alv', 192)
        w = np.clip((t - 27.0) / 1.0, 0, 1); w = w * w * (3 - 2 * w)
        return ((1 - w) * lx + w * (lx + ax) / 2, (1 - w) * (ly + 110) + w * 540, 1.25 - 0.25 * w)
    if i == 7:
        x, y = head('lee', f); return (x, y + 110, 1.25)
    if i == 8:
        x = np.interp(f, [202, 221, 241, 261, 285], [690, 578, 502, 470, 470]); y = np.interp(f, [202, 241, 285], [430, 500, 600])
        return (x, y, 1.15)
    if i in (9, 11, 13, 14):
        if i == 14:
            ax, ay = head('alv', 428); gx, gy = head('giu', f)
            w = np.clip((f - 428) / 18, 0, 1); w = w * w * (3 - 2 * w)
            return ((1 - w) * (ax + 30) + w * gx, (1 - w) * (ay + 40) + w * (gy + 60), 1.25)
        x, y = head('alv', f); return (x + 30, y + 40, 1.25)
    if i == 10:  # freeze f360: Álvarez, then pan right to the players outside the box, then back
        ax, ay = head('alv', 360)
        w = np.interp(t, [42.06, 46.0, 47.0, 50.2, 51.3], [0, 0, 1, 1, 1]); w = w * w * (3 - 2 * w)
        return ((1 - w) * (ax + 30) + w * 1380, (1 - w) * (ay + 40) + w * 520, 1.0 + 0.25 * (1 - w))
    if i == 12:  # freeze f420: Álvarez, then Giuliano
        ax, ay = head('alv', 420); gx, gy = head('giu', 420)
        w = np.interp(t, [57.12, 58.3, 59.15, 65.04], [0, 0, 1, 1]); w = w * w * (3 - 2 * w)
        return ((1 - w) * (ax + 30) + w * gx, (1 - w) * (ay + 40) + w * (gy + 60), 1.25)
    if i in (15, 16):
        x = np.interp(f, [860, 872, 880, 890, 910, 935], [1250, 1520, 1520, 1460, 1400, 1330]); return (x, 600, 1.0)
    if i == 17:
        x, y = head('giu', f) if f >= 440 else head('giu', 440); return (x - 60, y + 70, 1.15)
    if i == 18:
        x = np.interp(f, [456, 470, 490, 525], [760, 600, 560, 560]); y = np.interp(f, [456, 480, 525], [520, 520, 540])
        return (x, y, 1.15)
    raise ValueError(i)

# ---------------------------------------------------------------- tags: per segment, which track is the carrier
# (seg index -> (track, first_frame, pass_frame)); the tag disappears ON the pass/shot frame.
TAGS = {3: ('llo', 1, 2), 5: ('lee', 85, 202), 6: ('lee', 85, 202), 7: ('lee', 85, 202),
        9: ('alv', 338, 428), 10: ('alv', 338, 428), 11: ('alv', 338, 428), 12: ('alv', 338, 428), 13: ('alv', 338, 428),
        14: ('giu', 444, 456), 15: ('giuB', 875, 899), 16: ('giuB', 875, 899), 17: ('giu', 440, 456)}
TAG_HIDE = [(59.0, 65.04)]   # freeze 57-65: camera leaves the carrier to show Giuliano

# ---------------------------------------------------------------- spotlights (t0, t1, track)  start on the naming word
SPOTS = [(12.29, 13.11, 'llo'), (15.41, 17.32, 'lee'), (27.71, 31.40, 'alv'), (51.63, 54.60, 'alv'),
         (59.23, 64.80, 'giu'), (69.50, 72.50, 'giuB')]

def grass(im):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); h, s, v = cv2.split(hsv)
    return (h >= 30) & (h <= 58) & (s > 60) & (v > 70)

_img = {}
def img(c, f):
    k = (c, f)
    if k not in _img: _img[k] = cv2.imread(f'{SRCDIR[c]}/{f:04d}.jpg')
    return _img[k]

def body_box(c, f, hx, hy, big):
    """bbox of the full silhouette (non-grass pixels connected to the torso) below the head top."""
    if big:   # close-up in front of the ad boards: grass segmentation is meaningless, use the measured body envelope
        return (hx - 105, hy - 6, hx + 105, hy + 285)
    bw, bh = (230, 330) if big else (48, 92)
    im = img(c, f); x0, y0 = int(hx - bw), int(hy - 10); x1, y1 = int(hx + bw), int(hy + bh)
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(1920, x1), min(1080, y1)
    m = (~grass(im[y0:y1, x0:x1])).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    seeds = [(int(hx - x0), int(hy - y0 + k)) for k in ((6, 15, 30, 60) if not big else (20, 60, 120, 200))]
    ids = set()
    for sx, sy in seeds:
        if 0 <= sy < m.shape[0] and 0 <= sx < m.shape[1] and lab[sy, sx] > 0: ids.add(lab[sy, sx])
    if not ids:
        return (hx - 18, hy, hx + 18, hy + (70 if not big else 290))
    xs0 = min(st[i][0] for i in ids); ys0 = min(st[i][1] for i in ids)
    xs1 = max(st[i][0] + st[i][2] for i in ids); ys1 = max(st[i][1] + st[i][3] for i in ids)
    bx0, by0, bx1, by1 = x0 + xs0, y0 + ys0, x0 + xs1, y0 + ys1
    # a player's silhouette never exceeds this envelope; anything beyond is an ad board / another player merged in
    return (max(bx0, hx - 34), max(by0, hy - 4), min(bx1, hx + 34), min(by1, hy + 78))

# ---------------------------------------------------------------- per output frame computation
frames = []
for k in range(N):
    t = k / FPS + 1e-4
    i, c, f = src_at(t)
    frames.append((t, i, c, f))

# raw camera
raw = np.array([cam_target(i, c, f, t) for t, i, c, f in frames], float)
# gaussian smoothing (sigma 10 frames) inside each segment; freeze frames already deterministic
cam = raw.copy()
seg_ids = np.array([fr[1] for fr in frames])
g = np.exp(-0.5 * (np.arange(-30, 31) / 10.0) ** 2)
for s in range(len(SEG)):
    idx = np.where(seg_ids == s)[0]
    if len(idx) < 3: continue
    for j in range(3):
        v = raw[idx, j]; pad = np.pad(v, 30, mode='edge')
        cam[idx, j] = np.convolve(pad, g / g.sum(), mode='same')[30:-30]

# spotlight geometry (source coords) per frame
spot = [None] * N
for (t0, t1, tr) in SPOTS:
    ks = [k for k in range(N) if t0 - 0.25 <= frames[k][0] < t1 + 0.25]
    big = tr == 'giuB'
    boxes = {}
    for k in ks:
        t, i, c, f = frames[k]
        if TR[tr][0] != c: continue
        hx, hy = head(tr, f)
        boxes[k] = body_box(c, f, hx, hy, big)
    if not boxes: continue
    cx = {k: (b[0] + b[2]) / 2 for k, b in boxes.items()}; cy = {k: (b[1] + b[3]) / 2 for k, b in boxes.items()}
    margin = 8 if big else 9
    r = max(math.hypot(b[2] - b[0], b[3] - b[1]) / 2 + margin for b in boxes.values())
    kk = sorted(boxes)
    sx = np.convolve(np.pad([cx[k] for k in kk], 3, mode='edge'), np.ones(7) / 7, mode='same')[3:-3]
    sy = np.convolve(np.pad([cy[k] for k in kk], 3, mode='edge'), np.ones(7) / 7, mode='same')[3:-3]
    for j, k in enumerate(kk):
        t = frames[k][0]
        a = np.clip(min((t - t0) / 0.25 + 1.0, (t1 - t) / 0.25 + 1.0), 0, 1) if t < t0 else np.clip(min(1, (t1 + 0.25 - t) / 0.25), 0, 1)
        a = float(np.clip(min((t - (t0)) / 0.25, (t1 + 0.25 - t) / 0.25, 1), 0, 1))
        spot[k] = (float(sx[j]), float(sy[j]), float(r), a, tr, t0, t1)

def window(cx, cy, z):
    H = BAND_H / z; Wd = H * 9 / 16
    x0 = min(max(cx - Wd / 2, 0), 1920 - Wd); y0 = min(max(cy - H / 2, BAND_Y0), BAND_Y1 - H)
    return x0, y0, H

# tag visibility per frame
def tag_at(k):
    t, i, c, f = frames[k]
    if i not in TAGS: return None
    tr, fa, fp = TAGS[i]
    if any(a <= t < b for a, b in TAG_HIDE): return None
    if not (fa <= f < fp): return None
    if TR[tr][0] != c: return None
    return tr, head(tr, f)

# final camera with cut punch (+7%, back in 0.1 s) and spotlight zoom (+22%, never pushing the tagged player out)
out = []
cut_ts = [s[0] for s in SEG[1:]]
zoom_ok = {}
for (t0, t1, tr) in SPOTS:
    ok = True
    for k in range(N):
        t = frames[k][0]
        if not (t0 <= t < t1) or spot[k] is None: continue
        tg = tag_at(k)
        cx, cy, z = cam[k]; sxx, syy = spot[k][0], spot[k][1]
        x0, y0, H = window(cx + (sxx - cx) * 0.6, cy + (syy - cy) * 0.6, z * 1.22)
        Wd = H * 9 / 16
        for px, py, pr in ([(tg[1][0], tg[1][1], 40)] if tg else []) + [(sxx, syy, spot[k][2])]:
            if not (x0 + pr * 0.3 <= px <= x0 + Wd - pr * 0.3 and y0 <= py - 0 <= y0 + H):
                ok = False
    zoom_ok[(t0, t1, tr)] = ok and tr != 'giuB'   # close-up: the ring already fills the width

for k in range(N):
    t, i, c, f = frames[k]
    cx, cy, z = cam[k]
    sp = spot[k]
    if sp is not None and zoom_ok[(sp[5], sp[6], sp[4])]:
        p = np.clip((t - sp[5]) / max(0.6, (sp[6] - sp[5]) * 0.6), 0, 1); p = p * p * (3 - 2 * p)
        fade = np.clip((sp[6] + 0.25 - t) / 0.5, 0, 1)
        e = p * fade
        cx += (sp[0] - cx) * 0.6 * e; cy += (sp[1] - cy) * 0.6 * e; z *= 1 + 0.22 * e
    # cut punch
    for ct in cut_ts:
        if 0 <= t - ct < 0.1:
            z *= 1 + 0.07 * (1 - (t - ct) / 0.1)
    x0, y0, H = window(cx, cy, z)
    sc = 1920 / H
    o = {'s': [c, f], 'cam': [round(x0, 2), round(y0, 2), round(sc, 5)]}
    tg = tag_at(k)
    if tg:
        tr, (hx, hy) = tg
        o['tag'] = [tr, round((hx - x0) * sc, 1), round((hy - y0) * sc, 1)]
    if sp is not None and sp[3] > 0:
        o['sp'] = [round((sp[0] - x0) * sc, 1), round((sp[1] - y0) * sc, 1), round(sp[2] * sc, 1), round(sp[3], 3)]
    out.append(o)

# tag pop start times (start of each continuous run of the same tag)
prev = None
for k, o in enumerate(out):
    cur = o['tag'][0] if 'tag' in o else None
    if cur and cur != prev:
        o['pop'] = 1
    prev = cur

# subtitles: one word at a time from the script (words.json)
words = json.load(open(f'{W}/words.json'))
wl = []
for w in words:
    txt = w['text'].lower().strip('.,;:!?¡¿')
    wl.append([round(w['start'], 3), round(w['end'], 3), txt])
for j in range(len(wl) - 1):   # keep each word on screen until the next one starts (max +0.35 s)
    wl[j][1] = round(min(wl[j + 1][0], wl[j][1] + 0.35), 3)

# ---------------------------------------------------------------- images: one <img class="clip"> per run of identical source frame
runs = []
for k, (t, i, c, f) in enumerate(frames):
    if runs and runs[-1][1] == c and runs[-1][2] == f and runs[-1][3] == i:
        runs[-1][4] += 1
    else:
        runs.append([k, c, f, i, 1])
os.makedirs(P + '/frames', exist_ok=True)
for fn in os.listdir(P + '/frames'): os.remove(P + '/frames/' + fn)
imgs = []
for (k0, c, f, i, n) in runs:
    name = f'{c.lower()}{f:04d}.jpg'
    dst = P + '/frames/' + name
    if not os.path.exists(dst): os.link(f'{SRCDIR[c]}/{f:04d}.jpg', dst)
    start = max(0.0, k0 / FPS - 1 / (4 * FPS))
    dur = (k0 + n) / FPS - start - 1 / (4 * FPS) if k0 + n < N else DUR - start
    imgs.append(f'<img class="clip src" src="frames/{name}" data-start="{start:.4f}" data-duration="{dur:.4f}" alt="">')

# ---------------------------------------------------------------- sounds
snd = []
def add(src, t, dur, vol):
    snd.append(f'<audio id="a{len(snd)}" src="assets/sfx/{src}.wav" data-start="{max(0,t):.3f}" data-duration="{dur:.3f}" data-volume="{vol*0.88:.3f}"></audio>')
for j, ct in enumerate(cut_ts):
    if ct in FREEZE_T: continue
    wi=[1, 2, 3, 4][j % 4]; add(f'whoosh{wi}', ct - 0.12, [0.38, 0.32, 0.42, 0.30][wi - 1], 0.22)
for ft in FREEZE_T:
    add('freeze', ft, 0.45, 0.35)
# pops: each tag appearance + score banner
for k, o in enumerate(out):
    if o.get('pop'): add('pop', k / FPS, 0.12, 0.30)
BANNER_T, FLIP_T = 74.86, 76.70
add('pop', BANNER_T, 0.12, 0.30); add('pop', FLIP_T, 0.12, 0.30)
# ball strikes: on the output frame that shows the contact image
kick_ts = []
for k, (t, i, c, f) in enumerate(frames):
    if (c, f) in CONTACTS and (k == 0 or frames[k - 1][2:] != (c, f)):
        kick_ts.append(k / FPS)
for j, kt in enumerate(kick_ts):
    add(f'kick{j % 3 + 1}', kt, 0.25, 0.45)

meta = {'N': N, 'FPS': FPS, 'frames': out, 'words': wl, 'banner': BANNER_T, 'flip': FLIP_T,
        'names': {k: v[0] for k, v in PLAYER.items()}, 'logos': {k: v[1] for k, v in PLAYER.items()}}
open(P + '/data.js', 'w').write('window.GOL=' + json.dumps(meta, ensure_ascii=False, separators=(',', ':')) + ';')
json.dump({'cuts': cut_ts, 'freezes': FREEZE_T, 'kicks': kick_ts, 'zoom_ok': {f'{a}-{b}-{c}': v for (a, b, c), v in zoom_ok.items()},
           'segments': SEG}, open(W + '/build_info.json', 'w'), indent=1)

tpl = open(S + '/scripts/template.html').read()
html = tpl.replace('%%IMGS%%', '\n      '.join(imgs)).replace('%%AUDIO%%', '\n    '.join(snd)).replace('%%DUR%%', f'{DUR}')
open(P + '/index.html', 'w').write(html)
print('frames', N, 'imgs', len(imgs), 'sounds', len(snd), 'kicks', kick_ts)
print('zoom_ok', zoom_ok)
