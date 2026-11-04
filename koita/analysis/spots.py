"""Cercles du projecteur, image par image (source), + planches de contrôle toutes les 4 images."""
import json, cv2, numpy as np, sys
from blobs import frame, mask
from scipy.ndimage import gaussian_filter1d
def hd(name): return {int(k): v["head"] for k, v in json.load(open(f"head_{name}.json")).items()}
def from_head(name, n0, n1, dy, r, dx=0):
    h = hd(name); ns = [n for n in range(n0, n1 + 1) if n in h]
    xs = gaussian_filter1d(np.array([h[n][0] for n in ns]), 1.5); ys = gaussian_filter1d(np.array([h[n][1] for n in ns]), 1.5)
    return {n: [round(x + dx, 1), round(y + dy, 1), r] for n, x, y in zip(ns, xs, ys)}
def keeper(n0, n1, box0):
    out, (x1, y1, x2, y2) = {}, box0
    boxes = {}
    for n in range(n0, n1 + 1):
        img = frame("A", n)
        X1, Y1, X2, Y2 = int(x1 - 30), int(y1 - 30), int(x2 + 30), int(y2 + 30)
        m = mask(img[Y1:Y2, X1:X2], "orange")
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        ys, xs = np.where(m > 0)
        if len(xs) > 30:
            x1, x2 = X1 + np.percentile(xs, 1), X1 + np.percentile(xs, 99)
            y1, y2 = Y1 + np.percentile(ys, 1), Y1 + np.percentile(ys, 99)
        boxes[n] = (x1 - 6, y1 - 8, x2 + 6, y2 + 10)  # gants/chaussures/tête : marge
    ns = sorted(boxes)
    cx = gaussian_filter1d(np.array([(boxes[n][0] + boxes[n][2]) / 2 for n in ns]), 1.5)
    cy = gaussian_filter1d(np.array([(boxes[n][1] + boxes[n][3]) / 2 for n in ns]), 1.5)
    R = max(np.hypot(boxes[n][2] - boxes[n][0], boxes[n][3] - boxes[n][1]) / 2 for n in ns) + 10
    return {n: [round(float(x), 1), round(float(y), 1), round(float(R), 1)] for n, x, y in zip(ns, cx, cy)}
SPOTS = {
 "koita_S0":   ("A", from_head("koita_A", 360, 419, 56, 82, 4)),
 "jovic_S3":   ("A", from_head("jovic_A", 196, 232, 58, 82)),
 "koita_f278": ("A", {278: [1028, 614, 82]}),
 "koita_f318": ("A", {318: [1128, 614, 88]}),
 "cucu_f318":  ("A", {318: [1130, 572, 78]}),
 "koita_S14":  ("A", from_head("koita_A", 371, 392, 52, 80, 2)),
 "cucu_f392":  ("A", {392: [1212, 557, 74]}),
 "koita_f404": ("A", {404: [1132, 567, 72]}),
 "cucu_f404":  ("A", {404: [1199, 549, 64]}),
 "cucu_f417":  ("A", {417: [1155, 548, 80]}),
 "courtois":   ("A", keeper(424, 462, (1180, 390, 1260, 470))),
}
if __name__ == "__main__":
    AN = "/tmp/claude-0/-home-user-Fofana/daca3ac7-e701-5674-9337-1a49ad094954/scratchpad/an"
    json.dump({k: {"clip": c, "f": v} for k, (c, v) in SPOTS.items()}, open("spots.json", "w"))
    ims = []
    for k, (clip, d) in SPOTS.items():
        for n in sorted(d)[::4]:
            x, y, r = d[n]
            img = frame(clip, n).copy()
            cv2.circle(img, (int(x), int(y)), int(r), (255, 255, 255), 2)
            c = img[int(y - 110):int(y + 110), int(x - 110):int(x + 110)]
            c = cv2.resize(c, (330, 330)); cv2.putText(c, f"{k} {n}", (4, 18), 0, 0.5, (0, 255, 255), 2)
            ims.append(c)
    per = 8
    while len(ims) % per: ims.append(ims[0] * 0)
    cv2.imwrite(f"{AN}/spots.jpg", np.vstack([np.hstack(ims[i:i + per]) for i in range(0, len(ims), per)]))
    print(len(ims))
