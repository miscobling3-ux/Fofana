# Builds hf/index.html (HyperFrames composition) + per-frame data from the EDL, tracks and words.json.
import json, math, os, shutil, numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
FPS = 30
DUR = 59.9
OW, OH = 1080, 1920
WORDS = json.load(open("voice/words.json"))
HEADS = json.load(open("work/heads.json"))
FOLLOW = json.load(open("work/follow.json"))
FORBID = json.load(open("work/forbid.json"))
FOLLOW_CAP = {"FD10": 357, "FM": 846}

def sent_start(k):
    return min(w["start"] for w in WORDS if w["sentence"] == k)

def word_time(k, text, nth=0):
    ws = [w for w in WORDS if w["sentence"] == k and w["text"].strip(".,:;!?").lower() == text.lower()]
    return ws[nth]["start"]

S = [sent_start(k) for k in range(12)]
S[0] = 0.0

# ---------------- EDL ----------------
# kind: play (src a->b) or freeze (src a). cam: list of (src_frame, cx, cy) keys or ("follow", track, dx, dy)
SHOTS = [
    dict(id="E0", clip="A", a=786, b=870, T0=0.0, T1=S[1], H=760, cam=[("F", "FM", 0, 110)]),
    dict(id="E1", clip="B", a=50, b=168, T0=S[1], T1=S[2], H=700, cam=[("F", "FD1", -30, 60)]),
    dict(id="E2", clip="B", a=168, b=222, T0=S[2], T1=S[3], H=760, cam=[("F", "FB2", 40, 60)]),
    dict(id="E3", clip="A", a=490, b=540, T0=S[3], T1=S[4], H=980, cam=[("F", "FB3", 0, 330)]),
    dict(id="E4", clip="B", a=205, b=205, T0=S[4], T1=S[5], H=885, cam=[(205, 990, 640)], freeze=True),
    dict(id="E5", clip="A", a=540, b=578, T0=S[5], T1=S[6], H=980, cam=[("F", "FB3", 0, 330)]),
    dict(id="E6", clip="B", a=210, b=262, T0=S[6], T1=S[7], H=885, cam=[(210, 1000, 650), (224, 1020, 650), (262, 1480, 640)]),
    dict(id="E7", clip="A", a=600, b=700, T0=S[7], T1=S[8], H=1000, cam=[(600, 560, 600), (640, 580, 600), (672, 830, 600), (700, 1000, 620)]),
    dict(id="E8", clip="A", a=300, b=368, T0=S[8], T1=S[9], H=900, cam=[(300, 420, 560), (329, 300, 520), ("F", "FD8", 110, 200)]),
    dict(id="E9", clip="B", a=312, b=312, T0=S[9], T1=S[10], H=760, cam=[(312, 1440, 560)], freeze=True),
    dict(id="E10", clip="B", a=312, b=372, T0=S[10], T1=S[11], H=760, cam=[("F", "FD10", -60, 40), (335, 1330, 520), (352, 1130, 480), (372, 960, 470)]),
    dict(id="E11", clip="A", a=716, b=850, T0=S[11], T1=DUR, H=760, cam=[(716, 470, 700), (742, 760, 690), ("F", "FM", 0, 110)]),
]

# label segments (ball carrier): track, shot, from src frame, contact frame (label disappears AT this frame)
LABELS = [
    dict(shot="E0", trk="L0", f0=786, fc=791),
    dict(shot="E1", trk="L1", f0=100, fc=143),
    dict(shot="E2", trk="L2", f0=188, fc=222),
    dict(shot="E3", trk="L3", f0=490, fc=9999),
    dict(shot="E4", trk="L4", f0=205, fc=9999),
    dict(shot="E5", trk="L3", f0=540, fc=550),
    dict(shot="E6", trk="L2", f0=210, fc=222),
    dict(shot="E7", trk="L5", f0=672, fc=688),
    dict(shot="E8", trk="L6", f0=330, fc=366),
    dict(shot="E9", trk="L7", f0=312, fc=9999),
    dict(shot="E10", trk="L7", f0=312, fc=317),
    dict(shot="E11", trk="L8", f0=778, fc=791),
]
CLUB = {"Kylian Mbappé": "rm", "Denzel Dumfries": "rm", "Jude Bellingham": "rm"}
# contact frames -> ball sound
CONTACTS = [("E1", 143), ("E2", 188), ("E2", 222), ("E5", 550), ("E6", 222), ("E7", 672), ("E7", 688),
            ("E8", 366), ("E10", 317), ("E11", 778), ("E11", 791), ("E0", 791)]

