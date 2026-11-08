"""Verification of the FINAL rendered video (analysis only)."""
import cv2, json, sys, numpy as np
SC = '/tmp/claude-0/-home-user-Fofana/663162a9-9ff1-508a-a745-47f437945801/scratchpad'
video = sys.argv[1]
F = json.load(open(f'{SC}/frames_debug.json'))
OVER = [(84, 30, 318, 180), (1598, 44, 1834, 120), (1724, 864, 1856, 968), (752, 880, 1096, 936), (1562, 992, 1860, 1044)]

# 0. geometry: no crop window touches a TV overlay
bad = []
for f in F:
    w = f['ch']*9/16
    for a in OVER:
        if f['x0'] < a[2] and f['x0']+w > a[0] and f['y0'] < a[3] and f['y0']+f['ch'] > a[1]:
            bad.append(f['k'])
print('overlay-intersections:', len(bad))

def grass(im):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    h, s, v = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    return (h >= 30) & (h <= 85) & (s >= 60) & (v >= 55)

cap = cv2.VideoCapture(video)
rows = []; tiles = []; k = 0
while True:
    ok, im = cap.read()
    if not ok: break
    if k < len(F) and F[k]['tag']:
        ex, ey = F[k]['tag']['x'], F[k]['tag']['y']
        X0, X1 = int(max(0, ex-60)), int(min(1080, ex+60)); Y0, Y1 = int(max(0, ey-140)), int(min(1920, ey+10))
        sub = im[Y0:Y1, X0:X1].astype(int)
        red = (sub[..., 2] > 190) & (sub[..., 1] < 80) & (sub[..., 0] < 80)
        ys, xs = np.nonzero(red)
        if len(ys) > 20:
            ty = ys.max(); tx = xs[ys >= ty-2].mean()
            tipx, tipy = X0+tx, Y0+ty
            # head top under the tip: first row (below tip) where non-grass occupies the centre band
            band = im[int(tipy)+1:int(tipy)+90, max(0,int(tipx)-6):int(tipx)+7]
            gsub = im[max(0,int(tipy)-40):int(tipy)+90, max(0,int(tipx)-40):int(tipx)+41]
            gb = grass(gsub) if gsub.size else np.zeros((0,),bool)
            grass_ratio = gb.mean() if gb.size else 0
            ng = ~grass(band) if band.size else np.zeros((0, 0), bool)
            head = None
            if grass_ratio > 0.35 and ng.size:
                r = ng.mean(1) > 0.35
                for i in range(len(r)-2):
                    if r[i] and r[i+1] and r[i+2]: head = i+1; break
            rows.append(dict(k=k, tipx=round(float(tipx), 1), tipy=round(float(tipy), 1), dx=round(float(tipx-ex), 1),
                             gap=None if head is None else int(head), measurable=head is not None))
        else:
            rows.append(dict(k=k, tipx=None, tipy=None, dx=None, gap=None, measurable=False, missing=True))
        # zoom tile around the tip
        c = im[max(0, int(ey)-110):int(ey)+70, max(0, int(ex)-90):int(ex)+90]
        c = cv2.resize(c, (180, 180)) if c.size else np.zeros((180, 180, 3), np.uint8)
        cv2.putText(c, str(k), (3, 14), 0, 0.45, (0, 255, 255), 1)
        tiles.append(c)
    k += 1
print('frames read', k)
json.dump(rows, open(f'{SC}/verify_tags.json', 'w'))
meas = [r for r in rows if r['measurable']]
ok = [r for r in meas if 0 <= r['gap'] <= 16 and abs(r['dx']) <= 6]
print(f'tag frames: {len(rows)}  measurable(grass bg): {len(meas)}  within tolerance: {len(ok)}  missing arrow: {sum(1 for r in rows if r.get("missing"))}')
offs = [r for r in meas if not (0 <= r['gap'] <= 16)]
print('out-of-tolerance frames (k,gap):', [(r['k'], r['gap']) for r in offs][:80])
# contact sheets of ALL label frames
for i in range(0, len(tiles), 120):
    chunk = tiles[i:i+120]
    while len(chunk) % 12: chunk.append(np.zeros((180, 180, 3), np.uint8))
    sheet = np.vstack([np.hstack(chunk[j:j+12]) for j in range(0, len(chunk), 12)])
    cv2.imwrite(f'{SC}/vsheets/tags_{i//120:02d}.jpg', sheet, [cv2.IMWRITE_JPEG_QUALITY, 80])
