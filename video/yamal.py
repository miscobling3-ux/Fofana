"""Montage TikTok « gol de Lamine Yamal » (Barça - Alavés) : analyse tactique en espagnol.

- format 1080x1920, 30 i/s ; voix off espagnole (guion_yamal_es.py), PAS de sous-titres, PAS de musique
- zooms / recadrages qui suivent l'action, arrêts sur image, ralentis
- flèches de passe, triangles rouges au-dessus des joueurs, cercles en pointillés, joueurs « éclairés »
- logos des vidéos sources masqués (voir yamal_clean.py)

    python3 yamal_clean.py          # une fois : extrait les images et efface les logos
    python3 yamal.py                # -> ../output/lamine_yamal_es.mp4
    python3 yamal.py --stills 3,12,40   # aperçu : quelques images PNG dans build/yamal/
"""
import argparse
import json
import math
import os
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor

import cv2
import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import audio  # noqa: E402

BUILD = os.path.join(HERE, "build", "yamal")
FRAMES = os.path.join(BUILD, "frames")
OW, OH, FPS = 1080, 1920, 30
SRC_FPS = 50
SW, SH = 1920, 1080

RED = (40, 40, 235)        # BGR
WHITE = (255, 255, 255)
YELLOW = (40, 210, 255)
ORANGE = (30, 140, 255)
BLACK = (0, 0, 0)


# ------------------------------------------------------------------ utilitaires
def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def ease_out(u):
    u = min(max(u, 0.0), 1.0)
    return 1 - (1 - u) ** 3


def back_out(u):
    u = min(max(u, 0.0), 1.0)
    c = 1.9
    return 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2


def lerp(a, b, u):
    return a + (b - a) * u


def keyframes(kf, t):
    """kf : liste de (t, valeur ou tuple) ; interpolation lissée."""
    if t <= kf[0][0]:
        return kf[0][1]
    for (t0, v0), (t1, v1) in zip(kf, kf[1:]):
        if t <= t1:
            u = ease((t - t0) / (t1 - t0)) if t1 > t0 else 1
            if isinstance(v0, tuple):
                return tuple(lerp(a, b, u) for a, b in zip(v0, v1))
            return lerp(v0, v1, u)
    return kf[-1][1]


# ------------------------------------------------------------------ images source
_cache = {}


def src_frame(clip, t):
    """Image nettoyée à l'instant t (s) ; mélange de deux images pour les ralentis."""
    x = t * SRC_FPS
    i = int(math.floor(x))
    a = x - i
    n = len(os.listdir(os.path.join(FRAMES, clip))) if (clip, "n") not in _cache else _cache[(clip, "n")]
    _cache[(clip, "n")] = n
    i = max(0, min(n - 1, i))
    j = min(n - 1, i + 1)

    def load(k):
        key = (clip, k)
        if key not in _cache:
            if len(_cache) > 40:
                for kk in [kk for kk in _cache if kk[1] != "n"][:20]:
                    del _cache[kk]
            _cache[key] = cv2.imread(os.path.join(FRAMES, clip, f"{k:06d}.jpg"))
        return _cache[key]

    f0 = load(i)
    if a < 0.15 or j == i:
        return f0
    if a > 0.85:
        return load(j)
    return cv2.addWeighted(f0, 1 - a, load(j), a, 0)


# ------------------------------------------------------------------ suivi des joueurs (plan large)
TRACK_SEEDS = {   # nom : (instant de départ, centre x, centre y, instant de fin)
    "pedri": (0.0, 755, 750, 2.3),
    "lateral": (2.0, 1135, 905, 6.6),
    "fermin": (4.0, 882, 755, 6.9),
    "cancelo": (5.5, 838, 590, 7.0),
    "lamine": (5.5, 530, 720, 7.5),
}


def compute_tracks():
    path = os.path.join(BUILD, "tracks.json")
    if os.path.exists(path):
        return {k: {float(t): tuple(v) for t, v in d.items()} for k, d in json.load(open(path)).items()}
    out = {}
    for name, (t0, x, y, t1) in TRACK_SEEDS.items():
        f = cv2.imread(os.path.join(FRAMES, "wide", f"{int(t0 * SRC_FPS):06d}.jpg"))
        tr = cv2.TrackerCSRT_create()
        tr.init(f, (x - 22, y - 50, 44, 100))
        d = {t0: (x, y)}
        for i in range(int(t0 * SRC_FPS) + 1, int(t1 * SRC_FPS) + 1):
            f = cv2.imread(os.path.join(FRAMES, "wide", f"{i:06d}.jpg"))
            ok, b = tr.update(f)
            if ok:
                d[i / SRC_FPS] = (b[0] + b[2] / 2, b[1] + b[3] / 2)
        out[name] = d
        print(f"  suivi {name} : {len(d)} positions", flush=True)
    json.dump({k: {str(t): v for t, v in d.items()} for k, d in out.items()}, open(path, "w"))
    return out


TRACKS = None


def T(name, t):
    """Position (centre du corps) d'un joueur du plan large à l'instant source t."""
    d = TRACKS[name]
    ts = sorted(d)
    t = min(max(t, ts[0]), ts[-1])
    k = int(np.searchsorted(ts, t))
    if k == 0:
        return d[ts[0]]
    t0, t1 = ts[k - 1], ts[k]
    u = (t - t0) / (t1 - t0) if t1 > t0 else 0
    return tuple(lerp(a, b, u) for a, b in zip(d[t0], d[t1]))


def feet(p, dy=46):
    return (p[0], p[1] + dy)


def head(p, dy=-62):
    return (p[0], p[1] + dy)


