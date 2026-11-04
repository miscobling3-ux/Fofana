"""Suivi d'un joueur (couleur du maillot) + haut de la tête + silhouette complète (pixels non-pelouse)."""
import cv2, numpy as np, json, sys
from blobs import frame, mask
def grass(img):
    h = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # pelouse = vert ET assez lumineux (sinon les cheveux foncés passent pour du gazon)
    return cv2.inRange(h, (30, 50, 70), (90, 255, 255)) > 0
def lines(img):
    h = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    return cv2.inRange(h, (0, 0, 190), (180, 40, 255)) > 0
def track(clip, n0, n1, x0, y0, kind="yellow", R=45, keys=None, step=1):
    keys = keys or {}
    out = {}
    cx, cy = x0, y0
    rng = range(n0, n1 + 1) if step > 0 else range(n0, n1 - 1, -1)
    for n in rng:
        img = frame(clip, n)
        if n in keys: cx, cy = keys[n]
        x1, y1 = int(max(0, cx - R)), int(max(0, cy - R))
        sub = mask(img[y1:int(cy + R), x1:int(cx + R)], kind)
        sub = cv2.morphologyEx(sub, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        k, lab, st, cen = cv2.connectedComponentsWithStats(sub)
        best = None
        for i in range(1, k):
            if st[i][4] < 12: continue
            c = (cen[i][0] + x1, cen[i][1] + y1)
            d = np.hypot(c[0] - cx, c[1] - cy) - 0.15 * np.sqrt(st[i][4])
            if best is None or d < best[0]: best = (d, c, st[i], i)
        if best is not None and n not in keys:
            # centre de la zone maillot (pondéré) — lissé ensuite
            ys, xs = np.where(lab == best[3])
            cx, cy = xs.mean() + x1, ys.mean() + y1
        out[n] = {"torso": [float(cx), float(cy)]}
    return out
def silhouette(img, cx, cy, hint_h):
    """boîte englobante des pixels non-pelouse reliés au joueur autour du torse"""
    H = int(hint_h)
    x1, y1 = int(cx - H * 0.8), int(cy - H * 0.9)
    x2, y2 = int(cx + H * 0.8), int(cy + H * 1.3)
    x1, y1 = max(0, x1), max(0, y1)
    sub = img[y1:y2, x1:x2]
    ng = (~grass(sub)) & (~lines(sub) | (mask(sub, "white") > 0))
    ng = ng.astype(np.uint8)
    ng = cv2.morphologyEx(ng, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    k, lab, st, cen = cv2.connectedComponentsWithStats(ng)
    px, py = int(cx - x1), int(cy - y1)
    # composante contenant (ou la plus proche de) le torse
    l = lab[min(py, lab.shape[0]-1), min(px, lab.shape[1]-1)]
    if l == 0:
        d = [(np.hypot(cen[i][0]-px, cen[i][1]-py), i) for i in range(1, k) if st[i][4] > 20]
        if not d: return None
        l = min(d)[1]
    ys, xs = np.where(lab == l)
    return [int(xs.min() + x1), int(ys.min() + y1), int(xs.max() + x1), int(ys.max() + y1)]
def headtop(img, cx, cy, bw):
    """haut de la tête : 1re ligne non-pelouse au-dessus du torse dans une colonne étroite"""
    x1, x2 = int(cx - bw), int(cx + bw)
    top = None
    col = img[int(cy - 70):int(cy), x1:x2]
    ng = ~grass(col)
    rows = np.where(ng.sum(1) >= 2)[0]
    # remonter en continu depuis le torse
    r = col.shape[0] - 1
    gap = 0
    best = r
    while r >= 0:
        if ng[r].sum() >= 2: best = r; gap = 0
        else:
            gap += 1
            if gap > 2: break
        r -= 1
    xs = np.where(ng[best])[0]
    hx = x1 + (xs.mean() if len(xs) else bw)
    return float(hx), float(int(cy - 70) + best)
