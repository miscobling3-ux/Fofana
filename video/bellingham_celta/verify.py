"""Vérification de la vidéo FINALE : étiquettes image par image, bonne image source, cadre propre, planches."""
import cv2, json, sys, numpy as np
S = '/tmp/claude-0/-home-user-Fofana/9ccd27b4-b15c-5bb0-8040-d62d7f187762/scratchpad'
video = sys.argv[1]
plan = json.load(open(f'{S}/plan.json')); F = plan['frames']
cap = cv2.VideoCapture(video)
tag_rows = []; src_err = []; tiles = []; clean_top = []; clean_bot = []
n = 0
while True:
    ok, im = cap.read()
    if not ok or n >= len(F): break
    fr = F[n]
    # 1) bonne image source : recadrage attendu vs rendu (zone sans incrustations, basse résolution)
    src = cv2.imread(f'{S}/frames/f{fr["f"]:04d}.jpg')
    M = np.float32([[fr['s'], 0, -fr['x0'] * fr['s']], [0, fr['s'], -fr['y0'] * fr['s']]])
    exp = cv2.warpAffine(src, M, (1080, 1920))
    a = cv2.resize(im[300:1500], (108, 120)).astype(float); b = cv2.resize(exp[300:1500], (108, 120)).astype(float)
    # compare with neighbours to make sure the intended frame is the best match
    errs = {}
    for d in (-2, -1, 0, 1, 2):
        g = fr['f'] + d
        if 0 <= g < 761:
            s2 = cv2.imread(f'{S}/frames/f{g:04d}.jpg'); e2 = cv2.warpAffine(s2, M, (1080, 1920))
            errs[d] = float(np.mean(np.abs(a - cv2.resize(e2[300:1500], (108, 120)).astype(float))))
    src_err.append((n, fr['f'], errs[0], min(errs, key=errs.get)))
    # 2) étiquette : pointe rouge mesurée
    if 'tag' in fr and fr['tag']:
        name, X, Y = fr['tag']
        x0, x1 = int(max(0, X - 60)), int(min(1080, X + 60)); y0, y1 = int(max(0, Y - 140)), int(min(1920, Y + 30))
        roi = im[y0:y1, x0:x1].astype(int)
        red = (roi[..., 2] > 190) & (roi[..., 1] < 90) & (roi[..., 0] < 90)
        ys, xs = np.nonzero(red)
        if len(ys):
            ty = ys.max(); tx = xs[ys >= ty - 2].mean()
            tip = (x0 + tx, y0 + ty)
            tag_rows.append((n, fr['f'], name, X, Y, tip[0], tip[1], Y - tip[1], tip[0] - X))
        else:
            tag_rows.append((n, fr['f'], name, X, Y, None, None, None, None))
        c = im[int(Y) - 70:int(Y) + 50, int(X) - 60:int(X) + 60].copy()
        if c.shape[:2] == (120, 120):
            c = cv2.resize(c, (240, 240), interpolation=cv2.INTER_NEAREST)
            cv2.putText(c, f'{n}/f{fr["f"]}', (3, 14), 0, 0.45, (0, 255, 255), 1); tiles.append(c)
    # 3) cadre propre : bandes du haut et du bas toutes les 0,5 s
    if n % 15 == 0:
        clean_top.append(cv2.resize(im[0:420], (270, 105))); clean_bot.append(cv2.resize(im[1500:1920], (270, 105)))
    n += 1
print('frames read', n)
def grid(t, cols, out):
    if not t: return
    while len(t) % cols: t.append(np.zeros_like(t[0]))
    cv2.imwrite(out, np.vstack([np.hstack(t[k:k + cols]) for k in range(0, len(t), cols)]))
import os; os.makedirs(f'{S}/verif', exist_ok=True)
for k in range(0, len(tiles), 48): grid(tiles[k:k + 48], 8, f'{S}/verif/tags_{k // 48:02d}.jpg')
for k in range(0, len(clean_top), 40):
    grid(clean_top[k:k + 40], 8, f'{S}/verif/top_{k // 40}.jpg'); grid(clean_bot[k:k + 40], 8, f'{S}/verif/bot_{k // 40}.jpg')
bad = [r for r in tag_rows if r[7] is None or not (0 <= r[7] <= 16) or abs(r[8]) > 6]
print('tag frames', len(tag_rows), 'out of tolerance', len(bad))
for r in bad[:20]: print('  BAD', r)
dy = [r[7] for r in tag_rows if r[7] is not None]; dx = [r[8] for r in tag_rows if r[8] is not None]
if dy: print(f'  tip above head: min {min(dy):.1f} max {max(dy):.1f} px ; horizontal: min {min(dx):.1f} max {max(dx):.1f} px')
wrong = [r for r in src_err if r[3] != 0]
print('source frame check: frames', len(src_err), 'where a neighbour matches better', len(wrong), 'mean err', np.mean([r[2] for r in src_err]))
for r in wrong[:15]: print('  ', r)
json.dump({'tags': tag_rows, 'src': src_err}, open(f'{S}/verif/report.json', 'w'), default=float)
