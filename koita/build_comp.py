"""Génère la composition HyperFrames (hf/index.html) : EDL calée sur words.json, caméra 9:16,
étiquettes porteur, projecteur, sous-titres, bandeau de score et pistes de bruitages.
Python ne fabrique aucune image : il écrit le HTML/GSAP que HyperFrames rend."""
import json, os, re, shutil, math
import numpy as np
from scipy.ndimage import gaussian_filter1d

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = "/tmp/claude-0/-home-user-Fofana/daca3ac7-e701-5674-9337-1a49ad094954/scratchpad/src"
HF = f"{ROOT}/hf"
FPS, SFPS = 30, 50
W, H = 1080, 1920
BAND = (112, 852)           # zone source sans score télé / filigrane / bandeau (mesurée)
H0 = BAND[1] - BAND[0]      # 740 px source -> 1920 px
words = json.load(open(f"{ROOT}/build/words1.json"))
DUR = round(len(__import__("soundfile").read(f"{HF}/assets/voice.wav")[0]) / 48000, 3)
NF = int(round(DUR * FPS))
sent0 = {}
for w in words: sent0.setdefault(w["sent"], w["start"])
def S(i): return 0.0 if i == 0 else sent0[i]
def word_t(sent, text):
    for w in words:
        if w["sent"] == sent and w["w"].lower().startswith(text.lower()): return w["start"]
    raise KeyError((sent, text))
END = DUR

# ---------------------------------------------------------------- données d'analyse
AN = f"{ROOT}/analysis"
def heads(name): return {int(k): v["head"] for k, v in json.load(open(f"{AN}/head_{name}.json")).items()}
HEAD = {k: heads(k) for k in ("jovic_A", "koita_A", "koita_Bh", "koita_Bl")}
SPOT = {k: {int(n): v for n, v in d["f"].items()} for k, d in json.load(open(f"{AN}/spots.json")).items()}
# étiquettes : (clip, piste de tête, image de début, image de la passe/frappe (exclue))
LABELS = [
    ("A", "jovic_A", 196, 285, "Luka Jović", "aek"),
    ("A", "koita_A", 315, 419, "Aboubakary Koita", "aek"),
    ("B", "koita_Bh", 250, 352, "Aboubakary Koita", "aek"),
    ("B", "koita_Bl", 556, 637, "Aboubakary Koita", "aek"),
]
KICKS = {("A", 419), ("B", 352)}   # images de contact (frappe)

# ---------------------------------------------------------------- EDL
# seg: (t0, t1, clip, a, b) lecture a->b ; freeze : a == b ; focus = fonction(n, u) -> (x, y) source
def lab_focus(clip, n):
    for c, hk, a, b, *_ in LABELS:
        h = HEAD[hk]
        if c == clip and a <= n < b and n in h: return h[n]
    return None
def head_focus(hk):
    h = HEAD[hk]
    def f(n, u):
        k = min(h, key=lambda m: abs(m - n)); return h[k]
    return f
def lerp_focus(p0, p1):
    def f(n, u): return (p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u)
    return f
def ease(u): return u * u * (3 - 2 * u)
def pan_focus(p0, p1, u0=0.0, u1=0.5):
    def f(n, u):
        v = ease(min(1, max(0, (u - u0) / (u1 - u0)))); return (p0[0] + (p1[0] - p0[0]) * v, p0[1] + (p1[1] - p0[1]) * v)
    return f
YELLOW = {}
def yellow_focus(clip):
    import cv2
    def f(n, u):
        key = (clip, n)
        if key not in YELLOW:
            img = cv2.imread(f"{SRC}/{clip}/{n + 1:04d}.jpg")[BAND[0]:BAND[1]]
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            m = cv2.inRange(hsv, (18, 120, 120), (35, 255, 255))
            ys, xs = np.nonzero(m)
            YELLOW[key] = (float(np.median(xs)), float(np.median(ys)) + BAND[0]) if len(xs) > 500 else (960, 480)
        x, y = YELLOW[key]
        return (x - 150, y) if clip == "B" else (x, y)   # gros plan : le visage est à gauche du maillot
    return f
