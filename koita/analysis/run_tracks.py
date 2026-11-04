import json, sys, cv2, numpy as np
from blobs import frame
from track import track, headtop, silhouette
from scipy.ndimage import gaussian_filter1d
CFG = {
 "jovic_A":   ("A", 190, 292, 200, (705, 525), "yellow"),
 "koita_A":   ("A", 150, 452, 300, (1095, 600), "yellow"),
 "cucu_A":    ("A", 290, 440, 300, (1125, 545), "white"),
 "courtois_A":("A", 405, 480, 450, (1265, 455), "orange"),
 "koita_Bh":  ("B", 225, 356, 250, (736, 671), "yellow"),
 "koita_Bl":  ("B", 550, 642, 570, (683, 420), "yellow"),
}
KEYS = json.load(open("keys.json")) if __import__("os").path.exists("keys.json") else {}
def run(name):
    clip, a, b, n0, p0, kind = CFG[name]
    keys = {int(k): v for k, v in KEYS.get(name, {}).items()}
    fw = track(clip, n0, b, *p0, kind=kind, keys=keys)
    bw = track(clip, n0, a, *p0, kind=kind, keys=keys, step=-1)
    tr = {**bw, **fw}
    ns = sorted(tr)
    xs = gaussian_filter1d(np.array([tr[n]["torso"][0] for n in ns]), 1.0)
    ys = gaussian_filter1d(np.array([tr[n]["torso"][1] for n in ns]), 1.0)
    out = {}
    for n, x, y in zip(ns, xs, ys):
        img = frame(clip, n)
        hx, hy = headtop(img, x, y, 7)
        sil = silhouette(img, x, y, 40)
        out[n] = {"torso": [round(x, 1), round(y, 1)], "head": [round(hx, 1), round(hy, 1)], "sil": sil}
    # manual head overrides
    for k, v in KEYS.get(name + "_head", {}).items():
        if int(k) in out: out[int(k)]["head"] = v; out[int(k)]["manual"] = True
    json.dump(out, open(f"tr_{name}.json", "w"))
    return out
def sheet(name, out, path, every=1, half=55, s=2.0, per=12):
    clip = CFG[name][0]
    ims = []
    for n in sorted(out)[::every]:
        d = out[n]; hx, hy = d["head"]
        img = frame(clip, n)
        x1, y1 = int(hx - half), int(hy - half * 0.6)
        crop = img[max(0, y1):y1 + int(half * 2), max(0, x1):x1 + half * 2].copy()
        crop = cv2.resize(crop, (int(half * 2 * s), int(half * 2 * s)))
        cx, cy = int((hx - x1) * s), int((hy - y1) * s)
        cv2.line(crop, (cx - 10, cy), (cx + 10, cy), (0, 0, 255), 1); cv2.line(crop, (cx, cy - 10), (cx, cy + 10), (0, 0, 255), 1)
        if d.get("sil"):
            X1, Y1, X2, Y2 = d["sil"]; cv2.rectangle(crop, (int((X1 - x1) * s), int((Y1 - y1) * s)), (int((X2 - x1) * s), int((Y2 - y1) * s)), (255, 0, 255), 1)
        cv2.putText(crop, str(n), (3, 16), 0, 0.55, (0, 255, 255), 2)
        ims.append(crop)
    while len(ims) % per: ims.append(ims[0] * 0)
    cv2.imwrite(path, np.vstack([np.hstack(ims[i:i + per]) for i in range(0, len(ims), per)]))
if __name__ == "__main__":
    AN = "/tmp/claude-0/-home-user-Fofana/daca3ac7-e701-5674-9337-1a49ad094954/scratchpad/an"
    for name in sys.argv[1:]:
        out = run(name)
        sheet(name, out, f"{AN}/tr_{name}.jpg", every=int(__import__('os').environ.get("EVERY", 1)))
        print(name, len(out))
