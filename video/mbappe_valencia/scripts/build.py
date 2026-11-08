# Builds the HyperFrames composition (index.html) for the Mbappé goal analysis (Spanish voice).
# Python is only used to compute data (EDL, camera path, tracking); the edit itself is HTML/GSAP rendered by HyperFrames.
import json, math, re, os
import numpy as np

R = "/tmp/claude-0/-home-user-Fofana/ee96c0df-7bfe-5d5b-8578-10ba5a54e09d/scratchpad"
P = R + "/hfproj"
FPS = 30
SRC_FPS = 60
DUR = 67.20
N = int(round(DUR * FPS))
OW, OH = 1080, 1920
ASPECT = OW / OH

words = json.load(open(R + "/work/words.json"))
def wt(i):
    return words[i]["start"]
def find(word, after=0.0):
    for w in words:
        if w["start"] >= after - 1e-6 and re.sub(r"[^\wáéíóúüñ]", "", w["word"].lower()) == word:
            return w["start"]
    raise KeyError(word)

# ---------------- EDL (cut times = first word of each sentence) ----------------
T = {
    "todo": find("todo", 5), "sin": find("sin", 10), "el1": find("el", 18), "los": find("los", 23),
    "y": find("y", 27.4), "en1": find("en", 28.5), "con": find("con", 35), "en2": find("en", 40.5),
    "pero": find("pero", 51), "mb2": find("mbappé", 57), "el2": find("el", 60), "pero2": find("pero", 62),
    "empuja": find("empuja", 64), "lanza": find("lanza", 15),
}
shots = [
    # t0, t1, clip, f0, f1
    (0.0, T["todo"], "A", 1590, 1690),
    (T["todo"], T["sin"], "C", 0, 70),          # Konaté receives (clip C)
    (T["sin"], T["lanza"], "C", 157, 219),      # back-pass to Courtois (cut before the red arrow graphic)
    (T["lanza"], T["el1"], "B", 0, 80),         # long ball in the air (live)
    (T["el1"], T["los"], "B", 80, 140),
    (T["los"], T["y"], "A", 520, 580),
    (T["y"], T["en1"], "A", 580, 580),          # freeze: "es un genio"
    (T["en1"], T["con"], "A", 580, 665),
    (T["con"], T["en2"], "B", 140, 215),
    (T["en2"], T["pero"], "B", 215, 215),       # freeze: options
    (T["pero"], T["mb2"], "A", 935, 1110),
    (T["mb2"], T["el2"], "A", 1110, 1260),
    (T["el2"], T["pero2"], "A", 1260, 1310),
    (T["pero2"], T["empuja"], "A", 1310, 1348),
    (T["empuja"], DUR, "A", 1348, 1464),
]
FREEZES = [i for i, s in enumerate(shots) if s[3] == s[4]]

def shot_at(t):
    for i, s in enumerate(shots):
        if s[0] - 1e-9 <= t < s[1] - 1e-9:
            return i
    return len(shots) - 1

# source frame for each output frame (quarter-frame offset avoids rounding at boundaries)
out = []
for i in range(N):
    t = (i + 0.25) / FPS
    k = shot_at(t)
    t0, t1, clip, f0, f1 = shots[k]
    a = (t - t0) / (t1 - t0)
    sf = f0 + (f1 - f0) * a
    out.append({"t": t, "shot": k, "clip": clip, "sf": sf, "fi": int(min(max(round(sf), min(f0, f1)), max(f0, f1)))})

# ---------------- tracks ----------------
def interp_kf(kf, f):
    ks = sorted(kf)
    if f <= ks[0]: return np.array(kf[ks[0]], float)
    if f >= ks[-1]: return np.array(kf[ks[-1]], float)
    for a, b in zip(ks, ks[1:]):
        if a <= f <= b:
            u = (f - a) / (b - a)
            # smoothstep-free linear interpolation keeps measured keyframes exact
            return (1 - u) * np.array(kf[a], float) + u * np.array(kf[b], float)

