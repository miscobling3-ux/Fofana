"""Mesure la pointe rouge dans chaque image rendue où une étiquette est affichée,
et la compare au haut de la tête prévu (position mesurée sur la source, projetée)."""
import json, sys, cv2, numpy as np
S = '/tmp/claude-0/-home-user-Fofana/741607e6-9b49-5de3-8cc7-6117fa097297/scratchpad'
D = sys.argv[1] if len(sys.argv) > 1 else 'outfr3'
p = json.load(open(f'{S}/proj/plan.json')); F = p['frames']
res = []; bad = []
for k, st in enumerate(F):
    if 'tag' not in st: continue
    x, y = st['tag'][0], st['tag'][1]
    im = cv2.imread(f'{S}/{D}/{k+1:04d}.jpg')
    if im is None: continue
    x0, y0 = int(max(0, x - 60)), int(max(0, y - 160)); reg = im[y0:int(y + 20), x0:int(x + 60)].astype(int)
    b, g, r = reg[..., 0], reg[..., 1], reg[..., 2]
    m = (r > 190) & (g < 100) & (b < 100)
    ys, xs = np.where(m)
    if len(ys) < 30: bad.append((k, 'pas de flèche')); continue
    ty = ys.max(); tx = xs[ys >= ty - 3].mean()
    dy = y - (y0 + ty); dx = (x0 + tx) - x
    res.append((k, float(dx), float(dy)))
    if not (0 <= dy <= 16 and abs(dx) <= 6): bad.append((k, round(dx, 1), round(dy, 1)))
r = np.array([[a[1], a[2]] for a in res])
print('images avec étiquette', len(res), 'dx', r[:, 0].min().round(1), r[:, 0].max().round(1), 'dy', r[:, 1].min().round(1), r[:, 1].max().round(1))
print('hors tolérance', len(bad), bad[:30])
json.dump(res, open(f'{S}/proj/tagcheck.json', 'w'))
