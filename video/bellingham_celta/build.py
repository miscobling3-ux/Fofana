"""Génère hf/gol/index.html (composition HyperFrames) + plan.json pour l'analyse du but de Bellingham.
Source : clip 1920x1080 @50 i/s, une image JPEG par image source. Sortie 1080x1920 @30 i/s."""
import json, math, re, unicodedata
import numpy as np

S = '/tmp/claude-0/-home-user-Fofana/9ccd27b4-b15c-5bb0-8040-d62d7f187762/scratchpad'
FPS = 30
W_OUT, H_OUT = 1080, 1920
words = json.load(open(f'{S}/voice/words.json'))
DUR = round(78.943 + 0.06, 3)
NOUT = int(math.ceil(DUR * FPS))

# ---------------------------------------------------------------- word helpers
def norm(s):
    s = unicodedata.normalize('NFD', s.lower())
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in s if unicodedata.category(c) != 'Mn'))

def wt(seq, after=0.0, end=False):
    """time of the first word sequence `seq` (space separated) starting after `after`."""
    toks = [norm(t) for t in seq.split()]
    for i in range(len(words) - len(toks) + 1):
        if words[i]['s'] + 1e-6 < after: continue
        if all(norm(words[i + k]['w']) == toks[k] for k in range(len(toks))):
            return words[i + len(toks) - 1]['e'] if end else words[i]['s']
    raise KeyError(seq)

# ---------------------------------------------------------------- EDL  (t0, t1, f0, f1)
SEG = [
    (0.00, 4.66, 222, 280),   # accroche : le geste au ralenti
    (4.66, 8.82, 0, 77),      # contexte : course de Vinícius (plan serré)
    (8.82, 11.64, 99, 134),   # construction : Vinícius + Cucurella (plan large)
    (11.64, 12.70, 134, 146),
    (12.70, 13.96, 146, 146), # arrêt : "rodeado de camisetas del Celta"
    (13.96, 15.05, 146, 160), # "No fuerza el regate" (passe image 155)
    (15.05, 16.73, 160, 186), # "Toca hacia dentro para Kylian Mbappé"
    (16.73, 20.34, 186, 232), # Mbappé aguanta... abre (passe image 209)
    (20.34, 23.70, 205, 205), # ARRÊT "Mirad bien"
    (23.70, 27.16, 209, 246), # Bellingham llega desde la derecha
    (27.16, 33.05, 246, 246), # ARRÊT : le choix
    (33.05, 34.26, 246, 252), # Primero controla. Se perfila.
    (34.26, 36.26, 252, 252), # ARRÊT : la précision
    (36.26, 38.35, 226, 262), # "Un segundo de calma" : revoir l'action
    (38.35, 39.09, 238, 238), # ARRÊT "Ahora, el duelo"
    (39.09, 41.66, 222, 246), # le défenseur collé dans le dos
    (41.66, 44.56, 236, 266), # l'autre arrive de la gauche et tacle
    (44.56, 50.11, 252, 252), # ARRÊT : deux rivaux + Radu
    (50.11, 51.04, 240, 246), # "Y aquí está el gesto"
    (51.04, 52.41, 246, 246), # ARRÊT "No se precipita"
    (52.41, 54.25, 246, 254), # appui / frappe (contact image 253)
    (54.25, 54.78, 254, 258), # raso, seco
    (54.78, 57.48, 236, 266), # "Justo antes de que llegue el defensor que se tira"
    (57.48, 60.33, 253, 285), # le ballon part au ras du sol
    (60.33, 62.50, 285, 300),
    (62.50, 65.44, 253, 296), # "Mirad la trayectoria"
    (65.44, 67.74, 262, 300), # Radu se queda clavado
    (67.74, 71.06, 300, 420), # Gol. Vinícius va chercher le ballon
    (71.06, 72.03, 420, 468), # Uno a uno
    (72.03, 74.81, 516, 655), # célébration (x1)
    (74.81, DUR, 667, 760),   # question finale
]
FREEZE_SEGS = [i for i, s in enumerate(SEG) if s[2] == s[3]]

