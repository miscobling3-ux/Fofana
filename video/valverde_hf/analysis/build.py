#!/usr/bin/env python3
"""Analyse -> data for the HyperFrames composition (camera, labels, spotlight, captions).
Python computes numbers only; the video itself is assembled and rendered by HyperFrames."""
import json, math, os, re, shutil, difflib
import numpy as np

S = "/tmp/claude-0/-home-user-Fofana/0dc10ad3-8ae5-5d3f-b08b-3b4d72bae3e6/scratchpad"
AN, P = S + "/an", S + "/proj"
FPS = 30
DUR = 79.10
N = int(round(DUR * FPS))
CLIP = {"A": dict(fps=50, dir=AN + "/fa", nmax=667), "B": dict(fps=60, dir=AN + "/fbf", nmax=1474)}

# ---------------------------------------------------------------- words.json
SCRIPT = ("Por eso nunca se le debe dejar el más mínimo espacio a Valverde para disparar. "
 "El Real Madrid consigue un tiro libre en una zona peligrosa. Arda Güler y Mbappé se colocan frente al balón. "
 "En esta situación, podríamos pensar que será Arda Güler quien se encargue de ejecutar el tiro libre. "
 "Teniendo en cuenta la estructura defensiva del equipo rival, podemos imaginar que el balón pasará por encima de la barrera. "
 "Pero, en el momento en que el árbitro da la señal, observamos que Arda Güler permanece completamente inmóvil, "
 "lo que nos hace entender que será Mbappé quien golpeará el balón. Cuando Mbappé dispara, su lanzamiento es bloqueado "
 "por la barrera rival, y entonces el balón cae directamente a los pies de Valverde. Sin perder ni un segundo, Valverde "
 "controla el balón, pero tiene pocas opciones por delante. La mayoría de los jugadores habría optado por pasarle el balón "
 "a Arda Güler, que se encuentra en la frontal del área, o habría intentado enviar un centro. Sin embargo, no hay suficientes "
 "jugadores del Real Madrid dentro del área. Valverde descarta todas esas opciones, coloca su pie de apoyo, levanta la mano, "
 "y desata un disparo espectacular que termina en el fondo de la portería rival. ¡Qué golazo de Valverde! ¡Qué magia la de Valverde!")
raw = [l.split() for l in open(S + "/words_raw.txt", encoding="utf8") if l.strip()]
raw = [(w, float(a), float(b)) for w, a, b in raw]
toks = SCRIPT.split()
norm = lambda w: re.sub(r"[^\wáéíóúüñ]", "", w.lower())
sm = difflib.SequenceMatcher(a=[norm(t) for t in toks], b=[norm(r[0]) for r in raw], autojunk=False)
words = [None] * len(toks)
for a, b, n in sm.get_matching_blocks():
    for k in range(n):
        words[a + k] = dict(text=toks[a + k], start=raw[b + k][1], end=raw[b + k][2])
assert all(words), "unaligned word"
json.dump(words, open(P + "/words.json", "w"), ensure_ascii=False, indent=0)

# ---------------------------------------------------------------- EDL
# (out_start, out_end, clip, src_in, src_out)   src_in == src_out -> freeze
EDL = [
    (0.00, 4.96, "A", 5.84, 6.90),    # hook: Valverde's strike (side angle)
    (4.96, 8.56, "B", 0.00, 3.60),    # free kick won, wide
    (8.56, 11.92, "B", 3.60, 6.96),   # Güler + Mbappé at the ball
    (11.92, 18.08, "B", 6.96, 6.96),  # freeze: we'd think Güler takes it
    (18.08, 25.28, "B", 0.50, 2.50),  # the wall
    (25.28, 28.32, "B", 6.96, 8.30),  # referee signal
    (28.32, 32.32, "B", 8.30, 8.30),  # freeze: Güler doesn't move
    (32.32, 36.56, "B", 8.30, 9.80),  # Mbappé run-up
    (36.56, 40.96, "B", 9.80, 10.70), # shot blocked by the wall
    (40.96, 44.88, "A", 4.80, 5.60),  # ball drops to Valverde
    (44.88, 48.48, "A", 5.60, 6.10),  # control
    (48.48, 50.96, "A", 6.10, 6.10),  # freeze: few options
    (50.96, 59.92, "A", 1.80, 2.60),  # aerial: options
    (59.92, 64.80, "A", 2.60, 2.60),  # freeze aerial: empty box
    (64.80, 67.44, "A", 6.10, 6.60),  # Valverde discards options
    (67.44, 70.32, "A", 6.60, 6.60),  # freeze: plant foot, raised hand
    (70.32, 72.32, "A", 6.60, 6.96),  # the strike
    (72.32, 75.28, "A", 2.90, 4.30),  # aerial angle: bottom corner
    (75.28, DUR, "B", 15.50, 15.50 + (DUR - 75.28)),  # celebration x1
]
CUTS = [e[0] for e in EDL[1:]]

