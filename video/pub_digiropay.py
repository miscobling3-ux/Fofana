"""Pub verticale Digiropay (FR) : aplats de couleur, cartes flottantes, téléphone, sous-titres mot par mot.

python3 pub_digiropay.py                 -> ../output/digiropay_pub_fr.mp4
python3 pub_digiropay.py --stills 1,6,12  -> aperçus PNG dans build/digiropay/
"""
import argparse
import hashlib
import math
import os
import re
import subprocess

import numpy as np
import skia
import soundfile as sf

import audio

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.path.join(HERE, "models")
BUILD = os.path.join(HERE, "build", "digiropay")
W, H, FPS = 1080, 1920, 30

VOICE = "ff_siwis"
SPEED = 1.1
LANG = "fr-fr"

# couleurs (à caler sur la charte Digiropay)
BLUE = "#2563eb"
BLUE_DARK = "#1e40af"
GREEN = "#16a34a"
PINK = "#f9a8d4"
ORANGE = "#f97316"
YELLOW = "#facc15"
INK = "#0f172a"
MUTED = "#64748b"
SOFT = "#f1f5f9"
WHITE = "#ffffff"

# (texte prononcé, texte affiché, scène). « Digiro-pé » = prononciation, « Digiropay » = sous-titre.
LINES = [
    ("Tu es créateur de contenu, formateur, ou entrepreneur digital ? Ce message est pour toi !",
     "Tu es créateur de contenu, formateur ou entrepreneur digital ? Ce message est pour toi !", "hook"),
    ("Imagine vendre tes formations, tes ebooks, tes guides, et tes fichiers numériques sur Internet,",
     "Imagine vendre tes formations, tes ebooks, tes guides et tes fichiers numériques sur Internet,", "products"),
    ("directement depuis chez toi, avec ton téléphone ou ton ordinateur.",
     "directement depuis chez toi, avec ton téléphone ou ton ordinateur.", "phone"),
    ("Découvre Digiro-pé : la plateforme qui rend la vente en ligne simple et accessible.",
     "Découvre Digiropay : la plateforme qui rend la vente en ligne simple et accessible.", "brand"),
    ("Crée ton produit numérique, propose-le à tes clients, et développe ton activité.",
     "Crée ton produit numérique, propose-le à tes clients et développe ton activité.", "steps"),
    ("N'attends pas d'avoir des milliers d'abonnés pour vendre tes connaissances.",
     "N'attends pas d'avoir des milliers d'abonnés pour vendre tes connaissances.", "followers"),
    ("Ton prochain projet peut commencer depuis ta chambre. Inscris-toi sur Digiro-pé point com !",
     "Ton prochain projet peut commencer depuis ta chambre. Inscris-toi sur digiropay.com !", "outro"),
]
GAP = 0.35
OUTRO_TAIL = 2.6


# ---------------------------------------------------------------- outils de dessin
_tf = {}


