"""Génère le projet HyperFrames (index.html + data.js + images + sons) à partir de :
voice.json (mots), EDL ci-dessous, suivis trk/*.json, filigrane wm.json.
Tout le montage est rendu par HyperFrames (HTML/GSAP) ; Python ne fait que calculer les positions."""
import json, os, math, shutil, sys, numpy as np, cv2

S = '/tmp/claude-0/-home-user-Fofana/741607e6-9b49-5de3-8cc7-6117fa097297/scratchpad'
P = f'{S}/proj'; HF = f'{S}/hf'
FPS = 30; W_OUT, H_OUT = 1080, 1920
words = json.load(open(f'{P}/voice.json'))
VOICE_DUR = 86.71
N = int(round(VOICE_DUR * FPS))
tw = lambda i: words[i]['start']

def L(name):
    return {int(k): v for k, v in json.load(open(f'{S}/trk/{name}.json')).items()}
TR = {n: L(n) for n in ['dum_A1', 'mb_A1', 'gk_A1', 'bel_A3', 'dum_A3', 'dum_B1', 'dum_A2']}
# boîtes du gardien posées à la main pendant le plongeon (grille 10 px)
GK_KEY = {150: [1275, 365, 1340, 475], 158: [1250, 350, 1335, 470], 166: [1265, 335, 1340, 450],
          174: [1280, 335, 1340, 420], 182: [1260, 340, 1345, 405], 190: [1255, 335, 1355, 400], 200: [1255, 335, 1355, 400]}
BODY = {  # paramètres de silhouette : (k hauteur en largeurs de tête, demi-largeur en têtes)
    'dum_A1': (7.5, 3.2), 'mb_A1': (7.2, 3.6), 'gk_A1': (7.5, 4.0), 'bel_A3': (11.5, 2.8),
    'dum_A3': (10.5, 3.0), 'dum_B1': (8.0, 3.2), 'dum_A2': (8.0, 3.4)}

def head(tr, f):
    T = TR[tr]
    if f in T: return T[f]['head'], T[f]['s']
    ks = sorted(T); f = min(max(f, ks[0]), ks[-1]); return T[f]['head'], T[f]['s']

def body_box(tr, f):
    if tr == 'gk_A1' and f >= 150:
        ks = sorted(GK_KEY); f = min(max(f, ks[0]), ks[-1])
        lo = max(k for k in ks if k <= f); hi = min(k for k in ks if k >= f)
        t = 0 if hi == lo else (f - lo) / (hi - lo)
        return [GK_KEY[lo][i] + (GK_KEY[hi][i] - GK_KEY[lo][i]) * t for i in range(4)]
    (hx, hy), s = head(tr, f); k, hw = BODY[tr]
    return [hx - hw * s, hy - 0.3 * s, hx + hw * s, hy + k * s]

# ------------------------------------------------------------------ EDL
# chaque plan : start (s), clip, liste de morceaux [(type, ...)], options
# morceaux : ('play', f0, f1)  -> lecture de f0 à f1 répartie sur la durée allouée (vitesse constante)
#            ('freeze', f, dur_or_until)
def T(i): return tw(i)
EDL = [
    dict(t=0.0, clip='A', parts=[('play', 112, 182)], cam='mb_A1', cw=470, name='accroche'),
    dict(t=T(20), clip='B', parts=[('play', 31, 142)], cam='dum_B1', cw=520, name='contexte'),
    dict(t=T(38), clip='A', parts=[('play', 495, 553, T(52)), ('play', 553, 592)], cam='bel_A3', cw=560, name='construction1'),
    dict(t=T(62), clip='A', parts=[('play', 592, 730)], cam='dum_A3', cw=600, name='construction2'),
    dict(t=T(85), clip='A', parts=[('freeze', 90)], cam='dum_A1', cw=600, name='regardez_bien', freeze=True),
    dict(t=T(113), clip='A', parts=[('play', 60, 116, T(131)), ('freeze', 116, T(134)), ('play', 116, 140)], cam='dum_A1', cw=560, name='choix'),
    dict(t=T(154), clip='A', parts=[('play', 140, 150, T(164)), ('freeze', 150, T(181)), ('play', 150, 158)], cam='mb_A1', cw=520, name='duel'),
    dict(t=T(201), clip='A', parts=[('play', 770, 779, T(206)), ('freeze', 779, T(220)), ('play', 779, 800)], cam='pt_A3shot', cw=560, name='geste'),
    dict(t=T(233), clip='A', parts=[('play', 150, 178)], cam='gk_A1', cw=470, name='gardien'),
    dict(t=T(250), clip='A', parts=[('play', 158, 200)], cam='pt_goalA1', cw=520, name='trajectoire'),
    dict(t=T(267), clip='A', parts=[('play', 340, 398, T(281)), ('play', 398, 430)], cam='dum_A2', cw=600, name='angle'),
    dict(t=T(284), clip='B', parts=[('play', 562, 622)], cam='pt_mbclose', cw=607, name='celeb_mb'),
    dict(t=T(288), clip='B', parts=[('play', 690, 755)], cam='pt_dumclose', cw=607, name='celeb_dum'),
    dict(t=T(292), clip='A', parts=[('play', 884, 1004)], cam='pt_celeb', cw=607, name='celeb'),
]
FIXED_PTS = {'pt_A3shot': (1150, 560), 'pt_goalA1': (1250, 380), 'pt_mbclose': (1430, 600),
             'pt_dumclose': (1150, 560), 'pt_celeb': (1000, 560)}