def shot_at(t):
    for k, e in enumerate(EDL):
        if e[0] <= t < e[1] or (k == len(EDL) - 1 and t >= e[0]):
            return k
def src_frame(k, t):
    o0, o1, c, s0, s1 = EDL[k]
    s = s0 + (t - o0) * (s1 - s0) / (o1 - o0)
    n = int(round(s * CLIP[c]["fps"])) + 1
    return min(max(n, 1), CLIP[c]["nmax"])

# ---------------------------------------------------------------- tracks (head centre, source px)
def load_track(f):
    d = json.load(open(AN + "/" + f)); return {int(k): (v[0], v[1]) for k, v in d.items()}
TR = {"mbappe": ("B", load_track("tr_mbappe.json"), 15),
      "guler": ("B", load_track("tr_guler.json"), 12),
      "valverde": ("A", load_track("tr_valv.json"), 19)}
# Valverde (A, busy background): head-top keyframes set by hand on a 10 px zoomed grid, interpolated
VMAN = {284: (938, 479), 288: (893, 488), 292: (873, 505), 296: (867, 525), 300: (890, 523), 304: (913, 507),
        308: (920, 488), 312: (910, 465), 316: (887, 420), 320: (870, 404), 324: (860, 408), 328: (850, 418),
        332: (833, 423), 336: (803, 428), 340: (787, 452), 345: (777, 488)}
import sys, cv2
sys.path.insert(0, S)
from headtop import hair_top
_HT = {}
def measured_top(p, n):
    """B players on grass: hair top measured on the source frame, median-smoothed over 5 frames."""
    if (p, n) in _HT: return _HT[(p, n)]
    c, tr, off = TR[p]; ks = sorted(tr); vals = []
    for m in range(n - 2, n + 3):
        mm = min(max(m, ks[0]), ks[-1])
        im = cv2.imread(f"{CLIP[c]['dir']}/{mm:04d}.jpg")
        x, y, ok = hair_top(im, tr[mm][0], tr[mm][1], off)
        vals.append((x, y))
    r = (float(np.median([v[0] for v in vals])), float(np.median([v[1] for v in vals])))
    _HT[(p, n)] = r; return r
def head(p, n, top_only=False):
    c, tr, top = TR[p]
    ks = sorted(tr)
    n = min(max(n, ks[0]), ks[-1])
    x, y = tr[n]
    return x, y, y - top   # centre x, centre y, top of head (coarse; labels use label_head)
def label_head(p, n):
    if p == "valverde":
        ks = sorted(VMAN); m = min(max(n, ks[0]), ks[-1])
        for a, b in zip(ks, ks[1:]):
            if a <= m <= b:
                u = (m - a) / (b - a)
                return VMAN[a][0] + (VMAN[b][0] - VMAN[a][0]) * u, VMAN[a][1] + (VMAN[b][1] - VMAN[a][1]) * u
    return measured_top(p, n)

# ---------------------------------------------------------------- overlays to keep out of frame (x0,y0,x1,y1)
OVL = {"A": [(85, 35, 315, 180), (1580, 40, 1895, 170), (1565, 990, 1860, 1045)],
       "B": [(85, 35, 315, 180), (1595, 45, 1835, 120), (750, 880, 1100, 935), (1725, 868, 1855, 965), (1565, 990, 1860, 1045)]}
PAD = 8

# ---------------------------------------------------------------- labels: (player, clip, first src frame, contact frame -> disappears)
LABELS = [("valverde", "A", 284, 334),   # A: ball reaches Valverde @284, strike contact @334
          ("mbappe", "B", 499, 592)]      # B: Mbappé designated taker from the referee's signal, contact @592
def label_at(k, n):
    c = EDL[k][2]
    for p, lc, f0, f1 in LABELS:
        if lc == c and f0 <= n < f1:
            if p == "mbappe" and k not in (7, 8): continue
            if p == "valverde" and k not in (0, 10, 11, 14, 15, 16): continue
            return p
    return None

# ---------------------------------------------------------------- spotlights (out_start, out_end, player, zoom?)
SPOTS = [(3.12, 4.96, "valverde", False), (8.56, 9.44, "guler", True), (9.44, 11.92, "mbappe", True),
         (14.48, 17.60, "guler", True), (29.12, 32.32, "guler", True), (33.92, 36.56, "mbappe", True),
         (43.76, 44.88, "valverde", True), (64.80, 67.44, "valverde", False)]