KA, JA = HEAD["koita_A"], HEAD["jovic_A"]
SEGS = []
def seg(t0, t1, clip, a, b, focus, **kw): SEGS.append(dict(t0=t0, t1=t1, clip=clip, a=a, b=b, focus=focus, **kw))
seg(0, S(1), "A", 360, 430, head_focus("koita_A"))
seg(S(1), word_t(2, "toute"), "B", 1140, 1140 + round((word_t(2, "toute") - S(1)) * SFPS), yellow_focus("B"))
seg(word_t(2, "toute"), S(3), "A", 160, 196, lerp_focus((720, 470), JA[196]))
seg(S(3), S(4), "A", 196, 230, head_focus("jovic_A"))
seg(S(4), S(5), "A", 230, 250, head_focus("jovic_A"))
seg(S(5), S(6), "A", 250, 278, head_focus("jovic_A"))
seg(S(6), S(7), "A", 278, 278, lambda n, u: JA[278], freeze=True)
seg(S(7), S(8), "A", 278, 278, pan_focus(JA[278], KA[278], 0, 0.45), freeze=True, cont=True)
def nh(h, n): return h[min(h, key=lambda m: abs(m - n))]
def pass_focus(n, u):
    v = ease(min(1, max(0, (n - 283) / 7)))
    j, q = nh(JA, n), nh(KA, n)
    return (j[0] + (q[0] - j[0]) * v, j[1] + (q[1] - j[1]) * v)
seg(S(8), S(9), "A", 270, 290, pass_focus)
seg(S(9), S(10), "A", 290, 330, head_focus("koita_A"))
seg(S(10), S(12), "A", 318, 318, lambda n, u: KA[318], freeze=True)
seg(S(12), S(13), "A", 318, 335, head_focus("koita_A"))
seg(S(13), S(14), "A", 335, 371, head_focus("koita_A"))
seg(S(14), S(15), "A", 371, 392, head_focus("koita_A"))
seg(S(15), S(16), "B", 255, 300, head_focus("koita_Bh"))
seg(S(16), S(17), "B", 300, 345, head_focus("koita_Bh"))
seg(S(17), S(19), "A", 392, 392, lambda n, u: ((KA[392][0] + 1212) / 2, KA[392][1]), freeze=True)
seg(S(19), S(20), "B", 560, 600, head_focus("koita_Bl"))
seg(S(20), S(21), "B", 600, 600, pan_focus(HEAD["koita_Bl"][600], (1330, 420), 0.1, 0.55), freeze=True)
seg(S(21), S(22), "B", 595, 630, head_focus("koita_Bl"))
seg(S(22), S(23), "B", 318, 350, head_focus("koita_Bh"))
seg(S(23), S(25), "A", 404, 404, lambda n, u: ((KA[404][0] + 1199) / 2, KA[404][1]), freeze=True)
seg(S(25), S(26), "A", 398, 420, head_focus("koita_A"))
seg(S(26), S(28), "A", 417, 417, lambda n, u: ((KA[417][0] + 1155) / 2, KA[417][1]), freeze=True)
seg(S(28), S(29), "B", 615, 637, head_focus("koita_Bl"))
seg(S(29), S(30), "A", 410, 432, head_focus("koita_A"))
seg(S(30), S(31), "A", 350, 420, head_focus("koita_A"))
seg(S(31), S(33), "A", 419, 447, lerp_focus(KA[419], (1240, 470)))
seg(S(33), S(34), "B", 352, 392, lerp_focus(HEAD["koita_Bh"][352], (1640, 400)))
seg(S(34), S(35), "A", 424, 462, lambda n, u: tuple(SPOT["courtois"][n][:2]))
seg(S(35), S(36), "B", 650, 725, lambda n, u: (1245, 680), cy=680, hc=760)
seg(S(36), S(37), "A", 470, 548, yellow_focus("A"))
seg(S(37), S(38), "A", 590, 722, yellow_focus("A"))
seg(S(38), S(39), "A", 722, 767, yellow_focus("A"))
seg(S(39), END, "B", 1240, 1240 + round((END - S(39)) * SFPS), yellow_focus("B"))