# spotlights: shot, follow track, start time (word naming player), end time, body height(src px), extra radius
SPOTS = [
    dict(shot="E0", trk="FM", t0=word_time(0, "Mbappé"), t1=4.0, h=120),
    dict(shot="E1", trk="FD1", t0=word_time(1, "Dumfries"), t1=S[2] - 0.3, h=118),
    dict(shot="E10", trk="FD10", t0=word_time(10, "Dumfries"), t1=word_time(10, "Dumfries") + 1.7, h=112),
]

def track_pts(name, src):
    d = HEADS.get(name) or FOLLOW.get(name)
    p = d["pts"]
    cap = FOLLOW_CAP.get(name)
    keys = sorted(int(k) for k in p)
    if cap: keys = [k for k in keys if k <= cap]
    f = min(max(src, keys[0]), keys[-1])
    if str(f) in p: return p[str(f)]
    lo = max(k for k in keys if k <= f); hi = min(k for k in keys if k >= f)
    u = 0 if hi == lo else (f - lo) / (hi - lo)
    return [p[str(lo)][0] + u * (p[str(hi)][0] - p[str(lo)][0]), p[str(lo)][1] + u * (p[str(hi)][1] - p[str(lo)][1])]

def cam_center(sh, src):
    pts = []
    for c in sh["cam"]:
        if c[0] == "F":
            d = FOLLOW[c[1]]["pts"]; keys = [int(k) for k in d]
            if FOLLOW_CAP.get(c[1]): keys = [k for k in keys if k <= FOLLOW_CAP[c[1]]]
            for k in keys:
                if sh["a"] <= k <= sh["b"]:
                    pts.append((k, d[str(k)][0] + c[2], d[str(k)][1] + c[3]))
        else:
            pts.append(c)
    pts = sorted(set(pts))
    # keep manual keys authoritative: drop follow points that fall between two manual keys
    fs = [p[0] for p in pts]
    if src <= fs[0]: return pts[0][1:]
    if src >= fs[-1]: return pts[-1][1:]
    for i in range(len(pts) - 1):
        if pts[i][0] <= src <= pts[i + 1][0]:
            a, b = pts[i], pts[i + 1]; u = (src - a[0]) / max(1e-9, b[0] - a[0])
            return (a[1] + u * (b[1] - a[1]), a[2] + u * (b[2] - a[2]))

def fit_window(clip, src, cx, cy, H, keep=None):
    """largest window <= H centred near (cx,cy), inside 1920x1080, avoiding forbidden rects; keep=(x,y) must stay inside with margin"""
    rects = FORBID[clip][src - 1]
    while H > 300:
        W = H * 9 / 16
        x = min(max(cx - W / 2, 0), 1920 - W)
        if keep:
            x = min(max(x, keep[0] - W + 140), keep[0] - 140)
            x = min(max(x, 0), 1920 - W)
        # vertical range allowed given rects that overlap horizontally
        lo, hi = 0.0, 1080.0
        for (rx0, ry0, rx1, ry1) in rects:
            if rx1 <= x or rx0 >= x + W: continue
            if ry0 < 540: lo = max(lo, ry1 + 2)
            else: hi = min(hi, ry0 - 2)
        if hi - lo >= H:
            y = min(max(cy - H / 2, lo), hi - H)
            if keep and not (y + 230 < keep[1] < y + H - 150):
                y2 = min(max(keep[1] - 260, lo), hi - H)
                y = y2
            return x, y, H
        H *= 0.97
    raise RuntimeError("no window")

def gauss(a, sigma=10):
    a = np.asarray(a, float)
    if len(a) < 3: return a
    r = int(3 * sigma); k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2); k /= k.sum()
    p = np.pad(a, r, mode="edge")
    return np.convolve(p, k, mode="valid")

# ---------------- per output frame ----------------
NF = int(round(DUR * FPS))
frames = []
img_clips = []   # (clip, src, start, dur)
for si, sh in enumerate(SHOTS):
    n0 = int(math.ceil(sh["T0"] * FPS - 1e-6)); n1 = int(math.ceil(sh["T1"] * FPS - 1e-6))
    a, b = sh["a"], sh["b"]
    if sh.get("freeze"):
        rate = 0.0
        img_clips.append((sh["clip"], a, sh["T0"] - 1 / 120 if si else 0, sh["T1"] - sh["T0"] + (1 / 120 if si else 0)))
    else:
        rate = (b - a + 1) / (sh["T1"] - sh["T0"])  # source frames per second
        sh["rate"] = rate
        # each source image covers exactly the output samples that should show it, +/- 1/4 output frame
        smp = {}
        for n in range(n0, n1):
            k = min(b, a + int(math.floor((n / FPS - sh["T0"]) * rate + 1e-6)))
            smp.setdefault(k, []).append(n)
        for k in sorted(smp):
            st = smp[k][0] / FPS - 1 / 120; en = smp[k][-1] / FPS + 1 / 120
            if si == 0 and k == min(smp): st = 0
            img_clips.append((sh["clip"], k, round(max(0, st), 5), round(en - max(0, st), 5)))
    sh["n0"], sh["n1"] = n0, n1
    cx, cy, HH, lab = [], [], [], []
    for n in range(n0, n1):
        t = n / FPS
        src = a if rate == 0 else min(b, a + int(math.floor((t - sh["T0"]) * rate + 1e-6)))
        c = cam_center(sh, src)
        cx.append(c[0]); cy.append(c[1]); HH.append(sh["H"])
        frames.append(dict(n=n, t=t, shot=si, clip=sh["clip"], src=src))
    if rate:
        cx, cy = gauss(cx), gauss(cy)
    for i, n in enumerate(range(n0, n1)):
        frames[n].update(cx=float(cx[i]), cy=float(cy[i]), H=float(HH[i]))

