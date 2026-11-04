"""Vérification obligatoire sur la vidéo FINALE rendue (section 9 du master prompt)."""
import json, subprocess, sys, os, re
import cv2, numpy as np
ROOT = os.path.dirname(os.path.abspath(__file__))
VID = sys.argv[1] if len(sys.argv) > 1 else f"{ROOT}/out/koita_but_fr.mp4"
AN = "/tmp/claude-0/-home-user-Fofana/daca3ac7-e701-5674-9337-1a49ad094954/scratchpad/verif"
SRC = "/tmp/claude-0/-home-user-Fofana/daca3ac7-e701-5674-9337-1a49ad094954/scratchpad/src"
os.makedirs(AN, exist_ok=True)
plan = json.load(open(f"{ROOT}/build/plan.json"))
frames, cams = plan["frames"], plan["cams"]
cap = cv2.VideoCapture(VID)
out = []
while True:
    ok, f = cap.read()
    if not ok: break
    out.append(f)
N = len(out)
rep = {"frames_rendered": N, "frames_planned": len(frames)}
print("images rendues", N, "prévues", len(frames))

# ---------- 1. étiquettes : pointe rouge mesurée dans la vidéo rendue vs haut de la tête
def red_tip(img, ex, ey):
    x1, y1 = int(ex - 50), int(ey - 120)
    sub = img[max(0, y1):int(ey + 20), max(0, x1):int(ex + 50)]
    b, g, r = [sub[..., i].astype(int) for i in range(3)]
    m = (r > 200) & (g < 90) & (b < 90)
    ys, xs = np.nonzero(m)
    if len(ys) < 50: return None
    yb = ys.max()
    xs_b = xs[ys >= yb - 2]
    return x1 + xs_b.mean(), y1 + yb
def head_top(img, tx, ty):
    """premier pixel de tête (sombre/non-pelouse) sous la pointe, dans une colonne de ±10 px"""
    x1 = int(tx - 10)
    col = img[int(ty) + 1:int(ty) + 60, x1:int(tx + 11)]
    hsv = cv2.cvtColor(col, cv2.COLOR_BGR2HSV)
    grass = cv2.inRange(hsv, (30, 50, 50), (90, 255, 255)) > 0
    dark = (~grass) & (hsv[..., 2] < 140)
    for r in range(col.shape[0] - 3):
        if dark[r].sum() >= 3 and dark[r + 1].sum() >= 3 and dark[r + 2].sum() >= 3:
            xs = np.nonzero(dark[r:r + 4].any(0))[0]
            return x1 + xs.mean(), int(ty) + 1 + r
    return None
tag_rows, bad = [], []
for k, li, ox, tip, oy in plan["tags"]:
    if k >= N: continue
    img = out[k]
    t = red_tip(img, ox, tip)
    if t is None: bad.append((k, li, "pointe introuvable")); continue
    h = head_top(img, *t)
    if h is None: bad.append((k, li, "tête introuvable")); continue
    gap, dx = h[1] - t[1], h[0] - t[0]
    tag_rows.append((k, li, round(gap, 1), round(dx, 1)))
    if not (0 <= gap <= 16 and abs(dx) <= 6): bad.append((k, li, f"écart {gap:.1f} px, dx {dx:.1f}"))
rep["tags_checked"] = len(tag_rows); rep["tags_bad"] = bad
gaps = np.array([r[2] for r in tag_rows]); dxs = np.array([r[3] for r in tag_rows])
print(f"étiquettes : {len(tag_rows)} images mesurées ; écart pointe/tête {gaps.min():.0f}..{gaps.max():.0f} px (moy {gaps.mean():.1f}) ; dx {dxs.min():.0f}..{dxs.max():.0f} ; hors tolérance : {len(bad)}")
for b in bad[:40]: print("   ", b)
# planches zoomées de TOUTES les images avec étiquette
ims = []
for k, li, ox, tip, oy in plan["tags"]:
    if k >= N: continue
    c = out[k][int(tip - 90):int(tip + 70), int(ox - 80):int(ox + 80)]
    if c.shape[:2] != (160, 160): c = cv2.resize(c, (160, 160)) if c.size else np.zeros((160, 160, 3), np.uint8)
    c = c.copy(); cv2.putText(c, str(k), (3, 14), 0, 0.45, (0, 255, 255), 1); ims.append(c)