VKEY = {306: (893, 685), 320: (875, 642), 331: (783, 655), 346: (760, 720)}
def circle(p, n):
    hx, hy, top = head(p, n)
    if p == "guler": return hx + 8, hy + 108, 150
    if p == "mbappe": return hx + 25, hy + 115, (175 if n > 520 else 165)
    if n < 300: return hx + 15, hy + 140, 190
    ks = sorted(VKEY); n2 = min(max(n, ks[0]), ks[-1])
    for a, b in zip(ks, ks[1:]):
        if a <= n2 <= b:
            u = (n2 - a) / (b - a)
            return VKEY[a][0] * (1 - u) + VKEY[b][0] * u, VKEY[a][1] * (1 - u) + VKEY[b][1] * u, 375
def spot_at(t):
    for s0, s1, p, z in SPOTS:
        if s0 <= t < s1:
            a = min(1, (t - s0) / 0.25, (s1 - t) / 0.25)
            return p, max(0, a), z, s0
    return None

# ---------------------------------------------------------------- desired camera (centre x, centre y, crop height)
def lerp(a, b, u): return a + (b - a) * u
def cam_desired(k, t, n):
    o0, o1 = EDL[k][0], EDL[k][1]; u = (t - o0) / (o1 - o0)
    if k == 0:  x, y, _ = head("valverde", n); return x, y + 170, 1000
    if k == 1:  return 850, 560, 860
    if k == 2:
        if t < 9.44: x, y, _ = head("guler", n); return x, y + 110, 820
        x, y, _ = head("mbappe", n); return x + 40, y + 120, 820
    if k == 3:  return 820, 660, 820
    if k == 4:  return 870, 470, 700
    if k == 5:  return 300, 700, 880
    if k == 6:  return 935, 700, 820
    if k == 7:  x, y, _ = head("mbappe", n); return x + 60, y + 130, 820
    if k == 8:  return lerp(680, 950, u), lerp(640, 560, u), lerp(880, 1000, u)
    if k in (9, 10, 14): x, y, _ = head("valverde", n); return x, y + (190 if k == 14 else 170), (1050 if k == 14 else 1000)
    if k == 11: x, y, _ = head("valverde", 306); return x, y + 170, 1000
    if k == 12: return lerp(700, 850, u), lerp(350, 420, u), lerp(900, 1000, u)
    if k == 13: return 1000, 560, 1080
    if k == 15: return 785, 560, 1080
    if k == 16: return 790, 600, 1080
    if k == 17: v = min(1, u / 0.66); return lerp(750, 950, v), lerp(450, 720, v), lerp(1000, 1080, v)
    if k == 18:
        ks = [(931, 830, 430), (997, 840, 560), (1030, 1060, 560), (1057, 980, 520), (1117, 1000, 500), (1160, 1000, 500)]
        for (a, xa, ya), (b, xb, yb) in zip(ks, ks[1:]):
            if a <= n <= b: v = (n - a) / (b - a); return lerp(xa, xb, v), lerp(ya, yb, v), 880
        return 1000, 500, 880

def hits(x0, y0, x1, y1, rects):
    return [r for r in rects if x0 < r[2] + PAD and x1 > r[0] - PAD and y0 < r[3] + PAD and y1 > r[1] - PAD]
def solve(cx, cy, H, clip, keep=None):
    """Clamp the 9:16 crop inside the source, then shift/shrink it until no TV overlay is inside."""
    rects = OVL[clip]
    for _ in range(40):
        H = min(H, 1080); W = H * 9 / 16
        x0 = min(max(cx - W / 2, 0), 1920 - W); y0 = min(max(cy - H / 2, 0), 1080 - H)
        hs = hits(x0, y0, x0 + W, y0 + H, rects)
        if not hs: return x0 + W / 2, y0 + H / 2, H
        best = None
        for r in hs:
            for nx0, ny0 in ((r[0] - PAD - W, y0), (r[2] + PAD, y0), (x0, r[1] - PAD - H), (x0, r[3] + PAD)):
                nx0 = min(max(nx0, 0), 1920 - W); ny0 = min(max(ny0, 0), 1080 - H)
                if hits(nx0, ny0, nx0 + W, ny0 + H, rects): continue
                if keep and not (nx0 + 20 < keep[0] < nx0 + W - 20 and ny0 + 20 < keep[1] < ny0 + H - 20): continue
                d = abs(nx0 - x0) + abs(ny0 - y0)
                if best is None or d < best[0]: best = (d, nx0, ny0)
        if best: return best[1] + W / 2, best[2] + H / 2, H
        H *= 0.96
    raise RuntimeError("no clean crop")

def gsmooth(vals, sigma):
    v = np.array(vals, float); n = len(v)
    if sigma <= 0 or n < 3: return v
    r = int(3 * sigma); k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    p = np.pad(v, r, mode="edge"); return np.convolve(p, k, mode="valid")