def font(size, weight="ExtraBold"):
    if weight not in _tf:
        _tf[weight] = skia.Typeface.MakeFromFile(os.path.join(MODELS, "fonts", f"Montserrat-{weight}.ttf"))
    f = skia.Font(_tf[weight], size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    return f


def col(h, a=1.0):
    h = h.lstrip("#")
    return skia.Color4f(int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255, max(0.0, min(1.0, a)))


def paint(c, a=1.0, stroke=0, blur=0):
    p = skia.Paint(AntiAlias=True)
    p.setColor4f(col(c, a))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def ease_out(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def back_out(x):
    x = clamp01(x)
    return 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2


def appear(t, t0, dur=0.45):
    return back_out((t - t0) / dur)


def text(c, s, x, y, size, color=INK, weight="ExtraBold", align="center", alpha=1.0):
    f = font(size, weight)
    w = f.measureText(s)
    x0 = x - w / 2 if align == "center" else x
    c.drawString(s, x0, y + size * 0.36, f, paint(color, alpha))
    return w


def rrect(c, x, y, w, h, r, color, alpha=1.0, shadow=0.0):
    rect = skia.Rect.MakeXYWH(x, y, w, h)
    if shadow:
        c.drawRRect(skia.RRect.MakeRectXY(rect.makeOffset(0, 18), r, r), paint("#0f172a", shadow * alpha, blur=26))
    c.drawRRect(skia.RRect.MakeRectXY(rect, r, r), paint(color, alpha))


class group:
    """Bloc transformé (position, échelle, rotation, opacité)."""

    def __init__(self, c, x, y, s=1.0, rot=0.0, alpha=1.0):
        self.c, self.x, self.y, self.s, self.rot, self.alpha = c, x, y, s, rot, alpha

    def __enter__(self):
        c = self.c
        if self.alpha < 1:
            c.saveLayerAlpha(None, int(255 * clamp01(self.alpha)))
        else:
            c.save()
        c.translate(self.x, self.y)
        c.rotate(self.rot)
        c.scale(self.s, self.s)
        return c

    def __exit__(self, *a):
        self.c.restore()


def pill(c, s, x, y, size, bg, fg=WHITE, alpha=1.0, shadow=0.25, icon=None):
    f = font(size)
    tw = f.measureText(s)
    iw = size * 1.25 if icon else 0
    w, h = tw + iw + size * 1.6, size * 2.1
    rrect(c, x - w / 2, y - h / 2, w, h, h / 2, bg, alpha, shadow)
    if icon:
        icon(c, x - w / 2 + size * 0.8 + iw / 2 - size * 0.1, y, size * 0.95, fg, alpha)
    c.drawString(s, x - w / 2 + size * 0.8 + iw, y + size * 0.36, f, paint(fg, alpha))
    return w


# ---------------------------------------------------------------- icônes (traits simples)
def ic_play(c, x, y, s, color, a=1.0):
    p = skia.Path()
    p.moveTo(x - s * 0.3, y - s * 0.4)
    p.lineTo(x + s * 0.42, y)
    p.lineTo(x - s * 0.3, y + s * 0.4)
    p.close()
    c.drawPath(p, paint(color, a))


def ic_book(c, x, y, s, color, a=1.0):
    st = paint(color, a, stroke=s * 0.11)
    c.drawRoundRect(skia.Rect.MakeXYWH(x - s * 0.4, y - s * 0.45, s * 0.8, s * 0.9), s * 0.08, s * 0.08, st)
    c.drawLine(x - s * 0.18, y - s * 0.45, x - s * 0.18, y + s * 0.45, st)


def ic_doc(c, x, y, s, color, a=1.0):
    st = paint(color, a, stroke=s * 0.11)
    c.drawRoundRect(skia.Rect.MakeXYWH(x - s * 0.34, y - s * 0.45, s * 0.68, s * 0.9), s * 0.08, s * 0.08, st)
    for k in (-0.15, 0.05, 0.25):
        c.drawLine(x - s * 0.17, y + s * k, x + s * 0.17, y + s * k, st)


def ic_folder(c, x, y, s, color, a=1.0):
    p = skia.Path()
    p.moveTo(x - s * 0.45, y + s * 0.35)
    p.lineTo(x - s * 0.45, y - s * 0.35)
    p.lineTo(x - s * 0.1, y - s * 0.35)
    p.lineTo(x, y - s * 0.22)
    p.lineTo(x + s * 0.45, y - s * 0.22)
    p.lineTo(x + s * 0.45, y + s * 0.35)
    p.close()
    c.drawPath(p, paint(color, a, stroke=s * 0.11))


def ic_bulb(c, x, y, s, color, a=1.0):
    st = paint(color, a, stroke=s * 0.11)
    c.drawCircle(x, y - s * 0.1, s * 0.3, st)
    c.drawLine(x - s * 0.13, y + s * 0.32, x + s * 0.13, y + s * 0.32, st)
    c.drawLine(x - s * 0.08, y + s * 0.46, x + s * 0.08, y + s * 0.46, st)


def ic_check(c, x, y, s, color, a=1.0, progress=1.0):
    p = skia.Path()
    p.moveTo(x - s * 0.3, y)
    p.lineTo(x - s * 0.08, y + s * 0.22)
    p.lineTo(x + s * 0.32, y - s * 0.22)
    m = skia.PathMeasure(p, False)
    seg = skia.Path()
    m.getSegment(0, m.getLength() * clamp01(progress), seg, True)
    c.drawPath(seg, paint(color, a, stroke=s * 0.14))


def ic_bag(c, x, y, s, color, a=1.0):
    st = paint(color, a, stroke=s * 0.11)
    c.drawRoundRect(skia.Rect.MakeXYWH(x - s * 0.38, y - s * 0.2, s * 0.76, s * 0.62), s * 0.08, s * 0.08, st)
    c.drawArc(skia.Rect.MakeXYWH(x - s * 0.2, y - s * 0.48, s * 0.4, s * 0.5), 180, 180, False, st)


def ic_chart(c, x, y, s, color, a=1.0):
    st = paint(color, a, stroke=s * 0.12)
    p = skia.Path()
    p.moveTo(x - s * 0.42, y + s * 0.3)
    p.lineTo(x - s * 0.12, y)
    p.lineTo(x + s * 0.06, y + s * 0.15)
    p.lineTo(x + s * 0.42, y - s * 0.3)
    c.drawPath(p, st)
    c.drawLine(x + s * 0.42, y - s * 0.3, x + s * 0.18, y - s * 0.3, st)
    c.drawLine(x + s * 0.42, y - s * 0.3, x + s * 0.42, y - s * 0.06, st)


def logo(c, x, y, size, color=WHITE, mark=BLUE, alpha=1.0):
    """Logo provisoire : pastille « D » + nom."""
    f = font(size, "Black")
    tw = f.measureText("Digiropay")
    bw = size * 1.25
    total = bw + size * 0.35 + tw
    x0 = x - total / 2
    rrect(c, x0, y - bw / 2, bw, bw, bw * 0.3, color, alpha)
    text(c, "D", x0 + bw / 2, y, size * 0.85, mark, "Black", alpha=alpha)
    c.drawString("Digiropay", x0 + bw + size * 0.35, y + size * 0.36, f, paint(color, alpha))


def phone(c, cx, cy, s, screen):
    """Téléphone (390x800 à l'échelle s) ; screen(c, w, h) dessine l'écran en coordonnées locales."""
    w, h = 400, 820
    with group(c, cx, cy, s):
        rrect(c, -w / 2, -h / 2, w, h, 62, "#111827", 1, shadow=0.35)
        c.save()
        sx, sy, sw, sh = -w / 2 + 14, -h / 2 + 14, w - 28, h - 28
        c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(sx, sy, sw, sh), 50, 50), doAntiAlias=True)
        c.translate(sx, sy)
        screen(c, sw, sh)
        c.restore()
        rrect(c, -55, -h / 2 + 30, 110, 30, 15, "#111827")