per = 16
for p in range(0, len(ims), per * 10):
    chunk = ims[p:p + per * 10]
    while len(chunk) % per: chunk.append(np.zeros_like(ims[0]))
    cv2.imwrite(f"{AN}/tags_{p // (per * 10):02d}.jpg", np.vstack([np.hstack(chunk[i:i + per]) for i in range(0, len(chunk), per)]))

# ---------- 2. bonne image source : rendu vs recadrage attendu de l'image source prévue
def expected(k):
    _, clip, n, _ = frames[k]; x0, y0, s = cams[k]
    src = cv2.imread(f"{SRC}/{clip}/{n + 1:04d}.jpg")
    M = np.float32([[s, 0, -x0 * s], [0, s, -y0 * s]])
    return cv2.warpAffine(src, M, (1080, 1920))
def score(a, b):
    a = cv2.resize(a[300:1500], (135, 150)).astype(float); b = cv2.resize(b[300:1500], (135, 150)).astype(float)
    a -= a.mean(); b -= b.mean()
    return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-9))
wrong = []
corr = []
for k in range(0, min(N, len(frames))):
    c = score(out[k], expected(k)); corr.append(c)
    if c < 0.6:
        # l'image voisine correspond-elle mieux ? (décalage d'une image)
        _, clip, n, _ = frames[k]
        wrong.append((k, round(c, 2)))
rep["src_corr_min"] = min(corr); rep["src_low"] = wrong
print(f"bonne image source : corrélation min {min(corr):.2f}, médiane {np.median(corr):.2f}, images < 0,6 : {len(wrong)} {wrong[:10]}")

# ---------- 3. image propre : filigrane / score télé / bandeau, planches haut et bas toutes les 0,5 s
tmpl_src = cv2.imread(f"{SRC}/B/0635.jpg")[895:935, 690:1020]   # "X.com/marfawe" (B, image 634)
bug_src = cv2.imread(f"{SRC}/A/0101.jpg")[52:100, 64:612]         # score télé
ban_src = cv2.imread(f"{SRC}/A/0101.jpg")[905:975, 380:1540]      # bandeau télé du bas
hits = []
tops, bots = [], []
for k in range(0, N, 15):
    _, clip, n, _ = frames[k]; x0, y0, s = cams[k]
    src = cv2.imread(f"{SRC}/{clip}/{n + 1:04d}.jpg")
    # où est le filigrane dans l'image source de cette image ? (corrélation)
    g = cv2.cvtColor(src[850:1000], cv2.COLOR_BGR2GRAY); tg = cv2.cvtColor(tmpl_src, cv2.COLOR_BGR2GRAY)
    r = cv2.matchTemplate(g, tg, cv2.TM_CCOEFF_NORMED); _, mv, _, ml = cv2.minMaxLoc(r)
    wy = 850 + ml[1]
    win = (x0, y0, x0 + 1080 / s, y0 + 1920 / s)
    if mv > 0.55 and not (wy > win[3] or wy + 40 < win[1] or ml[0] > win[2] or ml[0] + 330 < win[0]):
        hits.append((k, "filigrane", round(mv, 2)))
    if win[1] < 100 and clip == "A": hits.append((k, "zone score télé", round(win[1])))
    if win[3] > 855 and clip == "A" and n < 335: hits.append((k, "zone bandeau télé", round(win[3])))
    if win[3] > 895: hits.append((k, "zone filigrane (y>895)", round(win[3])))
    tops.append(cv2.resize(out[k][0:420], (270, 105))); bots.append(cv2.resize(out[k][1500:1920], (270, 105)))
rep["clean_hits"] = hits
print(f"image propre : {len(hits)} alertes {hits[:10]}")
for nm, arr in (("haut", tops), ("bas", bots)):
    while len(arr) % 8: arr.append(np.zeros_like(arr[0]))
    cv2.imwrite(f"{AN}/propre_{nm}.jpg", np.vstack([np.hstack(arr[i:i + 8]) for i in range(0, len(arr), 8)]))

# ---------- 4. synchronisation voix / image à des instants clés
words = json.load(open(f"{ROOT}/build/words1.json"))
def wt(sent, w):
    for x in words:
        if x["sent"] == sent and x["w"].lower().startswith(w.lower()): return x["start"]
