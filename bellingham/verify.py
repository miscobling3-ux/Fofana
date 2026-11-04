# Vérification sur la vidéo FINALE rendue : étiquettes image par image, image propre, projecteur, synchro, son.
import cv2, json, sys, subprocess, re, numpy as np, os
B = '/home/user/Fofana/bellingham'
VID = sys.argv[1]; OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
P = json.load(open(f'{B}/analysis/plan.json'))
cap = cv2.VideoCapture(VID); N = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); FPS = cap.get(cv2.CAP_PROP_FPS)
frames = {}
def get(n):
    if n not in frames:
        cap.set(cv2.CAP_PROP_POS_FRAMES, n); ok, f = cap.read(); frames[n] = f if ok else None
    return frames[n]
def grid(ims, cols):
    while len(ims) % cols: ims.append(np.zeros_like(ims[0]))
    return np.vstack([np.hstack(ims[i:i + cols]) for i in range(0, len(ims), cols)])
report = {}

# 1) étiquettes : pointe rouge mesurée vs haut de la tête, sur CHAQUE image où l'étiquette est affichée
tag_rows = []; tiles = []
for te in P['tags']:
    HJ = json.load(open(f'{B}/analysis/heads.json'))
    HH = {int(k): v for k, v in HJ['vini_a'].items()} if 'Vin' in te['name'] else {int(k): v for k, v in HJ['cuc_hc'].items()}
    bias = -2 if 'Vin' in te['name'] else 0
    for n in range(N):
        t = n / FPS
        if not (te['t0'] + 0.13 <= t < te['t1'] - 1e-3): continue   # après le « pop » de 0,12 s
        f = get(n)
        red = (f[..., 2] > 200) & (f[..., 1] < 90) & (f[..., 0] < 90)
        ys, xs = np.where(red)
        if len(ys) == 0: tag_rows.append((n, None, None)); continue
        tipy = ys.max(); tipx = xs[ys >= tipy - 2].mean()
        # image source affichée à cet instant + transformation (recadrage, petit zoom de coupe)
        im = [i for i in P['images'] if i['t0'] <= t < i['t1']][-1]
        x0, y0, h = im['crop']; sc = 1920 / h
        st = max(sh['t0'] for sh in P['shots'] if sh['t0'] <= t)
        u = (t - st) / 0.1; pz = 1.0 if (u >= 1 or st == 0) else 1.07 - 0.07 * (1 - (1 - u) ** 2)
        sx = 540 + (tipx - 540) / pz; sy = 960 + (tipy - 960) / pz
        srcx, srcy = x0 + sx / sc, y0 + sy / sc
        hx, hy = HH[im['f']]; hy += bias
        d = (hy - srcy) * sc * pz          # écart vertical en pixels de sortie (pointe au-dessus = positif)
        dx = (srcx - hx) * sc * pz
        tag_rows.append((n, round(float(d), 1), round(float(dx), 1)))
        c = f[max(0, tipy - 70): tipy + 80, max(0, int(tipx) - 75): int(tipx) + 75].copy()
        c = cv2.resize(c, (150, 150)); c = cv2.resize(c, (300, 300), interpolation=cv2.INTER_NEAREST)
        hxo = (hx - x0) * sc; hyo = (hy - y0) * sc; hxo = 540 + (hxo - 540) * pz; hyo = 960 + (hyo - 960) * pz
        cx_, cy_ = int((hxo - (int(tipx) - 75)) * 2), int((hyo - max(0, tipy - 70)) * 2)
        cv2.drawMarker(c, (cx_, cy_), (0, 255, 255), cv2.MARKER_CROSS, 16, 1)
        cv2.putText(c, f'{n} d={d:.0f} dx={dx:.0f}', (3, 16), 0, 0.45, (255, 0, 255), 1)
        tiles.append(c)
ok = [r for r in tag_rows if r[1] is not None and 0 <= r[1] <= 16 and abs(r[2]) <= 6]
bad = [r for r in tag_rows if r not in ok]
report['tags'] = dict(frames=len(tag_rows), ok=len(ok), bad=bad, all=tag_rows)
for i in range(0, len(tiles), 60): cv2.imwrite(f'{OUT}/tags_{i // 60}.jpg', grid(tiles[i:i + 60], 10))

# 2) image propre : haut et bas de l'image toutes les 0,5 s
tops, bots = [], []
for k, t in enumerate(np.arange(0.25, N / FPS, 0.5)):
    f = get(int(t * FPS))
    a = cv2.resize(f[0:420], (270, 105)); b = cv2.resize(f[1480:1920], (270, 110))
    cv2.putText(a, f'{t:.1f}', (3, 14), 0, 0.45, (255, 0, 255), 1); tops.append(a); bots.append(b)
cv2.imwrite(f'{OUT}/clean_top.jpg', grid(tops, 12)); cv2.imwrite(f'{OUT}/clean_bottom.jpg', grid(bots, 12))

# 3) projecteur : toutes les 4 images
for i, sp in enumerate(P['spots']):
    ims = []
    for n in range(int(sp['t0'] * FPS), int(sp['t1'] * FPS), 4):
        f = cv2.resize(get(n), (270, 480)); cv2.putText(f, str(n), (3, 16), 0, 0.5, (255, 0, 255), 1); ims.append(f)
    cv2.imwrite(f'{OUT}/spot_{i}.jpg', grid(ims, 8))

# 4) synchro voix/image : 28 instants clés (mot affiché + image)
keys = ['gol', 'bellingham', 'carrera', 'todo', 'bernardo', 'vinícius', 'recibe', 'momento', 'defensor', 'cucurella', 'devolverle', 'fuera', 'perfila', 'zurda', 'mbappé', 'banda', 'cuanto', 'avanza', 'fíjate', 'alineados', 'jugadores', 'piensan', 'espacios', 'centrar', 'cabeza', 'velocidad', 'pase', 'controla', 'tacón', 'fondo']
ims = []; used = set(); sync = []
for k in keys:
    for a, b, w in P['subs']:
        if w.startswith(k.lower()) and (a, w) not in used and a > (sync[-1][1] if sync else -1):
            used.add((a, w)); n = int((a + 0.05) * FPS); f = cv2.resize(get(n), (270, 480))
            cv2.putText(f, f'{a:.2f}s {w}', (3, 16), 0, 0.5, (0, 255, 255), 1); ims.append(f); sync.append((k, a)); break
cv2.imwrite(f'{OUT}/sync.jpg', grid(ims, 7)); report['sync_points'] = len(ims)

# 5) son
r = subprocess.run(['ffmpeg', '-nostats', '-i', VID, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
I = re.findall(r'I:\s+(-?[\d.]+) LUFS', r)[-1]; TP = re.findall(r'Peak:\s+(-?[\d.]+) dBFS', r)[-1]
report['loudness'] = dict(I=float(I), true_peak=float(TP))
pr = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration,size:stream=codec_name,width,height,r_frame_rate', '-of', 'json', VID], capture_output=True, text=True).stdout
report['probe'] = json.loads(pr)
json.dump(report, open(f'{OUT}/report.json', 'w'), indent=1, default=str)
print(json.dumps({k: (v if k != 'tags' else dict(frames=v['frames'], ok=v['ok'], bad=v['bad'][:20])) for k, v in report.items()}, indent=1, default=str))
