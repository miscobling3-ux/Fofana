import cv2, json, numpy as np, sys
t = cv2.imread('frA/0060.jpg', 0)[903:947, 563:882]
t = cv2.Canny(t, 40, 120).astype(np.float32)
out = {}
for k, n in (('A', 1077), ('B', 887)):
    res = {}
    for f in range(1, n + 1):
        g = cv2.imread(f'fr{k}/{f:04d}.jpg', 0)[700:1080]
        g = cv2.copyMakeBorder(g, 0, 0, 330, 330, cv2.BORDER_CONSTANT)
        e = cv2.Canny(g, 40, 120).astype(np.float32)
        m = cv2.matchTemplate(e, t, cv2.TM_CCORR_NORMED)
        _, mv, _, ml = cv2.minMaxLoc(m)
        x = ml[0] - 330; y = ml[1] + 700
        res[f] = [x, y, x + t.shape[1], y + t.shape[0], round(float(mv), 3)]
    out[k] = res
json.dump(out, open('wm.json', 'w'))
for k in out:
    prev = None
    for f, v in out[k].items():
        key = (v[0] // 20, v[1] // 20)
        if key != prev: print(k, f, v); prev = key