# ------------------------------------------------------------------ dessin
class View:
    """Passage coordonnées source -> image de sortie pour un recadrage (cx, cy, zoom)."""

    def __init__(self, cx, cy, zoom):
        h = SH / zoom
        w = h * OW / OH
        cx = min(max(cx, w / 2), SW - w / 2)
        cy = min(max(cy, h / 2), SH - h / 2)
        self.x0, self.y0, self.w, self.h = cx - w / 2, cy - h / 2, w, h
        self.s = OH / h

    def P(self, p):
        return ((p[0] - self.x0) * self.s, (p[1] - self.y0) * self.s)

    def render(self, frame):
        m = np.float32([[self.s, 0, -self.x0 * self.s], [0, self.s, -self.y0 * self.s]])
        out = cv2.warpAffine(frame, m, (OW, OH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        if self.s > 1.9:  # un peu de netteté quand on zoome fort
            blur = cv2.GaussianBlur(out, (0, 0), 2.2)
            out = cv2.addWeighted(out, 1.35, blur, -0.35, 0)
        return out


SS = 4  # sur-échantillonnage pour l'anti-crénelage des formes pleines


def ipt(p, k=1):
    return (int(round(p[0] * k)), int(round(p[1] * k)))


def poly_fill(img, pts, color, alpha=1.0):
    layer = img.copy()
    cv2.fillPoly(layer, [np.array([ipt(p, 16) for p in pts], np.int32)], color, cv2.LINE_AA, shift=4)
    cv2.addWeighted(layer, alpha, img, 1 - alpha, 0, img)


def line(img, a, b, color, th, alpha=1.0):
    if alpha >= 1:
        cv2.line(img, ipt(a, 16), ipt(b, 16), color, th, cv2.LINE_AA, shift=4)
    else:
        layer = img.copy()
        cv2.line(layer, ipt(a, 16), ipt(b, 16), color, th, cv2.LINE_AA, shift=4)
        cv2.addWeighted(layer, alpha, img, 1 - alpha, 0, img)


def bezier(a, b, bend):
    """Courbe entre a et b, décalée perpendiculairement de bend (fraction de la longueur)."""
    a, b = np.array(a, float), np.array(b, float)
    d = b - a
    n = np.array([-d[1], d[0]])
    c = (a + b) / 2 + n * bend
    ts = np.linspace(0, 1, 60)[:, None]
    return (1 - ts) ** 2 * a + 2 * (1 - ts) * ts * c + ts ** 2 * b


def draw_arrow(img, a, b, prog, color=WHITE, th=10, bend=0.12, dashed=False, alpha=1.0, head_len=34):
    """Flèche courbe qui se dessine (prog 0->1), contour sombre + pointe."""
    if prog <= 0.01:
        return
    pts = bezier(a, b, bend)
    n = max(2, int(len(pts) * min(prog, 1)))
    pts = pts[:n]
    # longueur de la pointe retirée du tracé
    end, prev = pts[-1], pts[max(0, n - 6)]
    d = end - prev
    L = np.linalg.norm(d) + 1e-6
    d = d / L
    body = pts.copy()
    if n > 6:
        body[-1] = end - d * head_len * 0.6
    layer = img.copy()
    segs = []
    if dashed:
        acc, on, seg = 0.0, True, [body[0]]
        for p, q in zip(body, body[1:]):
            acc += np.linalg.norm(q - p)
            seg.append(q)
            if acc > (34 if on else 20):
                if on:
                    segs.append(seg)
                seg, acc, on = [q], 0.0, not on
        if on and len(seg) > 1:
            segs.append(seg)
    else:
        segs = [body]
    for s in segs:
        cv2.polylines(layer, [np.int32(np.array(s) * 16)], False, (20, 20, 20), th + 7, cv2.LINE_AA, shift=4)
    for s in segs:
        cv2.polylines(layer, [np.int32(np.array(s) * 16)], False, color, th, cv2.LINE_AA, shift=4)
    nrm = np.array([-d[1], d[0]])
    tip = end
    hl = head_len
    tri = [tip + d * 6, tip - d * hl + nrm * hl * 0.62, tip - d * hl * 0.72, tip - d * hl - nrm * hl * 0.62]
    cv2.fillPoly(layer, [np.int32(np.array(tri) * 16)], (20, 20, 20), cv2.LINE_AA, shift=4)
    cv2.polylines(layer, [np.int32(np.array(tri) * 16)], True, (20, 20, 20), 8, cv2.LINE_AA, shift=4)
    tri2 = [tip, tip - d * (hl - 6) + nrm * (hl - 8) * 0.58, tip - d * (hl - 6) * 0.72,
            tip - d * (hl - 6) - nrm * (hl - 8) * 0.58]
    cv2.fillPoly(layer, [np.int32(np.array(tri2) * 16)], color, cv2.LINE_AA, shift=4)
    cv2.addWeighted(layer, alpha, img, 1 - alpha, 0, img)


def draw_marker(img, p, t, appear=1.0, color=RED, size=44):
    """Triangle rouge pointé vers le bas au-dessus du joueur (rebondit doucement)."""
    if appear <= 0:
        return
    s = size * back_out(appear)
    bob = 6 * math.sin(t * 6.0)
    x, y = p[0], p[1] - 18 + bob
    pts = [(x, y), (x - s * 0.62, y - s * 1.15), (x + s * 0.62, y - s * 1.15)]
    poly_fill(img, [(px + 3, py + 4) for px, py in pts], (10, 10, 10), 0.45)
    poly_fill(img, pts, color, 1.0)
    cv2.polylines(img, [np.int32(np.array(pts) * 16)], True, WHITE, 3, cv2.LINE_AA, shift=4)


def draw_ring(img, p, rx, t, appear=1.0, color=ORANGE, dashed=True, th=6, spin=1.0):
    """Ellipse aux pieds du joueur (pointillés qui tournent, comme dans la référence)."""
    if appear <= 0:
        return
    rx = rx * (0.6 + 0.4 * back_out(appear))
    ry = rx * 0.42
    c = ipt(p, 16)
    axes = (int(rx * 16), int(ry * 16))
    glow = img.copy()
    cv2.ellipse(glow, c, axes, 0, 0, 360, color, th + 10, cv2.LINE_AA, shift=4)
    cv2.addWeighted(glow, 0.22 * min(1, appear * 2), img, 1 - 0.22 * min(1, appear * 2), 0, img)
    sweep = 360 * min(1, appear * 1.6)
    if dashed:
        off = (t * 60 * spin) % 30
        a = off
        while a < off + sweep:
            cv2.ellipse(img, c, axes, 0, a, min(a + 18, off + sweep), (15, 15, 15), th + 4, cv2.LINE_AA, shift=4)
            cv2.ellipse(img, c, axes, 0, a, min(a + 18, off + sweep), color, th, cv2.LINE_AA, shift=4)
            a += 30
    else:
        cv2.ellipse(img, c, axes, 0, 0, sweep, (15, 15, 15), th + 4, cv2.LINE_AA, shift=4)
        cv2.ellipse(img, c, axes, 0, 0, sweep, color, th, cv2.LINE_AA, shift=4)


def draw_cross(img, p, appear, size=46):
    if appear <= 0:
        return
    s = size * back_out(appear)
    for a, b in (((-1, -1), (1, 1)), ((-1, 1), (1, -1))):
        pa = (p[0] + a[0] * s, p[1] + a[1] * s)
        pb = (p[0] + b[0] * s, p[1] + b[1] * s)
        line(img, pa, pb, (15, 15, 15), 26)
        line(img, pa, pb, RED, 16)


def spotlight(img, centers, strength):
    """Assombrit tout sauf des ellipses autour des joueurs : le joueur est « éclairé »."""
    if strength <= 0:
        return img
    mask = np.zeros((OH // 4, OW // 4), np.float32)
    for (x, y), rx, ry in centers:
        cv2.ellipse(mask, (int(x / 4), int(y / 4)), (max(1, int(rx / 4)), max(1, int(ry / 4))), 0, 0, 360, 1.0, -1)
    mask = cv2.GaussianBlur(mask, (0, 0), 9)
    mask = cv2.resize(mask, (OW, OH))[..., None]
    k = 1 - 0.62 * strength * (1 - mask)
    lit = img.astype(np.float32) * k
    # léger halo chaud sur le joueur éclairé
    lit += mask * strength * 18
    return np.clip(lit, 0, 255).astype(np.uint8)


def red_tint(img, s):
    if s <= 0:
        return img
    f = img.astype(np.float32)
    gray = f.mean(axis=2, keepdims=True)
    red = np.concatenate([gray * 0.35, gray * 0.35, gray * 0.9 + 60], axis=2)
    return np.clip(f * (1 - 0.45 * s) + red * 0.45 * s, 0, 255).astype(np.uint8)


def desaturate(img, s):
    if s <= 0:
        return img
    g = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
    return cv2.addWeighted(img, 1 - s, g, s, 0)


def flash(img, s):
    if s <= 0:
        return img
    return cv2.addWeighted(img, 1 - s, np.full_like(img, 255), s, 0)


VIGNETTE = None


def vignette(img):
    global VIGNETTE
    if VIGNETTE is None:
        y, x = np.mgrid[0:OH, 0:OW].astype(np.float32)
        d = np.sqrt(((x - OW / 2) / (OW * 0.75)) ** 2 + ((y - OH / 2) / (OH * 0.7)) ** 2)
        VIGNETTE = (1 - 0.32 * np.clip(d - 0.35, 0, 1) ** 1.5)[..., None]
    return (img.astype(np.float32) * VIGNETTE).astype(np.uint8)


def freeze_border(img, s):
    """Cadre blanc discret + léger contraste pendant un arrêt sur image."""
    if s <= 0:
        return img
    out = cv2.addWeighted(img, 1 + 0.08 * s, img, 0, -6 * s)
    m = int(14 * s)
    if m > 0:
        cv2.rectangle(out, (0, 0), (OW - 1, OH - 1), (240, 240, 240), m)
    return out


# ------------------------------------------------------------------ plans
def appear(u, t0, dur=0.35):
    return min(max((u - t0) / dur, 0.0), 1.0)


class Shot:
    def __init__(self, line, clip, timeline, cam, draw=None, post=None, min_dur=0.0):
        self.line = line              # indice de la phrase de la voix off (ou None)
        self.clip = clip
        self.timeline = timeline      # [(durée, "play", a, b) | (durée|None, "freeze", a)]
        self.cam = cam                # fonction (u, src_t) -> (cx, cy, zoom)
        self.draw = draw              # fonction (img, view, u, src_t, dur)
        self.post = post              # fonction (img, u, dur) -> img (teinte, flash...)
        self.min_dur = min_dur
        self.dur = None

    def fit(self, dur):
        fixed = sum(d for d, *_ in self.timeline if d is not None)
        rest = max(0.0, dur - fixed)
        self.tl = [(d if d is not None else rest, *r) for d, *r in self.timeline]
        self.dur = sum(d for d, *_ in self.tl)

    def src_t(self, u):
        acc = 0.0
        for d, kind, *r in self.tl:
            if u < acc + d or (d, kind, *r) == self.tl[-1]:
                v = min(max((u - acc) / d, 0), 1) if d > 0 else 1
                if kind == "play":
                    return lerp(r[0], r[1], v), False
                return r[0], True
            acc += d
        return self.tl[-1][2], True

    def frozen_amount(self, u):
        acc = 0.0
        for d, kind, *r in self.tl:
            if acc <= u < acc + d:
                if kind != "freeze":
                    return 0.0
                return min(1.0, (u - acc) / 0.18) * min(1.0, (acc + d - u) / 0.12 + 0.0001)
            acc += d
        return 0.0


def cam_kf(kf):
    return lambda u, st: keyframes(kf, u)


def cam_follow(name, dx=0, dy=0, zoom=1.0, zkf=None):
    def f(u, st):
        x, y = T(name, st)
        z = keyframes(zkf, u) if zkf else zoom
        return (x + dx, y + dy, z)
    return f


# ---- positions fixes relevées à la main (pixels source 1920x1080)
BALL_W = [(0.0, (535, 720)), (1.0, (730, 825)), (1.2, (760, 835)), (2.0, (1057, 893)), (4.0, (972, 828)),
          (4.75, (955, 808)), (5.5, (960, 760)), (5.75, (910, 718)), (6.25, (820, 668)), (6.75, (675, 655)),
          (7.25, (770, 638))]
# défenseurs autour de Cancelo (w = 5.5) et défenseur qui bloque le latéral (w = 4.75)
CAGE = [(660, 557), (985, 588), (805, 712)]
BLOCKER = (1302, 812)
# plan rapproché (close) : Lamine
L_CLOSE = [(2.3, (1500, 640)), (2.8, (1640, 640)), (3.0, (1660, 640)), (3.3, (1500, 560)), (3.5, (1400, 520)),
           (3.7, (1265, 540)), (3.9, (1150, 560))]
BALL_C = [(2.3, (1205, 740)), (3.3, (1150, 740)), (3.5, (1150, 712)), (3.62, (1146, 690)), (3.7, (1140, 660))]
HAND = (1500, 396)
PLANT = (1226, 756)


def kfpos(kf, t):
    return keyframes([(a, b) for a, b in kf], t)


def goal13(dur):
    """Instant (dans le plan 13) où le ballon entre dans le but, vu de derrière le poteau (source 9.25 s)."""
    rest = dur - 2.95
    return 2.95 + rest * (9.25 - 7.9) / (9.8 - 7.9)


def build_shots():
    S = []

    # 0 — accroche : la frappe de Lamine, le but, puis retour en arrière vers le début de l'action
    def d0(img, v, u, st, dur):
        if u < 1.9:
            p = v.P(kfpos(L_CLOSE, st))
            draw_marker(img, v.P((kfpos(L_CLOSE, st)[0], kfpos(L_CLOSE, st)[1] - 200)), u, appear(u, 0.15))
            del p
    def p0(img, u, dur):
        img = flash(img, max(0, 1 - abs(u - 1.9) / 0.18) * 0.85)
        img = flash(img, max(0, 1 - abs(u - 4.15) / 0.2) * 0.9)
        if u > dur - 1.45:
            k = ease((u - (dur - 1.45)) / 0.3)
            img = desaturate(img, 0.75 * k)
            # lignes « rembobinage »
            ov = img.copy()
            for y in range(0, OH, 7):
                cv2.line(ov, (0, y), (OW, y), (255, 255, 255), 1)
            img = cv2.addWeighted(img, 1 - 0.12 * k, ov, 0.12 * k, 0)
        return img
    S.append(Shot(0, ["close", "close", "wide"], None, None))
    S[-1].multi = [
        ("close", [(1.9, "play", 3.02, 3.78)],
         lambda u, st: (*kfpos(L_CLOSE, st), keyframes([(0, 1.25), (1.9, 1.5)], u))),
        ("close", [(2.75, "play", 7.75, 9.55)],
         lambda u, st: (keyframes([(0, (880, 600)), (1.4, (640, 640)), (2.1, (400, 675)), (2.75, (390, 680))], u) + (keyframes([(0, 1.05), (2.75, 1.4)], u),))),
        ("wide", [(None, "play", 1.6, 0.0)], lambda u, st: (760, 760, keyframes([(0, 1.35), (1.4, 1.15)], u))),
    ]
    S[-1].draw, S[-1].post = d0, p0

    # 1 — Pedri au centre du terrain
    def d1(img, v, u, st, dur):
        p = T("pedri", st)
        a = appear(u, 0.9)
        img[:] = spotlight(img, [(v.P(p), 120 * v.s / 1.8, 190 * v.s / 1.8)], a)
        draw_ring(img, v.P(feet(p)), 62 * v.s / 1.78, u, a)
        draw_marker(img, v.P(head(p)), u, appear(u, 1.1))
    S.append(Shot(1, "wide", [(1.0, "play", 0.0, 0.5), (None, "freeze", 0.5)],
                  cam_follow("pedri", 60, -20, zkf=[(0, 1.15), (1.0, 1.3), (2.5, 1.45)]), d1))

    # 2 — contrôle et passe vers le côté
    def d2(img, v, u, st, dur):
        if u < 1.1:
            draw_marker(img, v.P(head(T("pedri", st))), u, 1)
        else:
            draw_marker(img, v.P(head(T("lateral", st))), u, appear(u, 1.1))
        if u > 1.55:
            pa = v.P(feet(T("pedri", 2.05), 30))
            pb = v.P(feet(T("lateral", 2.05), 30))
            draw_arrow(img, pa, pb, ease_out((u - 1.6) / 0.6), bend=0.10)
            draw_ring(img, v.P(feet(T("lateral", st))), 58 * v.s / 1.78, u, appear(u, 1.9))
    S.append(Shot(2, "wide", [(1.55, "play", 0.5, 2.05), (None, "freeze", 2.05)],
                  cam_kf([(0, (760, 790, 1.2)), (1.55, (870, 830, 1.0)), (3.0, (870, 830, 1.03))]), d2))

    # 3 — le latéral contrôle puis joue vers Fermín à l'entrée de la surface
    def d3(img, v, u, st, dur):
        fr = 1.9
        if u < fr:
            draw_marker(img, v.P(head(T("lateral", st))), u, 1)
        else:
            lat, fer = T("lateral", 3.98), T("fermin", 3.98)
            draw_marker(img, v.P(head(fer)), u, appear(u, fr + 0.55))
            draw_arrow(img, v.P(feet(lat, 25)), v.P(feet(fer, 25)), ease_out((u - fr - 0.1) / 0.55), bend=0.12)
            a = appear(u, fr + 0.65)
            img[:] = spotlight(img, [(v.P(fer), 110 * v.s / 1.8, 170 * v.s / 1.8),
                                     (v.P(lat), 90 * v.s / 1.8, 150 * v.s / 1.8)], 0.8 * a)
            draw_ring(img, v.P(feet(fer)), 58 * v.s / 1.78, u, a)
            # coin de la surface (« entrada del área »)
            corner = v.P((1100, 873))
            if u > fr + 1.2:
                k = appear(u, fr + 1.2, 0.5)
                cv2.circle(img, ipt(corner), int(16 * back_out(k)), YELLOW, -1, cv2.LINE_AA)
                cv2.circle(img, ipt(corner), int(16 * back_out(k)), (20, 20, 20), 3, cv2.LINE_AA)
    S.append(Shot(3, "wide", [(1.9, "play", 2.05, 3.98), (None, "freeze", 3.98)],
                  cam_kf([(0, (1080, 860, 1.25)), (1.9, (1000, 830, 1.2)), (2.6, (990, 815, 1.35))]), d3))

    # 4 — ce que la plupart auraient fait : passe vers le latéral qui part dans le dos
    FZ = 4.75

    def d4(img, v, u, st, dur):
        fer, lat = T("fermin", FZ), T("lateral", FZ)
        fr = 1.3
        if u < fr:
            draw_marker(img, v.P(head(T("fermin", st))), u, 1)
            return
        draw_marker(img, v.P(head(fer)), u, 1)
        draw_ring(img, v.P(feet(fer)), 52 * v.s / 1.78, u, appear(u, fr))
        # course du latéral dans le dos de la défense
        draw_arrow(img, v.P(feet(lat, 30)), v.P((1460, 900)), ease_out((u - fr - 1.2) / 0.8),
                   color=YELLOW, bend=0.05, th=8, head_len=28)
        draw_marker(img, v.P(head(lat)), u, appear(u, fr + 1.0), color=YELLOW)
        # la passe « évidente »
        draw_arrow(img, v.P(feet(fer, 35)), v.P((1415, 912)), ease_out((u - fr - 3.0) / 0.8),
                   dashed=True, bend=0.10)
    S.append(Shot(4, "wide", [(1.3, "play", 3.98, FZ), (None, "freeze", FZ)],
                  cam_kf([(0, (1000, 820, 1.3)), (1.3, (1060, 830, 1.25)), (3.0, (1170, 845, 1.0))]), d4))

    # 5 — ... mais il est bloqué par un défenseur
    def d5(img, v, u, st, dur):
        fer, lat = T("fermin", FZ), T("lateral", FZ)
        draw_marker(img, v.P(head(fer)), u, 1)
        draw_arrow(img, v.P(feet(lat, 30)), v.P((1460, 900)), 1, color=YELLOW, bend=0.05, th=8, head_len=28)
        draw_marker(img, v.P(head(lat)), u, 1, color=YELLOW)
        draw_arrow(img, v.P(feet(fer, 35)), v.P((1415, 912)), 1, dashed=True, bend=0.10, alpha=0.75)
        draw_ring(img, v.P(feet(BLOCKER, 40)), 60 * v.s / 1.78, u, appear(u, 0.25), color=RED, dashed=False)
        draw_marker(img, v.P(head(BLOCKER, -58)), u, appear(u, 0.3))
        draw_cross(img, v.P((1330, 868)), appear(u, 0.55))
    def p5(img, u, dur):
        return red_tint(img, 0.5 * appear(u, 0.25, 0.3) * (1 - appear(u, dur - 0.2, 0.2)))
    S.append(Shot(5, "wide", [(None, "freeze", FZ)],
                  cam_kf([(0, (1170, 845, 1.0)), (0.5, (1240, 845, 1.45))]), d5, p5))

    # 6 — Fermín écarte cette option et lève la tête
    F6 = 5.5

    def d6(img, v, u, st, dur):
        fr = 1.6
        fer = T("fermin", st)
        if u < fr:
            draw_marker(img, v.P(head(fer)), u, 1)
            draw_cross(img, v.P((1330, 868)), 1 - appear(u, 0.0, 0.4))
            return
        a = appear(u, fr)
        img[:] = spotlight(img, [(v.P(fer), 100 * v.s / 1.8, 170 * v.s / 1.8)], a)
        draw_ring(img, v.P(feet(fer)), 55 * v.s / 1.78, u, a)
        draw_marker(img, v.P(head(fer)), u, 1)
        # « regard » : cône qui balaie vers la surface
        eye = v.P(head(fer, -45))
        sweep = ease((u - fr - 0.9) / 1.3)
        ang = math.radians(lerp(-10, -128, sweep))
        L = 330 * v.s / 1.8
        for k, w in ((0, 0.20), (1, 0.12)):
            spread = math.radians(14 + 8 * k)
            pts = [eye, (eye[0] + L * math.cos(ang - spread), eye[1] + L * math.sin(ang - spread)),
                   (eye[0] + L * math.cos(ang + spread), eye[1] + L * math.sin(ang + spread))]
            poly_fill(img, pts, (180, 255, 255), w * appear(u, fr + 0.3))
    S.append(Shot(6, "wide", [(1.6, "play", FZ, F6), (None, "freeze", F6)],
                  cam_kf([(0, (1150, 840, 1.6)), (1.6, (1000, 800, 1.55)), (3.2, (960, 760, 1.7))]), d6))

    # 7 — Cancelo dans la surface, dans un petit espace, entouré de trois défenseurs
    def d7(img, v, u, st, dur):
        can = T("cancelo", F6)
        cage = [v.P(feet(p, 40)) for p in CAGE]
        a = appear(u, 0.5)
        img[:] = spotlight(img, [(v.P(can), 95 * v.s / 1.8, 160 * v.s / 1.8)], 0.7 * a)
        draw_marker(img, v.P(head(can)), u, appear(u, 0.9))
        draw_ring(img, v.P(feet(can)), 48 * v.s / 1.78, u, appear(u, 0.6), color=YELLOW)
        for i, p in enumerate(CAGE):
            draw_ring(img, v.P(feet(p, 40)), 46 * v.s / 1.78, u, appear(u, 3.3 + 0.3 * i), color=RED, dashed=False)
        k = appear(u, 4.3, 0.5)
        if k > 0:
            poly_fill(img, cage, (40, 40, 220), 0.22 * k)
            for i in range(3):
                draw_arrow(img, cage[i], cage[(i + 1) % 3], k, color=RED, bend=0.0, th=5, head_len=1, alpha=0.9)
    S.append(Shot(7, "wide", [(None, "freeze", F6)],
                  cam_kf([(0, (960, 760, 1.7)), (0.9, (830, 640, 1.42)), (4.0, (830, 635, 1.55))]), d7))

    # 8 — Fermín envoie le ballon dans la surface
    def d8(img, v, u, st, dur):
        fer, can = T("fermin", 6.15), T("cancelo", 6.15)
        if u > 1.5:
            draw_arrow(img, v.P(feet(fer, 20)), v.P(feet(can, 25)), ease_out((u - 1.55) / 0.6), bend=-0.12)
        draw_marker(img, v.P(head(T("cancelo", st))), u, 1)
        if u > 1.4:
            draw_ring(img, v.P(feet(T("cancelo", st))), 48 * v.s / 1.78, u, 1, color=YELLOW)
    S.append(Shot(8, "wide", [(1.5, "play", F6, 6.15), (None, "freeze", 6.15)],
                  cam_kf([(0, (920, 700, 1.45)), (1.5, (900, 700, 1.4)), (3.0, (900, 700, 1.45))]), d8))

    # 9 — une touche : Cancelo remet directement pour Lamine Yamal
    def d9(img, v, u, st, dur):
        fr = 1.5
        can, lam = T("cancelo", 6.62), T("lamine", 6.62)
        if u < fr:
            draw_marker(img, v.P(head(T("cancelo", st))), u, 1)
            draw_ring(img, v.P(feet(T("cancelo", st))), 48 * v.s / 1.78, u, 1, color=YELLOW)
        if u >= fr:
            draw_arrow(img, v.P(feet(can, 25)), v.P(feet(lam, 25)), ease_out((u - fr - 0.05) / 0.6), bend=0.15)
        if u >= fr:
            lam2 = T("lamine", st)
            a = appear(u, fr)
            img[:] = spotlight(img, [(v.P(lam2), 100 * v.s / 1.8, 170 * v.s / 1.8)], a)
            draw_marker(img, v.P(head(lam2)), u, appear(u, fr + 0.1))
            draw_ring(img, v.P(feet(lam2)), 56 * v.s / 1.78, u, a)
    S.append(Shot(9, "wide", [(1.5, "play", 6.15, 6.62), (None, "freeze", 6.62)],
                  cam_kf([(0, (780, 670, 1.7)), (1.5, (690, 690, 1.65)), (3.0, (640, 690, 1.85))]), d9))

    # 10 — plan rapproché : Lamine voit arriver le ballon et se place pour frapper
    def d10(img, v, u, st, dur):
        lam = kfpos(L_CLOSE, st)
        ball = kfpos(BALL_C, st)
        fr = 2.5
        draw_marker(img, v.P((lam[0], lam[1] - 190)), u, appear(u, 0.6))
        if u >= fr:
            a = appear(u, fr)
            img[:] = spotlight(img, [(v.P(lam), 230 * v.s / 1.8, 380 * v.s / 1.8),
                                     (v.P(ball), 60 * v.s / 1.8, 60 * v.s / 1.8)], a)
            draw_arrow(img, v.P((ball[0] - 200, ball[1] + 30)), v.P((ball[0] - 40, ball[1] + 5)),
                       ease_out((u - fr - 0.2) / 0.5), bend=0.0, th=9)
            draw_ring(img, v.P((ball[0], ball[1] + 25)), 48 * v.s / 1.78, u, appear(u, fr + 0.4), color=YELLOW)
    S.append(Shot(10, "close", [(2.5, "play", 2.3, 3.35), (None, "freeze", 3.35)],
                  lambda u, st: (*kfpos(L_CLOSE, min(st, 3.35)), keyframes([(0, 1.0), (2.5, 1.2), (4.5, 1.32)], u))))
    S[-1].draw = d10

    # 11 — main droite levée, pied d'appui planté
    def d11(img, v, u, st, dur):
        a1, a2 = appear(u, 0.85), appear(u, 1.75)
        img[:] = spotlight(img, [(v.P(HAND), 85 * v.s / 1.8, 85 * v.s / 1.8),
                                 (v.P(PLANT), 95 * v.s / 1.8, 60 * v.s / 1.8),
                                 (v.P((1380, 540)), 150 * v.s / 1.8, 260 * v.s / 1.8)], 0.85 * max(a1, a2) * 0.8)
        draw_ring(img, v.P(HAND), 44 * v.s / 1.6, u, a1, color=YELLOW)
        draw_arrow(img, v.P((HAND[0] + 190, HAND[1] - 120)), v.P((HAND[0] + 45, HAND[1] - 25)),
                   ease_out((u - 0.85) / 0.45), color=YELLOW, bend=0.15, th=9)
        draw_ring(img, v.P((PLANT[0], PLANT[1] + 8)), 50 * v.s / 1.6, u, a2, color=RED, dashed=False)
        draw_arrow(img, v.P((PLANT[0] - 220, PLANT[1] + 120)), v.P((PLANT[0] - 55, PLANT[1] + 25)),
                   ease_out((u - 1.75) / 0.45), color=RED, bend=-0.15, th=9)
    S.append(Shot(11, "close", [(0.6, "play", 3.35, 3.5), (None, "freeze", 3.5)],
                  cam_kf([(0, (1400, 560, 1.32)), (0.6, (1375, 580, 1.35)), (2.8, (1370, 585, 1.45))]), d11))

    # 12 — on sent qu'il prépare un missile
    def d12(img, v, u, st, dur):
        ball = v.P(kfpos(BALL_C, st))
        k = appear(u, 1.3)
        pulse = 0.5 + 0.5 * math.sin(u * 14)
        for r, a in ((90, 0.18), (60, 0.28), (38, 0.4)):
            ov = img.copy()
            cv2.circle(ov, ipt(ball), int(r * v.s / 1.6 * (1 + 0.12 * pulse)), (30, 90, 255), -1, cv2.LINE_AA)
            cv2.addWeighted(ov, a * k, img, 1 - a * k, 0, img)
        draw_ring(img, (ball[0], ball[1] + 10), 52 * v.s / 1.6, u, k, color=RED, dashed=True, spin=4)
    def p12(img, u, dur):
        k = appear(u, 1.3, 0.4)
        return red_tint(img, 0.35 * k)
    S.append(Shot(12, "close", [(1.4, "play", 3.5, 3.62), (None, "freeze", 3.62)],
                  lambda u, st: (keyframes([(0, (1350, 590)), (1.4, (1250, 620)), (3.5, (1200, 650))], u)
                                 + (keyframes([(0, 1.55), (1.4, 1.75), (3.5, 2.1)], u)
                                    + (0.02 * math.sin(u * 50) * appear(u, 1.3) if u > 1.3 else 0),)), d12, p12))

    # 13 — la frappe, le but
    S.append(Shot(13, ["close", "close"], None, None))
    S[-1].multi = [
        ("close", [(2.95, "play", 3.62, 6.57)],
         lambda u, st: (*keyframes([(3.62, (1230, 600)), (4.0, (700, 580)), (4.6, (520, 520)), (5.2, (350, 540)),
                                    (5.8, (640, 500)), (6.57, (930, 470))], st),
                        keyframes([(0, 1.2), (0.4, 1.0), (2.4, 1.0), (2.95, 1.3)], u))),
        ("close", [(None, "play", 7.9, 9.8)],
         lambda u, st: (keyframes([(0, (900, 600)), (1.5, (580, 645)), (2.2, (400, 675)), (3.4, (390, 680))], u) + (keyframes([(0, 1.0), (2.2, 1.2), (3.4, 1.3)], u),))),
    ]

    def p13(img, u, dur):
        img = flash(img, max(0, 1 - abs(u - 0.05) / 0.12) * 0.6)
        return flash(img, max(0, 1 - abs(u - goal13(dur)) / 0.22) * 0.8)
    S[-1].post = p13

    # fin : célébration de Lamine (sans voix)
    S.append(Shot(None, "close", [(2.6, "play", 13.9, 16.3)],
                  cam_kf([(0, (1600, 560, 1.05)), (2.6, (1640, 520, 1.2))])))
    return S


# ------------------------------------------------------------------ montage + audio
def plan(G):
    cache = os.path.join(BUILD, "voice")
    os.makedirs(cache, exist_ok=True)
    tts = None
    clips = []
    vf0 = getattr(G, "VOICE_FILE", None)
    for i, text in enumerate([] if vf0 and os.path.exists(os.path.join(HERE, vf0)) else G.LINES):
        p = os.path.join(cache, f"{G.VOICE}_{G.SPEED}_{i:02d}.wav")
        if not os.path.exists(p):
            if tts is None:
                tts = audio.load_tts(os.path.join(HERE, "models"))
            sf.write(p, audio.synth_line(tts, text, G.VOICE, G.SPEED, G.LANG), audio.SR)
        clips.append(sf.read(p)[0])
    shots = build_shots()
    vf = getattr(G, "VOICE_FILE", None)
    ext = vf and os.path.exists(os.path.join(HERE, vf))
    if ext:
        # voix enregistrée : bornes des plans = début de chaque phrase (un peu avant)
        bounds = [0.0] + [s - 0.12 for s in G.LINE_STARTS[1:]] + [G.VOICE_END + 0.45]
    t = 0.0
    starts = []
    for k, sh in enumerate(shots):
        lead = 0.15 if sh.line == 0 else 0.08
        if sh.line is not None and ext:
            dur = bounds[sh.line + 1] - bounds[sh.line]
        elif sh.line is not None:
            ln = len(clips[sh.line]) / audio.SR
            gap = 0.18 if G.LINES[sh.line].endswith(",") else 0.32
            dur = max(lead + ln + gap, sh.min_dur)
        else:
            dur = sum(d for d, *_ in sh.timeline if d is not None)
        if getattr(sh, "multi", None):
            fixed = sum(d for _, tl, _ in sh.multi for d, *_ in tl if d is not None)
            rest = max(0.4, dur - fixed)
            sh.parts = []
            for clip, tl, cam in sh.multi:
                tl2 = [(d if d is not None else rest, *r) for d, *r in tl]
                sh.parts.append((clip, tl2, cam, sum(d for d, *_ in tl2)))
            sh.dur = sum(p[3] for p in sh.parts)
        else:
            sh.fit(dur)
        sh.t0 = t
        starts.append((t + lead, sh.line))
        t += sh.dur
    duration = t
    voice = np.zeros(int((duration + 1) * audio.SR))
    if ext:
        import scipy.signal as ss
        dec = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(HERE, vf), "-ac", "1", "-ar", str(audio.SR),
                              "-f", "f32le", "-"], capture_output=True, check=True).stdout
        a = np.frombuffer(dec, np.float32).astype(np.float64)
        voice[:min(len(a), len(voice))] = a[:len(voice)]
        return shots, voice, duration
    for (s, li) in starts:
        if li is None:
            continue
        c = clips[li]
        j = int(s * audio.SR)
        voice[j:j + len(c)] += c
    return shots, voice, duration


def sfx_events(shots):
    ev = []
    for sh in shots:
        if getattr(sh, "parts", None):
            acc = sh.t0
            for i, p in enumerate(sh.parts):
                if i:
                    ev.append((acc - 0.1, "whoosh", 0.45))
                acc += p[3]
            continue
        acc = sh.t0
        for d, kind, *r in sh.tl:
            if kind == "freeze" and acc > sh.t0 + 0.05:
                ev.append((acc, "tick", 0.5))
            acc += d
        if sh.t0 > 0.1:
            ev.append((sh.t0 - 0.08, "whoosh", 0.3))
    s0 = shots[0]
    ev += [(s0.t0 + 1.9, "boom", 0.55), (s0.t0 + 4.15, "pop", 0.5), (s0.t0 + s0.dur - 1.5, "riser", 0.35)]
    s13 = shots[13]
    ev += [(s13.t0 + 0.02, "boom", 0.6), (s13.t0 + goal13(s13.dur), "boom", 0.7)]
    s5 = shots[5]
    ev += [(s5.t0 + 0.25, "error", 0.55)]
    s12 = shots[12]
    ev += [(s12.t0 + 0.2, "riser", 0.45)]
    return ev


def render_frame(shots, t):
    sh = next(s for s in shots if s.t0 <= t < s.t0 + s.dur) if t < shots[-1].t0 + shots[-1].dur else shots[-1]
    u = t - sh.t0
    frozen = 0.0
    if getattr(sh, "parts", None):
        acc = 0.0
        for clip, tl, cam, d in sh.parts:
            if u < acc + d or (clip, tl, cam, d) == sh.parts[-1]:
                uu = u - acc
                dd, kind, *r = tl[0]
                st = lerp(r[0], r[1], min(max(uu / dd, 0), 1)) if kind == "play" else r[0]
                cx, cy, z = cam(uu, st)
                break
            acc += d
    else:
        clip = sh.clip
        st, _ = sh.src_t(u)
        frozen = sh.frozen_amount(u)
        cx, cy, z = sh.cam(u, st)
    # petit « punch » de zoom quand l'image se fige
    z *= 1 + 0.035 * frozen
    v = View(cx, cy, z)
    img = v.render(src_frame(clip, st))
    if sh.draw:
        sh.draw(img, v, u, st, sh.dur)
    if sh.post:
        img = sh.post(img, u, sh.dur)
    img = freeze_border(img, frozen * 0.7)
    img = vignette(img)
    # fondu au tout début et à la fin
    total = shots[-1].t0 + shots[-1].dur
    if t < 0.12:
        img = (img * (t / 0.12)).astype(np.uint8)
    if t > total - 0.5:
        img = (img * max(0, (total - t) / 0.5)).astype(np.uint8)
    return img


def _worker(args):
    script, a, b, path = args
    G = __import__(script)
    global TRACKS
    TRACKS = compute_tracks()
    shots, _, _ = plan(G)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{OW}x{OH}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                           "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for k in range(a, b):
        ff.stdin.write(render_frame(shots, k / FPS).tobytes())
    ff.stdin.close()
    ff.wait()
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", default="guion_yamal_es")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "output", "lamine_yamal_es.mp4"))
    ap.add_argument("--stills", default="")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    args = ap.parse_args()
    if not os.path.isdir(os.path.join(FRAMES, "wide")):
        sys.exit("Lance d'abord : python3 yamal_clean.py")
    global TRACKS
    TRACKS = compute_tracks()
    G = __import__(args.script)
    shots, voice, duration = plan(G)
    print(f"durée : {duration:.1f} s")
    for i, sh in enumerate(shots):
        print(f"  plan {i:2d}  {sh.t0:5.2f} -> {sh.t0 + sh.dur:5.2f}")
    if args.stills:
        for s in args.stills.split(","):
            t = float(s)
            cv2.imwrite(os.path.join(BUILD, f"still_{t:05.1f}.png"), render_frame(shots, t))
        print("images dans", BUILD)
        return
    n = int(duration * FPS)
    w = max(1, args.workers)
    bounds = [(n * i // w, n * (i + 1) // w) for i in range(w)]
    parts = [os.path.join(BUILD, f"part{i}.mp4") for i in range(w)]
    with ProcessPoolExecutor(w) as ex:
        list(ex.map(_worker, [(args.script, a, b, p) for (a, b), p in zip(bounds, parts)]))
    lst = os.path.join(BUILD, "parts.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    # audio : voix + bruitages (pas de musique)
    mix = audio.mix_all(voice, np.zeros_like(voice), sfx_events(shots), duration)
    wav = os.path.join(BUILD, "mix.wav")
    sf.write(wav, mix, audio.SR)
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
                    "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-shortest", "-movflags", "+faststart", out], check=True)
    print("OK :", out)


if __name__ == "__main__":
    main()
