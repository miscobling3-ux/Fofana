import cv2, numpy as np
def hair_top(im, hx, hy, fallback_off, roi=(28, 45, 30)):
    """Top of the dark hair blob around (hx,hy). Returns (x, top, measured?)."""
    rx, up, down = roi
    x0, y0 = int(hx - rx), int(hy - up); x1, y1 = int(hx + rx), int(hy + down)
    x0 = max(0, x0); y0 = max(0, y0)
    p = im[y0:y1, x0:x1]
    hsv = cv2.cvtColor(p, cv2.COLOR_BGR2HSV)
    v = hsv[..., 2].astype(int); s = hsv[..., 1].astype(int); h = hsv[..., 0].astype(int)
    b, g, r = (p[..., k].astype(int) for k in range(3))
    grass = (g > r + 6) & (g > b + 6) & (v > 45)
    hair = (v < 95) & ~grass
    hair = cv2.morphologyEx(hair.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(hair)
    if n <= 1: return hx, hy - fallback_off, False
    cx, cy = hx - x0, hy - y0
    best = None
    for k in range(1, n):
        if st[k, cv2.CC_STAT_AREA] < 25: continue
        ys, xs = np.nonzero(lab == k)
        d = np.min(np.hypot(xs - cx, ys - cy))
        if best is None or d < best[0]: best = (d, k)
    if best is None or best[0] > 14: return hx, hy - fallback_off, False
    k = best[1]
    if st[k, cv2.CC_STAT_TOP] <= 1: return hx, hy - fallback_off, False   # dark background merges: not measurable
    ys, xs = np.nonzero(lab == k)
    top = ys.min()
    # rows with >=3 hair pixels to ignore stray pixels
    for yy in range(top, top + 8):
        if (ys == yy).sum() >= 3: top = yy; break
    tx = xs[ys <= top + 6].mean()
    return tx + x0, top + y0, True