# Porteurs du ballon : (clip, piste, f_début, f_passe) -> étiquette jusqu'à f_passe-1
TAGS = [('A', 'dum_A1', 60, 121, 'Denzel Dumfries'), ('B', 'dum_B1', 85, 143, 'Denzel Dumfries'),
        ('A', 'bel_A3', 492, 553, 'Jude Bellingham'), ('A', 'dum_A3', 642, 760, 'Denzel Dumfries'),
        ('A', 'dum_A2', 340, 372, 'Denzel Dumfries')]
# Spotlights : (mot début, mot fin (exclu), piste, plan)
SPOTS = [(4, 20, 'mb_A1', 'accroche'), (41, 47, 'bel_A3', 'construction1'), (62, 68, 'dum_A3', 'construction2'),
         (96, 105, 'mb_A1', 'regardez_bien'), (106, 113, 'gk_A1', 'regardez_bien'),
         (130, 134, 'dum_A1', 'choix'), (156, 164, 'mb_A1', 'duel'), (194, 201, 'mb_A1', 'duel'),
         (233, 245, 'gk_A1', 'gardien'), (276, 281, 'dum_A2', 'angle')]
KICKS = [('A', 160), ('A', 782), ('A', 392)]          # images de contact (frappe)
SCORE_IN, SCORE_FLIP = T(24), T(281)

# ------------------------------------------------------------------ images de sortie
plan_of = [None] * N; src = [None] * N; freeze = [False] * N
for pi, sh in enumerate(EDL):
    t0 = sh['t']; t_end = EDL[pi + 1]['t'] if pi + 1 < len(EDL) else VOICE_DUR
    parts = sh['parts']; cur = t0
    for qi, pt in enumerate(parts):
        if pt[0] == 'play':
            f0, f1 = pt[1], pt[2]; end = pt[3] if len(pt) > 3 else (t_end if qi == len(parts) - 1 else None)
        else:
            f0 = f1 = pt[1]; end = pt[2] if len(pt) > 2 else t_end
        if end is None: raise SystemExit(f'end missing {sh["name"]}')
        k0, k1 = int(round(cur * FPS)), int(round(end * FPS))
        for k in range(k0, min(k1, N)):
            u = (k - k0) / max(1, (k1 - k0))
            src[k] = (sh['clip'], int(round(f0 + (f1 - f0) * u))); plan_of[k] = pi; freeze[k] = (pt[0] == 'freeze')
        sp = (f1 - f0) / 50 / max(1e-6, (end - cur))
        print(f'{sh["name"]:14s} {pt[0]:6s} {f0}->{f1} {cur:6.2f}->{end:6.2f} vitesse x{sp:.2f}')
        cur = end
assert all(s is not None for s in src), [i for i, s in enumerate(src) if s is None][:5]