CHECK = [
    (0, "Koita", "Koita à l'image (A, porte le ballon)", lambda c, n: c == "A" and 360 <= n < 419),
    (1, "Douzième", "plan de contexte + bandeau 0-0", lambda c, n: True),
    (2, "toute", "milieu de terrain, ballon libre", lambda c, n: c == "A" and 160 <= n < 196),
    (3, "Jović", "Jović porteur", lambda c, n: c == "A" and 196 <= n < 285),
    (4, "protège", "Jović protège", lambda c, n: c == "A" and 230 <= n < 285),
    (5, "adversaire", "adversaire collé à Jović", lambda c, n: c == "A" and 250 <= n < 285),
    (6, "Autour", "arrêt sur image 278", lambda c, n: (c, n) == ("A", 278)),
    (7, "Koita", "Koita sur la droite (arrêt 278)", lambda c, n: (c, n) == ("A", 278)),
    (8, "ouvre", "passe de Jović (285)", lambda c, n: c == "A" and 270 <= n <= 290),
    (9, "récupère", "contrôle de Koita", lambda c, n: c == "A" and 300 <= n < 330),
    (10, "Regardez", "arrêt sur image 318", lambda c, n: (c, n) == ("A", 318)),
    (11, "défenseur", "Cucurella entouré (318)", lambda c, n: (c, n) == ("A", 318)),
    (14, "Koita", "Koita choisit le duel", lambda c, n: c == "A" and 371 <= n < 392),
    (15, "conduit", "conduite (ralenti haut)", lambda c, n: c == "B" and 255 <= n < 300),
    (17, "Cucurella", "Cucurella entouré (392)", lambda c, n: (c, n) == ("A", 392)),
    (19, "Personne", "Cucurella seul (ralenti bas)", lambda c, n: c == "B" and 560 <= n < 600),
    (21, "contre", "un contre un", lambda c, n: c == "B" and 595 <= n < 630),
    (23, "précipite", "arrêt sur image 404", lambda c, n: (c, n) == ("A", 404)),
    (25, "crochet", "le crochet", lambda c, n: c == "A" and 398 <= n < 420),
    (26, "Cucurella", "Cucurella dépassé (417)", lambda c, n: (c, n) == ("A", 417)),
    (29, "frappe", "la frappe (419)", lambda c, n: c == "A" and 410 <= n < 432),
    (31, "deuxième", "2e défenseur trop tard", lambda c, n: c == "A" and 419 <= n < 447),
    (33, "trajectoire", "trajectoire (ralenti haut)", lambda c, n: c == "B" and 352 <= n < 392),
    (34, "Courtois", "Courtois plonge", lambda c, n: c == "A" and 424 <= n < 462),
    (35, "angle", "autre angle, filets", lambda c, n: c == "B" and 650 <= n < 725),
    (36, "Un", "1-0 (bandeau retourné)", lambda c, n: c == "A" and n >= 470),
    (37, "Jović", "Jović rejoint Koita", lambda c, n: c == "A" and 590 <= n < 722),
    (39, "Alors", "gros plan Koita", lambda c, n: c == "B" and n >= 1240),
]
sync = []
for s, w, what, ok in CHECK:
    t = wt(s, w); k = min(len(frames) - 1, int(round(t * 30)) + 2)
    _, c, n, _ = frames[k]
    sync.append((f"{t:6.2f}s", w, what, f"{c}{n}", "OK" if ok(c, n) else "KO"))
rep["sync"] = sync
print("synchro :")
for r in sync: print("   ", *r)
sh = [cv2.resize(out[min(N - 1, int(round(float(r[0][:-1]) * 30)) + 2)], (216, 384)) for r in sync]
for i, im in enumerate(sh): cv2.putText(im, f"{sync[i][1]}", (4, 20), 0, 0.6, (0, 255, 255), 2)
while len(sh) % 7: sh.append(np.zeros_like(sh[0]))
cv2.imwrite(f"{AN}/synchro.jpg", np.vstack([np.hstack(sh[i:i + 7]) for i in range(0, len(sh), 7)]))

# ---------- 5. son et durée
r = subprocess.run(["ffmpeg", "-hide_banner", "-i", VID, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
I = re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1]; TP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1]
pr = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_name,width,height,r_frame_rate", "-of", "json", VID], capture_output=True, text=True).stdout)
rep.update(lufs=float(I), true_peak=float(TP), probe=pr)
print(f"son : {I} LUFS intégré, crête vraie {TP} dBTP")
print("format :", [(s.get("codec_name"), s.get("width"), s.get("height"), s.get("r_frame_rate")) for s in pr["streams"]], pr["format"])
json.dump(rep, open(f"{ROOT}/build/verif.json", "w"), ensure_ascii=False, indent=1, default=str)