def src_at(t):
    for k, (t0, t1, f0, f1) in enumerate(SEG):
        if t0 - 1e-9 <= t < t1 or (k == len(SEG) - 1 and t >= t0):
            if f0 == f1: return f0, k
            u = (t - t0) / (t1 - t0)
            return min(f1, int(math.floor(f0 + u * (f1 - f0) + 1e-6))), k
    return SEG[-1][3], len(SEG) - 1

out_src = []; out_seg = []
for n in range(NOUT):
    f, k = src_at(n / FPS); out_src.append(f); out_seg.append(k)

# ---------------------------------------------------------------- measured positions (source pixels)
H = {k: {int(f): v for f, v in d.items()} for k, d in json.load(open(f'{S}/heads.json')).items()}
BL = {int(f): v for f, v in json.load(open(f'{S}/trk_belli_long.json')).items()}  # Bellingham head 205..280
def interp(d, f):
    ks = sorted(d); f = min(max(f, ks[0]), ks[-1])
    return (float(np.interp(f, ks, [d[k][0] for k in ks])), float(np.interp(f, ks, [d[k][1] for k in ks])))
MB_HEAD = {170: (1106, 566), **{f: H['mbappe'][f] for f in H['mbappe']}}
RADU = {246: (312, 524), 256: (325, 524), 262: (354, 524), 268: (380, 524), 274: (426, 524), 280: (469, 552),
        286: (539, 524), 292: (605, 495), 298: (642, 552), 310: (639, 596)}
VINI_LATE = {300: (878, 640), 330: (628, 668), 360: (467, 769), 390: (403, 876), 420: (613, 876), 450: (812, 861), 468: (900, 830)}
CUCU = {99: (545, 770), 105: (528, 760), 124: (495, 735), 134: (477, 740)}
BALL = {253: (1287, 640), 262: (1000, 650), 268: (700, 610), 274: (520, 570), 280: (350, 530), 288: (220, 520), 300: (220, 520)}
CELE_X = {516: 780, 550: 1010, 570: 1130, 590: 1200, 610: 912, 640: 960, 666: 960}

def cam_target(f, seg):
    """camera centre (source px) + desired window height."""
    t0 = SEG[seg][0]
    if f <= 77:                                   # plan serré Vinícius
        x, y = interp(H['vini'], f); return x, y + 160, 860
    if f >= 667: return float(np.interp(f, [667, 700, 730, 760], [1500, 1550, 1450, 1230])), 560, 1080
    if f >= 516: return float(np.interp(f, sorted(CELE_X), [CELE_X[k] for k in sorted(CELE_X)])), 560, 1080
    if abs(t0 - 44.56) < 0.01 and RADU_WIN[0] <= T_NOW[0] <= RADU_WIN[1]:   # arrêt : on va chercher Radu
        x, y = interp(RADU, f); return x + 20, y + 10, 640
    if t0 >= 65.4 and t0 < 67.7:                  # sur Radu
        x, y = interp(RADU, f); return x + 60, y + 20, 640
    if f >= 300 or (t0 >= 67.7):
        x, y = interp(VINI_LATE, f); return x, y - 60, 640
    if t0 >= 57.4 and f >= 253:                    # suivre le ballon
        x, y = interp(BALL, f); return x - 60, y - 40, 700
    if f >= 209:
        x, y = interp(BL, f); return x - 40, y + 60, 620
    if f >= 186:
        x, y = interp(MB_HEAD, f); return x + 40, y + 70, 620
    if f >= 155:                                    # ballon de Vinícius vers Mbappé
        u = (f - 155) / 31; a = interp(H['vini'], 155); b = interp(MB_HEAD, 186)
        return a[0] + u * (b[0] - a[0]) + 20, a[1] + u * (b[1] - a[1]) + 60, 640
    x, y = interp(H['vini'], f); return x - 20, y + 60, 640

