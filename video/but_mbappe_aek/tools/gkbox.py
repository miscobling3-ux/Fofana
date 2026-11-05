"""Boîte du gardien par la couleur de son maillot (vert clair, peu saturé, composante bleue)."""
import cv2, json, numpy as np, sys
T = json.load(open('trk/gk_A1.json')); out = {}
px, py = T['100']['head']; px, py = px, py + 30
for f in range(60, 201):
    im = cv2.imread(f'frA/{f:04d}.jpg'); hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    m = ((hsv[..., 0] > 28) & (hsv[..., 0] < 70) & (hsv[..., 1] > 50) & (hsv[..., 1] < 200) & (hsv[..., 2] > 90) & (im[..., 0] > 40)).astype(np.uint8)
    x0, y0 = int(max(0, px - 160)), int(max(0, py - 160)); sub = m[y0:int(py + 160), x0:int(px + 160)]
    sub = cv2.morphologyEx(sub, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(sub, 8)
    best = None
    for i in range(1, n):
        if st[i, 4] < 150: continue
        cx, cy = x0 + cen[i][0], y0 + cen[i][1]; d = np.hypot(cx - px, cy - py)
        if best is None or d < best[0]: best = (d, i)
    if best is None: out[f] = None; continue
    i = best[1]; x, y, w, h, a = st[i]
    bx, by = x0 + x, y0 + y
    out[f] = [int(bx), int(by), int(w), int(h)]
    px, py = bx + w / 2, by + h / 2
json.dump(out, open('trk/gk_box.json', 'w'))
tiles = []
for f in range(60, 201, 5):
    im = cv2.imread(f'frA/{f:04d}.jpg'); b = out[f]
    if b: cv2.rectangle(im, (b[0], b[1]), (b[0] + b[2], b[1] + b[3]), (0, 0, 255), 2); c = im[max(0,b[1]-80):b[1]+b[3]+80, max(0,b[0]-80):b[0]+b[2]+80]
    else: c = im[:200, :200]
    c = cv2.resize(c, (200, 200)); cv2.putText(c, str(f), (3, 16), 0, 0.5, (0, 255, 255), 1); tiles.append(c)
while len(tiles) % 10: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite('sh/gkbox.jpg', np.vstack([np.hstack(tiles[i:i+10]) for i in range(0, len(tiles), 10)]))