# ------------------------------------------------------------------ zones interdites (habillage télé)
WM = json.load(open(f'{S}/wm.json'))
WMFIT = {'A': (-1.9793503, 681.79), 'B': (-1.9791658, 1402.17)}
def forbidden(clip, f):
    a, b = WMFIT[clip]; x = a * f + b; boxes = []
    for n in range(-2, 3):
        xx = x + n * 1910
        if xx < 1920 and xx + 319 > 0: boxes.append((xx - 12, 893, xx + 331, 957))
    boxes.append((1555, 45, 1835, 118))                     # LIVE + barre grise
    if clip == 'B' and f < 887: boxes.append((50, 35, 630, 115))   # score télé
    return boxes

# ------------------------------------------------------------------ caméra
def focus_point(cam, clip, f):
    if cam in FIXED_PTS: return FIXED_PTS[cam]
    b = body_box(cam, f); return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)

tag_at = [None] * N
for k in range(N):
    clip, f = src[k]
    for (c, tr, fa, fp, name) in TAGS:
        if c == clip and fa <= f < fp and tr in TR and (min(TR[tr]) <= f <= max(TR[tr])):
            tag_at[k] = (tr, name)
spot_at = [None] * N
for (w0, w1, tr, plan) in SPOTS:
    pi = [p['name'] for p in EDL].index(plan)
    for k in range(int(round(tw(w0) * FPS)), int(round(tw(w1) * FPS))):
        if 0 <= k < N and plan_of[k] == pi and (tr == 'gk_A1' or min(TR[tr]) <= src[k][1] <= max(TR[tr])): spot_at[k] = (tr, w0)

def gauss_smooth(arr, sigma, segs):
    out = arr.copy()
    for a, b in segs:
        x = arr[a:b]
        if len(x) < 3: continue
        r = int(3 * sigma); kern = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); kern /= kern.sum()
        pad = np.pad(x, ((r, r), (0, 0)), mode='edge')
        out[a:b] = np.stack([np.convolve(pad[:, j], kern, 'valid') for j in range(x.shape[1])], 1)
    return out

# segments continus (même plan, pas de gel) pour le lissage
segs = []; a = 0
for k in range(1, N + 1):
    if k == N or plan_of[k] != plan_of[a] or freeze[k] != freeze[a]:
        segs.append((a, k)); a = k
want = np.zeros((N, 3))
spot_p = np.zeros(N)       # progression du zoom spotlight 0..1
for k in range(N):
    clip, f = src[k]; sh = EDL[plan_of[k]]
    cx, cy = focus_point(sh['cam'], clip, f); cw = sh['cw']
    if spot_at[k]:
        tr, w0 = spot_at[k]; b = body_box(tr, f); px, py = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        p = min(1.0, (k / FPS - tw(w0)) / 0.8); p = 0.5 - 0.5 * math.cos(math.pi * max(0, p))
        spot_p[k] = p; cx += (px - cx) * p; cy += (py - cy) * p; cw = cw / (1 + 0.22 * p)
    want[k] = (cx, cy, cw)
want = gauss_smooth(want, 10, segs)

def need_pts(k, tm=160):
    """points qui doivent rester dans le cadre (avec marges en px de sortie)"""
    clip, f = src[k]; pts = []
    if tag_at[k]:
        tr = tag_at[k][0]; (hx, hy), s = head(tr, f); b = body_box(tr, f)
        pts.append((hx, hy, tm, 510 if k / FPS >= SCORE_IN - 0.2 else 300, tm, 40)); pts.append((hx, b[3], 0, 0, 0, 20))
    if spot_at[k]:
        b = body_box(spot_at[k][0], f); pts.append(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2, 0, 0, 0, 0)); pts.append((b[0], b[1], 40, 40, 0, 0)); pts.append((b[2], b[3], 0, 0, 40, 40))
    return pts

def ok(x0, y0, cw, ch, clip, f, pts):
    if x0 < 0 or y0 < 0 or x0 + cw > 1920 or y0 + ch > 1080: return False
    for (a, b, c, d) in forbidden(clip, f):
        if x0 < c and x0 + cw > a and y0 < d and y0 + ch > b: return False
    sc = W_OUT / cw
    for (px, py, ml, mt, mr, mb) in pts:
        if not (x0 + ml / sc <= px <= x0 + cw - mr / sc and y0 + mt / sc <= py <= y0 + ch - mb / sc): return False
    return True

