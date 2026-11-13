#!/usr/bin/env python3
"""Vérifications sur la vidéo FINALE. usage: python3 -I verify.py <scratch> <video.mp4>"""
import cv2, json, sys, math, numpy as np, subprocess, os
S, V = sys.argv[1], sys.argv[2]
plan = json.load(open(f'{S}/an/' + os.environ.get('PLAN', 'plan.json')))
trkB = {int(k): v for k, v in json.load(open(f'{S}/an/trk_B.json')).items()}
OUT = f'{S}/' + os.environ.get('VDIR', 'verif'); os.makedirs(OUT, exist_ok=True)
cap = cv2.VideoCapture(V)
frames = plan['frames']
lab_rows, lab_tiles, src_scores, edge_tiles = [], [], [], []
i = 0
while True:
    ok, im = cap.read()
    if not ok: break
    if i >= len(frames): i += 1; continue
    f = frames[i]
    cx, cy, h = f['cam']; s = 1920 / h; w = h * 9 / 16
    # --- bonne image source : corrélation entre la sortie et le recadrage attendu de la source
    if i % 3 == 0:
        src = cv2.imread(f"{S}/proj/frames/{f['clip']}/{f['k']:04d}.jpg")
        M = np.float32([[s, 0, -(cx - w / 2) * s], [0, s, -(cy - h / 2) * s]])
        exp = cv2.warpAffine(src, M, (1080, 1920))
        a = cv2.cvtColor(cv2.resize(im, (135, 240)), cv2.COLOR_BGR2GRAY).astype(float)
        b = cv2.cvtColor(cv2.resize(exp, (135, 240)), cv2.COLOR_BGR2GRAY).astype(float)
        sl = slice(0, 190)   # ignore sous-titres
        a, b = a[sl], b[sl]
        c = np.corrcoef(a.ravel(), b.ravel())[0, 1]
        # comparaison avec l'image source voisine (±2) pour vérifier qu'on a la bonne
        best = c; bestk = f['k']
        for dk in (-2, 2):
            p = f"{S}/proj/frames/{f['clip']}/{f['k'] + dk:04d}.jpg"
            if os.path.exists(p):
                e2 = cv2.warpAffine(cv2.imread(p), M, (1080, 1920))
                b2 = cv2.cvtColor(cv2.resize(e2, (135, 240)), cv2.COLOR_BGR2GRAY).astype(float)[sl]
                c2 = np.corrcoef(a.ravel(), b2.ravel())[0, 1]
                if c2 > best + 0.002: best, bestk = c2, f['k'] + dk
        src_scores.append((i, f['t'], f['clip'], f['k'], round(float(c), 4), bestk))
    # --- étiquette : pointe rouge mesurée sur la vidéo rendue
    if f['label']:
        hx, hy = trkB[f['k']][:2]
        X = (hx - (cx - w / 2)) * s; Y = (hy - (cy - h / 2)) * s
        x0, x1 = int(X - 60), int(X + 60); y0, y1 = int(Y - 140), int(Y + 30)
        roi = im[max(0, y0):y1, max(0, x0):x1].astype(int)
        red = (roi[..., 2] > 200) & (roi[..., 1] < 90) & (roi[..., 0] < 90)
        ys, xs = np.where(red)
        if len(ys):
            ty = ys.max(); txs = xs[ys >= ty - 2]; tx = txs.mean()
            TY = max(0, y0) + ty; TX = max(0, x0) + tx
            dy = Y - TY; dx = TX - X
            ok_ = (0 <= dy <= 16) and abs(dx) <= 6
        else:
            TY = TX = None; dy = dx = None; ok_ = False
        lab_rows.append(dict(i=i, t=round(f['t'], 3), k=f['k'], head=(round(X, 1), round(Y, 1)), tip=(None if TX is None else round(TX, 1), None if TY is None else int(TY)), dy=None if dy is None else round(float(dy), 1), dx=None if dx is None else round(float(dx), 1), ok=bool(ok_)))
        crop = cv2.copyMakeBorder(im, 200, 200, 200, 200, cv2.BORDER_CONSTANT)[int(Y) + 200 - 90:int(Y) + 200 + 60, int(X) + 200 - 75:int(X) + 200 + 75].copy()
        crop = cv2.resize(crop, (300, 300), interpolation=cv2.INTER_NEAREST)
        cv2.line(crop, (0, 180), (300, 180), (255, 0, 255), 1)       # haut de la tête attendu
        cv2.putText(crop, f"{i} k{f['k']} dy{lab_rows[-1]['dy']} dx{lab_rows[-1]['dx']}", (3, 15), 0, 0.42, (0, 255, 255), 1)
        lab_tiles.append(crop)
    # --- image propre : haut et bas toutes les 0,5 s
    if i % 15 == 0:
        top = cv2.resize(im[0:300], (540, 150)); bot = cv2.resize(im[1620:1920], (540, 150))
        t = np.vstack([top, np.full((6, 540, 3), 255, np.uint8), bot]); cv2.putText(t, f"{f['t']:.1f}s", (5, 20), 0, 0.6, (0, 255, 255), 2)
        edge_tiles.append(t)
    i += 1
n_out = i
def board(tiles, cols, path):
    if not tiles: return
    while len(tiles) % cols: tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[r:r + cols]) for r in range(0, len(tiles), cols)]
    for j in range(0, len(rows), 8):
        cv2.imwrite(path.replace('.jpg', f'_{j // 8}.jpg'), np.vstack(rows[j:j + 8]), [cv2.IMWRITE_JPEG_QUALITY, 82])
board(lab_tiles, 8, f'{OUT}/labels.jpg'); board(edge_tiles, 6, f'{OUT}/edges.jpg')
bad_lab = [r for r in lab_rows if not r['ok']]
bad_src = [r for r in src_scores if r[4] < 0.80 or r[5] != r[3]]
json.dump(dict(labels=lab_rows, src=src_scores), open(f'{OUT}/verif.json', 'w'))
print('frames video', n_out, 'plan', len(frames))
print('labels', len(lab_rows), 'hors tolérance', len(bad_lab), bad_lab[:10])
dys = [r['dy'] for r in lab_rows if r['dy'] is not None]; dxs = [r['dx'] for r in lab_rows if r['dx'] is not None]
if dys: print('dy min/max', min(dys), max(dys), 'dx min/max', min(dxs), max(dxs))
print('source frames checked', len(src_scores), 'corr min', min(r[4] for r in src_scores), 'suspects', len(bad_src), bad_src[:15])
