import sys, cv2
# grid.py img out [x y w h] [scale]
im = cv2.imread(sys.argv[1]); out = sys.argv[2]
x, y, w, h = map(int, sys.argv[3:7]) if len(sys.argv) > 6 else (0, 0, im.shape[1], im.shape[0])
sc = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
step = int(sys.argv[8]) if len(sys.argv) > 8 else 50
c = im[y:y+h, x:x+w].copy()
for gx in range((x // step + 1) * step, x + w, step):
    cv2.line(c, (gx - x, 0), (gx - x, h), (0, 255, 255) if gx % (step*2) == 0 else (0, 140, 255), 1)
    if gx % (step*2) == 0: cv2.putText(c, str(gx), (gx - x + 2, 14), 0, 0.45, (0, 255, 255), 1)
for gy in range((y // step + 1) * step, y + h, step):
    cv2.line(c, (0, gy - y), (w, gy - y), (0, 255, 255) if gy % (step*2) == 0 else (0, 140, 255), 1)
    if gy % (step*2) == 0: cv2.putText(c, str(gy), (2, gy - y - 2), 0, 0.45, (0, 255, 255), 1)
c = cv2.resize(c, None, fx=sc, fy=sc, interpolation=cv2.INTER_CUBIC)
cv2.imwrite(out, c)