cams = np.zeros((N, 3)); nozoom = 0
for k in range(N):
    clip, f = src[k]; cx, cy, cw = want[k]; pts = need_pts(k)
    found = None
    for shrink in [1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 1.05, 1.1, 1.15]:
        c = min(607.5, cw * shrink); ch = c * 16 / 9
        best = None
        for dy in range(-400, 401, 8):
            for dx in range(-400, 401, 8):
                x0 = cx - c / 2 + dx; y0 = cy - ch / 2 + dy
                if ok(x0, y0, c, ch, clip, f, pts):
                    d = dx * dx + dy * dy
                    if best is None or d < best[0]: best = (d, x0, y0)
            # pas de sortie anticipée : on garde le plus proche
        if best: found = (best[1], best[2], c); break
    if not found:
        pts2 = need_pts(k, 110)
        for c in [min(607.5, cw * sh_) for sh_ in (1.0, 0.95, 0.9, 0.85, 0.8)] + [502, 498, 494, 490, 485, 480, 470]:
            ch = c * 16 / 9; best = None
            for dy in range(-500, 501, 4):
                for dx in range(-500, 501, 2):
                    x0 = cx - c / 2 + dx; y0 = cy - ch / 2 + dy
                    if ok(x0, y0, c, ch, clip, f, pts2):
                        d = dx * dx + dy * dy
                        if best is None or d < best[0]: best = (d, x0, y0)
            if best: found = (best[1], best[2], c); break
    if not found:
        for shrink in [1.0, 0.9, 0.8, 0.7]:
            c = min(607.5, cw * shrink); ch = c * 16 / 9; best = None
            for dy in range(-500, 501, 10):
                for dx in range(-500, 501, 10):
                    x0 = cx - c / 2 + dx; y0 = cy - ch / 2 + dy
                    if ok(x0, y0, c, ch, clip, f, []):
                        d = dx * dx + dy * dy
                        if best is None or d < best[0]: best = (d, x0, y0)
            if best: found = (best[1], best[2], c); print('relâché', k, src[k]); break
    cams[k] = found
# lissage léger après contraintes, conservé seulement si toujours valide
sm = gauss_smooth(cams, 4, segs)
for k in range(N):
    clip, f = src[k]; x0, y0, c = sm[k]
    if ok(x0, y0, c, c * 16 / 9, clip, f, need_pts(k, 110)): cams[k] = sm[k]

# ------------------------------------------------------------------ états par image
cuts = [int(round(sh['t'] * FPS)) for sh in EDL[1:]]
frames = []
tag_first = {}
for k in range(N):
    clip, f = src[k]; x0, y0, c = cams[k]; sc = W_OUT / c
    # punch +7 % à chaque coupe, retombe en 0,1 s (zoom autour du centre)
    punch = 1.0
    for cu in cuts:
        if 0 <= k - cu < 3: punch = 1.07 - 0.07 * (k - cu) / 3
    st = dict(x=round(-x0 * sc, 2), y=round(-y0 * sc, 2), s=round(sc, 5), p=round(punch, 4))
    if tag_at[k]:
        tr, name = tag_at[k]; (hx, hy), s_ = head(tr, f)
        ox = (hx - x0) * sc; oy = (hy - y0) * sc
        ox = W_OUT / 2 + (ox - W_OUT / 2) * punch; oy = H_OUT / 2 + (oy - H_OUT / 2) * punch
        key = (tr, plan_of[k])
        if key not in tag_first: tag_first[key] = k
        st['tag'] = [round(ox, 1), round(oy, 1), name, round((k - tag_first[key]) / FPS, 3)]
    if spot_at[k]:
        tr, w0 = spot_at[k]; b = body_box(tr, f)
        bx0, by0, bx1, by1 = [(b[0] - x0) * sc, (b[1] - y0) * sc, (b[2] - x0) * sc, (b[3] - y0) * sc]
        st['spot_raw'] = [(bx0 + bx1) / 2, (by0 + by1) / 2, 0.5 * math.hypot(bx1 - bx0, by1 - by0) * 1.12, w0]
    frames.append(st)
# rayon constant par spotlight + centre lissé + fondu 0,25 s
groups = {}
for k, st in enumerate(frames):
    if 'spot_raw' in st: groups.setdefault(st['spot_raw'][3], []).append(k)
