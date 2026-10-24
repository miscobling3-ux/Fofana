"""Pixel Story : histoire vraie en pixel art rétro 16 bits, vidéo TikTok 1080x1920.

Tout est dessiné sur une toile de 270x480 pixels puis agrandi x4 sans lissage.
Usage : python3 pixel_story.py [--script historia_copa_es] [--out ../output/x.mp4] [--stills 2,10]
"""
import argparse
import hashlib
import importlib
import math
import multiprocessing as mp
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import audio  # noqa: E402
import chiptune  # noqa: E402

CW, CH, SCALE, FPS = 270, 480, 4, 30
STEP = 1 / 8          # les animations avancent par à-coups, 8 fois par seconde
TRANS = 0.4           # durée des transitions

PAL = {
    "B": (5, 3, 0),          # fond
    "K": (22, 13, 4),        # contour
    "D": (62, 37, 11),       # ambre très sombre
    "a": (150, 92, 28),      # ambre sombre
    "A": (232, 163, 58),     # ambre (couleur dominante)
    "L": (255, 214, 130),    # ambre clair
    "W": (244, 232, 208),    # crème
    "g": (62, 58, 54),
    "G": (118, 112, 104),
    "H": (190, 184, 174),
    "R": (216, 49, 44),      # accent
    "r": (122, 26, 22),
    "S": (236, 180, 122),    # peau
}
C = {k: np.array(v, np.uint8) for k, v in PAL.items()}
HALO = [np.array(c, np.uint8) for c in [(5, 3, 0), (17, 10, 2), (30, 18, 5), (45, 27, 8), (62, 38, 12)]]
HALO_RED = [np.array(c, np.uint8) for c in [(5, 3, 0), (22, 5, 3), (40, 9, 6), (60, 14, 9), (82, 20, 13)]]