def notif(c, x, y, w, title, body, icon_bg=BLUE, alpha=1.0, s=1.0):
    with group(c, x, y, s, alpha=alpha) as g:
        h = 120
        rrect(g, -w / 2, -h / 2, w, h, 30, WHITE, 1, shadow=0.22)
        rrect(g, -w / 2 + 18, -32, 64, 64, 18, icon_bg)
        text(g, "D", -w / 2 + 50, 0, 38, WHITE, "Black")
        text(g, title, -w / 2 + 100, -18, 27, INK, "ExtraBold", "left")
        text(g, body, -w / 2 + 100, 20, 23, MUTED, "SemiBold", "left")


# ---------------------------------------------------------------- scènes (t = temps local, d = durée)
def sc_hook(c, t, d):
    c.clear(col(BLUE))
    words = [("CRÉATEUR", YELLOW, INK, -6, ic_play), ("FORMATEUR", WHITE, BLUE, 5, ic_book),
             ("ENTREPRENEUR", PINK, INK, -4, ic_bulb)]
    starts = [0.15, 0.85, 1.55]
    for i, ((w, bg, fg, rot, ic), t0) in enumerate(zip(words, starts)):
        k = appear(t, t0)
        if k <= 0:
            continue
        fy = math.sin(t * 2 + i) * 8
        with group(c, W / 2 + (i - 1) * 40, 430 + i * 190 + fy, 0.4 + 0.6 * k, rot * k, alpha=clamp01(k * 2)) as g:
            pill(g, w, 0, 0, 74, bg, fg, icon=ic)
    k = appear(t, 2.6, 0.5)
    if k > 0:
        with group(c, W / 2, 1110, 0.6 + 0.4 * k, alpha=clamp01(k * 2)) as g:
            text(g, "CE MESSAGE", 0, -50, 96, WHITE, "Black")
            text(g, "EST POUR TOI !", 0, 60, 96, YELLOW, "Black")


