import sys, cv2, numpy as np
# usage: sheet.py dir f0 f1 step x y w h out [cols] [scale]
d, f0, f1, st, x, y, w, h, out = sys.argv[1:10]
cols = int(sys.argv[10]) if len(sys.argv) > 10 else 6
sc = float(sys.argv[11]) if len(sys.argv) > 11 else 0.5
f0, f1, st, x, y, w, h = map(int, (f0, f1, st, x, y, w, h))
tiles = []
for f in range(f0, f1 + 1, st):
    im = cv2.imread(f'{d}/{f:04d}.jpg')[y:y+h, x:x+w]
    im = cv2.resize(im, None, fx=sc, fy=sc)
    cv2.putText(im, str(f), (5, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    tiles.append(im)
while len(tiles) % cols: tiles.append(np.zeros_like(tiles[0]))
rows = [np.hstack(tiles[i:i+cols]) for i in range(0, len(tiles), cols)]
cv2.imwrite(out, np.vstack(rows))
