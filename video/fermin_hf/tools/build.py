"""Builds index.html (HyperFrames composition) from plan.py, tracks and words.json.

python3 tools/build.py --frames-a <dir of clip A jpgs> --frames-b <dir of clip B jpgs>
Writes: index.html, assets/frames/*.jpg (only the source frames used), data/state.json
"""
import argparse, json, math, os, shutil, sys
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import plan as P

ap = argparse.ArgumentParser()
ap.add_argument("--frames-a", required=True)
ap.add_argument("--frames-b", required=True)
ap.add_argument("--no-copy", action="store_true")
args = ap.parse_args()
FR = {"a": args.frames_a, "b": args.frames_b}
FPS, W_OUT, H_OUT = P.FPS, 1080, 1920
NF = int(round(P.DURATION * FPS))

# ------------------------------------------------------------------ tracks
def load_track(name):
    d = json.load(open(f"{ROOT}/data/tracks/{name}.json"))
    return {int(k): v for k, v in d.items()}

TR = {n: load_track(n) for n in ["A_rafa", "A_lamine1", "A2_lam", "A3_lam", "A3_fer",
                                  "B1_lam", "B1_fer", "B2_lam", "B2_fer"]}

def fix(tr, bad, valid=None):
    """drop bad frames / keep only valid range, then fill by interpolation/hold"""
    keys = sorted(tr)
    good = {k: v for k, v in tr.items() if k not in bad and (valid is None or valid[0] <= k <= valid[1])}
    gk = sorted(good)
    out = {}
    for k in range(min(keys), max(keys) + 1):
        if k in good: out[k] = dict(good[k]); continue
        lo = max([g for g in gk if g < k], default=None); hi = min([g for g in gk if g > k], default=None)
        if lo is None: out[k] = dict(good[hi]); continue
        if hi is None: out[k] = dict(good[lo]); continue
        a = (k - lo) / (hi - lo); v = {}
        for f in ("hx", "hy", "bx", "by", "bw", "bh"):
            v[f] = good[lo][f] * (1 - a) + good[hi][f] * a
        v["ok"] = False; out[k] = v
    return out

TR["A_lamine1"] = fix(TR["A_lamine1"], set(), (47, 144))
TR["B1_fer"] = fix(TR["B1_fer"], set(range(206, 211)) | set(range(250, 255)), (197, 279))
TR["B1_lam"] = fix(TR["B1_lam"], set(), (67, 222))
TR["B2_lam"] = fix(TR["B2_lam"], set(), (357, 451))
TR["B2_fer"] = fix(TR["B2_fer"], set(), (487, 603))
TR["A3_fer"] = fix(TR["A3_fer"], set(), (219, 362))
TR["A_rafa"] = fix(TR["A_rafa"], set(), (1, 75))

def tget(name, f):
    tr = TR[name]; ks = sorted(tr)
    f = min(max(f, ks[0]), ks[-1])
    return tr[f]

# static / keyframed targets -------------------------------------------------
def kf_interp(kfs, f):
    ks = sorted(kfs)
    if f <= ks[0]: return kfs[ks[0]]
    if f >= ks[-1]: return kfs[ks[-1]]
    for a, b in zip(ks, ks[1:]):
        if a <= f <= b:
            u = (f - a) / (b - a)
            return tuple(kfs[a][i] * (1 - u) + kfs[b][i] * u for i in range(2))

GOAL = {345: (760, 560), 375: (700, 540), 388: (700, 560), 420: (760, 560), 458: (800, 560)}
CELEB = {459: (1300, 600), 475: (1104, 620), 488: (960, 600), 500: (760, 600), 513: (640, 600),
         525: (600, 600), 538: (560, 600), 550: (640, 600), 563: (680, 600), 575: (760, 600),
         588: (720, 600), 600: (800, 620), 614: (800, 620)}
KEEPER = (573, 503)

def target_point(name, f):
    if name == "goal": return kf_interp(GOAL, f)
    if name == "celeb": return kf_interp(CELEB, f)
    if name == "keeper": return KEEPER
    d = tget(name, f)
    return (d["bx"] + d["bw"] / 2, d["by"] + d["bh"] * 0.55)

# ------------------------------------------------------------- body boxes
_img_cache = {}
def img(clip, f):
    key = (clip, f)
    if key not in _img_cache:
        if len(_img_cache) > 60: _img_cache.clear()
        _img_cache[key] = cv2.imread(f"{FR[clip]}/{f:04d}.jpg")
    return _img_cache[key]

def grass(im):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); h, s, v = cv2.split(hsv)
    return (h >= 28) & (h <= 95) & (s >= 45) & (v >= 75)

