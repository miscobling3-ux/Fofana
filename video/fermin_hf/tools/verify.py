"""Verification on the FINAL rendered mp4.

1. Labels, every frame: red arrow tip measured in the render vs the top of the head below it
   (tolerance 0..16 px above, +-6 px horizontally) + zoomed contact sheets of all label frames.
2. Clean picture: top / bottom strips every 0.5 s (score bug, watermark, hashtag must never show).
3. Right source frame: every output frame compared to the planned source frame (through the camera).

python3 tools/verify.py renders/final.mp4 <frames_a> <frames_b> <outdir>
"""
import sys, json, os, math
import numpy as np, cv2

mp4, FA, FB, out = sys.argv[1:5]
FR = {"a": FA, "b": FB}
os.makedirs(out, exist_ok=True)
state = json.load(open("data/state.json"))["frames"]
cap = cv2.VideoCapture(mp4)
frames = []
while True:
    ok, im = cap.read()
    if not ok: break
    frames.append(im)
print("rendered frames:", len(frames), "planned:", len(state))

def grass(im):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); h, s, v = cv2.split(hsv)
    return (h >= 28) & (h <= 95) & (s >= 45) & (v >= 75)

# ---------------------------------------------------------------- 1. labels
res = []; tiles = []
for e in state:
    if "label" not in e or e["k"] >= len(frames): continue
    im = frames[e["k"]]; L = e["label"]
    x, y = int(L["x"]), int(L.get("tip", L["y"]))
    x0, x1 = max(0, x - 60), min(1080, x + 60); y0, y1 = max(0, y - 120), min(1920, y + 25)
    roi = im[y0:y1, x0:x1].astype(int)
    red = (roi[:, :, 2] > 190) & (roi[:, :, 1] < 90) & (roi[:, :, 0] < 90)
    ys, xs = np.nonzero(red)
    if len(ys) < 6:
        res.append((e["k"], None, None, "no arrow")); continue
    tip_y = ys.max() + y0
    bottom = ys >= ys.max() - 3
    tip_x = xs[bottom].mean() + x0
    # head top: first non-grass, non-arrow row under the tip (column band +-14 px)
    g = grass(im)
    head = None
    for yy in range(int(tip_y) + 1, min(1920, int(tip_y) + 60)):
        band = ~g[yy, int(tip_x) - 14:int(tip_x) + 15]
        rowpx = im[yy, int(tip_x) - 14:int(tip_x) + 15].astype(int)
        notred = ~((rowpx[:, 2] > 150) & (rowpx[:, 1] < 90))
        outline = (rowpx.sum(1) < 120)            # arrow's dark outline right under the tip
        cnt = (band & notred).sum()
        if yy <= tip_y + 3 and outline.any(): continue
        if cnt >= 4: head = yy; break
    if head is None:
        res.append((e["k"], round(tip_x, 1), None, "no head")); continue
    hb = ~g[head:head + 12, int(tip_x) - 40:int(tip_x) + 41]
    cols = np.nonzero(hb.any(0))[0]
    # head centre = middle of the contiguous non-grass run that contains the tip column
    c = 40; lo = hi = c
    colset = set(cols.tolist())
    if c in colset:
        while lo - 1 in colset: lo -= 1
        while hi + 1 in colset: hi += 1
        hcx = int(tip_x) - 40 + (lo + hi) / 2
    else:
        hcx = int(tip_x) - 40 + cols.mean() if len(cols) else tip_x
    gap = head - tip_y; dx = tip_x - hcx
    res.append((e["k"], round(float(gap), 1), round(float(dx), 1), "ok" if (0 <= gap <= 16 and abs(dx) <= 6) else "OUT"))
    z = im[max(0, int(tip_y) - 70):int(tip_y) + 60, max(0, int(tip_x) - 65):int(tip_x) + 65].copy()
    z = cv2.resize(z, (130 * 2, z.shape[0] * 2)) if z.size else np.zeros((260, 260, 3), np.uint8)
    cv2.putText(z, f"{e['k']} g{gap:.0f} dx{dx:.0f}", (3, 14), 0, 0.45, (0, 255, 255) if res[-1][3] == "ok" else (0, 0, 255), 1)
    tiles.append(cv2.copyMakeBorder(z, 0, max(0, 260 - z.shape[0]), 0, 0, cv2.BORDER_CONSTANT)[:260])
n_ok = sum(1 for r in res if r[3] == "ok")
print(f"label frames: {len(res)}  within tolerance: {n_ok}  out: {len(res) - n_ok}")
bad = [r for r in res if r[3] != "ok"]
for r in bad[:40]: print("   ", r)
json.dump(res, open(f"{out}/labels.json", "w"))
cols = 14
for p in range(0, len(tiles), cols * 8):
    chunk = tiles[p:p + cols * 8]
    while len(chunk) % cols: chunk.append(np.zeros_like(tiles[0]))
    cv2.imwrite(f"{out}/labels_{p // (cols * 8):02d}.jpg", np.vstack([np.hstack(chunk[k:k + cols]) for k in range(0, len(chunk), cols)]), [cv2.IMWRITE_JPEG_QUALITY, 70])

# ---------------------------------------------------------------- 2. clean picture strips
strips = []
for k in range(0, len(frames), 15):
    im = frames[k]
    top = cv2.resize(im[:420], (270, 105)); bot = cv2.resize(im[-420:], (270, 105))
    t = np.vstack([top, np.full((4, 270, 3), 255, np.uint8), bot])
    cv2.putText(t, f"{k / 30:.1f}s", (3, 12), 0, 0.4, (0, 255, 255), 1); strips.append(t)
cols = 12
while len(strips) % cols: strips.append(np.zeros_like(strips[0]))
cv2.imwrite(f"{out}/strips.jpg", np.vstack([np.hstack(strips[k:k + cols]) for k in range(0, len(strips), cols)]), [cv2.IMWRITE_JPEG_QUALITY, 75])

# ---------------------------------------------------------------- 3. right source frame
worst = []
for e in state[::3]:
    if e["k"] >= len(frames): continue
    x0, y0, Hc = e["cam"]; s = 1920 / Hc
    src = cv2.imread(f"{FR[e['clip']]}/{e['f']:04d}.jpg")
    M = np.float32([[s, 0, -x0 * s], [0, s, -y0 * s]])
    exp = cv2.warpAffine(src, M, (1080, 1920))
    got = frames[e["k"]]
    m = np.zeros((1920, 1080), bool); m[300:1550, 60:1020] = True        # away from subtitles / banner
    a = cv2.cvtColor(exp, cv2.COLOR_BGR2GRAY)[m].astype(float); b = cv2.cvtColor(got, cv2.COLOR_BGR2GRAY)[m].astype(float)
    best = np.corrcoef(a, b)[0, 1]
    # compare with neighbouring source frames: the planned one must match best
    alt = []
    for df in (-2, 2):
        p = f"{FR[e['clip']]}/{e['f'] + df:04d}.jpg"
        if os.path.exists(p):
            ex2 = cv2.warpAffine(cv2.imread(p), M, (1080, 1920))
            alt.append(np.corrcoef(cv2.cvtColor(ex2, cv2.COLOR_BGR2GRAY)[m].astype(float), b)[0, 1])
    worst.append((e["k"], round(best, 3), round(max(alt), 3) if alt else None))
mism = [w for w in worst if w[2] is not None and w[2] > w[1] + 0.01]
print("source-frame check:", len(worst), "frames sampled; min corr", min(w[1] for w in worst), "; neighbour matched better:", len(mism))
for w in mism[:15]: print("   ", w)