# labels per frame
for L in LABELS:
    si = [s["id"] for s in SHOTS].index(L["shot"]); sh = SHOTS[si]
    first = None
    for n in range(sh["n0"], sh["n1"]):
        fr = frames[n]
        if L["f0"] <= fr["src"] < L["fc"]:
            hx, hy = track_pts(L["trk"], fr["src"])
            if first is None: first = fr["t"]
            fr["label"] = dict(name=HEADS[L["trk"]]["name"], hx=hx, hy=hy, t0=first)

# windows (respecting labelled player)
for fr in frames:
    keep = (fr["label"]["hx"], fr["label"]["hy"]) if "label" in fr else None
    fr["win"] = fit_window(fr["clip"], fr["src"], fr["cx"], fr["cy"], fr["H"], keep)
# smooth windows again inside each played shot, then re-validate
for si, sh in enumerate(SHOTS):
    idx = list(range(sh["n0"], sh["n1"]))
    if sh.get("freeze"): continue
    xs = gauss([frames[n]["win"][0] for n in idx], 6); ys = gauss([frames[n]["win"][1] for n in idx], 6); hs = gauss([frames[n]["win"][2] for n in idx], 6)
    for i, n in enumerate(idx):
        fr = frames[n]; W = hs[i] * 9 / 16
        keep = (fr["label"]["hx"], fr["label"]["hy"]) if "label" in fr else None
        fr["win"] = fit_window(fr["clip"], fr["src"], xs[i] + W / 2, ys[i] + hs[i] / 2, hs[i], keep)

# spotlights: circle in source coords, constant radius = max needed
for sp in SPOTS:
    si = [s["id"] for s in SHOTS].index(sp["shot"]); sh = SHOTS[si]
    ns = [n for n in range(sh["n0"], sh["n1"]) if sp["t0"] <= n / FPS < sp["t1"]]
    cs = []
    for n in ns:
        hx, hy = track_pts(sp["trk"], frames[n]["src"])
        cs.append((hx, hy + sp["h"] * 0.5))
    R = sp["h"] * 0.5 + 34  # half body + margin (arms, feet, ball)
    xs = gauss([c[0] for c in cs], 3); ys = gauss([c[1] for c in cs], 3)
    sp["R"] = R
    for i, n in enumerate(ns):
        frames[n]["spot"] = dict(x=float(xs[i]), y=float(ys[i]), R=R, t0=sp["t0"], t1=sp["t1"])

# final per-frame transform (zoom on cuts +7% decaying in 0.1 s; spotlight zoom +22% toward player)
out = []
for fr in frames:
    x, y, H = fr["win"]; W = H * 9 / 16
    sh = SHOTS[fr["shot"]]
    z = 1.0
    dtc = fr["t"] - sh["T0"]
    if fr["shot"] > 0 and dtc < 0.1: z *= 1 + 0.07 * (1 - dtc / 0.1)
    fx, fy = x + W / 2, y + H / 2
    if "spot" in fr:
        sp = fr["spot"]; p = min(1, (fr["t"] - sp["t0"]) / 1.2); q = min(1, max(0, (sp["t1"] - fr["t"]) / 0.25))
        e = (0.5 - 0.5 * math.cos(math.pi * p)) * q
        z *= 1 + 0.22 * e
        fx += (sp["x"] - fx) * 0.6 * e; fy += (sp["y"] - fy) * 0.6 * e
    H2 = H / z; W2 = H2 * 9 / 16
    x2 = min(max(fx - W2 / 2, x), x + W - W2); y2 = min(max(fy - H2 / 2, y), y + H - H2)
    s = OH / H2
    rec = dict(n=fr["n"], s=round(s, 5), tx=round(-x2 * s, 2), ty=round(-y2 * s, 2), src=f'{fr["clip"]}{fr["src"]}')
    if "label" in fr:
        L = fr["label"]
        rec["lab"] = dict(name=L["name"], x=round((L["hx"] - x2) * s, 1), y=round((L["hy"] - y2) * s, 1), t0=round(L["t0"], 4))
    if "spot" in fr:
        sp = fr["spot"]
        a = min(1, (fr["t"] - sp["t0"]) / 0.25, (sp["t1"] - fr["t"]) / 0.25)
        rec["spot"] = dict(x=round((sp["x"] - x2) * s, 1), y=round((sp["y"] - y2) * s, 1), r=round(sp["R"] * s, 1), a=round(max(0, a), 3))
    out.append(rec)