PRODUCTS = [("Formation vidéo", "12 leçons", ic_play, BLUE), ("Ebook", "PDF · 48 pages", ic_book, ORANGE),
            ("Guide pratique", "Pas à pas", ic_doc, GREEN), ("Fichiers numériques", "Modèles, packs…", ic_folder,
                                                                                         "#a855f7")]


def product_card(c, x, y, i, alpha=1.0, s=1.0, rot=0.0):
    name, sub, ic, accent = PRODUCTS[i]
    with group(c, x, y, s, rot, alpha) as g:
        w, h = 820, 160
        rrect(g, -w / 2, -h / 2, w, h, 36, WHITE, 1, shadow=0.18)
        rrect(g, -w / 2 + 24, -45, 90, 90, 26, accent)
        ic(g, -w / 2 + 69, 0, 52, WHITE)
        text(g, name, -w / 2 + 140, -20, 36, INK, "ExtraBold", "left")
        text(g, sub, -w / 2 + 140, 26, 28, MUTED, "SemiBold", "left")
        pill(g, "En vente", w / 2 - 105, 0, 24, SOFT, accent, shadow=0)


def sc_products(c, t, d):
    c.clear(col(WHITE))
    k = appear(t, 0.0, 0.5)
    with group(c, W / 2, 330, alpha=k) as g:
        text(g, "VENDS TES", 0, -50, 88, INK, "Black")
        text(g, "CONNAISSANCES", 0, 50, 88, BLUE, "Black")
    for i in range(4):
        t0 = 0.35 + i * d / 5
        k = ease_out((t - t0) / 0.55)
        if k <= 0:
            continue
        side = -1 if i % 2 == 0 else 1
        x = W / 2 + side * (1 - k) * 1000 + side * 20
        y = 640 + i * 205 + math.sin(t * 1.8 + i) * 7
        product_card(c, x, y, i, s=1.0, rot=side * 2 * (1 - k) + side * 1.2)


def sc_phone(c, t, d):
    c.clear(col("#fdf2f8"))
    # cercles décoratifs
    c.drawCircle(160, 330, 220, paint(PINK, 0.55))
    c.drawCircle(960, 1250, 260, paint("#bfdbfe", 0.7))
    k = ease_out(t / 0.6)
    py = 1050 + (1 - k) * 900

    def screen(g, w, h):
        g.clear(col(BLUE))
        text(g, "21:30", w / 2, 120, 92, WHITE, "Bold")
        text(g, "Depuis ta chambre", w / 2, 190, 26, WHITE, "SemiBold", alpha=0.8)
        for i, (ti, bo) in enumerate([("Nouvelle vente", "Ebook acheté"),
                                      ("Nouvelle vente", "Formation achetée"),
                                      ("Paiement reçu", "Sur ton compte")]):
            kk = appear(t, 0.9 + i * 0.75, 0.4)
            if kk > 0:
                notif(g, w / 2, 300 + i * 150, w - 30, ti, bo, alpha=clamp01(kk * 2), s=0.8 + 0.2 * kk)

    phone(c, W / 2, py, 1.15, screen)
    k2 = appear(t, 0.3, 0.5)
    with group(c, W / 2, 230, alpha=clamp01(k2)) as g:
        text(g, "DEPUIS CHEZ TOI", 0, 0, 84, INK, "Black")


def sc_brand(c, t, d):
    c.clear(col(GREEN))
    k = ease_out(t / 0.5)
    with group(c, W / 2, 300, alpha=k) as g:
        logo(g, 0, 0, 96)
    k2 = appear(t, 0.35, 0.5)
    with group(c, W / 2 - 20, 520, alpha=clamp01(k2 * 2)) as g:
        text(g, "La vente en ligne,", 0, -55, 80, WHITE, "Black")
        text(g, "simple et accessible", 0, 45, 80, YELLOW, "Black")

    def screen(g, w, h):
        g.clear(col("#0b1220"))
        text(g, "Mes produits", 36, 110, 44, WHITE, "ExtraBold", "left")
        text(g, "3 en vente", 36, 160, 26, "#94a3b8", "SemiBold", "left")
        for i in range(3):
            kk = appear(t, 0.9 + i * 0.35, 0.4)
            if kk <= 0:
                continue
            name, sub, ic, accent = PRODUCTS[i]
            y = 240 + i * 140
            with group(g, 0, 0, alpha=clamp01(kk * 2)) as q:
                rrect(q, 24, y, w - 48, 116, 28, "#1e293b")
                rrect(q, 44, y + 20, 76, 76, 22, accent)
                ic(q, 82, y + 58, 44, WHITE)
                text(q, name.split()[0], 140, y + 42, 28, WHITE, "ExtraBold", "left")
                text(q, sub, 140, y + 80, 22, "#94a3b8", "SemiBold", "left")
        rrect(g, 24, h - 150, w - 48, 92, 46, GREEN)
        text(g, "+ Nouveau produit", w / 2, h - 104, 30, WHITE, "ExtraBold")

    py = 1130 + (1 - ease_out((t - 0.2) / 0.7)) * 900
    phone(c, W / 2, py, 0.8, screen)