# ---------------------------------------------------------------- per output frame
frames = []
for i in range(N):
    t = i / FPS
    k = shot_at(t); n = src_frame(k, t)
    frames.append(dict(i=i, t=t, k=k, clip=EDL[k][2], n=n))
# desired camera, smoothed inside each shot (sigma = 10 frames), fixed on freezes
cam = [None] * N
for k in range(len(EDL)):
    idx = [f["i"] for f in frames if f["k"] == k]
    d = [cam_desired(k, frames[i]["t"], frames[i]["n"]) for i in idx]
    freeze = EDL[k][3] == EDL[k][4]
    sig = 0 if freeze else 10
    xs, ys, hs = (gsmooth([v[j] for v in d], sig) for j in range(3))
    for j, i in enumerate(idx): cam[i] = [xs[j], ys[j], hs[j]]
# spotlight zoom (+22 %, progressive, toward the player) and cut punch (+7 %, back in 0.1 s)
spot = [None] * N
for f in frames:
    i, t = f["i"], f["t"]
    sp = spot_at(t)
    if sp:
        p, a, z, s0 = sp
        cx, cy, r = circle(p, f["n"])
        spot[i] = dict(p=p, a=a, cx=cx, cy=cy, r=r)
        if z:
            e = min(1, (t - s0) / 0.9); e = e * e * (3 - 2 * e); e *= min(1, a * 1.0) if a < 1 and t > s0 + 0.3 else 1
            c = cam[i]; cam[i] = [lerp(c[0], cx, 0.6 * e), lerp(c[1], cy, 0.6 * e), c[2] / (1 + 0.22 * e)]
    for c0 in CUTS + [0.0]:
        if c0 <= t < c0 + 0.1:
            cam[i][2] /= 1 + 0.07 * (1 - (t - c0) / 0.1)
# smooth spotlight circles lightly within each spotlight
for s0, s1, p, z in SPOTS:
    idx = [i for i in range(N) if spot[i] and s0 <= frames[i]["t"] < s1]
    for key in ("cx", "cy"):
        v = gsmooth([spot[i][key] for i in idx], 2)
        for j, i in enumerate(idx): spot[i][key] = v[j]
    r = max(spot[i]["r"] for i in idx)
    for i in idx: spot[i]["r"] = r
# label positions
lab = [None] * N
for f in frames:
    p = label_at(f["k"], f["n"])
    if p:
        hx, top = label_head(p, f["n"]); lab[f["i"]] = dict(p=p, x=hx, top=top)
# hard constraints: no overlay, labelled head stays in frame
for f in frames:
    i = f["i"]; L = lab[i]
    keep = (L["x"], L["top"] - 60) if L else None
    cam[i] = list(solve(*cam[i], f["clip"], keep))
    if L:
        W = cam[i][2] * 9 / 16; x0 = cam[i][0] - W / 2; y0 = cam[i][1] - cam[i][2] / 2
        assert x0 < L["x"] < x0 + W and y0 < L["top"] - 40, ("label out of frame", i)

# ---------------------------------------------------------------- export
used = sorted({(f["clip"], f["n"]) for f in frames})
fd = P + "/assets/frames"; os.makedirs(fd, exist_ok=True)
for c, n in used:
    dst = f"{fd}/{c}_{n:04d}.jpg"
    if not os.path.exists(dst): shutil.copy(f"{CLIP[c]['dir']}/{n:04d}.jpg", dst)
runs = []
for f in frames:
    key = (f["clip"], f["n"])
    if runs and runs[-1][0] == key and runs[-1][2] == f["i"]: runs[-1][2] += 1
    else: runs.append([key, f["i"], f["i"] + 1])
out = []
for f in frames:
    i = f["i"]; cx, cy, H = cam[i]; s = 1920 / H; W = H * 9 / 16
    x0, y0 = cx - W / 2, cy - H / 2
    row = dict(t=round(i / FPS, 5), s=round(s, 5), x=round(-x0 * s, 2), y=round(-y0 * s, 2), k=f["k"], c=f["clip"], n=f["n"])
    if lab[i]:
        L = lab[i]; row["lab"] = [L["p"], round((L["x"] - x0) * s, 1), round((L["top"] - y0) * s, 1)]
    if spot[i]:
        sp = spot[i]; row["spot"] = [sp["p"], round((sp["cx"] - x0) * s, 1), round((sp["cy"] - y0) * s, 1), round(sp["r"] * s, 1), round(sp["a"], 3)]
    out.append(row)
json.dump(dict(frames=out, runs=[[f"{c}_{n:04d}.jpg", a, b] for (c, n), a, b in runs], edl=EDL, words=words,
               fps=FPS, dur=DUR), open(S + "/plan.json", "w"))
print("frames", N, "images", len(used), "runs", len(runs))
