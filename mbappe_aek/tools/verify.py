# Checks on the FINAL rendered video: label tips frame by frame, right source image, clean image, spotlight, sync, audio.
import cv2, json, numpy as np, subprocess, sys, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VID = "output/mbappe_aek_es.mp4"
SCR = sys.argv[1]
FR = json.load(open("work/frames_out.json"))
EDL = json.load(open("work/edl.json"))
cap = cv2.VideoCapture(VID)
frames = []
while True:
    ok, im = cap.read()
    if not ok: break
    frames.append(im)
print("rendered frames", len(frames), "expected", len(FR))
rep = {}

# 1) label tip measured in rendered frame vs head top (expected from track, mapped through the camera)
def red_mask(im):
    b, g, r = cv2.split(im.astype(int))
    return (r > 200) & (g < 80) & (b < 80)
bad = []; rows = []; tiles = []
for f in FR:
    if "lab" not in f: continue
    n = f["n"]; im = frames[n]; L = f["lab"]
    if n / 30 - L["t0"] < 0.12 - 1e-6:
        rep.setdefault("label_pop_frames", []).append(n); continue
    x0, x1 = int(L["x"] - 45), int(L["x"] + 45); y0, y1 = int(L["y"] - 140), int(L["y"] + 10)
    x0 = max(0, x0); y0 = max(0, y0)
    m = red_mask(im[y0:y1, x0:x1])
    ys, xs = np.nonzero(m)
    if len(ys) == 0:
        rows.append((n, None)); bad.append((n, "no arrow")); continue
    ty = ys.max() + y0; tx = np.median(xs[ys >= ys.max() - 3]) + x0
    above = L["y"] - ty; dx = tx - L["x"]
    rows.append((n, round(float(above), 1), round(float(dx), 1)))
    if not (0 <= above <= 16 and abs(dx) <= 6): bad.append((n, round(float(above), 1), round(float(dx), 1)))
    # zoomed tile for visual review (head top marked with a thin cyan tick)
    c = im[max(0, int(L["y"]) - 110):int(L["y"]) + 90, max(0, int(L["x"]) - 100):int(L["x"]) + 100].copy()
    c = cv2.resize(c, (200, 200))
    cv2.putText(c, f"{n}", (3, 14), 0, .45, (0, 255, 255), 1); tiles.append(c)
rep["label_frames"] = len(rows); rep["label_out_of_tolerance"] = bad
def board(tiles, path, cols=12):
    if not tiles: return
    while len(tiles) % cols: tiles.append(np.zeros_like(tiles[0]))
    cv2.imwrite(path, np.vstack([np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]))
for i in range(0, len(tiles), 120):
    board(tiles[i:i + 120], f"{SCR}/v_labels_{i // 120}.jpg")

# 2) right source image: warp expected source with the camera transform and correlate (labels/captions/banner masked)
def expected(f):
    clip, k = f["src"][0], int(f["src"][1:])
    src = cv2.imread(f"src/{clip}/{k:04d}.jpg")
    M = np.float32([[f["s"], 0, f["tx"]], [0, f["s"], f["ty"]]])
    return cv2.warpAffine(src, M, (1080, 1920))
def neighbors(f):
    clip, k = f["src"][0], int(f["src"][1:])
    out = []
    for d in (-1, 1):
        p = f"src/{clip}/{k + d:04d}.jpg"
        if os.path.exists(p):
            src = cv2.imread(p); M = np.float32([[f["s"], 0, f["tx"]], [0, f["s"], f["ty"]]])
            out.append(cv2.warpAffine(src, M, (1080, 1920)))
    return out
mism = []
mask = np.ones((1920, 1080), bool); mask[:300] = False; mask[1560:1720] = False
for f in FR[::3]:
    if "spot" in f or "lab" in f: continue
    im = frames[f["n"]].astype(np.float32); e = expected(f).astype(np.float32)
    d0 = np.abs(im - e)[mask].mean()
    dn = [np.abs(im - x.astype(np.float32))[mask].mean() for x in neighbors(f)]
    if dn and min(dn) < d0 - 0.5: mism.append((f["n"], f["src"], round(float(d0), 2), round(float(min(dn)), 2)))
rep["source_checked"] = len(FR[::3]); rep["source_mismatch"] = mism

# 3) clean image: top and bottom strips every 0.5 s
tiles = []
for n in range(0, len(frames), 15):
    im = frames[n]
    t = np.vstack([cv2.resize(im[:330], (360, 110)), cv2.resize(im[1590:], (360, 110))])
    cv2.putText(t, f"{n / 30:.1f}s", (3, 14), 0, .45, (0, 255, 255), 1); tiles.append(t)
board(tiles, f"{SCR}/v_clean.jpg", 10)
# full frames every 0.5 s (small) for the watermark/score bug check
tiles = []
for n in range(0, len(frames), 15):
    t = cv2.resize(frames[n], (180, 320)); cv2.putText(t, f"{n / 30:.1f}", (3, 14), 0, .45, (0, 255, 255), 1); tiles.append(t)
board(tiles, f"{SCR}/v_full.jpg", 20)

# 4) spotlight: circle drawn on the SOURCE every 4 frames
tiles = []
for f in FR[::4]:
    if "spot" not in f: continue
    sp = f["spot"]; clip, k = f["src"][0], int(f["src"][1:])
    src = cv2.imread(f"src/{clip}/{k:04d}.jpg")
    cx = (sp["x"] - f["tx"]) / f["s"]; cy = (sp["y"] - f["ty"]) / f["s"]; r = sp["r"] / f["s"]
    cv2.circle(src, (int(cx), int(cy)), int(r), (255, 255, 255), 2)
    h = int(r * 1.4)
    c = src[max(0, int(cy) - h):int(cy) + h, max(0, int(cx) - h):int(cx) + h]
    c = cv2.resize(c, (220, 220)); cv2.putText(c, f"{f['n']}", (3, 14), 0, .45, (0, 255, 255), 1); tiles.append(c)
board(tiles, f"{SCR}/v_spot.jpg", 10)

# 5) sync: shot starts vs first word of their sentence
W = json.load(open("voice/words.json"))
sync = []
for k, sh in enumerate(EDL["shots"]):
    w = [x for x in W if x["sentence"] == k][0]
    sync.append((sh["id"], round(sh["T0"], 3), w["text"], round(w["start"], 3)))
rep["sync"] = sync
json.dump(rep, open("work/verify.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: (v if k != "sync" else v) for k, v in rep.items()}, ensure_ascii=False)[:3000])