# projecteurs : (clé spots.json, t0, t1, zoom autorisé)
SPOTS = [
    ("koita_S0", word_t(0, "Koita"), 2.6, True),
    ("jovic_S3", word_t(3, "Jović"), S(4) - 0.05, True),
    ("koita_f278", word_t(7, "Koita"), S(8) - 0.05, False),
    ("koita_f318", word_t(10, "Koita"), S(11), True),
    ("cucu_f318", S(11), S(12) - 0.05, True),
    ("koita_S14", word_t(14, "Koita"), S(15) - 0.05, True),
    ("cucu_f392", word_t(17, "Cucurella"), S(19) - 0.05, True),
    ("koita_f404", S(23), S(24), True),
    ("cucu_f404", word_t(24, "Cucurella"), S(25) - 0.05, True),
    ("cucu_f417", S(26), S(28) - 0.05, True),
    ("courtois", word_t(34, "Courtois"), S(35) - 0.05, True),
]

# ---------------------------------------------------------------- image source par image de sortie
frames = []   # par image de sortie : (seg index, clip, n, u)
for k in range(NF):
    t = k / FPS
    si = max(i for i, s in enumerate(SEGS) if s["t0"] <= t + 1e-6)
    s = SEGS[si]
    u = (t - s["t0"]) / (s["t1"] - s["t0"])
    n = s["a"] if s["a"] == s["b"] else min(s["b"] - 1, s["a"] + int(math.floor((s["b"] - s["a"]) * u + 1e-6)))
    frames.append((si, s["clip"], n, u))

# ---------------------------------------------------------------- projecteur actif par image
def spot_at(k):
    t = k / FPS; si, clip, n, u = frames[k]
    for key, t0, t1, zoom in SPOTS:
        if t0 - 0.25 <= t <= t1 + 0.25:
            d = SPOT[key]
            if n in d:
                a = min(1, (t - t0 + 0.25) / 0.25, (t1 + 0.25 - t) / 0.25)
                return key, d[n], max(0, a), zoom, (t - t0)
    return None

# ---------------------------------------------------------------- caméra
cams = []
raw = []
for k in range(NF):
    si, clip, n, u = frames[k]
    s = SEGS[si]
    fx, fy = s["focus"](n, u)
    raw.append((si, fx, fy))
# lissage gaussien sigma = 10 images, par segment (pas à travers une coupe), sauf arrêts sur image
xs = np.array([r[1] for r in raw], float); ys = np.array([r[2] for r in raw], float)
sm_x, sm_y = xs.copy(), ys.copy()
k = 0
while k < NF:
    si = raw[k][0]; j = k
    while j < NF and (raw[j][0] == si or (SEGS[raw[j][0]].get("cont") and raw[j][0] == si + 1)): j += 1
    if not SEGS[si].get("freeze"):
        sm_x[k:j] = gaussian_filter1d(xs[k:j], 10, mode="nearest"); sm_y[k:j] = gaussian_filter1d(ys[k:j], 10, mode="nearest")
    k = j
cut_frames = [int(round(s["t0"] * FPS)) for s in SEGS[1:] if not s.get("cont")]
def labeled_heads(k):
    si, clip, n, u = frames[k]
    out = []
    for c, hk, a, b, *_ in LABELS:
        if c == clip and a <= n < b and n in HEAD[hk]: out.append(HEAD[hk][n])
    return out
