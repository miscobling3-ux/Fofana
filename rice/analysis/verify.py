# Vérification de la vidéo FINALE (analyse uniquement).
import json, subprocess, math, sys, numpy as np, cv2
VID = sys.argv[1]; OUT = 'analysis/verif'
import os; os.makedirs(OUT, exist_ok=True)
P = json.load(open('analysis/plan.json')); T = json.load(open('analysis/tracks.json'))
W, H = 1080, 1920
frames = P['frames']
tags = {w: {round(e[0] * 30): e for e in [json.loads(x) for x in v]} for w, v in P['tags'].items()}
spot = {round(json.loads(x)[0] * 30): json.loads(x) for x in P['spots']}
SRC = {'A': (720, 960), 'B': (572, 626)}

def expected(f):
    S, cx, cy = f['cam']; src = f['src']
    im = cv2.imread(f"frames/{src}/{f['sf']:04d}.jpg")
    M = np.float32([[S, 0, W / 2 - cx * S], [0, S, H / 2 - cy * S]])
    return cv2.warpAffine(im, M, (W, H))

p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', VID, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
res_corr = []; tag_err = []; tag_tiles = []; spot_tiles = []; edge_tiles = []
n = 0
while True:
    buf = p.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    im = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    if n < len(frames):
        f = frames[n]
        # 1) bonne image source : corrélation avec l'image attendue (zone hors sous-titres)
        if n % 3 == 0:
            def g(img): 
                x = cv2.cvtColor(cv2.resize(img[200:1550], (108, 135)), cv2.COLOR_BGR2GRAY).astype(float); x -= x.mean(); return x / (np.sqrt((x * x).sum()) + 1e-9)
            a = g(im); best = None
            for k in range(-4, 5):
                ff = dict(f); ff['sf'] = f['sf'] + k
                if not os.path.exists(f"frames/{f['src']}/{ff['sf']:04d}.jpg"): continue
                c = float((a * g(expected(ff))).sum())
                if best is None or c > best[1]: best = (k, c)
            c0 = float((a * g(expected(f))).sum())
            res_corr.append((n, f['shot'], f['sf'], c0, best[0], best[1]))
        # 2) étiquettes : pointe rouge mesurée vs haut de la tête
        for w, d in tags.items():
            if n in d:
                _, x, y, dx = d[n]
                head_y = y + 5 * abs(math.sin(2 * math.pi * 1.4 * n / 30))
                x0, x1 = int(max(0, x - 40)), int(min(W, x + 40)); y0, y1 = int(max(0, y - 100)), int(min(H, y + 8))
                roi = im[y0:y1, x0:x1].astype(int)
                red = (roi[:, :, 2] > 225) & (roi[:, :, 1] < 70) & (roi[:, :, 0] < 70)
                ys, xs = np.where(red)
                if len(ys):
                    ty = y0 + ys.max(); tx = x0 + xs[ys >= ys.max() - 3].mean()
                    tag_err.append((n, w, float(head_y - ty), float(tx - x)))
                else:
                    tag_err.append((n, w, None, None))
                c = im[int(max(0, head_y - 70)):int(head_y + 50), int(max(0, x - 60)):int(x + 60)].copy()
                c = cv2.resize(c, (120, 120)) if c.size else np.zeros((120, 120, 3), np.uint8)
                cv2.putText(c, str(n), (2, 12), 0, 0.4, (0, 255, 255), 1); tag_tiles.append(c)
        # 3) spotlight : planche toutes les 4 images
        if n in spot and n % 4 == 0:
            _, x, y, r = spot[n]
            c = im[int(max(0, y - r - 30)):int(min(H, y + r + 30)), int(max(0, x - r - 30)):int(min(W, x + r + 30))]
            c = cv2.resize(c, (160, 160)); cv2.putText(c, str(n), (2, 12), 0, 0.4, (0, 255, 255), 1); spot_tiles.append(c)
    # 4) image propre : haut et bas toutes les 0,5 s
    if n % 15 == 0:
        edge_tiles.append(np.vstack([cv2.resize(im[:320], (216, 64)), cv2.resize(im[1600:], (216, 64))]))
    n += 1

def sheet(tiles, cols, path):
    if not tiles: return
    while len(tiles) % cols: tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
    for k in range(0, len(rows), 12): cv2.imwrite(f'{path}_{k // 12:02d}.jpg', np.vstack(rows[k:k + 12]))
sheet(tag_tiles, 16, f'{OUT}/tags'); sheet(spot_tiles, 10, f'{OUT}/spots'); sheet(edge_tiles, 10, f'{OUT}/edges')
bad_tag = [e for e in tag_err if e[2] is None or not (0 <= e[2] <= 16 and abs(e[3]) <= 6)]
low = [r for r in res_corr if abs(r[4]) > 1 and r[5] - r[3] > 0.02]
json.dump(dict(frames=n, corr=res_corr, tag=tag_err), open(f'{OUT}/report.json', 'w'))
print('images rendues', n, 'attendues', len(frames))
print('image source : %d contrôles, meilleure correspondance décalée de plus d\'1 image : %d' % (len(res_corr), len(low)), low[:10])
print('étiquettes mesurées', len(tag_err), 'hors tolérance', len(bad_tag), bad_tag[:15])
