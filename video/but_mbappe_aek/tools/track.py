"""Suivi de la tête d'un joueur : template matching (tête + épaules) puis affinage du haut de la tête
sur les pixels « non pelouse » (pelouse = vert ET lumineux).
track.py dir f0 f1 hx hy s out.json [--norefine] [--body k]
(hx,hy) = haut de la tête sur f0, s = largeur de tête (px). f1 < f0 => suivi arrière.
--body k : hauteur du joueur ≈ k*s (pour la boîte du corps / spotlight), défaut 7."""
import sys, json, cv2, numpy as np
d = sys.argv[1]; f0, f1 = int(sys.argv[2]), int(sys.argv[3])
hx, hy, s = map(float, sys.argv[4:7]); out = sys.argv[7]
refine = '--norefine' not in sys.argv
k = float(sys.argv[sys.argv.index('--body') + 1]) if '--body' in sys.argv else 7.0
rd = lambda f: cv2.imread(f'{d}/{f:04d}.jpg')
def grass(p):
    p = p.astype(np.int32); b, g, r = p[..., 0], p[..., 1], p[..., 2]
    return (g > r + 8) & (g > b + 25) & (g > 70)
def refine_top(im, hx, hy):
    R = s * 0.9
    x0, x1 = int(max(0, hx - R)), int(min(im.shape[1], hx + R))
    y0, y1 = int(max(0, hy - R)), int(min(im.shape[0], hy + R))
    ng = ~grass(im[y0:y1, x0:x1])
    if ng.mean() > 0.6: return None          # fond non pelouse : pas d'affinage
    n, lab, st, cen = cv2.connectedComponentsWithStats(ng.astype(np.uint8), 8)
    best = None
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < s * s * 0.25: continue
        cx = x0 + x + w / 2
        if abs(cx - hx) > s: continue
        # point le plus haut de la composante proche de hx
        ys, xs = np.where(lab[:, max(0, int(hx - x0 - s * 0.6)):int(hx - x0 + s * 0.6)] == i)
        if len(ys) == 0: continue
        top = ys.min(); xt = xs[ys <= top + 1].mean() + max(0, int(hx - x0 - s * 0.6))
        cand = (abs(y0 + top - hy), x0 + xt, y0 + top)
        if best is None or cand[0] < best[0]: best = cand
    if best is None or best[0] > s * 0.7: return None
    return best[1], best[2]
TW, TH = int(s * 2.2), int(s * 2.4)          # tête + épaules
ox, oy = TW / 2, s * 0.25                       # position du haut de la tête dans le template
step = 1 if f1 >= f0 else -1
im = rd(f0)
tx, ty = int(hx - ox), int(hy - oy)
tmpl = im[ty:ty+TH, tx:tx+TW].astype(np.float32)
res = {f0: dict(head=[hx, hy], s=s, k=k, score=1.0, src='seed')}
for f in range(f0 + step, f1 + step, step):
    im = rd(f)
    m = int(s * 1.6)
    sx0, sy0 = max(0, tx - m), max(0, ty - m)
    reg = im[sy0:min(im.shape[0], ty + TH + m), sx0:min(im.shape[1], tx + TW + m)].astype(np.float32)
    r = cv2.matchTemplate(reg, tmpl, cv2.TM_CCOEFF_NORMED)
    _, mv, _, ml = cv2.minMaxLoc(r)
    tx, ty = sx0 + ml[0], sy0 + ml[1]
    phx, phy = tx + ox, ty + oy; src = 'tm'
    if refine:
        rr = refine_top(im, phx, phy)
        if rr: phx, phy, src = rr[0], rr[1], 'ref'
    p = im[ty:ty+TH, tx:tx+TW].astype(np.float32)
    if p.shape == tmpl.shape: tmpl = 0.8 * tmpl + 0.2 * p
    res[f] = dict(head=[round(float(phx), 1), round(float(phy), 1)], s=s, k=k, score=round(float(mv), 3), src=src)
json.dump({str(a): b for a, b in sorted(res.items())}, open(out, 'w'))
print(out, len(res), 'min score', min(v['score'] for v in res.values()))