for k in range(NF):
    si, clip, n, u = frames[k]
    s = SEGS[si]
    hc = s.get("hc", H0)
    cx, cy = sm_x[k], s.get("cy", (BAND[0] + BAND[1]) / 2)
    zoom = 1.0
    sp = spot_at(k)
    if sp and sp[3]:
        key, (px, py, r), a, _, dt = sp
        z = 1 + 0.22 * ease(min(1, max(0, dt / 0.8)))
        if dt < 0: z = 1.0
        hz = hc / z; wz = hz * 9 / 16
        # la caméra se rapproche du joueur
        tx = cx + (px - cx) * ease(min(1, max(0, dt / 0.8)))
        ty = cy + (py - cy) * ease(min(1, max(0, dt / 0.8)))
        ty = min(max(ty, BAND[0] + hz / 2), BAND[1] - hz / 2)
        ok = all(tx - wz / 2 + 30 < hx < tx + wz / 2 - 30 and ty - hz / 2 + 120 < hy < ty + hz / 2 for hx, hy in labeled_heads(k))
        # le cercle doit rester entier dans le cadre
        ok = ok and (tx - wz / 2 < px - r and px + r < tx + wz / 2)
        if ok: zoom, cx, cy = z, tx, ty
    # punch +7 % à chaque coupe, retombe en 0,1 s
    for cf in cut_frames:
        if cf <= k < cf + 3: zoom *= 1 + 0.07 * (1 - (k - cf) / 3)
    hz = hc / zoom; wz = hz * 9 / 16
    cy = min(max(cy, (BAND[0] if not s.get("hc") else 300) + hz / 2), (BAND[1] if not s.get("hc") else 1060) - hz / 2)
    cx = min(max(cx, wz / 2), 1920 - wz / 2)
    cams.append((cx - wz / 2, cy - hz / 2, H / hz))   # x0, y0 source, échelle

# ---------------------------------------------------------------- copier les images source utilisées
os.makedirs(f"{HF}/assets/frames", exist_ok=True)
used = sorted({(c, n) for _, c, n, _ in frames})
for c, n in used:
    dst = f"{HF}/assets/frames/{c}{n:04d}.jpg"
    if not os.path.exists(dst): shutil.copy(f"{SRC}/{c}/{n + 1:04d}.jpg", dst)

# ---------------------------------------------------------------- HTML
def f3(x): return f"{x:.3f}"
imgs = []
k = 0
while k < NF:
    si, c, n, _ = frames[k]; j = k
    while j < NF and frames[j][1:3] == (c, n) and frames[j][0] == si: j += 1
    t0 = max(0, (k - 0.25) / FPS); t1 = (j - 0.25) / FPS if j < NF else DUR
    imgs.append(f'<img id="f{len(imgs)}" class="clip src" src="assets/frames/{c}{n:04d}.jpg" data-start="{f3(t0)}" data-duration="{f3(t1 - t0)}" alt="">')
    k = j

js = []
def at(k): return f3(max(0, (k - 0.25) / FPS))
for k in range(NF):
    x0, y0, s = cams[k]
    js.append(f'C({at(k)},{-x0 * s:.1f},{-y0 * s:.1f},{s:.4f});')

# étiquettes
label_html = []
for li, (c, hk, a, b, name, club) in enumerate(LABELS):
    label_html.append(f'<div class="tag" id="tag{li}"><div class="logo"><img src="assets/logos/{club}.png" alt=""></div><div class="name">{name}</div><svg class="arrow" viewBox="0 0 64 86" width="64" height="86"><path d="M10 2 H54 V44 H62 L32 84 L2 44 H10 Z" fill="#ff1f1f" stroke="#3a0000" stroke-width="3" stroke-linejoin="round"/></svg></div>')
pops = []
tag_meas = []   # pour la vérification : (k, li, x_out, y_out_pointe)
for li, (c, hk, a, b, *_ ) in enumerate(LABELS):
    h = HEAD[hk]; vis_prev = False; start_t = None
    for k in range(NF):
        si, clip, n, u = frames[k]
        vis = clip == c and a <= n < b and n in h
        t = k / FPS
        if vis:
            x0, y0, s = cams[k]
            hx, hy = h[n]
            ox, oy = (hx - x0) * s, (hy - y0) * s
            if not vis_prev: start_t = t; pops.append(t)
            bounce = 5 * abs(math.sin(2 * math.pi * 1.4 * (t - start_t)))
            tip = oy - 1 - bounce
            sc = min(1, (t - start_t) / 0.12)
            sc = 1 - (1 - sc) ** 3
            js.append(f'T({at(k)},{li},{ox:.1f},{tip:.1f},{sc:.3f});')
            tag_meas.append((k, li, ox, tip, oy))
        elif vis_prev:
            js.append(f'T({at(k)},{li},0,0,0);')
        vis_prev = vis