def body_box(clip, name, f):
    """bounding box of the whole player silhouette (non-grass pixels connected to the shirt blob)"""
    if isinstance(name, tuple) and name[0] == "box":
        return name[1:]
    if name in P.MANUAL_BOXES:
        kb = P.MANUAL_BOXES[name]; ks = sorted(kb)
        f = min(max(f, ks[0]), ks[-1])
        for a, b in zip(ks, ks[1:]):
            if a <= f <= b:
                u = (f - a) / (b - a)
                return tuple(kb[a][i] * (1 - u) + kb[b][i] * u for i in range(4))
        return kb[ks[-1]]
    d = tget(name, f); im = img(clip, f)
    bx, by, bw, bh, hy = d["bx"], d["by"], d["bw"], d["bh"], d["hy"]
    hgt = max(bh * 1.9, (by + bh - hy) * 1.6)
    x0 = int(max(0, bx - 0.7 * hgt)); x1 = int(min(1920, bx + bw + 0.7 * hgt))
    y0 = int(max(0, hy - 0.15 * hgt)); y1 = int(min(1080, hy + 1.25 * hgt))
    sub = im[y0:y1, x0:x1]
    ng = (~grass(sub)).astype(np.uint8)
    ng = cv2.morphologyEx(ng, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(ng)
    seed = lab[int(np.clip(by + bh * 0.4 - y0, 0, sub.shape[0] - 1)), int(np.clip(bx + bw / 2 - x0, 0, sub.shape[1] - 1))]
    fb = (bx - hgt * 0.32, hy, bx + bw + hgt * 0.32, hy + hgt)          # fallback silhouette
    if seed == 0:
        return fb
    X, Y, Wc, Hc = st[seed, 0] + x0, st[seed, 1] + y0, st[seed, 2], st[seed, 3]
    box = (X, Y, X + Wc, Y + Hc)
    # merged with lines/other players -> too big: use fallback union with blob
    if Wc > hgt * 1.5 or Hc > hgt * 1.5:
        return fb
    return (min(box[0], bx), min(box[1], hy), max(box[2], bx + bw), max(box[3], by + bh))

# ------------------------------------------------------------- timing
def seg_src(seg, t):
    if "freeze" in seg: return float(seg["freeze"])
    u = (t - seg["t0"]) / (seg["t1"] - seg["t0"])
    return seg["f0"] + u * (seg["f1"] - seg["f0"])

def speed(seg):
    if "freeze" in seg: return 0.0
    return (seg["f1"] - seg["f0"]) / 50.0 / (seg["t1"] - seg["t0"])

for i, s in enumerate(P.SEGMENTS):
    sp = speed(s)
    print(f"seg{i:02d} {s['t0']:6.2f}-{s['t1']:6.2f} {s['clip']} " +
          (f"freeze {s['freeze']}" if 'freeze' in s else f"{s['f0']}-{s['f1']} x{sp:.3f}"))
    if "freeze" not in s and not (0.25 - 1e-3 <= sp <= 1.05):
        print("   !! speed outside 0.25..1.0")

def seg_at(t):
    for i, s in enumerate(P.SEGMENTS):
        if s["t0"] - 1e-9 <= t < s["t1"] - 1e-9: return i, s
    return len(P.SEGMENTS) - 1, P.SEGMENTS[-1]

def out_time_of_src(segi, f):
    s = P.SEGMENTS[segi]
    return s["t0"] + (f - s["f0"]) / (s["f1"] - s["f0"]) * (s["t1"] - s["t0"])

# ------------------------------------------------------------- per-frame raw state
def ease(u): u = min(max(u, 0), 1); return u * u * (3 - 2 * u)

frames = []
for k in range(NF):
    t = (k + 0.5) / FPS          # sample in the middle of the output frame
    i, s = seg_at(t)
    src = seg_src(s, t)
    fi = int(math.floor(src + 1e-6))
    fi = max(1, fi)
    st = dict(k=k, t=t, seg=i, clip=s["clip"], src=src, f=fi)
    # camera target
    tx = ty = wsum = 0
    for (name, w, dx, dy) in s["cam"]:
        x, y = target_point(name, fi); tx += w * (x + dx); ty += w * (y + dy); wsum += w
    tx /= wsum; ty /= wsum
    if "cam2" in s:      # pan to a second target between two source frames
        name2, fa, fb = s["cam2"]; u = ease((fi - fa) / (fb - fa))
        x2, y2 = target_point(name2, fi); tx = tx * (1 - u) + x2 * u; ty = ty * (1 - u) + y2 * u
    if "cam2t" in s:     # time-based pan (used on freezes)
        name2, ta2, tb2 = s["cam2t"]; u = ease((t - ta2) / (tb2 - ta2))
        x2, y2 = target_point(name2, fi); tx = tx * (1 - u) + x2 * u; ty = ty * (1 - u) + y2 * u
    st["target"] = [tx, ty]; st["H0"] = s["H"]
    # labels
    st["label"] = None
    for (name, who, a, b) in s.get("labels", []):
        if a <= fi < b and t < s.get("label_until", 1e9):
            d = tget(name, fi)
            st["label"] = dict(who=who, hx=d["hx"], hy=d["hy"], track=name, start=a); break
    # spotlight
    st["spot"] = None
    for (name, ta, tb) in s.get("spots", []):
        if ta - 0.25 <= t < tb + 0.25:
            st["spot"] = dict(name=name if isinstance(name, str) else list(name), ta=ta, tb=tb,
                              box=list(map(float, body_box(s["clip"], name, fi))))
            break
    frames.append(st)

# spotlight circles: constant radius per spotlight = largest needed; centre lightly smoothed
groups = {}
for st in frames:
    if st["spot"]:
        key = (st["seg"], st["spot"]["ta"]); groups.setdefault(key, []).append(st)
for key, lst in groups.items():
    cs = np.array([[(b[0] + b[2]) / 2, (b[1] + b[3]) / 2] for b in (x["spot"]["box"] for x in lst)])
    rs = np.array([math.hypot(b[2] - b[0], b[3] - b[1]) / 2 for b in (x["spot"]["box"] for x in lst)])
    sm = np.stack([gaussian_filter1d(cs[:, 0], 1.5, mode="nearest"), gaussian_filter1d(cs[:, 1], 1.5, mode="nearest")], 1)
    # radius must still contain every raw box after smoothing the centre
    need = [max(math.hypot(max(abs(b[0] - c[0]), abs(b[2] - c[0])), max(abs(b[1] - c[1]), abs(b[3] - c[1]))), 0)
            for b, c in zip((x["spot"]["box"] for x in lst), sm)]
    R = max(need) * 1.12 + 6
    for x, c in zip(lst, sm):
        x["spot"]["c"] = [float(c[0]), float(c[1])]; x["spot"]["r"] = float(R)

# ------------------------------------------------------------- camera
def spot_amount(st):
    sp = st["spot"]
    if not sp: return 0.0
    t = st["t"]
    a = ease((t - sp["ta"]) / 0.25)            # 0.25 s fade in
    b = 1 - ease((t - sp["tb"]) / 0.25)        # 0.25 s fade out
    return max(0.0, min(a, b))

def zoom_amount(st):
    """progressive +22 % zoom: ramps over the spotlight, falls back with the fade out"""
    sp = st["spot"]
    if not sp or (isinstance(sp["name"], str) and sp["name"] in P.NOZOOM_SPOTS): return 0.0
    t = st["t"]
    ramp = ease((t - sp["ta"]) / max(0.6, min(1.5, sp["tb"] - sp["ta"])))
    return ramp * (1 - ease((t - sp["tb"]) / 0.25))

seg_bounds = [s["t0"] for s in P.SEGMENTS[1:]]

# 1) smooth targets per segment (gaussian sigma = 10 output frames), constant on freezes
tx = np.array([f["target"][0] for f in frames]); ty = np.array([f["target"][1] for f in frames])
segid = np.array([f["seg"] for f in frames])
for i, s in enumerate(P.SEGMENTS):
    idx = np.nonzero(segid == i)[0]
    if len(idx) == 0: continue
    if "freeze" in s and "cam2t" not in s:
        tx[idx] = tx[idx].mean(); ty[idx] = ty[idx].mean()
    else:
        tx[idx] = gaussian_filter1d(tx[idx], 10, mode="nearest"); ty[idx] = gaussian_filter1d(ty[idx], 10, mode="nearest")

def inside(rect, pts, margin):
    x0, y0, x1, y1 = rect
    return all(x0 + margin <= px <= x1 - margin and y0 + margin <= py <= y1 - margin for px, py in pts)

def hits(rect):
    x0, y0, x1, y1 = rect
    return any(not (x1 <= a or x0 >= c or y1 <= b or y0 >= d) for (a, b, c, d) in P.OVERLAYS)

FALLBACKS = []
CUR = [None]
def solve(cx, cy, H, must):
    """closest crop (x0,y0,H) to the wish that stays in the frame, avoids overlays, contains `must` points"""
    best = None
    Hs = sorted(set([min(1080, H)] + [min(1080, H * m) for m in (0.96, 0.92, 0.88, 0.84, 0.8, 0.75, 0.7, 1.05, 1.1, 1.2, 1.3, 1.45)]))
    for Hc in Hs:
        Wc = Hc * 9 / 16
        xs = [cx - Wc / 2]; ys = [cy - Hc / 2]
        for (a, b, c, d) in P.OVERLAYS:
            xs += [c + 1, a - Wc - 1]; ys += [d + 1, b - Hc - 1]
        if must:
            mx0 = min(p[0] for p in must); mx1 = max(p[0] for p in must)
            my0 = min(p[1] for p in must); my1 = max(p[1] for p in must)
            xs += [mx1 + 40 - Wc, mx0 - 40]; ys += [my1 + 40 - Hc, my0 - 40]
        for x0 in xs:
            x0 = min(max(x0, 0), 1920 - Wc)
            for y0 in ys:
                y0 = min(max(y0, 0), 1080 - Hc)
                r = (x0, y0, x0 + Wc, y0 + Hc)
                if hits(r) or not inside(r, must, 25): continue
                cost = abs(x0 + Wc / 2 - cx) + abs(y0 + Hc / 2 - cy) + 1.5 * abs(Hc - H)
                if best is None or cost < best[0]: best = (cost, x0, y0, Hc)
    if best is None:
        if must:
            FALLBACKS.append(CUR[0])
            return solve(cx, cy, H, must[:-2] if len(must) > 2 else [])
        raise RuntimeError(f"no crop for {cx,cy,H}")
    return best[1:]

cams = []
for n, st in enumerate(frames):
    z = zoom_amount(st)
    cx, cy = tx[n], ty[n]
    must = []
    if st["label"]:
        L = st["label"]; d = tget(L["track"], st["f"])
        k_ = st["H0"] / 1920.0
        top_need = 262 + (330 if P.SCORE["show"] <= st["t"] < P.SCORE["hide"] else 16)
        must += [(L["hx"] - 175 * k_, L["hy"] - top_need * k_), (L["hx"] + 175 * k_, L["hy"] - top_need * k_),
                 (d["bx"], d["by"] + d["bh"]), (d["bx"] + d["bw"], d["by"] + d["bh"])]
    if st["spot"]:
        c, r = st["spot"]["c"], st["spot"]["r"]
        cx = cx * (1 - 0.6 * z) + c[0] * 0.6 * z; cy = cy * (1 - 0.6 * z) + c[1] * 0.6 * z
        bb = st["spot"]["box"]
        must += [(bb[0], bb[1]), (bb[2], bb[3])]
    H = st["H0"] / (1 + 0.22 * z)
    cams.append([cx, cy, H, must])

# solve, smooth (within segment), re-solve
sol = []
for n, c in enumerate(cams):
    CUR[0] = ('pass1', frames[n]['seg'])
    try: sol.append(solve(*c))
    except RuntimeError:
        st = frames[n]; print("NOCROP k", n, "t", round(st["t"], 2), "seg", st["seg"], "f", st["f"], "must", [(round(a), round(b)) for a, b in c[3]])
        sol.append(solve(c[0], c[1], c[2], []))
X = np.array([s[0] + s[2] * 9 / 32 for s in sol]); Y = np.array([s[1] + s[2] / 2 for s in sol]); Hh = np.array([s[2] for s in sol])
for i, s in enumerate(P.SEGMENTS):
    idx = np.nonzero(segid == i)[0]
    if "freeze" in s and not s.get("spots") and "cam2t" not in s:
        X[idx] = X[idx][0]; Y[idx] = Y[idx][0]; Hh[idx] = Hh[idx][0]; continue
    X[idx] = gaussian_filter1d(X[idx], 3, mode="nearest"); Y[idx] = gaussian_filter1d(Y[idx], 3, mode="nearest")
    Hh[idx] = gaussian_filter1d(Hh[idx], 3, mode="nearest")
final = []
for n, st in enumerate(frames):
    CUR[0] = ('pass2', st['seg'])
    x0, y0, Hc = solve(X[n], Y[n], Hh[n], cams[n][3])
    # punch-in +7 % at each cut, falling back in 0.1 s
    tcut = P.SEGMENTS[st["seg"]]["t0"]; pu = max(0.0, 1 - (st["t"] - tcut) / 0.1) if st["seg"] > 0 else 0
    if pu > 0:
        Hp = Hc / (1 + 0.07 * pu); cx0 = x0 + Hc * 9 / 32; cy0 = y0 + Hc / 2
        x0p, y0p = cx0 - Hp * 9 / 32, cy0 - Hp / 2
        r = (x0p, y0p, x0p + Hp * 9 / 16, y0p + Hp)
        if not hits(r) and inside(r, cams[n][3], 25) and x0p >= 0 and y0p >= 0 and r[2] <= 1920 and r[3] <= 1080:
            x0, y0, Hc = x0p, y0p, Hp
    final.append((x0, y0, Hc))

# ------------------------------------------------------------- output-space state
def to_out(cam, p):
    x0, y0, Hc = cam; s = 1920 / Hc
    return ((p[0] - x0) * s, (p[1] - y0) * s)

state = []
label_runs = []   # (who, start_k, end_k) for pop sounds
prev_label = None
for n, st in enumerate(frames):
    cam = final[n]; s = 1920 / cam[2]
    e = dict(k=n, clip=st["clip"], f=st["f"], cam=[round(cam[0], 2), round(cam[1], 2), round(cam[2], 2)])
    t = n / FPS
    if st["label"]:
        L = st["label"]; hx, hy = to_out(cam, (L["hx"], L["hy"]))
        e["label"] = dict(who=L["who"], x=round(hx, 1), y=round(hy, 1), src_head=[L["hx"], L["hy"]])
        key = (L["who"], st["seg"], L["start"])
        if key != prev_label: label_runs.append([L["who"], n, n]); prev_label = key
        else: label_runs[-1][2] = n
    else:
        prev_label = None
    if st["spot"]:
        c = to_out(cam, st["spot"]["c"]); e["spot"] = dict(x=round(c[0], 1), y=round(c[1], 1),
                                                         r=round(st["spot"]["r"] * s, 1), a=round(spot_amount(st), 3),
                                                         src_c=st["spot"]["c"], src_r=st["spot"]["r"], box=st["spot"]["box"])
    s_ = P.SEGMENTS[st["seg"]]
    if "lane" in s_ and st["t"] >= s_["lane"][1]:
        (ta, tb), t_l = s_["lane"]
        da, db = tget(ta, st["f"]), tget(tb, st["f"])
        pa = to_out(cam, (da["bx"] + da["bw"] / 2, da["by"] + da["bh"] * 1.05))
        pb = to_out(cam, (db["bx"] + db["bw"] / 2, db["by"] + db["bh"] * 1.05))
        e["lane"] = dict(a=[round(v, 1) for v in pa], b=[round(v, 1) for v in pb], u=round(ease((st["t"] - t_l) / 0.6), 3))
    if "rings" in s_:
        rr = []
        for (cx_, cy_, rx_, ry_), tr_ in s_["rings"]:
            if st["t"] >= tr_:
                c = to_out(cam, (cx_, cy_)); rr.append([round(c[0], 1), round(c[1], 1), round(rx_ * s, 1), round(ry_ * s, 1), round(ease((st["t"] - tr_) / 0.2), 3)])
        if rr: e["rings"] = rr
    state.append(e)

json.dump(dict(frames=state, label_runs=label_runs), open(f"{ROOT}/data/state.json", "w"))

# ------------------------------------------------------------- frames used -> assets
used = {}   # (clip,f) -> list of output frame indices
for e in state: used.setdefault((e["clip"], e["f"]), []).append(e["k"])
os.makedirs(f"{ROOT}/assets/frames", exist_ok=True)
if not args.no_copy:
    for (clip, f) in used:
        dst = f"{ROOT}/assets/frames/{clip}{f:04d}.jpg"
        if not os.path.exists(dst):
            im = cv2.imread(f"{FR[clip]}/{f:04d}.jpg"); cv2.imwrite(dst, im, [cv2.IMWRITE_JPEG_QUALITY, 95])
import collections
print("source frames used:", len(used), "| solver fallbacks:", collections.Counter(FALLBACKS))

# image clips: contiguous runs of output frames showing the same source frame
runs = []
for e in state:
    key = (e["clip"], e["f"])
    if runs and runs[-1][0] == key and runs[-1][2] == e["k"] - 1: runs[-1][2] = e["k"]
    else: runs.append([key, e["k"], e["k"]])

# ------------------------------------------------------------- sounds
words = json.load(open(f"{ROOT}/data/words.json"))
sfx = []
cut_ids = ["166", "174", "168", "3115"]
for i, s in enumerate(P.SEGMENTS[1:], 1):
    sfx.append((f"sfx/{cut_ids[(i - 1) % 4]}.mp3", max(0, s["t0"] - 0.12), 0.30, f"cut{i}"))
for tf in P.FREEZE_TIMES:
    sfx.append(("sfx/1492.mp3", tf, 0.35, f"freeze{tf}"))
for who, a, b in label_runs:
    sfx.append(("sfx/3005.mp3", a / FPS, 0.40, f"pop_{who}_{a}"))
sfx.append(("sfx/3005.mp3", P.SCORE["show"], 0.45, "pop_score"))
kick_ids = ["2112", "2108", "2099"]
for j, (segi, ev) in enumerate(P.CONTACTS):
    f = P.EV[ev]; s = P.SEGMENTS[segi]
    if "freeze" in s or not (s["f0"] <= f <= s["f1"]): continue
    sfx.append((f"sfx/{kick_ids[j % 3]}.mp3", out_time_of_src(segi, f), 0.55, f"kick{segi}"))
MIX_GAIN = 0.80   # measured on render v2: -12.1 LUFS -> -14 LUFS
SFX_DUR = {"166": 0.809796, "174": 1.044898, "168": 0.888163, "3115": 0.600816, "1492": 1.38449,
           "3005": 0.20898, "2112": 1.462857, "2108": 0.966531, "2099": 1.593469}

# ------------------------------------------------------------- HTML
def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
import re
def sub_word(w):
    w = w.lower()
    return re.sub(r"[.,;:]", "", w)

H = []
H.append("""<!doctype html>
<html lang="es" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="assets/gsap.min.js"></script>
<style>
@font-face{font-family:Poppins;font-weight:500;src:url(assets/fonts/poppins-latin-500-normal.woff2) format("woff2")}
@font-face{font-family:Poppins;font-weight:800;src:url(assets/fonts/poppins-latin-800-normal.woff2) format("woff2")}
@font-face{font-family:Montserrat;font-weight:800;src:url(assets/fonts/montserrat-latin-800-normal.woff2) format("woff2")}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#000}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;background:#000}
#cam{position:absolute;left:0;top:0;width:1920px;height:1080px;transform-origin:0 0;z-index:1}
#cam img{position:absolute;left:0;top:0;width:1920px;height:1080px}
#dim{position:absolute;inset:0;z-index:5;opacity:0;--x:540px;--y:960px;--r:200px;
  background:rgba(0,0,0,.58);backdrop-filter:blur(5px);-webkit-backdrop-filter:blur(5px);
  -webkit-mask-image:radial-gradient(circle at var(--x) var(--y),transparent calc(var(--r) - 1px),#000 var(--r));
  mask-image:radial-gradient(circle at var(--x) var(--y),transparent calc(var(--r) - 1px),#000 var(--r))}
#ring{position:absolute;left:0;top:0;z-index:6;opacity:0;border:5px solid #fff;border-radius:50%;
  box-shadow:0 0 14px rgba(255,255,255,.75),inset 0 0 10px rgba(255,255,255,.35)}
.tag{position:absolute;left:0;top:0;z-index:20;width:0;height:0;opacity:0}
.tag .in{position:absolute;left:0;bottom:0;transform:translateX(-50%);display:flex;flex-direction:column;align-items:center;transform-origin:50% 100%}
.tag .logo{width:84px;height:84px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;
  box-shadow:0 3px 8px rgba(0,0,0,.45)}
.tag .logo img{width:64px;height:64px;object-fit:contain}
.tag .name{margin-top:8px;font-family:Montserrat;font-weight:800;font-size:38px;line-height:1;color:#fff;white-space:nowrap;
  background:rgba(12,12,16,.88);padding:10px 18px 11px;border-radius:14px;box-shadow:0 3px 10px rgba(0,0,0,.4)}
.tag .in.compact{display:grid;grid-template-columns:auto auto;grid-template-rows:auto auto;column-gap:10px;align-items:center;justify-items:center}
.tag .in.compact .logo{grid-column:1;grid-row:1}
.tag .in.compact .name{grid-column:2;grid-row:1;margin-top:0}
.tag .in.compact svg{grid-column:1 / span 2;grid-row:2}
.tag svg{display:block;margin-top:8px;filter:drop-shadow(0 2px 3px rgba(0,0,0,.55))}
#lane{position:absolute;left:0;top:0;width:1080px;height:1920px;z-index:7;pointer-events:none}
#rings{position:absolute;left:0;top:0;width:1080px;height:1920px;z-index:7}
.sub{position:absolute;left:0;width:1080px;top:1600px;z-index:40;text-align:center;font-family:Poppins;font-weight:500;
  font-size:46px;line-height:1.15;color:#fff;text-shadow:0 2px 4px rgba(0,0,0,.85)}
#score{position:absolute;top:210px;left:50%;z-index:30;transform:translateX(-50%);display:flex;align-items:center;gap:0;opacity:0;
  font-family:Poppins;font-weight:800;color:#fff;font-size:40px;filter:drop-shadow(0 4px 10px rgba(0,0,0,.5))}
#score .team{background:#111;padding:10px 20px;display:flex;align-items:center;gap:12px}
#score .team img{width:42px;height:42px;object-fit:contain}
#score .res{background:#e10600;padding:10px 22px;display:flex;align-items:center;gap:14px;font-size:44px}
#score .dig{position:relative;display:inline-block;width:28px;height:54px;text-align:center;line-height:54px}
#score .dig span{position:absolute;left:0;top:0;width:100%}
#score .min{background:#fff;color:#111;padding:10px 16px;font-size:34px}
#end{position:absolute;left:0;top:560px;width:1080px;z-index:35;text-align:center;opacity:0;font-family:Poppins;font-weight:800;color:#fff;
  text-shadow:0 6px 18px rgba(0,0,0,.8)}
#end .t{font-size:104px;line-height:1.02;white-space:pre-line}
#end .s{display:inline-block;margin-top:34px;font-size:40px;background:#e10600;padding:12px 26px;border-radius:10px}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="%DUR%" data-width="1080" data-height="1920">
<div id="cam">
""".replace("%DUR%", f"{P.DURATION:.2f}"))

q = 0.25 / FPS     # quarter-frame offset so frame boundaries never fall on a sample
for (clip, f), a, b in runs:
    start = max(0.0, a / FPS - q); end = (b + 1) / FPS - q if b < NF - 1 else P.DURATION
    H.append(f'<img class="clip" src="assets/frames/{clip}{f:04d}.jpg" data-start="{start:.5f}" data-duration="{end - start:.5f}" alt="">')
H.append("</div>")
H.append('<div id="dim"></div><div id="ring"></div>')
H.append('<svg id="lane" viewBox="0 0 1080 1920"><line id="laneL" x1="0" y1="0" x2="0" y2="0" stroke="#ffe600" stroke-width="9" stroke-linecap="round" stroke-dasharray="26 18" opacity="0"/><circle id="laneA" r="0" fill="#ffe600"/></svg>')
H.append('<svg id="rings" viewBox="0 0 1080 1920"><ellipse id="ring0" fill="none" stroke="#ff1f1f" stroke-width="7" opacity="0"/><ellipse id="ring1" fill="none" stroke="#ff1f1f" stroke-width="7" opacity="0"/></svg>')
ARROW = ('<svg width="64" height="86" viewBox="0 0 64 86"><path d="M20 2 H44 V44 H62 L32 84 L2 44 H20 Z" fill="#ff1f1f" '
         'stroke="#3a0000" stroke-width="3" stroke-linejoin="round"/></svg>')
for who, (nm, club) in P.NAMES.items():
    H.append(f'<div class="tag" id="tag_{who}"><div class="in" id="tagin_{who}"><div class="logo"><img src="assets/logos/{club}.svg" alt=""></div>'
             f'<div class="name">{esc(nm)}</div>{ARROW}</div></div>')
sc = P.SCORE
H.append(f'<div id="score"><div class="team"><img src="assets/logos/barca.svg" alt="">{sc["home"]}</div>'
         f'<div class="res"><span class="dig"><span id="h0">{sc["before"][0]}</span><span id="h1" style="opacity:0">{sc["after"][0]}</span></span>'
         f'<span>–</span><span class="dig"><span>{sc["before"][1]}</span></span></div>'
         f'<div class="team">{sc["away"]}<img src="assets/logos/villarreal.svg" alt=""></div><div class="min">{sc["minute"]}</div></div>')
ec = P.END_CARD
H.append(f'<div id="end"><div class="t">{esc(ec["title"])}</div><div class="s">{esc(ec["sub"])}</div></div>')
for j, w in enumerate(words):
    nxt = words[j + 1]["start"] if j + 1 < len(words) else P.DURATION
    st_, en_ = w["start"], min(nxt, max(w["end"], w["start"] + 0.08))
    if j + 1 < len(words) and nxt - w["end"] < 0.35: en_ = nxt
    H.append(f'<div class="sub clip" data-start="{st_:.3f}" data-duration="{en_ - st_:.3f}">{esc(sub_word(w["text"]))}</div>')
H.append(f'<audio id="voice" src="assets/audio/voice_es.wav" data-start="0" data-duration="{P.DURATION:.2f}" data-volume="{MIX_GAIN:.3f}"></audio>')
for j, (src, t0, vol, nm) in enumerate(sfx):
    d = min(SFX_DUR[src.split("/")[1][:-4]], P.DURATION - t0)
    H.append(f'<audio id="sfx{j}" src="assets/{src}" data-start="{t0:.3f}" data-duration="{d:.3f}" data-volume="{vol * MIX_GAIN:.3f}"></audio>')
H.append("</div>")

# --------- per-frame label corrections measured on the previous render (tools/verify.py)
CORR = {}
if os.path.exists(f"{ROOT}/data/label_corr.json"):
    CORR = {int(k): v for k, v in json.load(open(f"{ROOT}/data/label_corr.json")).items()}
for e in state:
    if "label" in e and e["k"] in CORR:
        e["label"]["x"] = round(e["label"]["x"] + CORR[e["k"]], 1)

# --------- timeline: per-frame sets
js = ["const tl = gsap.timeline({ paused: true });", "const S=(sel,v,t)=>tl.set(sel,v,t);",
      'tl.set(".tag .in",{scale:1},0);tl.set("#h1",{opacity:0,scaleY:1},0);tl.set("#h0",{opacity:1,scaleY:1},0);']
lastvis = {w: False for w in P.NAMES}
lastcompact = {}
spot_on = False; lane_on = False; rings_on = [False, False]
for e in state:
    t = round(e["k"] / FPS, 5)
    x0, y0, Hc = e["cam"]; s = 1920 / Hc
    js.append(f'S("#cam",{{x:{-x0 * s:.2f},y:{-y0 * s:.2f},scale:{s:.5f}}},{t});')
    vis = {w: False for w in P.NAMES}
    if "label" in e:
        L = e["label"]; vis[L["who"]] = True
        bounce = 5 * abs(math.sin(2 * math.pi * 1.4 * t))
        tipy = L["y"] - 3 - bounce
        limit_top = 300 if P.SCORE["show"] <= t < P.SCORE["hide"] else 10
        tipy = float(tipy); compact = bool((tipy - 256) < limit_top + 4)
        L["compact"] = compact; L["tip"] = round(tipy, 1)
        js.append(f'S("#tag_{L["who"]}",{{x:{L["x"]:.1f},y:{tipy:.1f},opacity:1}},{t});')
        if compact != lastcompact.get(L["who"]):
            js.append(f'tl.set("#tagin_{L["who"]}",{{className:"in{" compact" if compact else ""}"}},{t});')
            lastcompact[L["who"]] = compact
        if not lastvis[L["who"]]:
            js.append(f'S("#tagin_{L["who"]}",{{scale:0.2}},{t});tl.to("#tagin_{L["who"]}",{{scale:1,duration:0.12,ease:"back.out(2)"}},{t});')
    for w in P.NAMES:
        if lastvis[w] and not vis[w]: js.append(f'S("#tag_{w}",{{opacity:0}},{t});')
    lastvis = vis
    if "spot" in e:
        sp = e["spot"]; r = sp["r"]
        js.append(f'S("#dim",{{"--x":"{sp["x"]:.1f}px","--y":"{sp["y"]:.1f}px","--r":"{r:.1f}px",opacity:{sp["a"]}}},{t});')
        js.append(f'S("#ring",{{x:{sp["x"] - r:.1f},y:{sp["y"] - r:.1f},width:{2 * r:.1f},height:{2 * r:.1f},opacity:{sp["a"]}}},{t});')
        spot_on = True
    elif spot_on:
        js.append(f'S("#dim",{{opacity:0}},{t});S("#ring",{{opacity:0}},{t});'); spot_on = False
    if "lane" in e:
        la = e["lane"]; ax, ay = la["a"]; bx, by = la["b"]; u = la["u"]
        js.append(f'S("#laneL",{{attr:{{x1:{ax},y1:{ay},x2:{ax + (bx - ax) * u:.1f},y2:{ay + (by - ay) * u:.1f}}},opacity:1}},{t});')
        lane_on = True
    elif lane_on:
        js.append(f'S("#laneL",{{opacity:0}},{t});'); lane_on = False
    rr = e.get("rings", [])
    for j in range(2):
        if j < len(rr):
            cx_, cy_, rx_, ry_, a_ = rr[j]
            js.append(f'S("#ring{j}",{{attr:{{cx:{cx_},cy:{cy_},rx:{rx_ * (0.6 + 0.4 * a_):.1f},ry:{ry_ * (0.6 + 0.4 * a_):.1f}}},opacity:{a_}}},{t});')
            rings_on[j] = True
        elif rings_on[j]:
            js.append(f'S("#ring{j}",{{opacity:0}},{t});'); rings_on[j] = False
# score banner
js.append(f'tl.fromTo("#score",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.15,ease:"back.out(2)"}},{sc["show"]});')
js.append(f'tl.to("#h0",{{scaleY:0,duration:0.1}},{sc["flip"]});tl.set("#h0",{{opacity:0}},{sc["flip"] + 0.1});')
js.append(f'tl.set("#h1",{{opacity:1,scaleY:0}},{sc["flip"] + 0.1});tl.to("#h1",{{opacity:1,scaleY:1,duration:0.12}},{sc["flip"] + 0.1});')
js.append(f'tl.to("#score",{{opacity:0,duration:0.25}},{sc["hide"]});')
js.append(f'tl.fromTo("#end",{{opacity:0,scale:0.7}},{{opacity:1,scale:1,duration:0.2,ease:"back.out(2)"}},{ec["t0"]});')
js.append(f'tl.set({{}},{{}},{P.DURATION});')
js.append('window.__timelines = window.__timelines || {}; window.__timelines["main"] = tl; tl.seek(0);')
H.append("<script>\n" + "\n".join(js) + "\n</script>\n</body>\n</html>\n")
open(f"{ROOT}/index.html", "w").write("\n".join(H))
print("index.html written:", len(runs), "image clips,", len(sfx), "sfx,", len(words), "words")
json.dump(dict(frames=state, label_runs=label_runs), open(f"{ROOT}/data/state.json", "w"))
json.dump([dict(src=s_[0], t=s_[1], vol=s_[2], name=s_[3]) for s_ in sfx], open(f"{ROOT}/data/sfx.json", "w"), indent=0)

# ------------------------------------------------------------- label fit report
def label_box(e):
    L = e["label"]; nm = P.NAMES[L["who"]][0]
    wname = 36 + 25.5 * len(nm)
    if L["compact"]: w = 84 + 10 + wname; h = 84 + 8 + 86
    else: w = max(84, wname); h = 84 + 8 + 58 + 8 + 86
    return (L["x"] - w / 2, L["tip"] - h, L["x"] + w / 2, L["tip"])
bad = []
for e in state:
    if "label" not in e: continue
    x0, y0, x1, y1 = label_box(e); t = e["k"] / FPS
    top_lim = 300 if P.SCORE["show"] <= t < P.SCORE["hide"] else 0
    if x0 < 0 or x1 > 1080 or y0 < top_lim: bad.append((e["k"], round(t, 2), e["label"]["who"], round(x0), round(y0), round(x1)))
print("label boxes clipped:", len(bad))
for b in bad[:: max(1, len(bad) // 25)]: print("  ", b)
