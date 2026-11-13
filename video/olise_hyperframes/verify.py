"""Checks on the FINAL rendered video: tag tip vs head (every frame), clean top/bottom strips, spotlight sheets, sync stills."""
import json, sys, subprocess, numpy as np, cv2
S = '/tmp/claude-0/-home-user-Fofana/adbce7f5-53e3-54dc-bd95-fa9317b2d1f9/scratchpad'
video = sys.argv[1]
plan = json.load(open(S + '/work/plan.json'))
F = plan['frames']
cap = cv2.VideoCapture(video)
frames = []
while True:
    ok, im = cap.read()
    if not ok: break
    frames.append(im)
print('decoded', len(frames), 'planned', len(F))
bad = []; rows = []; tiles = []
for i, fr in enumerate(F[:len(frames)]):
    g = fr['tag']
    if not g: continue
    im = frames[i]; hx, hy = g['head']
    x0, x1 = int(max(0, hx - 60)), int(min(1080, hx + 60)); y0, y1 = int(max(0, hy - 140)), int(min(1920, hy + 20))
    roi = im[y0:y1, x0:x1].astype(int)
    B, G, R = roi[..., 0], roi[..., 1], roi[..., 2]
    red = (R > 170) & (G < 90) & (B < 90)
    ys, xs = np.nonzero(red)
    if len(ys) < 30:
        bad.append((i, 'no-arrow')); continue
    tip_y = ys.max() + y0
    tip_x = float(np.median(xs[ys >= ys.max() - 4])) + x0
    # red fill ends ~3 px above the outline tip
    gap = hy - (tip_y + 3); dx = tip_x - hx
    rows.append((i, round(gap, 1), round(dx, 1)))
    if not (0 <= gap <= 16 and abs(dx) <= 6): bad.append((i, gap, dx))
    if i % 1 == 0:
        c = im[int(max(0, hy - 120)):int(min(1920, hy + 80)), int(max(0, hx - 100)):int(min(1080, hx + 100))].copy()
        c = cv2.resize(c, (200, 200))
        cv2.putText(c, str(i), (3, 16), 0, 0.5, (0, 255, 255), 1)
        tiles.append(c)
print('tag frames', len(rows), 'out of tolerance', len(bad))
print('gap range', min(r[1] for r in rows), max(r[1] for r in rows), 'dx range', min(r[2] for r in rows), max(r[2] for r in rows))
print('bad sample', bad[:20])
json.dump(dict(rows=rows, bad=bad), open(S + '/work/verify_tags.json', 'w'), default=float)
def sheet(ts, out, cols=12):
    ts = list(ts)
    while len(ts) % cols: ts.append(np.zeros_like(ts[0]))
    cv2.imwrite(out, np.vstack([np.hstack(ts[k:k + cols]) for k in range(0, len(ts), cols)]), [cv2.IMWRITE_JPEG_QUALITY, 70])
for k in range(0, len(tiles), 240):
    sheet(tiles[k:k + 240], f'{S}/frames/v_tags_{k // 240}.jpg', 16)
# clean image: top 330 px and bottom 330 px every 0.5 s
tops = []; bots = []
for i in range(0, len(frames), 15):
    t = cv2.resize(frames[i][:330], (270, 82)); b = cv2.resize(frames[i][-330:], (270, 82))
    cv2.putText(t, f'{i/30:.1f}', (3, 14), 0, 0.45, (0, 255, 255), 1); tops.append(t); bots.append(b)
sheet(tops, S + '/frames/v_top.jpg', 8); sheet(bots, S + '/frames/v_bot.jpg', 8)
# spotlight sheets every 4 frames
sp = []
for i, fr in enumerate(F[:len(frames)]):
    if fr['spot'] and i % 4 == 0:
        t = cv2.resize(frames[i], (180, 320)); cv2.putText(t, str(i), (3, 14), 0, 0.45, (0, 255, 255), 1); sp.append(t)
for k in range(0, len(sp), 60): sheet(sp[k:k + 60], f'{S}/frames/v_spot_{k // 60}.jpg', 12)