# projecteur
spot_meas = []
prev = False
for k in range(NF):
    sp = spot_at(k)
    if sp:
        key, (px, py, r), a, _, _ = sp
        x0, y0, s = cams[k]
        ox, oy, orad = (px - x0) * s, (py - y0) * s, r * s
        js.append(f'P({at(k)},{ox:.1f},{oy:.1f},{orad:.1f},{a:.3f});')
        spot_meas.append((k, key, ox, oy, orad))
        prev = True
    elif prev:
        js.append(f'P({at(k)},0,0,0,0);'); prev = False

# sous-titres (texte du script, un mot à la fois)
subs = []
for i, w in enumerate(words):
    t0 = w["start"]; t1 = words[i + 1]["start"] if i + 1 < len(words) else min(DUR, w["end"] + 0.3)
    txt = re.sub(r"[.,:;!?]+$", "", w["w"]).lower()
    subs.append(f'<div id="w{i}" class="clip sub" data-start="{f3(t0)}" data-duration="{f3(max(0.05, t1 - t0))}">{txt}</div>')

# bandeau de score
t_score = S(1); t_flip = S(36)
# sons
audio = [f'<audio id="vo" class="clip" src="assets/voice.wav" data-start="0" data-duration="{f3(DUR)}" data-volume="0.76"></audio>']
def snd(name, t, vol, dur):
    if t < 0 or t >= DUR: return
    audio.append(f'<audio id="sfx{len(audio)}" class="clip" src="assets/sfx/{name}.wav" data-start="{f3(t)}" data-duration="{f3(min(dur, DUR - t))}" data-volume="{vol * 0.76:.3f}"></audio>')
SDUR = {"cut1": .32, "cut2": .28, "cut3": .36, "cut4": .30, "freeze": .45, "pop": .12, "kick1": .3, "kick2": .3, "kick3": .3}
for i, cf in enumerate(cut_frames):
    snd(["cut1", "cut2", "cut3", "cut4"][i % 4], cf / FPS - 0.12, 0.30, SDUR["cut1"])
for s in SEGS:
    if s.get("freeze") and not s.get("cont"): snd("freeze", s["t0"], 0.35, .45)
for t in pops: snd("pop", t, 0.30, .12)
snd("pop", t_score, 0.30, .12)
ki = 0
for k in range(1, NF):
    si, c, n, u = frames[k]; _, pc, pn, _ = frames[k - 1]
    if (c, n) in KICKS and (pc, pn) != (c, n):
        snd(["kick1", "kick2", "kick3"][ki % 3], k / FPS, 0.45, .3); ki += 1