# ---------------------------------------------------------------- tags (porteur du ballon)
def tag_at(f):
    if f <= 77 or (99 <= f <= 154): return 'Vinícius Júnior', interp(H['vini'], f)
    if 186 <= f <= 208: return 'Kylian Mbappé', interp(H['mbappe'], f)
    if 246 <= f <= 252: return 'Jude Bellingham', interp(H['belli'], f)
    return None

# ---------------------------------------------------------------- spotlights (t0, t1, who)
def body(who, f):
    if who == 'belli': x, y = interp(BL, f); return x, y + 34, 60
    if who == 'vini': x, y = interp(H['vini'], f); return x, y + 34, 60
    if who == 'mbappe': x, y = interp(MB_HEAD, f); return x, y + 34, 60
    if who == 'cucu': x, y = interp(CUCU, f); return x, y, 62
    if who == 'radu': x, y = interp(RADU, f); return x, y, 62
    if who == 'vini_late': x, y = interp(VINI_LATE, f); return x, y, 70
SPOT = [
    (wt('Jude Bellingham'), 2.6, 'belli'),
    (wt('Vinícius arranca'), wt('con Cucurella'), 'vini'),
    (wt('Cucurella'), 11.6, 'cucu'),
    (wt('Kylian Mbappé'), wt('levanta'), 'mbappe'),
    (wt('Jude Bellingham', 17), 20.3, 'belli'),
    (wt('pendiente de Mbappé', 20), 23.65, 'mbappe'),
    (wt('Bellingham llega'), 27.1, 'belli'),
    (wt('Pero Bellingham'), 34.2, 'belli'),
    (wt('Radu', 44), 47.5, 'radu'),
    (wt('Radu se queda'), 67.6, 'radu'),
    (wt('Vinícius corre'), 70.9, 'vini_late'),
]

# ---------------------------------------------------------------- overlays to keep out of frame
def forbidden(f):
    xc = 359 + 1.5725 * f
    return [(80, 30, 325, 185), (1600, 40, 1840, 125), (1605, 985, 1865, 1050), (xc - 10, 872, xc + 255, 928)]

def window_ok(x0, y0, w, h, f):
    if x0 < 0 or y0 < 0 or x0 + w > 1920 or y0 + h > 1080: return False
    for a, b, c, d in forbidden(f):
        if x0 < c and x0 + w > a and y0 < d and y0 + h > b: return False
    return True

def place(cx, cy, h, f):
    h = min(h, 1080)
    while h > 300:
        w = h * 9 / 16
        best = None
        for dy in range(0, 401, 6):
            for sy in ((0,) if dy == 0 else (-1, 1)):
                for dx in range(0, 301, 6):
                    for sx in ((0,) if dx == 0 else (-1, 1)):
                        x0 = cx - w / 2 + sx * dx; y0 = cy - h / 2 + sy * dy
                        x0 = min(max(x0, 0), 1920 - w); y0 = min(max(y0, 0), 1080 - h)
                        if window_ok(x0, y0, w, h, f):
                            c = (x0 + w / 2 - cx) ** 2 + (y0 + h / 2 - cy) ** 2
                            if best is None or c < best[0]: best = (c, x0, y0)
                if best and best[0] < (dy + 1) ** 2: break
            if best and best[0] < (dy + 1) ** 2: break
        if best: return best[1], best[2], h
        h *= 0.96
    raise RuntimeError(f'no window f={f}')

# ---------------------------------------------------------------- camera path
cuts = [n for n in range(1, NOUT) if out_seg[n] != out_seg[n - 1]]
spot_p = np.zeros(NOUT); spot_who = [None] * NOUT
for (a, b, who) in SPOT:
    for n in range(int(a * FPS), min(NOUT, int(b * FPS) + 1)):
        u = (n / FPS - a) / max(0.01, b - a)
        spot_p[n] = min(1, u); spot_who[n] = who