# head top (x,y) and feet y; body half-width
MB_HOOK = {1590: (1300, 377, 960), 1605: (1193, 343, 950), 1620: (1060, 310, 940), 1635: (953, 280, 930),
           1650: (890, 260, 920), 1665: (853, 250, 915), 1680: (827, 240, 910), 1690: (833, 250, 910), 1700: (867, 260, 910)}
KO_C = {0: (130, 259, 347), 15: (171, 235, 327), 30: (204, 220, 310), 45: (230, 210, 300), 60: (245, 213, 296), 70: (230, 206, 291),
        157: (252, 213, 297), 170: (247, 206, 294), 185: (245, 214, 299)}
CO_C = {196: (255, 96, 169), 205: (253, 96, 169), 225: (260, 104, 171), 243: (264, 107, 178)}
GU_B = {100: (1459, 489, 543), 115: (1476, 481, 554), 130: (1487, 492, 554), 145: (1487, 494, 550), 160: (1474, 497, 548),
        175: (1484, 484, 546), 190: (1489, 470, 532), 205: (1479, 476, 535), 215: (1489, 475, 539)}
GU_AW = {520: (1894, 713, 795), 540: (1856, 712, 777), 560: (1809, 705, 787), 580: (1767, 695, 780), 600: (1716, 683, 763),
         620: (1681, 684, 752), 640: (1684, 702, 767), 665: (1811, 791, 871)}

MB_CLOSE = {1182: (771, 169), 1185: (771, 169), 1200: (730, 172), 1215: (700, 195), 1230: (677, 238), 1245: (707, 209), 1260: (711, 199),
            1275: (753, 185), 1290: (794, 162), 1305: (840, 109), 1320: (849, 86), 1335: (758, 94), 1347: (690, 104)}
# close-angle Mbappé from the pink-kit tracker (box x,y,w,h), smoothed
mc = json.load(open(R + "/tracks/mC.raw.json"))
mc_f = sorted(int(k) for k in mc if mc[k] is not None)
arr = np.array([mc[str(f)] for f in mc_f], float)
def gsmooth(x, s):
    if s <= 0: return x
    r = int(3 * s); k = np.exp(-0.5 * (np.arange(-r, r + 1) / s) ** 2); k /= k.sum()
    xp = np.pad(x, ((r, r),) + ((0, 0),) * (x.ndim - 1), mode="edge")
    return np.stack([np.convolve(xp[:, j], k, mode="valid") for j in range(x.shape[1])], 1) if x.ndim > 1 else np.convolve(xp, k, mode="valid")
# robust: median filter then gaussian
from statistics import median
med = np.array([[median(arr[max(0, i - 3):i + 4, j]) for j in range(4)] for i in range(len(arr))])
sm = gsmooth(med, 3)
MBC = {f: sm[i] for i, f in enumerate(mc_f)}
def mb_close(f):
    f = int(round(f)); f = min(max(f, mc_f[0]), mc_f[-1])
    x, y, w, h = MBC[f]
    hx, hy = interp_kf(MB_CLOSE, f)
    return np.array([hx, hy, y + h * 1.04, w])

def carrier(k, sf):
    """returns (name, head_x, head_y, feet_y, halfwidth) or None for the ball carrier in shot k at source frame sf"""
    t0, t1, clip, f0, f1 = shots[k]
    if k == 0:
        hx, hy, fy = interp_kf(MB_HOOK, sf); return ("Kylian Mbappé", hx, hy, fy, 210)
    if clip == "C" and ((k == 1 and sf >= 62) or (k == 2 and sf < 166)):
        hx, hy, fy = interp_kf(KO_C, sf); return ("Ibrahima Konaté", hx, hy, fy, 22)
    if clip == "B" and k in (4, 8, 9) and sf >= 100:
        hx, hy, fy = interp_kf(GU_B, sf); return ("Arda Güler", hx, hy, fy, 34)
    if clip == "A" and k in (5, 6, 7):
        hx, hy, fy = interp_kf(GU_AW, sf); return ("Arda Güler", hx, hy, fy, 52)
    if clip == "A" and k in (11, 12, 13) and 1182 <= sf < 1348:
        hx, hy, fy, w = mb_close(sf); return ("Kylian Mbappé", hx, hy, fy, max(w * 0.62, 120))
    return None