html = f'''<!doctype html>
<html lang="fr" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="lib/gsap.min.js"></script>
<style>
@font-face {{ font-family: "Montserrat"; font-weight: 800; src: url(assets/fonts/Montserrat-ExtraBold.ttf); }}
@font-face {{ font-family: "Poppins"; font-weight: 500; src: url(assets/fonts/Poppins-Medium.ttf); }}
@font-face {{ font-family: "Poppins"; font-weight: 800; src: url(assets/fonts/Poppins-ExtraBold.ttf); }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: #000; }}
#root {{ position: relative; width: 1080px; height: 1920px; overflow: hidden; }}
#cam {{ position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; transform-origin: 0 0; }}
#cam img.src {{ position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; }}
#dim {{ position: absolute; inset: 0; z-index: 10; opacity: 0; background: rgba(0,0,0,.58);
  backdrop-filter: blur(5px); -webkit-backdrop-filter: blur(5px);
  --x: 540px; --y: 960px; --r: 200px;
  -webkit-mask-image: radial-gradient(circle var(--r) at var(--x) var(--y), transparent calc(var(--r) - 1px), #000 var(--r));
          mask-image: radial-gradient(circle var(--r) at var(--x) var(--y), transparent calc(var(--r) - 1px), #000 var(--r)); }}
#ring {{ position: absolute; z-index: 11; left: 0; top: 0; width: 400px; height: 400px; border-radius: 50%; opacity: 0;
  border: 5px solid #fff; box-shadow: 0 0 14px rgba(255,255,255,.55), inset 0 0 10px rgba(255,255,255,.25); }}
.tag {{ position: absolute; z-index: 20; left: 0; top: 0; width: 0; height: 0; transform-origin: 0 0; transform: scale(0); }}
.tag .arrow {{ position: absolute; left: -32px; top: -86px; filter: drop-shadow(0 3px 3px rgba(0,0,0,.5)); }}
.tag .name {{ position: absolute; left: 0; top: -150px; transform: translateX(-50%); white-space: nowrap;
  font: 800 38px/1 "Montserrat", sans-serif; color: #fff; background: rgba(12,12,14,.86); padding: 9px 20px 10px; border-radius: 30px; }}
.tag .logo {{ position: absolute; left: -42px; top: -246px; width: 84px; height: 84px; border-radius: 50%; background: #fff;
  display: flex; align-items: center; justify-content: center; box-shadow: 0 3px 8px rgba(0,0,0,.45); }}
.tag .logo img {{ height: 64px; width: auto; }}
.sub {{ position: absolute; z-index: 40; left: 0; width: 1080px; top: 1600px; text-align: center;
  font: 500 46px/1.15 "Poppins", sans-serif; color: #fff; text-shadow: 0 2px 4px rgba(0,0,0,.85); }}
#score {{ position: absolute; z-index: 30; top: 150px; left: 50%; transform: translateX(-50%) scale(0); display: flex; align-items: stretch;
  font: 800 40px/1 "Poppins", sans-serif; color: #fff; border-radius: 14px; overflow: hidden; box-shadow: 0 6px 18px rgba(0,0,0,.5); }}
#score .team {{ background: rgba(10,10,12,.88); padding: 16px 22px; }}
#score .box {{ background: #e3121b; padding: 16px 20px; display: flex; gap: 14px; }}
#score .dig {{ position: relative; display: inline-block; width: 28px; height: 40px; }}
#score .dig span {{ position: absolute; left: 0; top: 0; width: 28px; text-align: center; }}
#score .min {{ background: #fff; color: #e3121b; padding: 16px 16px; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{f3(DUR)}" data-width="1080" data-height="1920">
<div id="cam">
{chr(10).join(imgs)}
</div>
<div id="dim"></div><div id="ring"></div>
{chr(10).join(label_html)}
<div id="score"><div class="team">AEK</div><div class="box"><div class="dig" data-layout-allow-overlap><span id="d0">0</span><span id="d1" style="transform: scaleY(0)">1</span></div><div>–</div><div class="dig"><span>0</span></div></div><div class="team">RMA</div><div class="min">12'</div></div>
{chr(10).join(subs)}
{chr(10).join(audio)}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
const cam = document.getElementById("cam"), dim = document.getElementById("dim"), ring = document.getElementById("ring");
const tags = [...document.querySelectorAll(".tag")];
function C(t, x, y, s) {{ tl.set(cam, {{ x: x, y: y, scale: s, transformOrigin: "0 0" }}, t); }}
function T(t, i, x, y, s) {{ tl.set(tags[i], {{ x: x, y: y, scale: s, transformOrigin: "0 0" }}, t); }}
function P(t, x, y, r, a) {{
  tl.set(dim, {{ "--x": x + "px", "--y": y + "px", "--r": r + "px", opacity: a }}, t);
  tl.set(ring, {{ x: x - r, y: y - r, width: 2 * r, height: 2 * r, opacity: a }}, t);
}}
{chr(10).join(js)}
tl.fromTo("#score", {{ scale: 0 }}, {{ scale: 1, duration: 0.12, ease: "back.out(2)" }}, {f3(t_score)});
tl.to("#d0", {{ scaleY: 0, duration: 0.17, ease: "power2.in" }}, {f3(t_flip)});
tl.fromTo("#d1", {{ scaleY: 0 }}, {{ scaleY: 1, duration: 0.17, ease: "power2.out", immediateRender: false }}, {f3(t_flip + 0.17)});
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = tl;
tl.seek(0);
</script>
</body>
</html>
'''
open(f"{HF}/index.html", "w").write(html)
json.dump({"frames": frames, "cams": cams, "tags": tag_meas, "spots": spot_meas, "segs": [{k: v for k, v in s.items() if k != "focus"} for s in SEGS],
           "cuts": cut_frames, "dur": DUR}, open(f"{ROOT}/build/plan.json", "w"))
print("durée", DUR, "images sortie", NF, "imgs", len(imgs), "sources", len(used), "sets", len(js))
