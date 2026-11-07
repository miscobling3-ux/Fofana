#!/usr/bin/env python3
"""Checks on the FINAL render: arrow tip vs head top on every labelled frame, contact sheets."""
import cv2, json, sys, numpy as np
sys.path.insert(0, "/tmp/claude-0/-home-user-Fofana/0dc10ad3-8ae5-5d3f-b08b-3b4d72bae3e6/scratchpad")
from headtop import hair_top
indep = []
S = "/tmp/claude-0/-home-user-Fofana/0dc10ad3-8ae5-5d3f-b08b-3b4d72bae3e6/scratchpad"
vid = sys.argv[1]
plan = json.load(open(S + "/plan.json"))
fr = plan["frames"]
cap = cv2.VideoCapture(vid)
bad, rows, tiles, strips = [], [], [], []
i = 0
while True:
    ok, im = cap.read()
    if not ok: break
    if i < len(fr) and "lab" in fr[i]:
        p, X, Y = fr[i]["lab"]           # X,Y = head top in output pixels (from tracking)
        x0, x1 = int(X - 45), int(X + 45); y0, y1 = int(Y - 140), int(Y + 15)
        win = im[max(0, y0):y1, max(0, x0):x1].astype(int)
        b, g, r = win[..., 0], win[..., 1], win[..., 2]
        red = (r > 200) & (g < 90) & (b < 90)
        ys, xs = np.nonzero(red)
        if len(ys) == 0:
            bad.append((i, "no arrow")); tip = None
        else:
            yb = ys.max(); xb = xs[ys >= yb - 3].mean()
            tipy, tipx = yb + max(0, y0), xb + max(0, x0)
            gap = Y - tipy; dx = tipx - X
            rows.append((i, round(gap, 1), round(dx, 1)))
            if not (0 <= gap <= 16 and abs(dx) <= 6): bad.append((i, gap, dx))
            tip = (int(tipx), int(tipy))
            if p == "mbappe":   # independent check on the RENDERED frame: hair top under the arrow (grass background)
                hx, ht, okm = hair_top(im, tipx, tipy + 40, 0, roi=(45, 38, 60))
                if okm: indep.append((i, round(ht - tipy, 1), round(hx - tipx, 1)))
        c = im[int(Y - 110):int(Y + 110), int(X - 110):int(X + 110)].copy()
        if c.shape[:2] == (220, 220):
            cv2.line(c, (100, 110), (120, 110), (0, 255, 0), 1)
            cv2.putText(c, str(i), (3, 14), 0, 0.45, (0, 255, 255), 1)
            tiles.append(c)
    if i % 15 == 0:   # every 0.5 s: top and bottom strips for TV-overlay check
        strips.append(np.vstack([cv2.resize(im[:300], (270, 75)), cv2.resize(im[-300:], (270, 75))]))
    i += 1
print("frames", i, "labelled", len(rows), "out of tolerance", len(bad))
if rows:
    g = np.array([r[1] for r in rows]); d = np.array([r[2] for r in rows])
    print("gap px min/max", g.min(), g.max(), "dx min/max", d.min(), d.max())
print("bad sample", bad[:20])
if indep:
    a = np.array([r[1] for r in indep]); b = np.array([r[2] for r in indep])
    print("INDEPENDENT (rendered) mbappe: n", len(indep), "tip->hair gap min/max", a.min(), a.max(), "dx min/max", b.min(), b.max(), "out", sum(1 for r in indep if not (0 <= r[1] <= 16 and abs(r[2]) <= 6)))
def sheet(ts, n, out):
    while len(ts) % n: ts.append(np.zeros_like(ts[0]))
    cv2.imwrite(out, np.vstack([np.hstack(ts[k:k + n]) for k in range(0, len(ts), n)]))
for k in range(0, len(tiles), 80):
    sheet(tiles[k:k + 80], 10, f"{S}/ver/labels_{k // 80:02d}.jpg")
sheet(strips, 16, f"{S}/ver/strips.jpg")
json.dump(dict(rows=rows, bad=bad), open(S + "/ver/labels.json", "w"))