def spot_target(kk, sf):
    if kk == 2:
        hx, hy, fy = interp_kf(CO_C, sf); return ("Thibaut Courtois", hx, hy, fy, 30)
    if kk == 1:
        hx, hy, fy = interp_kf(KO_C, sf); return ("Ibrahima Konaté", hx, hy, fy, 24)
    return carrier(kk, sf)

# ---------------- spotlights ----------------
SPOTS = [  # (t_in, t_out, shot index)
    (find("konaté", 8), T["sin"] - 0.15, 1),
    (find("thibaut", 12), T["lanza"] - 0.2, 2),
    (find("arda", 18), T["los"] - 0.25, 4),
    (T["y"], T["en1"] - 0.05, 6),
    (T["en2"] + 0.1, find("jugar", 44) - 0.2, 9),
    (T["mb2"], T["el2"] - 0.25, 11),
    (find("mbappé", 62), T["empuja"] - 0.1, 13),
]
FADE = 0.25
def spot_alpha(t):
    for j, (a, b, k) in enumerate(SPOTS):
        if a - 1e-6 <= t <= b:
            return j, min(1.0, (t - a) / FADE, (b - t) / FADE)
    return None, 0.0

# ---------------- camera ----------------
H_DEFAULT = {0: 880, 1: 600, 2: 600, 3: 740, 4: 640, 5: 560, 6: 560, 7: 560, 8: 640, 9: 700, 10: 880, 11: 880, 12: 880, 13: 880, 14: 880}
# explicit camera paths (source frame -> centre) for shots without a tracked player
PATHS = {
    1: {0: (150, 330), 30: (215, 300), 60: (245, 290), 70: (235, 285)},
    2: {157: (255, 300), 175: (255, 290), 200: (255, 250), 219: (262, 245)},
    3: {0: (1450, 480), 40: (1445, 500), 80: (1455, 505)},
    10: {935: (700, 430), 960: (1100, 520), 990: (1400, 540), 1020: (1500, 600), 1050: (1150, 580), 1080: (1060, 570), 1110: (1350, 560)},
    14: {1348: (620, 520), 1380: (1080, 560), 1410: (1420, 560), 1440: (1560, 560), 1464: (1560, 560)},
}

# overlays burned into the source (must never be inside the 9:16 window)
def overlays(clip, f):
    pad = 8
    if clip == "C":
        r = [(150, 0, 330, 112)] if f >= 220 else []
        r += [(0, 0, 0, 0)] if False else []
        return [(a - pad, b - pad, c + pad, d + pad) for a, b, c, d in r]
    r = [(760, 885, 1092, 930), (1733, 874, 1852, 962), (1572, 996, 1856, 1040), (1600, 50, 1830, 112)]
    if clip == "A":
        r.append((92, 38, 312, 174))
    if clip == "B" and f < 230:
        r.append((698, 905, 1448, 1008))  # TV score bar at the bottom
    return [(a - pad, b - pad, c + pad, d + pad) for a, b, c, d in r]

def window(cx, cy, H):
    W = H * ASPECT
    return [cx - W / 2, cy - H / 2, W, H]

DIMS = {"A": (1920, 1080), "B": (1920, 1080), "C": (720, 794)}
DW, DH = 1920, 1080
def valid(win, ovs):
    x, y, w, h = win
    if x < -0.5 or y < -0.5 or x + w > DW + 0.5 or y + h > DH + 0.5: return False
    for a, b, c, d in ovs:
        if x < c and x + w > a and y < d and y + h > b: return False
    return True