for w0, ks in groups.items():
    R = max(frames[k]['spot_raw'][2] for k in ks) + 14
    C = np.array([frames[k]['spot_raw'][:2] for k in ks])
    if len(C) > 5: C = gauss_smooth(C, 2, [(0, len(C))])
    a, b = ks[0], ks[-1]
    for j, k in enumerate(ks):
        op = min(1, (k - a + 1) / (0.25 * FPS), (b - k + 1) / (0.25 * FPS))
        frames[k]['spot'] = [round(C[j][0], 1), round(C[j][1], 1), round(R, 1), round(op, 3)]
        del frames[k]['spot_raw']

# ------------------------------------------------------------------ fichiers
os.makedirs(f'{HF}/frames', exist_ok=True)
used = sorted(set(src))
for clip, f in used:
    dst = f'{HF}/frames/{clip}{f:04d}.jpg'
    if not os.path.exists(dst): shutil.copy(f'{S}/fr{clip}/{f:04d}.jpg', dst)
# clips image : un <img> par série d'images de sortie identiques
imgs = []; a = 0
for k in range(1, N + 1):
    if k == N or src[k] != src[a]:
        imgs.append((src[a], a, k - a)); a = k
# sons
SFX = []
whoosh = ['whoosh1', 'whoosh2', 'whoosh3', 'whoosh4']
for i, cu in enumerate(cuts):
    SFX.append((whoosh[i % 4], cu / FPS - 0.12, 0.30))
for k in range(1, N):
    if freeze[k] and not freeze[k - 1]: SFX.append(('freeze', k / FPS, 0.5))
for key, k in tag_first.items(): SFX.append(('pop', k / FPS, 0.25))
SFX.append(('pop', SCORE_IN, 0.25)); SFX.append(('pop', SCORE_FLIP, 0.25))
for clip, fk in KICKS:
    for k in range(N):
        if src[k] == (clip, fk) and (k == 0 or src[k - 1] != (clip, fk)): SFX.append(('kick', k / FPS, 0.35))
SFX = [s for s in SFX if s[1] >= 0]

data = dict(N=N, FPS=FPS, frames=frames,
            words=[dict(t=w['text'].lower().replace(' :', '').replace(' ?', '').replace(' !', '').rstrip('.,'), a=w['start'], b=w['end']) for w in words],
            scoreIn=SCORE_IN, scoreFlip=SCORE_FLIP, dur=VOICE_DUR)
open(f'{HF}/data.js', 'w').write('window.EDIT=' + json.dumps(data, separators=(',', ':')) + ';')
json.dump(dict(src=src, cams=cams.tolist(), tag=[t[1] if t else None for t in tag_at], frames=frames, sfx=SFX, cuts=cuts,
               freeze=freeze), open(f'{P}/plan.json', 'w'))

img_html = '\n'.join(
    f'<img id="im{k0}" class="clip src" src="frames/{c}{f:04d}.jpg" data-start="{max(0, (k0 - 0.25) / FPS):.4f}" data-duration="{(n + (0.25 if k0 > 0 else 0)) / FPS:.4f}" data-track-index="1" alt="">'
    for (c, f), k0, n in imgs)
sfx_html = '\n'.join(
    f'<audio id="sfx{i}" class="clip" src="sfx/{n}.wav" data-start="{t:.3f}" data-duration="{d:.3f}" data-volume="0.14" data-track-index="{10 + i}"></audio>'
    for i, (n, t, d) in enumerate(SFX))
tpl = open(f'{P}/tools/template.html').read()
html = tpl.replace('{{IMGS}}', img_html).replace('{{SFX}}', sfx_html).replace('{{DUR}}', f'{VOICE_DUR:.3f}')
open(f'{HF}/index.html', 'w').write(html)
print('images de sortie', N, 'images source', len(used), 'clips img', len(imgs), 'sons', len(SFX))

# ---- contrôle final des contraintes
bad = [k for k in range(N) if not ok(*cams[k][:2], cams[k][2], cams[k][2] * 16 / 9, *src[k], need_pts(k, 110))]
dirty = [k for k in range(N) if not ok(*cams[k][:2], cams[k][2], cams[k][2] * 16 / 9, *src[k], [])]
print('contraintes non tenues', len(bad), bad[:20], 'image sale', len(dirty))
for k in bad[:200:10]:
    print(' ', k, src[k], tag_at[k], spot_at[k], [round(v) for v in cams[k]])