def sc_steps(c, t, d):
    c.clear(col(WHITE))
    text(c, "EN 3 ÉTAPES", W / 2, 300, 92, INK, "Black", alpha=ease_out(t / 0.4))
    steps = [("Crée ton produit", BLUE, ic_bulb), ("Propose-le en ligne", ORANGE, ic_bag),
             ("Développe ton activité", GREEN, ic_chart)]
    for i, (s, accent, ic) in enumerate(steps):
        t0 = 0.3 + i * d / 3.6
        k = appear(t, t0, 0.5)
        if k <= 0:
            continue
        y = 560 + i * 250
        with group(c, W / 2, y, 0.7 + 0.3 * k, alpha=clamp01(k * 2)) as g:
            w, h = 900, 190
            rrect(g, -w / 2, -h / 2, w, h, 46, SOFT)
            rrect(g, -w / 2 + 30, -60, 120, 120, 34, accent)
            ic(g, -w / 2 + 90, 0, 70, WHITE)
            text(g, f"0{i + 1}", -w / 2 + 190, -34, 30, accent, "Black", "left")
            text(g, s, -w / 2 + 190, 18, 41, INK, "ExtraBold", "left")
            rrect(g, w / 2 - 110, -40, 80, 80, 40, GREEN, clamp01((t - t0 - 0.4) / 0.2))
            ic_check(g, w / 2 - 70, 0, 56, WHITE, progress=(t - t0 - 0.45) / 0.3)


def sc_followers(c, t, d):
    c.clear(col(ORANGE))
    text(c, "PAS BESOIN DE", W / 2, 330, 80, WHITE, "Black", alpha=ease_out(t / 0.4))
    k = appear(t, 0.25, 0.5)
    with group(c, W / 2, 600, 0.6 + 0.4 * k, -4, alpha=clamp01(k * 2)) as g:
        text(g, "100 000", 0, 0, 210, WHITE, "Black")
        text(g, "abonnés", 0, 150, 80, WHITE, "ExtraBold")
        lk = ease_out((t - 1.1) / 0.35)
        if lk > 0:
            g.drawLine(-420, 40, -420 + 840 * lk, -40, paint(INK, 1, stroke=24))
    k3 = appear(t, 2.0, 0.5)
    if k3 > 0:
        with group(c, W / 2, 1050, 0.7 + 0.3 * k3, 3, alpha=clamp01(k3 * 2)) as g:
            pill(g, "Commence maintenant", 0, 0, 62, INK, YELLOW, shadow=0.3)


def sc_outro(c, t, d):
    c.clear(col(BLUE))
    for i in range(14):  # confettis
        rng = np.random.default_rng(i)
        x0, sp, ph = rng.uniform(60, W - 60), rng.uniform(120, 260), rng.uniform(0, 6)
        y = -60 + (t * sp + ph * 200) % (H + 120)
        cc = [YELLOW, PINK, WHITE, "#86efac"][i % 4]
        with group(c, x0 + math.sin(t * 2 + ph) * 30, y, rot=t * 90 + ph * 50) as g:
            g.drawRect(skia.Rect.MakeXYWH(-10, -18, 20, 36), paint(cc, 0.8))
    k = appear(t, 0.0, 0.5)
    with group(c, W / 2, 600, 0.6 + 0.4 * k, alpha=clamp01(k * 2)) as g:
        logo(g, 0, 0, 110)
    k2 = appear(t, 0.5, 0.5)
    with group(c, W / 2, 840, alpha=clamp01(k2 * 2)) as g:
        text(g, "Ton prochain projet", 0, -45, 64, WHITE, "ExtraBold")
        text(g, "commence depuis ta chambre", 0, 45, 56, YELLOW, "ExtraBold")
    k3 = appear(t, 1.6, 0.5)
    if k3 > 0:
        pulse = 1 + 0.04 * math.sin(max(0.0, t - 2.2) * 6)
        with group(c, W / 2, 1100, (0.6 + 0.4 * k3) * pulse, alpha=clamp01(k3 * 2)) as g:
            pill(g, "Créer mon compte  →", 0, 0, 58, WHITE, BLUE, shadow=0.35)
        text(c, "digiropay.com", W / 2, 1250, 54, WHITE, "Bold", alpha=clamp01(k3 * 2))