_B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16 + 1 / 32
BAYER = np.tile(_B4, (CH // 4, CW // 4 + 1))[:CH, :CW]
NOISE = np.random.default_rng(3).random((CH, CW))
BLOCKS = np.random.default_rng(4).random((CH // 3 + 1, CW // 3 + 1)).repeat(3, 0).repeat(3, 1)[:CH, :CW]
YY, XX = np.mgrid[0:CH, 0:CW]


def col(c):
    return C[c] if isinstance(c, str) else np.asarray(c, np.uint8)


# ---------------------------------------------------------------- police pixel 5x7
_G = {
    "A": ".###. #...# #...# ##### #...# #...# #...#", "B": "####. #...# #...# ####. #...# #...# ####.",
    "C": ".###. #...# #.... #.... #.... #...# .###.", "D": "####. #...# #...# #...# #...# #...# ####.",
    "E": "##### #.... #.... ####. #.... #.... #####", "F": "##### #.... #.... ####. #.... #.... #....",
    "G": ".###. #...# #.... #.### #...# #...# .####", "H": "#...# #...# #...# ##### #...# #...# #...#",
    "I": "### .#. .#. .#. .#. .#. ###", "J": "..### ...#. ...#. ...#. #..#. #..#. .##..",
    "K": "#...# #..#. #.#.. ##... #.#.. #..#. #...#", "L": "#.... #.... #.... #.... #.... #.... #####",
    "M": "#...# ##.## #.#.# #.#.# #...# #...# #...#", "N": "#...# ##..# ##..# #.#.# #..## #..## #...#",
    "O": ".###. #...# #...# #...# #...# #...# .###.", "P": "####. #...# #...# ####. #.... #.... #....",
    "Q": ".###. #...# #...# #...# #.#.# #..#. .##.#", "R": "####. #...# #...# ####. #.#.. #..#. #...#",
    "S": ".#### #.... #.... .###. ....# ....# ####.", "T": "##### ..#.. ..#.. ..#.. ..#.. ..#.. ..#..",
    "U": "#...# #...# #...# #...# #...# #...# .###.", "V": "#...# #...# #...# #...# #...# .#.#. ..#..",
    "W": "#...# #...# #...# #.#.# #.#.# #.#.# .#.#.", "X": "#...# #...# .#.#. ..#.. .#.#. #...# #...#",
    "Y": "#...# #...# .#.#. ..#.. ..#.. ..#.. ..#..", "Z": "##### ....# ...#. ..#.. .#... #.... #####",
    "0": ".###. #...# #..## #.#.# ##..# #...# .###.", "1": ".#. ##. .#. .#. .#. .#. ###",
    "2": ".###. #...# ....# ...#. ..#.. .#... #####", "3": "####. ....# ....# .###. ....# ....# ####.",
    "4": "...#. ..##. .#.#. #..#. ##### ...#. ...#.", "5": "##### #.... ####. ....# ....# #...# .###.",
    "6": ".###. #.... #.... ####. #...# #...# .###.", "7": "##### ....# ...#. ..#.. .#... .#... .#...",
    "8": ".###. #...# #...# .###. #...# #...# .###.", "9": ".###. #...# #...# .#### ....# ....# .###.",
    ".": ". . . . . . #", ",": ".. .. .. .. .. .# #.", ":": ". . # . . # .", ";": ".. .. .# .. .. .# #.",
    "!": "# # # # # . #", "¡": "# . # # # # #",
    "?": ".###. #...# ....# ...#. ..#.. ..... ..#..", "¿": "..#.. ..... ..#.. .#... #.... #...# .###.",
    "-": "... ... ... ### ... ... ...", "·": ". . . # . . .", "'": "# # . . . . .",
    "£": "..##. .#..# .#... ###.. .#... .#... #####", "/": "....# ...#. ...#. ..#.. .#... .#... #....",
    "(": ".# #. #. #. #. #. .#", ")": "#. .# .# .# .# .# #.", "+": "..... ..#.. ..#.. ##### ..#.. ..#.. .....",
}
GLYPHS = {k: np.array([[c == "#" for c in r] for r in v.split()]) for k, v in _G.items()}
_ACC = {"Á": ("A", "acute"), "É": ("E", "acute"), "Í": ("I", "acute"), "Ó": ("O", "acute"),
        "Ú": ("U", "acute"), "Ñ": ("N", "tilde"), "Ü": ("U", "diaer"), "À": ("A", "grave"),
        "Â": ("A", "circ"), "È": ("E", "grave"), "Ê": ("E", "circ"), "Ë": ("E", "diaer"), "Î": ("I", "circ"),
        "Ï": ("I", "diaer"), "Ô": ("O", "circ"), "Ù": ("U", "grave"), "Û": ("U", "circ"), "Ç": ("C", "cedil")}
for _k, (_b, _kind) in _ACC.items():
    base = GLYPHS[_b]
    g = np.zeros((12, base.shape[1]), bool)
    g[3:10] = base
    w = base.shape[1]
    pts = {"acute": [(w // 2 + 1, 0), (w // 2, 1)], "diaer": [(1, 1), (w - 2, 1)],
           "tilde": [(1, 0), (2, 0), (4, 0), (0, 1), (3, 1)], "grave": [(w // 2 - 1, 0), (w // 2, 1)],
           "circ": [(w // 2 - 1, 1), (w // 2, 0), (w // 2 + 1, 1)], "cedil": [(w // 2, 10), (w // 2 - 1, 11)]}[_kind]
    for x, y in pts:
        g[y, min(x, w - 1)] = True
    GLYPHS[_k] = g
for _k, _v in list(GLYPHS.items()):
    if _v.shape[0] == 7:
        GLYPHS[_k] = np.vstack([np.zeros((3, _v.shape[1]), bool), _v, np.zeros((2, _v.shape[1]), bool)])


def text_mask(s, sc=1):
    """Masque booléen du texte (12 lignes par caractère : 3 pour les accents, 2 pour la cédille)."""
    s = s.upper()
    cols = []
    for ch in s:
        g = GLYPHS.get(ch)
        if g is None:
            g = np.zeros((12, 3), bool)
        cols += [g, np.zeros((12, 1), bool)]
    m = np.hstack(cols[:-1]) if cols else np.zeros((12, 1), bool)
    return m.repeat(sc, 0).repeat(sc, 1)


def text_w(s, sc=1):
    return text_mask(s, sc).shape[1]


def paint(img, m, x, y, c):
    x, y = int(round(x)), int(round(y))
    h, w = m.shape
    x0, y0, x1, y1 = max(0, x), max(0, y), min(CW, x + w), min(CH, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    sub = m[y0 - y:y1 - y, x0 - x:x1 - x]
    img[y0:y1, x0:x1][sub] = col(c)


def dilate(m, r=1):
    p = np.pad(m, r)
    out = np.zeros_like(p)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out |= np.roll(np.roll(p, dy, 0), dx, 1)
    return out


def text(img, s, x, y, sc=1, c="W", outline="K", shadow=None, align="center", n=None):
    """y = haut des lettres (hors accents). align : center (x = centre), left."""
    if n is not None:
        full = text_w(s, sc)
        s = s[:max(0, n)]
    m = text_mask(s, sc)
    w = full if n is not None else m.shape[1]
    x0 = x - w // 2 if align == "center" else x
    y0 = y - 3 * sc
    if shadow:
        paint(img, m, x0 + sc, y0 + sc, shadow)
    if outline:
        paint(img, dilate(m), x0 - 1, y0 - 1, outline)
    paint(img, m, x0, y0, c)


# ---------------------------------------------------------------- primitives
def rect(img, x, y, w, h, c):
    x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(CW, int(x + w)), min(CH, int(y + h))
    if x1 > x0 and y1 > y0:
        img[y0:y1, x0:x1] = col(c)


def box(img, x, y, w, h, fill, line="K"):
    rect(img, x, y, w, h, line)
    rect(img, x + 1, y + 1, w - 2, h - 2, fill)


def dither(img, x, y, w, h, c, density):
    x0, y0, x1, y1 = max(0, int(x)), max(0, int(y)), min(CW, int(x + w)), min(CH, int(y + h))
    if x1 > x0 and y1 > y0:
        img[y0:y1, x0:x1][BAYER[y0:y1, x0:x1] < density] = col(c)


def disc_mask(r):
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]
    return xx * xx + yy * yy <= r * r + r * 0.6


def disc(img, cx, cy, r, c, outline=None):
    m = disc_mask(int(r))
    if outline:
        paint(img, dilate(m), cx - r - 1, cy - r - 1, outline)
    paint(img, m, cx - r, cy - r, c)


def line(img, x0, y0, x1, y1, c, dashed=False):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    xs = np.round(np.linspace(x0, x1, n)).astype(int)
    ys = np.round(np.linspace(y0, y1, n)).astype(int)
    ok = (xs >= 0) & (xs < CW) & (ys >= 0) & (ys < CH)
    if dashed:
        ok &= (np.arange(n) // 2) % 2 == 0
    img[ys[ok], xs[ok]] = col(c)


def halo(img, cx, cy, r, strength=1.0, red=False):
    """Halo de lumière chaude, tramé (dithering ordonné) en 5 niveaux."""
    y0, y1 = max(0, int(cy - r)), min(CH, int(cy + r))
    x0, x1 = max(0, int(cx - r)), min(CW, int(cx + r))
    d = np.hypot(XX[y0:y1, x0:x1] - cx, (YY[y0:y1, x0:x1] - cy) * 1.1) / r
    inten = np.clip(1 - d, 0, 1) ** 1.4 * strength * 4
    lv = np.clip((inten + BAYER[y0:y1, x0:x1]).astype(int), 0, 4)
    pal = np.stack(HALO_RED if red else HALO)
    reg = img[y0:y1, x0:x1]
    sel = lv > 0
    reg[sel] = pal[lv[sel]]


# ---------------------------------------------------------------- sprites
def sprite(txt):
    rows = [r.strip() for r in txt.strip().split("\n")]
    w = max(len(r) for r in rows)
    rgb = np.zeros((len(rows), w, 3), np.uint8)
    m = np.zeros((len(rows), w), bool)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in PAL:
                rgb[y, x], m[y, x] = PAL[ch], True
    return rgb, m


def blit(img, spr, x, y, s=2, flip=False, keep=None):
    rgb, m = spr
    if flip:
        rgb, m = rgb[:, ::-1], m[:, ::-1]
    if keep is not None:
        m = m & keep
    if s > 1:
        rgb, m = rgb.repeat(s, 0).repeat(s, 1), m.repeat(s, 0).repeat(s, 1)
    h, w = m.shape
    x, y = int(round(x)), int(round(y))
    x0, y0, x1, y1 = max(0, x), max(0, y), min(CW, x + w), min(CH, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    sub = m[y0 - y:y1 - y, x0 - x:x1 - x]
    img[y0:y1, x0:x1][sub] = rgb[y0 - y:y1 - y, x0 - x:x1 - x][sub]


def blitc(img, spr, cx, by, s=2, **kw):
    """Ancre en bas au centre."""
    h, w = spr[1].shape
    blit(img, spr, cx - w * s // 2, by - h * s, s, **kw)


def ghost(img, spr, cx, by, s=2, c="G"):
    """Contour en pointillés de l'objet disparu."""
    m = spr[1]
    o = (dilate(m)[1:-1, 1:-1] & ~m).repeat(s, 0).repeat(s, 1)
    o &= (np.add.outer(np.arange(o.shape[0]), np.arange(o.shape[1])) // 3) % 2 == 0
    h, w = m.shape
    paint(img, o, cx - w * s // 2, by - h * s, c)


def dissolve_keep(spr, p, seed=0):
    h, w = spr[1].shape
    return np.random.default_rng(seed).random((h, w)) >= p


TROPHY = sprite("""
....KKKKKKKK....
...KLLLLLLLAK...
...KLAAAAAAaK...
....KLAAAAaK....
.....KLAAaK.....
.KK...KLaK...KK.
KLAK..KLaK..KALK
KLAAK.KLaK.KAaLK
.KLAAKKLaKKAaLK.
..KLAAALAAAaLK..
...KLAAAAAAaK...
....KLAAAAaK....
.....KLAAaK.....
.....KLAAaK.....
......KLaK......
......KLaK......
.....KLLAaK.....
.....KLAAaK.....
....KLLAAAaK....
....KLAAAAaK....
...KKKKKKKKKK...
...KDaaaaaaDK...
..KKKKKKKKKKKK..
..KDgGGGGGGgDK..
..KDgGHHHHGgDK..
..KDgGGGGGGgDK..
.KKKKKKKKKKKKKK.
.KDaaaaaaaaaaDK.
.KKKKKKKKKKKKKK.
""")

_DOG_TOP = """
................KK....
...............KgGK...
..............KgggKK..
.............KgggWgKK.
..K..........KgKgWWWK.
.KgK.........KggWWWWK.
..KgKKKKKKKKKRRRWWKK..
...KgggggGGGgRRRKK....
...KgggggggggggWK.....
...KgggggggggWWWK.....
...KggKKKKKKKgWK......
"""
DOG = [sprite(_DOG_TOP + """
...KgK.KgK..KgKgK.....
...KgK.KgK..KgKgK.....
...KKK.KKK..KKKKK.....
"""), sprite(_DOG_TOP + """
..KgK...KgKKgK..KgK...
.KgK.....KKgK....KgK..
.KKK......KKK....KKK..
""")]


def _sniff(spr):
    rgb, m = spr[0].copy(), spr[1].copy()
    head_rgb, head_m = rgb[0:7, 12:].copy(), m[0:7, 12:].copy()
    rgb[0:7, 12:], m[0:7, 12:] = 0, False
    rgb = np.vstack([rgb, np.zeros((3, rgb.shape[1], 3), np.uint8)])
    m = np.vstack([m, np.zeros((3, m.shape[1]), bool)])
    sel = head_m
    rgb[4:11, 12:][sel], m[4:11, 12:][sel] = head_rgb[sel], True
    return rgb[:-3], m[:-3]


DOG_SNIFF = _sniff(DOG[0])

_MAN_TOP = """
....KKKKK.....
...KgggggK....
..KgggggggKK..
..KKKKKKKKKKK.
...KSSSSSK....
...KSSSKSK....
...KSSSSSSK...
...KSSSSSK....
....KSSSK.....
...KKaaaKK....
..KaaaaaaaK...
.KaaaaaaaaaK..
.KaaKaaaaDaK..
.KaaKaaaaDaK..
.KaaKaaaaDaK..
.KaaKaaaaDaK..
.KSSKaaaaDaK..
..KK.KaaaDaK..
.....KaaaDaK..
.....KaaaDaK..
.....KKKKKKK..
"""
_LEGS = ["""
.....KggKggK..
.....KggKggK..
.....KggKggK..
.....KggKggK..
....KKKKKKKKK.
""", """
....KggK.KggK.
...KggK...KggK
...KggK...KggK
..KggK....KggK
..KKKK....KKKK
"""]
MAN = [sprite(_MAN_TOP + l) for l in _LEGS]

_BOBBY_TOP = """
.....KKKK.....
....KggggK....
...KgggggK....
...KggAggK....
...KgggggK....
..KKKKKKKKK...
...KSSSSSK....
...KSSSKSK....
...KSSSSSSK...
...KSSSSSK....
....KSSSK.....
...KKgggKK....
..KgggggggK...
.KgggAgggggK..
.KgKggggKggK..
.KgKgAgggKgK..
.KgKggggKggK..
.KgKgAgggKgK..
.KgKKKKKKKgK..
.KSKgggggKSK..
..KKgggggKK...
....KgggggK...
"""
BOBBY = [sprite(_BOBBY_TOP + l) for l in _LEGS]

PARCEL = sprite("""
KKKKKKKKKKKKKKKK
KHHHHHHHHHHHHHHK
KHgggHgHgggHHHHK
KHHHHHHHHHHHHHHK
KHggHgggHggHgHHK
KHHHHHHHHHHHHHHK
KGGGGGGGGGGGGGGK
KKKKKKKKKKKKKKKK
""")

BONE = sprite("""
KK......KK
KWK....KWK
.KWKKKKKWK
.KWWWWWWWK
KWKKKKKKWK
KK......KK
""")


# ---------------------------------------------------------------- éléments d'interface
def bubble(img, s, cx, by, age, c="K"):
    """Bulle en forme de nuage, au-dessus de (cx, by)."""
    if age is None or age < 0:
        return
    pop = -3 if age < STEP else (-1 if age < 2 * STEP else 0)
    tw = text_w(s, 1)
    w, h = tw + 12, 15
    x, y = cx - w // 2, by - h - 8 + pop
    m = np.zeros((h + 10, w + 8), bool)
    m[5:5 + h, 4:4 + w] = True
    d = disc_mask(4)
    for bx in range(8, w + 1, 8):
        m[1:10, bx - 4:bx + 5] |= d
    paint(img, dilate(m), x - 5, y - 6, "K")
    paint(img, m, x - 4, y - 5, "W")
    for i, (dx, dy, r) in enumerate([(-6, 7, 2), (-10, 12, 1)]):
        disc(img, cx + dx, by + dy - 8 + pop, r, "W", outline="K")
    text(img, s, cx, y + 4, 1, c, outline=None)


def stamp_img(s):
    """Tampon incliné (RGBA PIL) avec texture d'encre."""
    m = text_mask(s, 2)
    h, w = m.shape
    pad = 5
    H, Wd = h + 2 * pad, w + 2 * pad
    a = np.zeros((H, Wd), bool)
    a[0:2, :], a[-2:, :], a[:, 0:2], a[:, -2:] = True, True, True, True
    a[pad:pad + h, pad:pad + w] |= m
    rng = np.random.default_rng(len(s))
    a &= rng.random(a.shape) > 0.12
    rgba = np.zeros((H, Wd, 4), np.uint8)
    rgba[a] = (*PAL["R"], 255)
    im = Image.fromarray(rgba, "RGBA").rotate(9, resample=Image.NEAREST, expand=True)
    return im


def counter_str(arg, frac):
    pre = re.match(r"^\D*", arg).group(0)
    num = int(re.sub(r"\D", "", arg))
    v = int(num * min(1.0, frac))
    return pre + f"{v:,}".replace(",", ".")


# ---------------------------------------------------------------- scènes
# textes dessinés dans les scènes ; le script peut les remplacer avec un dict TXT
T = {
    "title": ("LA COPA", "ROBADA"), "sub": "HISTORIA REAL EN PIXEL ART", "woof": "¡GUAU!",
    "month": "JULIO", "cup": "MUNDIAL", "note": ("£15.000", "O LA COPA", "SE FUNDE"), "trace": "¿Y LA COPA?",
    "final": "FINAL", "q": ("¿CONOCÍAS", "ESTA HISTORIA?"), "cta": ("DÍMELO EN LOS", "COMENTARIOS"),
    "follow": "SÍGUEME",
}


class S:
    """Contexte de scène : temps local (par à-coups), événements, aléatoire."""

    def __init__(self, t, seg):
        self.t = t
        self.T = t - seg["t0"]
        self.lt = math.floor(self.T / STEP) * STEP
        self.seg = seg
        self.k = int(self.T / STEP)

    def ev(self, name):
        te = self.seg["ev"].get(name)
        if te is None or self.t < te:
            return None
        return math.floor((self.t - te) / STEP) * STEP


def pop_y(age):
    if age is None:
        return None
    return -4 if age < STEP else (-1 if age < 2 * STEP else 0)


def sparkle(img, x, y, k, c="W"):
    r = [1, 2, 3, 2][k % 4]
    line(img, x - r, y, x + r, y, c)
    line(img, x, y - r, x, y + r, c)


def floor_line(img, y, c="D"):
    rect(img, 0, y, CW, 1, c)
    dither(img, 0, y + 1, CW, 6, c, 0.35)


def sc_hook(img, s):
    halo(img, 135, 250, 105, 1.0 + 0.06 * (s.k % 3 == 0))
    text(img, T["title"][0], 135, 70, 4, "A", shadow="D")
    text(img, T["title"][1], 135, 116, 4, "A", shadow="D")
    text(img, T["sub"], 135, 154, 1, "W")
    steal, dog = s.ev("steal"), s.ev("dog")
    by = 300
    if steal is not None and dog is None:
        p = min(1.0, steal / 0.6)
        ghost(img, TROPHY, 135, by, 3, "G")
        blitc(img, TROPHY, 135, by, 3, keep=dissolve_keep(TROPHY, p))
    else:
        blitc(img, TROPHY, 135, by, 3)
        sparkle(img, 120 + (s.k // 6 % 3) * 12, 225 + (s.k // 6 % 2) * 20, s.k)
    if dog is not None:
        blitc(img, DOG[s.k // 3 % 2 if dog < 0.6 else 0], 200, by + pop_y(dog), 2, flip=True)
        bubble(img, T["woof"], 214, by - 30, dog)
    floor_line(img, by)


def sc_londres(img, s):
    halo(img, 135, 205, 120, 0.9)
    disc(img, 214, 112, 10, "W")
    disc(img, 210, 110, 2, "H")
    disc(img, 218, 116, 1, "H")
    # parlement
    for x0, x1, top in [(8, 116, 238), (154, 262, 246)]:
        rect(img, x0, top, x1 - x0, 300 - top, "D")
        for x in range(x0 + 2, x1 - 4, 12):
            line(img, x, top, x + 4, top - 8, "D")
            line(img, x + 4, top - 8, x + 8, top, "D")
            rect(img, x + 2, top - 4, 5, 4, "D")
        for wy in range(top + 8, 292, 12):
            for wx in range(x0 + 5, x1 - 5, 8):
                lit = (NOISE[wy, wx] + 0.08 * ((s.k + wx) % 7 == 0)) > 0.45
                rect(img, wx, wy, 3, 5, "A" if lit else "K")
    # Big Ben
    rect(img, 120, 182, 30, 118, "K")
    rect(img, 121, 182, 28, 118, "a")
    for x in range(124, 148, 4):
        rect(img, x, 186, 1, 112, "D")
    rect(img, 116, 148, 38, 36, "K")
    rect(img, 117, 149, 36, 34, "a")
    disc(img, 135, 166, 12, "A", outline="K")
    disc(img, 135, 166, 10, "L")
    ang = s.lt * 0.6
    line(img, 135, 166, 135 + 8 * math.sin(ang), 166 - 8 * math.cos(ang), "K")
    line(img, 135, 166, 135 + 5 * math.sin(ang / 12 + 2), 166 - 5 * math.cos(ang / 12 + 2), "K")
    rect(img, 119, 126, 32, 23, "K")
    rect(img, 120, 127, 30, 21, "a")
    for x in range(123, 148, 7):
        rect(img, x, 131, 4, 12, "D")
    for y in range(126, 88, -1):
        hw = int((y - 88) * 16 / 38)
        rect(img, 135 - hw - 1, y, 2 * hw + 2, 1, "K")
        rect(img, 135 - hw, y, 2 * hw, 1, "a" if y % 6 else "D")
    rect(img, 134, 80, 2, 9, "A")
    # niebla y río
    for i, y in enumerate(range(282, 300, 3)):
        dither(img, 0, y, CW, 3, "g", 0.12 + 0.05 * math.sin(s.lt * 2 + i))
    rect(img, 0, 300, CW, 40, "B")
    for i in range(18):
        x = (i * 37 + s.k * 3) % (CW + 20) - 10
        y = 304 + (i * 7) % 30
        rect(img, x, y, 6 + i % 4 * 3, 1, "a" if i % 3 else "A")
    cal = s.ev("cal")
    if cal is not None:
        y = 96 + pop_y(cal)
        box(img, 22, y, 50, 54, "W")
        rect(img, 23, y + 1, 48, 13, "R")
        text(img, T["month"], 47, y + 4, 1, "W", outline=None)
        text(img, "11", 47, y + 21, 3, "K", outline=None)
        text(img, T["cup"], 47, y + 60, 1, "A")


def _stamp_small(img, x, y, w, h, fill, k):
    rect(img, x, y, w, h, "W")
    for i in range(x + 1, x + w, 3):
        img[y, i] = img[y + h - 1, i] = col("B")
    for j in range(y + 1, y + h, 3):
        img[j, x] = img[j, x + w - 1] = col("B")
    rect(img, x + 3, y + 3, w - 6, h - 6, fill)
    cx, cy = x + w // 2, y + h // 2 - 2
    r = max(2, w // 6)
    disc(img, cx, cy, r, "L" if fill != "L" else "a")
    rect(img, cx - r, cy + r, 2 * r + 1, max(2, r), "L" if fill != "L" else "a")


def sc_vitrina(img, s):
    empty = s.ev("empty")
    alarm = empty is not None and (s.k // 2) % 2 == 0
    rect(img, 0, 110, CW, 190, (14, 8, 2))
    for x in range(0, CW, 10):
        rect(img, x, 110, 1, 190, (20, 12, 3))
    halo(img, 135, 215, 95, 1.0, red=alarm)
    st = s.ev("stamps")
    if st is not None:
        fills = ["a", "r", "g", "D", "A", "G"]
        i = 0
        for xs in (18, 54, 186, 222):
            for ys in (140, 186, 232):
                if st >= i * 0.06:
                    _stamp_small(img, xs, ys, 30, 36, fills[i % 6], s.k)
                i += 1
    # suelo
    rect(img, 0, 300, CW, 60, (14, 8, 2))
    floor_line(img, 300, "D")
    # pedestal
    box(img, 102, 262, 66, 40, "a")
    rect(img, 108, 268, 54, 28, "D")
    rect(img, 100, 258, 70, 5, "K")
    rect(img, 101, 259, 68, 3, "A")
    # trofeo / vacío
    if empty is None:
        blitc(img, TROPHY, 135, 256, 2)
    else:
        ghost(img, TROPHY, 135, 256, 2, "R" if alarm else "G")
    # vitrina de cristal
    gx0, gy0, gx1, gy1 = 106, 170, 164, 258
    dither(img, gx0, gy0, gx1 - gx0, gy1 - gy0, "g", 0.08)
    for x in (gx0, gx1):
        rect(img, x, gy0, 1, gy1 - gy0, "H")
    rect(img, gx0, gy0, gx1 - gx0 + 1, 3, "G")
    gl = (s.k * 4) % 140
    if gl < 70:
        line(img, gx0 + 4 + gl // 2, gy0 + 6, gx0 + gl // 2 - 10, gy0 + 30, "W")
    if empty is not None:
        line(img, gx1, gy0, gx1 + 14, gy0 + 8, "H")
        rect(img, gx1, gy0 + 3, 1, gy1 - gy0 - 3, (5, 3, 0))
        disc(img, 135, gy0 - 6, 4, "R" if alarm else "r", outline="K")
        if alarm:
            for a in range(0, 360, 45):
                r = math.radians(a + s.k * 10)
                line(img, 135 + 7 * math.cos(r), gy0 - 6 + 7 * math.sin(r),
                      135 + 12 * math.cos(r), gy0 - 6 + 12 * math.sin(r), "R")


def sc_sellos(img, s):
    halo(img, 135, 225, 120, 0.9, red=s.k % 4 == 0 and s.T < 1.2)
    fills = ["a", "r", "g", "D", "A", "G"]
    vals = ["1D", "3D", "6D", "1/-", "2/6", "5/-"]
    only = s.ev("only")
    for i in range(6):
        r, c = divmod(i, 3)
        x, y = 37 + c * 68, 152 + r * 78
        if s.T < i * 0.12:
            continue
        _stamp_small(img, x, y, 58, 70, fills[i], s.k)
        text(img, vals[i], x + 14, y + 56, 1, "W", outline="K")
        if only is not None:
            dither(img, x, y, 58, 70, "B", 0.6)
    if only is not None:
        ghost(img, TROPHY, 135, 262 + pop_y(only), 3, "L" if s.k % 2 else "A")


def sc_policia(img, s):
    rect(img, 0, 140, CW, 160, (14, 8, 2))
    bx = min(150, 50 + 4 * s.k // 2)
    tx, ty = bx + 16, 258
    ang = math.radians(-8 + 14 * math.sin(s.lt * 1.3))
    # ladrillos iluminados por la linterna
    dx, dy = XX[140:300] - tx, YY[140:300] - ty
    a = np.arctan2(dy, dx) - ang
    dist = np.hypot(dx, dy)
    beam = np.clip(1 - np.abs(a) / 0.35, 0, 1) * np.clip(1 - dist / 170, 0, 1) * (dx > 0)
    lamp = np.clip(1 - np.hypot(XX[140:300] - 30, YY[140:300] - 170) / 70, 0, 1)
    light = np.maximum(beam * 1.2, lamp * 0.9) + 0.08
    yy, xx = YY[140:300], XX[140:300]
    mortar = (yy % 8 == 0) | (((xx + 8 * ((yy // 8) % 2)) % 16) == 0)
    reg = img[140:300]
    lit = light > BAYER[140:300]
    reg[lit & ~mortar] = C["D"]
    reg[lit & mortar] = C["K"]
    reg[(light > 0.7 + BAYER[140:300] * 0.3) & ~mortar] = C["a"]
    # farola
    rect(img, 29, 160, 3, 140, "g")
    rect(img, 23, 154, 15, 8, "K")
    rect(img, 25, 156, 11, 5, "L")
    floor_line(img, 300, "g")
    walk = s.k // 2 % 2 if bx < 150 else 0
    blitc(img, BOBBY[walk], bx, 300, 2)
    # linterna
    rect(img, tx - 2, ty - 2, 6, 4, "G")
    # tache de lumière au bout du faisceau
    lx, ly = tx + 60 * math.cos(ang), ty + 60 * math.sin(ang)
    disc(img, lx, ly, 9, "K")
    disc(img, lx, ly, 7, "L" if s.k % 2 else "A")
    se = s.ev("search")
    if se is not None:
        for i, (qx, qy) in enumerate([(70, 168), (200, 160), (232, 222)]):
            if se >= i * 0.25:
                bubble(img, "?", qx, qy, se - i * 0.25)
    no = s.ev("none")
    if no is not None:
        bubble(img, "???", bx, 236, no)


def sc_nota(img, s):
    note = s.ev("note")
    red = note is not None and s.k % 4 < 2 and s.T < 6
    halo(img, 135, 220, 125, 1.0, red=red)
    if note is None:
        # enveloppe qui arrive par à-coups
        y = min(196, 120 + 12 * s.k)
        box(img, 95, y, 80, 50, "W")
        line(img, 96, y + 1, 135, y + 26, "G")
        line(img, 174, y + 1, 135, y + 26, "G")
        rect(img, 130, y + 22, 11, 9, "R")
        return
    y0 = 138 + pop_y(note)
    box(img, 62, y0, 146, 158, "W")
    rect(img, 206, y0 + 2, 2, 156, "H")
    rect(img, 64, y0 + 156, 144, 2, "H")
    dither(img, 63, y0 + 78, 144, 1, "H", 0.7)
    lines = T["note"]
    fills = ["A", "H", "g", "L", "R", "a"]
    n = int(note / 0.05)
    i = 0
    rng = np.random.default_rng(9)
    for li, ln in enumerate(lines):
        x = 135 - len(ln) * 13 // 2
        for ch in ln:
            jit = int(rng.integers(-2, 3))
            f = fills[int(rng.integers(0, len(fills)))]
            if ch != " " and i < n:
                box(img, x, y0 + 16 + li * 44 + jit, 12, 20, f)
                fg = "W" if f in ("g", "R", "a") else "K"
                text(img, ch, x + 6, y0 + 20 + li * 44 + jit, 2, fg, outline=None)
            x += 13
            i += 1
    tr = s.ev("trace")
    if tr is not None:
        bubble(img, T["trace"], 135, y0 - 2, tr)


def _house(img, x, w, h, k, smoke=True):
    top = 290 - h
    rect(img, x, top, w, h, "D")
    rh = w // 3
    for j in range(rh):
        inset = (rh - j) * (w // 2) // rh
        rect(img, x + inset, top - rh + j, w - 2 * inset, 1, "D")
    rect(img, x + w - 12, top - 16, 6, 14, "D")
    if smoke:
        for j in range(3):
            yy = top - 20 - ((k + j * 4) % 12) * 3
            disc(img, x + w - 9 + (j % 2) * 2, yy, 2 + j % 2, "g")
    for wx in range(x + 5, x + w - 6, 12):
        for wy in range(top + 8, 282, 14):
            rect(img, wx, wy, 5, 7, "A" if NOISE[wy, wx % CW] > 0.35 else "K")


def sc_paseo(img, s):
    halo(img, 135, 235, 135, 0.8)
    off = (s.k * 2) % 300
    for i, (w, h) in enumerate([(60, 70), (50, 55), (70, 80), (56, 64), (64, 72)]):
        x = (i * 75 - off) % 375 - 60
        _house(img, x, w, h, s.k)
    rect(img, 0, 290, CW, 10, (14, 8, 2))
    floor_line(img, 300, "g")
    for i in range(3):
        x = (i * 130 - s.k * 5) % 390 - 40
        rect(img, x, 200, 3, 100, "g")
        rect(img, x - 5, 194, 13, 7, "K")
        rect(img, x - 3, 196, 9, 4, "L")
        halo(img, x + 1, 210, 22, 0.35)
    f = s.k // 2 % 2
    blitc(img, MAN[f], 105, 300, 2)
    blitc(img, DOG[1 - f], 165, 300, 2)
    line(img, 117, 268, 166, 284, "a")
    nm = s.ev("name")
    if nm is not None:
        bubble(img, "PICKLES", 175, 266, nm, c="R")


def sc_seto(img, s):
    open_ = s.ev("open")
    halo(img, 165, 250, 120, 1.2 if open_ is not None else 0.9)
    # seto
    m = np.zeros((CH, CW), bool)
    for cx, cy, r in [(170, 270, 24), (200, 256, 30), (238, 262, 30), (262, 250, 26), (186, 288, 18), (226, 290, 20)]:
        m |= (XX - cx) ** 2 + (YY - cy) ** 2 <= r * r
    m &= YY < 300
    edge = dilate(m)[1:-1, 1:-1] & ~m
    img[edge] = C["K"]
    img[m] = C["D"]
    img[m & (NOISE > 0.72)] = C["a"]
    img[m & (NOISE < 0.06)] = C["K"]
    floor_line(img, 300, "g")
    blitc(img, MAN[0], 70, 300, 2)
    sn = s.ev("sniff")
    blitc(img, DOG_SNIFF if sn is not None and open_ is None else DOG[0], 128, 300, 2)
    if sn is not None and open_ is None:
        bubble(img, "!", 150, 268, sn, c="R")
    pa = s.ev("parcel")
    if pa is not None and open_ is None:
        halo(img, 176, 294, 18, 0.5 + 0.2 * (s.k % 2))
        blitc(img, PARCEL, 176, 300, 2)
        sparkle(img, 168 + (s.k % 3) * 8, 280, s.k)
    if open_ is not None:
        for i in range(12):
            a = math.radians(i * 30 + s.k * 6)
            line(img, 176 + 22 * math.cos(a), 250 + 22 * math.sin(a),
                 176 + 60 * math.cos(a), 250 + 60 * math.sin(a), "a" if i % 2 else "A", dashed=True)
        rect(img, 150, 296, 52, 4, "H")
        rect(img, 150, 299, 52, 1, "K")
        rise = min(1.0, open_ / 0.6)
        blitc(img, TROPHY, 176, int(300 - 24 * rise), 2)
        for i in range(3):
            sparkle(img, 160 + i * 16, 210 + ((s.k + i * 3) % 6) * 4, s.k + i)


def sc_wembley(img, s):
    halo(img, 135, 230, 135, 1.0)
    rng = np.random.default_rng(s.k // 2)
    for i in range(3):
        if (s.k // 4 + i) % 3 == 0:
            fx, fy = int(rng.integers(30, 240)), int(rng.integers(90, 170))
            for a in range(0, 360, 30):
                r = math.radians(a)
                d = 6 + (s.k % 4) * 3
                rect(img, fx + d * math.cos(r), fy + d * math.sin(r), 2, 2, "ARWL"[i % 4])
    rect(img, 22, 222, 226, 78, "K")
    rect(img, 23, 223, 224, 77, "G")
    for x in range(30, 240, 14):
        rect(img, x, 236, 8, 30, "g")
        disc(img, x + 4, 236, 4, "g")
    rect(img, 23, 280, 224, 20, "H")
    for tx in (66, 204):
        rect(img, tx - 18, 166, 36, 120, "K")
        rect(img, tx - 17, 167, 34, 119, "W")
        rect(img, tx + 6, 167, 11, 119, "H")
        disc(img, tx, 166, 16, "W", outline="K")
        rect(img, tx - 17, 166, 34, 17, "W")
        rect(img, tx - 10, 190, 6, 14, "g")
        rect(img, tx + 2, 190, 6, 14, "g")
        rect(img, tx, 132, 1, 20, "K")
        fl = s.k // 2 % 2
        rect(img, tx + 1, 133, 12, 7 - fl, "R")
        rect(img, tx + 1, 133 + 6 - fl, 6 + 4 * fl, 1, "r")
    sc = s.ev("score")
    if sc is not None:
        y = 98 + pop_y(sc)
        box(img, 88, y, 94, 40, "B", line="A")
        text(img, T["final"], 135, y + 4, 1, "W", outline=None)
        if s.k % 4 or sc > 1:
            text(img, "4-2", 135, y + 16, 3, "L", outline=None)
        rng2 = np.random.default_rng(1)
        for i in range(70):
            x = int(rng2.integers(0, CW))
            y0 = int(rng2.integers(-200, 0))
            yy = y0 + int(sc / STEP) * (3 + i % 3)
            if 0 <= yy < 340:
                x2 = x + int(3 * math.sin(yy / 12 + i))
                rect(img, x2, yy % 340, 2, 2 + (i + s.k) % 2, "ARWL"[i % 4])


def sc_banquete(img, s):
    rect(img, 0, 120, CW, 180, (14, 8, 2))
    for x in range(10, CW, 64):
        box(img, x, 140, 44, 54, (20, 12, 3), line="D")
    halo(img, 135, 232, 120, 1.0)
    # lámpara
    line(img, 135, 100, 135, 128, "g")
    rect(img, 105, 128, 61, 3, "A")
    for x in range(108, 166, 14):
        rect(img, x, 122, 2, 6, "W")
        rect(img, x, 119 - (s.k + x) % 2, 2, 3, "L")
    # perro sentado detrás de la mesa
    wo = s.ev("woof")
    blitc(img, DOG[0], 135, 272, 3)
    rect(img, 137, 245, 5, 6, "R")
    rect(img, 147, 245, 5, 6, "R")
    rect(img, 142, 246, 5, 4, "r")
    # mesa
    rect(img, 10, 262, 250, 3, "K")
    rect(img, 10, 265, 250, 8, "W")
    rect(img, 10, 273, 250, 22, "H")
    for x in range(14, 258, 12):
        rect(img, x, 273, 1, 22, "G")
    rect(img, 10, 295, 250, 2, "K")
    for px in (50, 220):
        rect(img, px - 12, 259, 24, 4, "H")
        rect(img, px - 9, 258, 18, 1, "W")
    blitc(img, BONE, 220, 260, 2)
    for cx in (80, 190):
        rect(img, cx - 1, 238, 4, 24, "W")
        rect(img, cx, 232 - (s.k % 2), 2, 5, "L")
        rect(img, cx, 231 - (s.k % 2), 2, 2, "A")
        halo(img, cx + 1, 234, 14, 0.4)
    if wo is not None:
        bubble(img, T["woof"], 168, 226, wo)
    floor_line(img, 300, "D")


def sc_rio(img, s):
    gone = s.ev("gone")
    dim = 1.0 if gone is None else max(0.45, 1 - gone / 3)
    halo(img, 135, 250, 105, dim)
    # Pan de Azúcar
    for cx, r, h in [(40, 40, 70), (230, 55, 100), (190, 30, 60)]:
        m = ((XX - cx) / r) ** 2 + ((YY - 300) / h) ** 2 <= 1
        m &= YY < 300
        img[m] = C["D"]
        img[m & (BAYER < 0.15)] = C["K"]
    line(img, 40, 230, 230, 200, "g", dashed=True)
    by = 300
    if gone is None:
        blitc(img, TROPHY, 135, by, 3)
        sparkle(img, 120 + (s.k // 6 % 3) * 12, 225 + (s.k // 6 % 2) * 20, s.k)
    else:
        p = min(1.0, gone / 1.4)
        ghost(img, TROPHY, 135, by, 3, "G")
        blitc(img, TROPHY, 135, by, 3, keep=dissolve_keep(TROPHY, p))
    floor_line(img, by)


def sc_outro(img, s):
    halo(img, 135, 240, 110, 0.8)
    q, cta = s.ev("q"), s.ev("cta")
    if s.k % 4 < 3:
        ghost(img, TROPHY, 135, 296, 2, "A")
    if q is not None:
        text(img, T["q"][0], 135, 92 + pop_y(q), 3, "A", shadow="D")
        text(img, T["q"][1], 135, 124 + pop_y(q), 3, "A", shadow="D")
    if cta is not None:
        text(img, T["cta"][0], 135, 166, 2, "W")
        text(img, T["cta"][1], 135, 186, 2, "W")
        if cta > 0.6:
            y = 314 + pop_y(cta - 0.6)
            box(img, 70, y, 130, 28, "R" if s.k % 6 < 5 else "r")
            text(img, T["follow"], 135, y + 9, 2, "W", outline=None)


SCENES = {k[3:]: v for k, v in globals().items() if k.startswith("sc_")}
ZOOM_C = {"policia": (135, 240), "nota": (135, 210), "seto": (160, 260), "wembley": (135, 200)}
STAMP_POS = {"hook": (135, 196), "vitrina": (135, 214), "nota": (135, 230), "seto": (135, 158),
             "banquete": (135, 176), "rio": (135, 214)}


# ---------------------------------------------------------------- timeline
CMD_RE = re.compile(r"\{([^}:]+)(?::([^}]*))?\}")


def parse_line(txt):
    """-> mots {text, spoken, key, cmds}. Une commande isolée s'applique au mot suivant."""
    words, pending = [], []
    for tok in txt.split():
        cmds = [(c, a.replace("_", " ")) for c, a in CMD_RE.findall(tok)]
        tok = CMD_RE.sub("", tok)
        if not tok:
            pending += cmds
            continue
        key = "*" in tok
        tok = tok.replace("*", "")
        if "=" in tok:
            disp, spoken = tok.split("=", 1)
            punct = re.search(r"[,.:;?!]+$", spoken)
            if punct and not re.search(r"[,.:;?!]+$", disp):
                disp += punct.group(0)
            spoken = spoken.replace("-", " ")
        else:
            disp = spoken = tok
        words.append(dict(text=disp, spoken=spoken, key=key, cmds=pending + cmds))
        pending = []
    if pending and words:
        words[-1]["late"] = pending   # commandes en fin de phrase : jouées à la fin du dernier mot
    return words


def tts_lines(G, lines, cache_dir, model_dir):
    os.makedirs(cache_dir, exist_ok=True)
    tts, out = None, []
    for words in lines:
        txt = " ".join(w["spoken"] for w in words)
        lang = getattr(G, "LANG", "es")
        h = hashlib.md5(f"{lang}|{G.VOICE}|{G.SPEED}|{txt}".encode()).hexdigest()[:12]
        path = os.path.join(cache_dir, f"{h}.wav")
        if not os.path.exists(path):
            if tts is None:
                tts = audio.load_tts(model_dir)
            sf.write(path, audio.synth_line(tts, txt, G.VOICE, G.SPEED, lang), audio.SR)
            print(f"  voix : {txt}", flush=True)
        out.append(sf.read(path)[0])
    return out


def build(G, cache_dir, model_dir):
    parsed = [(sc, parse_line(txt)) for sc, txt in G.LINES]
    clips = tts_lines(G, [w for _, w in parsed], cache_dir, model_dir)
    segs, starts, sfx = [], [], []
    t, prev = 0.4, None
    for (sc, words), clip in zip(parsed, clips):
        if sc != prev:
            if prev is not None:
                t += 0.45
            segs.append(dict(name=sc, t0=0.0 if prev is None else t - 0.35, ev={}, stamps=[], counts=[],
                             labels=[]))
            if prev is not None:
                sfx.append((t - 0.35, "sweep", 0.8))
            prev = sc
        seg = segs[-1]
        starts.append(t)
        for w, (a, b) in zip(words, audio.word_times([w["spoken"] for w in words], clip)):
            w["t0"], w["t1"] = t + a, t + b
            for cmd, arg, te in [(c, x, w["t0"] - 0.04) for c, x in w["cmds"]] + \
                    [(c, x, w["t1"]) for c, x in w.get("late", [])]:
                if cmd == "ev":
                    seg["ev"][arg] = te
                    if arg in G.EV_SFX:
                        sfx.append((te, G.EV_SFX[arg], 1.0))
                elif cmd == "stamp":
                    seg["stamps"].append((te, arg))
                    sfx.append((te, "thud", 1.0))
                elif cmd == "count":
                    seg["counts"].append((te, arg))
                    for i in range(8):
                        sfx.append((te + i * 0.1, "tick", 1.0))
                    sfx.append((te + 0.85, "coin", 1.0))
                elif cmd == "label":
                    seg["labels"].append((te, arg))
                    sfx.append((te, "blip", 0.7))
                elif cmd == "sfx":
                    sfx.append((te, arg, 1.0))
        t += len(clip) / audio.SR + 0.15
    duration = t + 1.6
    for i, s in enumerate(segs):
        s["t1"] = segs[i + 1]["t0"] if i + 1 < len(segs) else duration
        s["i"] = i

    voice = np.zeros(int(duration * audio.SR) + audio.SR)
    for st, clip in zip(starts, clips):
        i = int(st * audio.SR)
        voice[i:i + len(clip)] += clip

    caps = []
    if G.SUBTITLES:
        for sc, words in parsed:
            if sc == "outro":
                continue
            cur = []
            for w in words:
                cur.append(w)
                if len(cur) >= 3 or re.search(r"[,.:;?!]$", w["text"]) or \
                        len(" ".join(x["text"] for x in cur)) > 15:
                    caps.append(cur)
                    cur = []
            if cur:
                caps.append(cur)
        for i, c in enumerate(caps):
            nxt = caps[i + 1][0]["t0"] if i + 1 < len(caps) else duration
            caps[i] = dict(t0=c[0]["t0"] - 0.04, t1=min(nxt - 0.04, c[-1]["t1"] + 0.5), words=c)

    secs = [(s["t0"], s["t1"], G.LEVELS.get(s["name"], 0.5)) for s in segs]
    music = chiptune.make_music(duration, secs)
    mix = chiptune.mix_all(voice, music, sfx, duration)
    return dict(segs=segs, caps=caps, duration=duration, brand=G.BRAND), mix


# ---------------------------------------------------------------- rendu
def render_scene(seg, t):
    img = np.empty((CH, CW, 3), np.uint8)
    img[:] = C["B"]
    s = S(t, seg)
    SCENES[seg["name"]](img, s)
    # zoom lent par à-coups + « punch » et tremblement sur les tampons
    z = 1 + min(0.1, 0.015 * math.floor(s.T / 0.75))
    dx = dy = 0
    for te, _ in seg["stamps"]:
        a = t - te
        if 0 <= a < 0.3:
            z += 0.05
            r = np.random.default_rng(int(t * FPS))
            dx, dy = int(r.integers(-3, 4)), int(r.integers(-3, 4))
    if z > 1.0001 or dx or dy:
        zx, zy = ZOOM_C.get(seg["name"], (135, 230))
        xs = np.clip(((np.arange(CW) - zx) / z + zx + dx).astype(int), 0, CW - 1)
        ys = np.clip(((np.arange(CH) - zy) / z + zy + dy).astype(int), 0, CH - 1)
        img = img[ys][:, xs]
    return img


def overlays(img, seg, t, data):
    for te, s in seg["labels"]:
        a = t - te
        if a < 0:
            continue
        sc = 2 if text_w(s, 2) <= 250 else 1
        n = int(a * 22)
        text(img, s, 135, 56, sc, "A", n=n)
        w = text_w(s, sc)
        uw = min(w, int(a * 22 * 6 * sc))
        rect(img, 135 - w // 2, 56 + 7 * sc + 3, uw, 1, "a")
        if n < len(s) and int(t * 8) % 2:
            rect(img, 135 - w // 2 + text_w(s[:n], sc) + 2, 56, 2 * sc, 7 * sc, "A")
    for te, arg in seg["counts"]:
        a = t - te
        if a >= 0:
            frac = math.floor(min(1, a / 0.85) * 12) / 12
            text(img, counter_str(arg, frac), 135, 96, 3, "L", shadow="a")
    for te, s in seg["stamps"]:
        a = t - te
        if a < 0:
            continue
        im = stamp_img(s)
        k = 1.8 if a < 0.05 else (1.3 if a < 0.1 else 1.0)
        if k != 1.0:
            im = im.resize((int(im.width * k), int(im.height * k)), Image.NEAREST)
        cx, cy = STAMP_POS.get(seg["name"], (135, 230))
        arr = np.asarray(im)
        paint_rgba(img, arr, cx - arr.shape[1] // 2, cy - arr.shape[0] // 2)
    if seg["name"] in ("hook", "outro"):
        text(img, data["brand"], 135, 34, 1, "G", outline=None)


def paint_rgba(img, arr, x, y):
    m = arr[..., 3] > 0
    h, w = m.shape
    x0, y0, x1, y1 = max(0, x), max(0, y), min(CW, x + w), min(CH, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    sub = m[y0 - y:y1 - y, x0 - x:x1 - x]
    img[y0:y1, x0:x1][sub] = arr[y0 - y:y1 - y, x0 - x:x1 - x, :3][sub]


def captions(img, data, t):
    for c in data["caps"]:
        if c["t0"] <= t < c["t1"]:
            ws = [w for w in c["words"] if w["t0"] - 0.04 <= t]
            full = " ".join(w["text"] for w in c["words"])
            sc = 2 if text_w(full, 2) <= 256 else 1
            x = 135 - text_w(full, sc) // 2
            for w in ws:
                text(img, w["text"], x, 350, sc, "A" if w["key"] else "W", align="left")
                x += text_w(w["text"] + " ", sc) + (3 if sc == 1 else 0)
            return


def frame(data, t):
    segs = data["segs"]
    seg = next((s for s in segs if s["t0"] <= t < s["t1"]), segs[-1])
    img = render_scene(seg, t)
    a = t - seg["t0"]
    if seg["i"] > 0 and a < TRANS:
        old = render_scene(segs[seg["i"] - 1], t)
        overlays(old, segs[seg["i"] - 1], t, data)
        p = math.floor(a / TRANS * 10) / 10
        if seg["i"] % 2:
            keep_old = BLOCKS >= p
        else:
            keep_old = YY >= p * CH
            edge = (YY >= p * CH) & (YY < p * CH + 3)
            old[edge] = C["A"]
        img[keep_old] = old[keep_old]
    if a >= TRANS or seg["i"] == 0:
        overlays(img, seg, t, data)
    captions(img, data, t)
    return img


# ---------------------------------------------------------------- sortie
_DATA = None


def _render_range(args):
    i0, i1, path = args
    ff = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{CW}x{CH}",
         "-r", str(FPS), "-i", "-", "-vf", f"scale={CW * SCALE}:{CH * SCALE}:flags=neighbor",
         "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", path],
        stdin=subprocess.PIPE)
    for i in range(i0, i1):
        ff.stdin.write(frame(_DATA, i / FPS).tobytes())
    ff.stdin.close()
    ff.wait()
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", default="historia_copa_es")
    ap.add_argument("--out", default=None, help="défaut : output/<OUT du script>")
    ap.add_argument("--models", default=os.environ.get("MODELS_DIR", os.path.join(HERE, "models")))
    ap.add_argument("--build", default=os.path.join(HERE, "build"))
    ap.add_argument("--stills", default="", help="temps (s) séparés par des virgules : n'exporte que ces images")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()

    G = importlib.import_module(a.script)
    T.update(getattr(G, "TXT", {}))
    a.out = a.out or os.path.join(HERE, "..", "output", getattr(G, "OUT", f"pixel_story_{a.script}.mp4"))
    os.makedirs(a.build, exist_ok=True)
    print("1/3 voix + timeline…", flush=True)
    data, mix = build(G, os.path.join(a.build, "tts_cache"), a.models)
    print(f"   durée : {data['duration']:.1f}s", flush=True)
    for s in data["segs"]:
        print(f"   {s['t0']:6.2f}  {s['name']}")

    if a.stills:
        for ts in a.stills.split(","):
            img = Image.fromarray(frame(data, float(ts))).resize((CW * SCALE, CH * SCALE), Image.NEAREST)
            img.save(os.path.join(a.build, f"pixel_{float(ts):05.1f}.png"))
        print("images exportées dans", a.build)
        return

    wav = os.path.join(a.build, "pixel_mix.wav")
    sf.write(wav, np.stack([mix, mix], 1).astype(np.float32), audio.SR)
    print("2/3 rendu des images…", flush=True)
    global _DATA
    _DATA = data
    n = int(data["duration"] * FPS)
    k = a.workers
    bounds = [round(n * i / k) for i in range(k + 1)]
    jobs = [(bounds[i], bounds[i + 1], os.path.join(a.build, f"pxpart{i}.mp4")) for i in range(k)]
    with mp.get_context("fork").Pool(k) as pool:
        parts = pool.map(_render_range, jobs)
    lst = os.path.join(a.build, "pxparts.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
    print("3/3 assemblage…", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", a.out], check=True)
    print("OK ->", os.path.abspath(a.out))


if __name__ == "__main__":
    main()
