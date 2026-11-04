"""Planche de grilles 10 px zoomées pour poser des images clés à la main."""
import cv2, numpy as np, sys, json
from blobs import frame
def kgrid(clip, items, out, half=(90, 70), s=3, per=4):
    ims = []
    for n, (cx, cy) in items:
        x1, y1 = int(cx - half[0]), int(cy - half[1])
        im = frame(clip, n)[y1:y1 + 2 * half[1], x1:x1 + 2 * half[0]]
        im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_NEAREST)
        for x in range((x1 // 10 + 1) * 10, x1 + 2 * half[0], 10):
            c = (0, 0, 255) if x % 50 == 0 else (90, 90, 90)
            cv2.line(im, ((x - x1) * s, 0), ((x - x1) * s, im.shape[0]), c, 1)
            if x % 50 == 0: cv2.putText(im, str(x), ((x - x1) * s + 2, 12), 0, 0.4, (0, 0, 255), 1)
        for y in range((y1 // 10 + 1) * 10, y1 + 2 * half[1], 10):
            c = (255, 0, 0) if y % 50 == 0 else (90, 90, 90)
            cv2.line(im, (0, (y - y1) * s), (im.shape[1], (y - y1) * s), c, 1)
            if y % 50 == 0: cv2.putText(im, str(y), (2, (y - y1) * s - 2), 0, 0.4, (255, 0, 0), 1)
        cv2.putText(im, f"{clip}{n}", (4, im.shape[0] - 6), 0, 0.7, (0, 255, 255), 2)
        ims.append(im)
    while len(ims) % per: ims.append(ims[0] * 0)
    cv2.imwrite(out, np.vstack([np.hstack(ims[i:i + per]) for i in range(0, len(ims), per)]))
if __name__ == "__main__":
    clip = sys.argv[1]; items = json.loads(sys.argv[2]); out = sys.argv[3]
    kgrid(clip, [(int(k), v) for k, v in items], out)