json.dump(out, open("work/frames_out.json", "w"))
json.dump(dict(shots=[{k: v for k, v in s.items() if k != "cam"} for s in SHOTS], spots=SPOTS), open("work/edl.json", "w"), indent=1, default=str)

# ---------------- assets ----------------
os.makedirs("hf/assets/frames", exist_ok=True)
for f in os.listdir("hf/assets/frames"): os.remove(os.path.join("hf/assets/frames", f))
for c, k, st, du in img_clips:
    shutil.copy(f"src/{c}/{k:04d}.jpg", f"hf/assets/frames/{c}{k:04d}.jpg")

# ---------------- audio events ----------------
def out_time(shot_id, src):
    sh = SHOTS[[s["id"] for s in SHOTS].index(shot_id)]
    return sh["T0"] + (src - sh["a"]) / sh["rate"]
audio = []
cuts = [s["T0"] for s in SHOTS[1:]]
for i, t in enumerate(cuts):
    nm = f"whoosh{i % 4 + 1}"; d = {1: .32, 2: .30, 3: .34, 4: .28}[i % 4 + 1]
    audio.append((nm, max(0, t - 0.12), d, 0.25))
for s in SHOTS:
    if s.get("freeze"): audio.append(("freeze", s["T0"], .45, 0.35))
seen = set()
for fr in out:
    if "lab" in fr:
        key = (fr["lab"]["name"], fr["lab"]["t0"])
        if key not in seen:
            seen.add(key); audio.append(("pop", fr["lab"]["t0"], .12, 0.18))
BANNER_IN = S[1]
audio.append(("pop", BANNER_IN, .12, 0.18))
for i, (sid, f) in enumerate(CONTACTS):
    t = out_time(sid, f)
    if 0 <= t < DUR - 0.2: audio.append((f"kick{i % 3 + 1}", t, .18, 0.32))
GOAL_T = out_time("E11", 841)

# ---------------- captions ----------------
caps = []
for w in WORDS:
    txt = w["text"].lower().strip(",.;:!?¡¿")
    caps.append((txt, w["start"]))
cap_html = []
for i, (txt, st) in enumerate(caps):
    en = caps[i + 1][1] if i + 1 < len(caps) else DUR
    en = min(en, DUR)
    cap_html.append(f'<div id="cap{i}" class="cap clip" data-start="{st:.3f}" data-duration="{max(0.05, en - st):.3f}" data-track-index="20">{txt}</div>')

img_html = "\n".join(
    f'<img id="f{c}{k:04d}_{int(st*1000)}" class="clip src" src="assets/frames/{c}{k:04d}.jpg" data-start="{st:.5f}" data-duration="{du:.5f}" data-track-index="1" alt="">'
    for c, k, st, du in img_clips)
aud_html = "\n".join(
    f'<audio id="sfx{i}" class="clip" src="assets/sfx/{nm}.wav" data-start="{st:.3f}" data-duration="{du:.3f}" data-volume="{vol}" data-track-index="{30 + i}"></audio>'
    for i, (nm, st, du, vol) in enumerate(audio))

html = open("tools/template.html").read()
html = (html.replace("__DUR__", f"{DUR}").replace("__IMGS__", img_html).replace("__CAPS__", "\n".join(cap_html))
        .replace("__AUDIO__", aud_html).replace("__FRAMES__", json.dumps(out, separators=(",", ":")))
        .replace("__BANNER_IN__", f"{BANNER_IN:.3f}").replace("__GOAL_T__", f"{GOAL_T:.3f}")
        .replace("__VOICE_VOL__", os.environ.get("VOICE_VOL", "1.0")))
open("hf/index.html", "w").write(html)
print("frames", len(out), "imgs", len(img_clips), "audio", len(audio), "goal_t", round(GOAL_T, 3))
for s in SHOTS: print(s["id"], round(s["T0"], 2), round(s["T1"], 2), s["clip"], s["a"], s["b"], round(s.get("rate", 0) / 50, 3))