raw = []
T_NOW = [0.0]
RADU_WIN = (wt('Radu', 44) - 0.5, 47.6)
for n in range(NOUT):
    f, k = out_src[n], out_seg[n]; T_NOW[0] = n / FPS
    cx, cy, h = cam_target(f, k)
    if spot_who[n]:
        bx, by, r = body(spot_who[n], f)
        p = spot_p[n]
        tg = tag_at(f)
        if spot_who[n] == 'cucu' and tg:      # le porteur tagué doit rester dans le cadre : pas de zoom
            hx, hy = tg[1]; cx = (bx + hx) / 2; cy = (by + hy + 30) / 2; h = max(h, (abs(bx - hx) + 2 * r + 60) * 16 / 9)
        else:
            cx = cx + 0.6 * p * (bx - cx); cy = cy + 0.6 * p * (by - cy)
            h = h / (1 + 0.22 * p)
    raw.append([cx, cy, h])
raw = np.array(raw)
# gaussian smoothing sigma=10 output frames inside each segment run
sm = raw.copy()
starts = [0] + cuts + [NOUT]
for a, b in zip(starts[:-1], starts[1:]):
    for j in range(3):
        sm[a:b, j] = gauss = np.array([np.average(raw[max(a, i - 30):min(b, i + 31), j],
                                    weights=np.exp(-0.5 * ((np.arange(max(a, i - 30), min(b, i + 31)) - i) / 10.0) ** 2)) for i in range(a, b)])
# zoom pulse +7% at each cut, back in 0.1 s
for c in cuts:
    for k in range(0, 4):
        if c + k < NOUT: sm[c + k, 2] /= (1 + 0.07 * (1 - k / 3))
win = []
for n in range(NOUT):
    x0, y0, h = place(sm[n, 0], sm[n, 1], sm[n, 2], out_src[n])
    win.append((x0, y0, h))

def to_out(n, x, y):
    x0, y0, h = win[n]; s = H_OUT / h
    return (x - x0) * s, (y - y0) * s, s

# ---------------------------------------------------------------- per-frame overlay data
frames = []
for n in range(NOUT):
    f = out_src[n]; x0, y0, h = win[n]; s = H_OUT / h
    fr = {'n': n, 'f': f, 'x0': round(x0, 2), 'y0': round(y0, 2), 'h': round(h, 2), 's': round(s, 5)}
    tg = tag_at(f)
    if tg:
        X, Y, _ = to_out(n, *tg[1]); fr['tag'] = [tg[0], round(X, 1), round(Y, 1)]
    if spot_who[n] is not None:
        bx, by, r = body(spot_who[n], f); X, Y, _ = to_out(n, bx, by)
        fr['spot'] = [spot_who[n], round(X, 1), round(Y, 1), r]
    frames.append(fr)
# constant radius per spotlight (largest needed), fades 0.25 s
for (a, b, who) in SPOT:
    ns = [n for n in range(NOUT) if a * FPS <= n <= b * FPS and 'spot' in frames[n] and frames[n]['spot'][0] == who]
    R = max(frames[n]['spot'][3] * frames[n]['s'] for n in ns)
    xs = np.array([frames[n]['spot'][1] for n in ns]); ys = np.array([frames[n]['spot'][2] for n in ns])
    k = np.exp(-0.5 * (np.arange(-6, 7) / 2.0) ** 2); k /= k.sum()
    xs2 = np.convolve(np.pad(xs, 6, mode='edge'), k, 'valid'); ys2 = np.convolve(np.pad(ys, 6, mode='edge'), k, 'valid')
    for i, n in enumerate(ns):
        t = n / FPS; op = min(1, (t - a) / 0.25, (b - t) / 0.25)
        frames[n]['spot'] = [who, round(float(xs2[i]), 1), round(float(ys2[i]), 1), round(float(R), 1), round(max(0, op), 3)]

json.dump({'seg': SEG, 'frames': frames, 'cuts': cuts, 'spot': SPOT, 'dur': DUR}, open(f'{S}/plan.json', 'w'))
print('frames', NOUT, 'cuts', len(cuts), 'min h', min(w[2] for w in win), 'max h', max(w[2] for w in win))