def solve(cx, cy, H, ovs, keep=None):
    """closest valid window to the desired one; keep = (x0,y0,x1,y1) region that must stay inside"""
    best = None; bc = 1e18
    for hs in [1.0, 0.96, 0.92, 0.88, 0.84, 0.8, 0.76, 0.72, 0.68, 0.64, 0.6]:
        h = H * hs; w = h * ASPECT
        xs = [cx - w / 2, 0, DW - w]; ys = [cy - h / 2, 0, DH - h]
        for a, b, c, d in ovs:
            xs += [c, a - w]; ys += [d, b - h]
        for x in xs:
            for y in ys:
                win = [x, y, w, h]
                if not valid(win, ovs): continue
                if keep is not None:
                    kx0, ky0, kx1, ky1 = keep
                    if kx0 < x or kx1 > x + w or ky0 < y or ky1 > y + h: continue
                cost = (x + w / 2 - cx) ** 2 + (y + h / 2 - cy) ** 2 + (1 - hs) * 4e5
                if cost < bc: bc = cost; best = win
        if best is not None and hs < 1.0 and bc < 1e5: break
    if best is None:  # relax keep
        return solve(cx, cy, H, ovs, None) if keep is not None else window(cx, cy, H * 0.6)
    return best

# desired centre per output frame
des = []
for o in out:
    k = o["shot"]; sf = o["sf"]; H = H_DEFAULT[k]
    c = carrier(k, sf)
    if k in PATHS:
        px, py = interp_kf(PATHS[k], sf); cx, cy = px, py
    elif c is not None:
        _, hx, hy, fy, hw = c
        bh = fy - hy
        cx = hx; cy = hy + 0.26 * H  # head at ~20% from the top, room for the label above
        if k == 0: cy = hy + 0.36 * H
    elif k == 9:
        cx, cy = 1489, 560
    else:
        cx, cy = 960, 540
    des.append([cx, cy, H])
des = np.array(des, float)

# options freeze (shot 8): explore the frame -> teammate, other side, back
t_jugar = find("jugar", 44); t_otro = find("otro", 50); t_pero = T["pero"]
def options_path(t):
    G = (1489, 560); M = (760, 600); L = (300, 560)
    keys = [(T["en2"], G), (t_jugar, G), (t_jugar + 0.9, M), (t_otro - 1.2, M), (t_otro - 0.1, L), (t_pero - 0.9, L), (t_pero, G)]
    for (ta, a), (tb, b) in zip(keys, keys[1:]):
        if ta <= t <= tb:
            u = (t - ta) / max(tb - ta, 1e-6); u = u * u * (3 - 2 * u)
            return a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u
    return G
for i, o in enumerate(out):
    if o["shot"] == 9:
        des[i, 0], des[i, 1] = options_path(o["t"])

# smooth inside each shot (sigma 10 frames), freezes stay as designed
sm_des = des.copy()
for k in range(len(shots)):
    idx = [i for i, o in enumerate(out) if o["shot"] == k]
    if not idx or k in (6, 9): continue
    sm_des[idx] = gsmooth(des[idx], 10)

# spotlight zoom (+22%) toward the player, eased with the spotlight alpha
spot_info = []
for i, o in enumerate(out):
    j, al = spot_alpha(o["t"])
    spot_info.append((j, al))
    if j is not None and al > 0:
        c = spot_target(o["shot"], o["sf"])
        if c is not None:
            _, hx, hy, fy, hw = c
            bx, by = hx, (hy + fy) / 2
            sm_des[i, 0] += (bx - sm_des[i, 0]) * 0.5 * al
            sm_des[i, 1] += (by - sm_des[i, 1]) * 0.5 * al
            sm_des[i, 2] /= (1 + 0.22 * al)