SCENES = dict(hook=sc_hook, products=sc_products, phone=sc_phone, brand=sc_brand, steps=sc_steps,
              followers=sc_followers, outro=sc_outro)
SCENE_COLOR = dict(hook=BLUE, products=WHITE, phone="#fdf2f8", brand=GREEN, steps=WHITE, followers=ORANGE,
                   outro=BLUE)


# ---------------------------------------------------------------- sous-titres
CAP_Y = 1560


def captions(c, t, caps):
    for t0, t1, groups in caps:
        if not (t0 <= t < t1 + 0.15):
            continue
        for words in groups:
            if not (words[0][1] - 0.05 <= t < words[-1][2] + 0.25) and not (t >= words[-1][2] and words is groups[-1]):
                continue
            f = font(64, "Black")
            sp = f.measureText(" ")
            ws = [f.measureText(w) for w, _, _ in words]
            total = sum(ws) + sp * (len(words) - 1)
            ga = ease_out((t - words[0][1] + 0.05) / 0.15)
            pad = 34
            with group(c, W / 2, CAP_Y, 0.9 + 0.1 * ga, alpha=ga) as g:
                rrect(g, -total / 2 - pad, -60, total + 2 * pad, 120, 40, INK, 0.92, shadow=0.2)
                x = -total / 2
                for (w, a, b), wd in zip(words, ws):
                    active = a <= t < b + 0.05
                    g.drawString(w, x, 64 * 0.36, f, paint(YELLOW if active else WHITE))
                    x += wd + sp
            return


def group_words(words, times, maxw=3, maxlen=20):
    out, cur = [], []
    for w, (a, b) in zip(words, times):
        if cur and (len(cur) >= maxw or len(" ".join(x[0] for x in cur + [(w,)])) > maxlen):
            out.append(cur)
            cur = []
        cur.append((w, a, b))
        if re.search(r"[,.:?!]$", w):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


# ---------------------------------------------------------------- montage
def build_timeline():
    os.makedirs(BUILD, exist_ok=True)
    tts = None
    voice_parts, lines, t = [], [], 0.3
    for spoken, shown, scene in LINES:
        path = os.path.join(BUILD, "v" + hashlib.md5(f"{VOICE}|{SPEED}|{spoken}".encode()).hexdigest()[:12] + ".wav")
        if not os.path.exists(path):
            tts = tts or audio.load_tts(MODELS)
            sf.write(path, audio.synth_line(tts, spoken, VOICE, SPEED, LANG), audio.SR)
            print("  voix :", shown, flush=True)
        a, _ = sf.read(path)
        dur = len(a) / audio.SR
        words = shown.split()
        times = [(t + x, t + y) for x, y in audio.word_times(words, a)]
        lines.append(dict(t0=t, t1=t + dur, scene=scene, groups=group_words(words, times)))
        voice_parts.append((t, a))
        t += dur + GAP
    total = lines[-1]["t1"] + OUTRO_TAIL
    for i, L in enumerate(lines):
        L["s0"] = 0.0 if i == 0 else L["t0"] - 0.2
        L["s1"] = lines[i + 1]["t0"] - 0.2 if i + 1 < len(lines) else total
    return lines, voice_parts, total


