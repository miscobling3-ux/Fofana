import cv2, sys
from blobs import frame
clip, n, x1, y1, x2, y2, out = sys.argv[1], int(sys.argv[2]), *map(int, sys.argv[3:7]), sys.argv[7]
img = frame(clip, n)[y1:y2, x1:x2].copy()
for x in range((x1 // 50 + 1) * 50, x2, 50):
    cv2.line(img, (x - x1, 0), (x - x1, y2 - y1), (0, 0, 255) if x % 100 == 0 else (0, 0, 120), 1)
    if x % 100 == 0: cv2.putText(img, str(x), (x - x1 + 2, 14), 0, 0.45, (0, 0, 255), 1)
for y in range((y1 // 50 + 1) * 50, y2, 50):
    cv2.line(img, (0, y - y1), (x2 - x1, y - y1), (255, 0, 0) if y % 100 == 0 else (120, 0, 0), 1)
    if y % 100 == 0: cv2.putText(img, str(y), (2, y - y1 - 3), 0, 0.45, (255, 0, 0), 1)
s = float(sys.argv[8]) if len(sys.argv) > 8 else 1
img = cv2.resize(img, None, fx=s, fy=s)
cv2.putText(img, f"{clip}{n}", (10, 40), 0, 1.2, (0, 255, 255), 3)
cv2.imwrite(out, img)