cams = []
for i, o in enumerate(out):
    cx, cy, H = sm_des[i]
    DW, DH = DIMS[o["clip"]]
    ovs = overlays(o["clip"], o["fi"])
    c = carrier(o["shot"], o["sf"])
    keep = None
    if c is not None and o["shot"] != 9:
        _, hx, hy, fy, hw = c
        lab = (290 if o["shot"] else 250) * H / OH  # label height (output px) in source px
        keep = (hx - 1.15 * 150 * H / OH, hy - lab, hx + 1.15 * 150 * H / OH, hy + 10)
    cams.append(solve(cx, cy, H, ovs, keep))
cams = np.array(cams, float)
# light smoothing of the solved path, keep only if still valid
for k in range(len(shots)):
    idx = [i for i, o in enumerate(out) if o["shot"] == k]
    if not idx or k in (6,): continue
    s = gsmooth(cams[idx], 3)
    for n, i in enumerate(idx):
        DW, DH = DIMS[out[i]["clip"]]
        if valid(list(s[n]), overlays(out[i]["clip"], out[i]["fi"])):
            cams[i] = s[n]

# ---------------- per output frame data ----------------
NAME_LOGO = {"Kylian Mbappé": "assets/rma.png", "Arda Güler": "assets/rma.png"}
frames = []
label_on_prev = None
for i, o in enumerate(out):
    x0, y0, w, h = cams[i]
    s = OH / h
    # punch zoom +7% at each cut, back in 0.1 s
    k = o["shot"]; dt = o["t"] - shots[k][0]
    punch = 1 + 0.07 * max(0.0, 1 - dt / 0.1) if k > 0 else 1.0
    c = carrier(k, o["sf"])
    lab = None
    if c is not None:
        name, hx, hy, fy, hw = c
        lx, ly = (hx - x0) * s, (hy - y0) * s
        if 60 <= lx <= OW - 60 and 165 <= ly <= OH:
            lab = [name, round(lx, 1), round(ly, 1)]
    j, al = spot_info[i]
    sp = None
    if j is not None and al > 0:
        a, b, kk = SPOTS[j]
        cc = spot_target(kk, o["sf"]) if kk == k else None
        if cc is not None:
            # constant radius = largest needed during this spotlight (computed below)
            _, hx, hy, fy, hw = cc
            sp = [j, round(al, 3), hx, (hy + fy) / 2]
    frames.append({"cam": [round(x0, 2), round(y0, 2), round(s, 5), round(punch, 4)], "lab": lab, "sp": sp})

# constant spotlight radius per spotlight (source px), centre lightly smoothed
for j in range(len(SPOTS)):
    idx = [i for i, f in enumerate(frames) if f["sp"] and not f.get("spdone") and f["sp"][0] == j]
    if not idx: continue
    rmax = 0
    for i in idx:
        o = out[i]; c = spot_target(SPOTS[j][2], o["sf"])
        _, hx, hy, fy, hw = c
        rmax = max(rmax, math.hypot(hw, (fy - hy) / 2))
    rmax *= 1.18
    cen = np.array([[frames[i]["sp"][2], frames[i]["sp"][3]] for i in idx])
    cen = gsmooth(cen, 2)
    for n, i in enumerate(idx):
        x0, y0, s, _ = frames[i]["cam"]
        frames[i]["spdone"] = True
        frames[i]["sp"] = [frames[i]["sp"][1], round((cen[n, 0] - x0) * s, 1), round((cen[n, 1] - y0) * s, 1), round(rmax * s, 1)]

# label appearance: pop at each new appearance / new shot
for i, f in enumerate(frames):
    if f["lab"]:
        prev = frames[i - 1] if i else None
        newpop = (prev is None or not prev["lab"] or prev["lab"][0] != f["lab"][0] or out[i]["shot"] != out[i - 1]["shot"])
        f["lab"].append(0 if newpop else frames[i - 1]["lab"][3] + 1)

bt = np.array([0.0 if (f["lab"] and f["lab"][2] < 470) else 1.0 for f in frames])
bt = np.convolve(np.pad(bt, 3, mode="edge"), np.ones(7) / 7, mode="valid")
for i, f in enumerate(frames):
    f["bv"] = round(float(bt[i]), 3)