def render_frame(c, t, lines):
    cur = max(i for i, L in enumerate(lines) if L["s0"] <= t or i == 0)
    L = lines[cur]
    lt = t - L["s0"]
    SCENES[L["scene"]](c, lt, L["s1"] - L["s0"])
    # transition : cercle de la nouvelle couleur qui s'ouvre depuis le bas
    if cur > 0 and lt < 0.4:
        prev = lines[cur - 1]
        k = ease_out(lt / 0.4)
        c.save()
        clip = skia.Path()
        clip.addCircle(W / 2, H * 0.75, 2300 * k)
        c.clipPath(clip, skia.ClipOp.kDifference, True)
        SCENES[prev["scene"]](c, t - prev["s0"], prev["s1"] - prev["s0"])
        c.restore()
    captions(c, t, [(x["t0"], x["t1"], x["groups"]) for x in lines])


def make_audio(voice_parts, lines, total):
    n = int(total * audio.SR)
    v = np.zeros(n)
    for t0, a in voice_parts:
        i = int(t0 * audio.SR)
        v[i:i + len(a)] += a[:n - i]
    music = upbeat_music(total)
    events = [(max(0, L["t0"] - 0.45), "whoosh", 0.7) for L in lines[1:]]
    events += [(0.15, "pop", 0.8), (0.85, "pop", 0.8), (1.55, "pop", 0.8)]
    events += [(lines[-1]["s0"] + 1.6, "boom", 0.5)]
    return audio.mix_all(v, music, events, total)


def upbeat_music(duration, bpm=112):
    """Boucle pop lumineuse (do majeur) : kick, clap, charleston, accords et basse."""
    SR = audio.SR
    rng = np.random.default_rng(3)
    n = int(duration * SR) + SR
    mix = np.zeros(n)
    beat = 60 / bpm
    bar = 4 * beat
    prog = [(60, [60, 64, 67]), (67, [59, 62, 67]), (69, [60, 64, 69]), (65, [60, 65, 69])]  # C G Am F
    k, cl, hh = audio.kick(rng), audio.clap(rng), audio.hat(rng)

    def add(sig, t, g=1.0):
        i = int(t * SR)
        if i < n:
            e = min(n, i + len(sig))
            mix[i:e] += sig[:e - i] * g

    for b in range(int(duration / bar) + 1):
        t0 = b * bar
        root, chord = prog[b % 4]
        for s in range(16):
            ts = t0 + s * beat / 4
            if s in (0, 4, 8, 12):
                add(k, ts, 0.9)
            if s in (4, 12):
                add(cl, ts, 0.8)
            if s % 2 == 1:
                add(hh, ts, 0.6)
        # accords piqués sur les contre-temps
        for s in (2, 6, 10, 14):
            ln = int(beat * 0.45 * SR)
            tt = np.arange(ln) / SR
            sig = sum(np.sin(2 * np.pi * audio.note_hz(m) * tt) + 0.3 * np.sin(4 * np.pi * audio.note_hz(m) * tt)
                      for m in chord) / 3
            add(sig * np.exp(-tt * 9) * 0.22, t0 + s * beat / 4)
        # basse
        for s in (0, 3, 8, 11):
            ln = int(beat * 0.6 * SR)
            tt = np.arange(ln) / SR
            sig = np.tanh(2 * np.sin(2 * np.pi * audio.note_hz(root - 24) * tt)) * np.exp(-tt * 4) * 0.35
            add(sig, t0 + s * beat / 4)
    return mix[:int(duration * SR)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", default=None, help="secondes séparées par des virgules -> PNG")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "output", "digiropay_pub_fr.mp4"))
    a = ap.parse_args()
    lines, voice_parts, total = build_timeline()
    surface = skia.Surface(W, H)
    c = surface.getCanvas()
    if a.stills:
        for s in a.stills.split(","):
            render_frame(c, float(s), lines)
            surface.makeImageSnapshot().save(os.path.join(BUILD, f"still_{s}.png"), skia.kPNG)
        print("aperçus dans", BUILD)
        return
    wav = os.path.join(BUILD, "mix.wav")
    sf.write(wav, make_audio(voice_parts, lines, total), audio.SR)
    nf = int(total * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-i", wav, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-preset", "medium",
         "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest",
         "-movflags", "+faststart", a.out], stdin=subprocess.PIPE)
    for f in range(nf):
        render_frame(c, f / FPS, lines)
        ff.stdin.write(surface.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).tobytes())
        if f % 150 == 0:
            print(f"  image {f}/{nf}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("OK :", os.path.abspath(a.out), f"({total:.1f} s)")


if __name__ == "__main__":
    main()