# ---------------------------------------------------------------- events (sounds)
def out_time_of_src(fsrc, segs=None):
    """first output time where the source frame fsrc is shown (moving segments only)."""
    res = []
    for k, (t0, t1, f0, f1) in enumerate(SEG):
        if f0 < f1 and f0 < fsrc <= f1:
            n0 = int(math.ceil(t0 * FPS))
            for n in range(n0, NOUT):
                if out_seg[n] != k: break
                if out_src[n] >= fsrc: res.append(n / FPS); break
    return res
kicks = []
for fc in (155, 209, 253):
    kicks += [(t, fc) for t in out_time_of_src(fc)]
kicks.sort()
pops = []
prev = None
for n, fr in enumerate(frames):
    cur = fr['tag'][0] if 'tag' in fr else None
    if cur and cur != prev: pops.append(n / FPS)
    prev = cur
SCORE_IN = wt('cero a uno'); SCORE_FLIP = wt('Uno a uno', 70)

# ---------------------------------------------------------------- HTML
def js(v): return json.dumps(v, ensure_ascii=False)
OFF = 0.25 / FPS
clips = []
run_start = 0
for n in range(1, NOUT + 1):
    if n == NOUT or out_src[n] != out_src[run_start]:
        st = max(0.0, run_start / FPS - OFF) if run_start else 0.0
        en = n / FPS - OFF if n < NOUT else DUR
        clips.append((out_src[run_start], round(st, 4), round(en - st, 4)))
        run_start = n
imgs = '\n'.join(f'<img id="im{j}" class="clip src" src="assets/frames/f{f:04d}.jpg" data-start="{s}" data-duration="{d}" alt="">' for j, (f, s, d) in enumerate(clips))

subs = []
for i, w in enumerate(words):
    txt = re.sub(r'[^\wáéíóúüñÁÉÍÓÚÜÑ]', '', w['w']).lower()
    nxt = words[i + 1]['s'] if i + 1 < len(words) else DUR
    st = w['s']; du = max(0.08, min(nxt, st + 1.2) - st)
    subs.append(f'<div id="w{i}" class="clip sub" data-start="{st:.3f}" data-duration="{du:.3f}">{txt}</div>')
subs = '\n'.join(subs)

sfx = []; ci = 0
cut_ids = ['166', '174', '168', '3115']
SFX_DUR = {'166': 0.81, '174': 1.045, '168': 0.888, '3115': 0.6, '1492': 1.384, '3005': 0.209, '2112': 1.463, '2108': 0.967, '2099': 1.593}
def add(idn, t, vol):
    sfx.append(f'<audio id="sx{len(sfx)}" class="clip" src="assets/sfx/{idn}.mp3" data-start="{max(0, t):.3f}" data-duration="{SFX_DUR[idn]}" data-volume="{vol}" data-track-index="{len(sfx) + 2}"></audio>')
for c in cuts:
    t = c / FPS; seg = out_seg[c]
    if SEG[seg][2] == SEG[seg][3]:
        add('1492', t - 0.05, 'VOL_FREEZE')
    else:
        add(cut_ids[ci % 4], t - 0.12, 'VOL_CUT'); ci += 1
for t in pops: add('3005', t, 'VOL_POP')
add('3005', SCORE_IN, 'VOL_POP')
kick_ids = ['2112', '2108', '2099']
for j, (t, fc) in enumerate(kicks): add(kick_ids[j % 3], t, 'VOL_KICK')
sfx = '\n'.join(sfx)

data = {'frames': [[fr['x0'], fr['y0'], fr['s'], fr.get('tag'), fr.get('spot')] for fr in frames], 'fps': FPS,
        'scoreIn': SCORE_IN, 'scoreFlip': SCORE_FLIP, 'cuts': [c / FPS for c in cuts]}
html = open(f'{S}/template.html').read()
html = html.replace('__DUR__', str(DUR)).replace('__IMGS__', imgs).replace('__SUBS__', subs).replace('__SFX__', sfx)
html = html.replace('__DATA__', js(data))
open(f'{S}/hf/gol/index.html.tmpl', 'w').write(html)
print('clips', len(clips), 'kicks', kicks, 'pops', pops, 'score', SCORE_IN, SCORE_FLIP)