# ---------------- image clips ----------------
clips = []
cur = None
for i, o in enumerate(out):
    key = (o["clip"], o["fi"])
    if cur and cur[0] == key:
        cur[2] = i + 1
    else:
        cur = [key, i, i + 1]; clips.append(cur)
img_html = []
for (clip, fi), a, b in clips:
    st = a / FPS; du = (b - a) / FPS
    dw, dh = DIMS[clip]
    img_html.append(f'<img class="clip src" style="width:{dw}px;height:{dh}px" src="frames/{clip}/{fi:05d}.jpg" data-start="{st:.4f}" data-duration="{du:.4f}" alt="">')

# ---------------- subtitles (one word at a time, script text) ----------------
subs = []
for n, w in enumerate(words):
    st = w["start"]; en = words[n + 1]["start"] if n + 1 < len(words) else min(w["end"] + 0.3, DUR)
    en = min(en, w["end"] + 0.35) if n + 1 < len(words) and words[n + 1]["start"] - w["end"] > 0.4 else en
    txt = re.sub(r"[.,]", "", w["word"]).lower()
    subs.append(f'<div class="clip sub" data-start="{st:.3f}" data-duration="{max(en - st, 0.05):.3f}">{txt}</div>')

# ---------------- sounds ----------------
cut_times = [s[0] for s in shots[1:]]
snd = []
wh = 0
for n, ct in enumerate(cut_times):
    if (shots[n + 1][3] == shots[n + 1][4]):
        snd.append(("freeze", ct, 0.35, 0.55))
    else:
        snd.append((f"whoosh{1 + wh % 2}", max(0, ct - 0.12), 0.42, 0.42)); wh += 1
# pops: each label appearance and the score banner
for i, f in enumerate(frames):
    if f["lab"] and f["lab"][3] == 0:
        snd.append(("pop", out[i]["t"], 0.14, 0.45))
BANNER_T = T["todo"]
snd.append(("pop", BANNER_T, 0.14, 0.45))
# ball strike on the contact frame of the finish
snd.append(("kick", T["empuja"], 0.32, 0.7))
FLIP_T = find("red", 66)
audio_html = ['<audio id="voice" class="clip" src="assets/voice.wav" data-start="0" data-duration="66.800" data-volume="1.0"></audio>']
for n, (nm, st, du, vol) in enumerate(snd):
    audio_html.append(f'<audio id="sfx{n}" class="clip" src="assets/sfx/{nm}.wav" data-start="{st:.3f}" data-duration="{du:.3f}" data-volume="{vol}"></audio>')

# options freeze overlay (arrows drawn in source coordinates, inside the stage)
opt = {"t_jugar": round(t_jugar, 3), "t_otro": round(t_otro - 0.3, 3), "t_end": round(t_pero, 3)}

data = {"fps": FPS, "n": N, "frames": frames, "opt": opt, "flip": round(FLIP_T, 3), "banner": round(BANNER_T, 3),
        "shot8": [round(shots[9][0], 3), round(shots[9][1], 3)]}
json.dump(data, open(P + "/assets/data.json", "w"), separators=(",", ":"))

html = open(R + "/scripts/template.html").read()
html = html.replace("{{IMGS}}", "\n        ".join(img_html)).replace("{{SUBS}}", "\n      ".join(subs)).replace("{{AUDIO}}", "\n    ".join(audio_html))
html = html.replace("{{DATA}}", json.dumps(data, separators=(",", ":"))).replace("{{DUR}}", f"{DUR:.3f}")
open(P + "/index.html", "w").write(html)
print("frames", N, "clips", len(clips), "subs", len(subs), "sfx", len(snd))
print("cuts", [round(c, 2) for c in cut_times])
json.dump({"out": [{"t": o["t"], "clip": o["clip"], "fi": o["fi"], "shot": o["shot"]} for o in out], "cams": cams.tolist()}, open(R + "/work/edl_debug.json", "w"))
