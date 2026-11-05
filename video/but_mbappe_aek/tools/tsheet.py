"""Planche zoomée : toutes les images d'un suivi avec la croix sur le haut de la tête.
tsheet.py framesdir track.json out.jpg [step] [half] [cols]"""
import sys, json, cv2, numpy as np
d, tj, out = sys.argv[1:4]; st = int(sys.argv[4]) if len(sys.argv) > 4 else 1
half = int(sys.argv[5]) if len(sys.argv) > 5 else 40; cols = int(sys.argv[6]) if len(sys.argv) > 6 else 12
T = json.load(open(tj)); fs = sorted(map(int, T))[::st]
tiles = []
for f in fs:
    im = cv2.imread(f'{d}/{f:04d}.jpg'); hx, hy = T[str(f)]['head']
    hx, hy = int(hx), int(hy)
    pad = cv2.copyMakeBorder(im, half, half, half, half, cv2.BORDER_CONSTANT)
    c = pad[hy:hy + 2 * half, hx:hx + 2 * half].copy()
    c = cv2.resize(c, (160, 160), interpolation=cv2.INTER_NEAREST)
    cv2.line(c, (80, 60), (80, 100), (0, 0, 255), 1); cv2.line(c, (60, 80), (100, 80), (0, 0, 255), 1)
    cv2.putText(c, str(f), (3, 14), 0, 0.45, (0, 255, 255), 1)
    tiles.append(c)
while len(tiles) % cols: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out, np.vstack([np.hstack(tiles[i:i+cols]) for i in range(0, len(tiles), cols)]))
