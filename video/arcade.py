"""Rendu « borne d'arcade » : cabinet, écran CRT et écrans de jeu (sélection, VS, vainqueur)."""
import math
import os

import numpy as np
import skia

from engine import W, H, GOLD, INK, col, paint, font, pill, ease, ease_out, ease_back, clamp01, lerp

HERE = os.path.dirname(os.path.abspath(__file__))
SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
NEAREST = skia.SamplingOptions(skia.FilterMode.kNearest)

# écran dans le cabinet (coordonnées image à l'échelle 1)
SCR = skia.Rect.MakeLTRB(118, 452, 962, 1176)
SW, SH = 844, 724
P1, P2 = "#ff3b3b", "#3b8bff"


# ---------------------------------------------------------------- texte pixel
_ptext = {}


def pixel_text(c, text, x, y, size, color="#ffffff", align="center", shadow=True, alpha=1.0, px=None,
               weight="Black"):
    """Texte rendu en petit sans anticrénelage puis agrandi au plus proche : look 16 bits."""
    if px is None:
        px = max(2, min(6, round(size / 14)))
    key = (text, size, color, px, weight)
    if key not in _ptext:
        f = font(size / px, weight)
        f.setEdging(skia.Font.Edging.kAlias)
        f.setSubpixel(False)
        tw = f.measureText(text)
        w, h = int(tw + 4), int(size / px * 1.35 + 4)
        s = skia.Surface(w, h)
        cc = s.getCanvas()
        cc.clear(skia.ColorTRANSPARENT)
        p = skia.Paint(AntiAlias=False)
        p.setColor4f(col(color))
        cc.drawString(text, 2, size / px * 1.0 + 1, f, p)
        _ptext[key] = s.makeImageSnapshot()
    img = _ptext[key]
    w, h = img.width() * px, img.height() * px
    x0 = x - w / 2 if align == "center" else (x - w if align == "right" else x)
    y0 = y - h / 2
    if shadow:
        sh = skia.Paint(Alphaf=0.85 * alpha)
        sh.setColorFilter(skia.ColorFilters.Blend(col("#000000"), skia.BlendMode.kSrcIn))
        c.drawImageRect(img, skia.Rect.MakeXYWH(x0 + px, y0 + px, w, h), NEAREST, sh)
    c.drawImageRect(img, skia.Rect.MakeXYWH(x0, y0, w, h), NEAREST, skia.Paint(Alphaf=alpha))
    return w


# ---------------------------------------------------------------- portraits
class Portraits:
    def __init__(self, ids):
        self.img, self.pix = {}, {}
        for pid in ids:
            path = os.path.join(HERE, "assets", "players", f"{pid}.png")
            im = skia.Image.open(path)
            self.img[pid] = im
            # version « pixelisée » pour les vignettes de la grille
            s = skia.Surface(96, 96)
            s.getCanvas().drawImageRect(im, skia.Rect.MakeWH(96, 96), SAMP)
            self.pix[pid] = s.makeImageSnapshot()

    def draw(self, c, pid, rect, alpha=1.0, pixel=False, gray=0.0, zoom=1.0):
        im = self.pix[pid] if pixel else self.img[pid]
        p = skia.Paint(Alphaf=alpha)
        if gray > 0:
            g = gray
            m = [lerp(1, .3, g), lerp(0, .59, g), lerp(0, .11, g), 0, 0,
                 lerp(0, .3, g), lerp(1, .59, g), lerp(0, .11, g), 0, 0,
                 lerp(0, .3, g), lerp(0, .59, g), lerp(1, .11, g), 0, 0,
                 0, 0, 0, 1, 0]
            m = [v * (1 - 0.45 * g) if i % 5 < 3 and i < 15 else v for i, v in enumerate(m)]
            p.setColorFilter(skia.ColorFilters.Matrix(m))
        iw, ih = im.width(), im.height()
        sw, sh = iw / zoom, ih / zoom
        src = skia.Rect.MakeXYWH((iw - sw) / 2, (ih - sh) * 0.15, sw, sh)
        c.save()
        c.clipRect(rect, doAntiAlias=True)
        c.drawImageRect(im, src, rect, NEAREST if pixel else SAMP, p)
        c.restore()


# ---------------------------------------------------------------- cabinet statique
def make_cabinet(brand, scale=2):
    s = skia.Surface(W * scale, H * scale)
    c = s.getCanvas()
    c.scale(scale, scale)
    # pièce sombre
    c.drawPaint(skia.Paint(Shader=skia.GradientShader.MakeRadial(
        (W / 2, 820), 1300, [col("#20232b"), col("#08090c")])))
    # corps
    body = skia.Path()
    body.moveTo(40, 120)
    body.lineTo(1040, 120)
    body.lineTo(1040, 1920)
    body.lineTo(40, 1920)
    body.close()
    c.drawPath(body, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(40, 0), (1040, 0)], [col("#1b1d22"), col("#3a3d45"), col("#2b2e35"), col("#16181c")],
        [0, 0.15, 0.85, 1])))
    # montants latéraux
    for x in (40, 1000):
        c.drawRect(skia.Rect.MakeXYWH(x, 120, 40, 1800), skia.Paint(Shader=skia.GradientShader.MakeLinear(
            [(x, 0), (x + 40, 0)], [col("#0f1013"), col("#2c2f36"), col("#0f1013")])))
    # fronton (haut-parleurs)
    top = skia.Rect.MakeLTRB(80, 140, 1000, 360)
    c.drawRRect(skia.RRect.MakeRectXY(top, 14, 14), paint("#121318"))
    c.drawRRect(skia.RRect.MakeRectXY(top.makeInset(6, 6), 12, 12), skia.Paint(
        AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 140), (0, 360)],
                                                              [col("#3c3f47"), col("#24262c")])))
    for cx in (300, 700):
        c.drawCircle(cx, 250, 92, paint("#0c0d10"))
        c.drawCircle(cx, 250, 86, paint("#4a4e57", stroke=6))
        for r in range(10, 80, 8):
            c.drawCircle(cx, 250, r, paint("#1d1f24", 0.9, stroke=3))
        for i in range(-70, 71, 9):
            for j in range(-70, 71, 9):
                if i * i + j * j < 74 * 74:
                    c.drawCircle(cx + i, 250 + j, 2.2, paint("#050506"))
    # logo de la chaîne en haut à droite (comme la référence)
    from timeline import draw_badge
    draw_badge(c, 905, 250, 58, 1.0, brand=brand)
    # cadre écran
    bez = skia.Rect.MakeLTRB(80, 392, 1000, 1236)
    c.drawRRect(skia.RRect.MakeRectXY(bez, 18, 18), paint("#0d0e11"))
    c.drawRRect(skia.RRect.MakeRectXY(bez.makeInset(10, 10), 14, 14), skia.Paint(
        AntiAlias=True, Shader=skia.GradientShader.MakeLinear([(0, 392), (0, 1236)],
                                                              [col("#5a5e68"), col("#30333a"), col("#4a4e57")])))
    inner = SCR.makeOutset(26, 26)
    c.drawRRect(skia.RRect.MakeRectXY(inner, 40, 40), paint("#07080a"))
    for (x, y) in ((100, 412), (980, 412), (100, 1216), (980, 1216)):
        c.drawCircle(x, y, 7, paint("#15161a"))
        c.drawCircle(x - 1.5, y - 1.5, 3, paint("#8a8e98"))
    # panneau de commande en perspective
    panel = skia.Path()
    panel.moveTo(60, 1300)
    panel.lineTo(1020, 1300)
    panel.lineTo(1040, 1500)
    panel.lineTo(40, 1500)
    panel.close()
    c.drawPath(panel, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(0, 1300), (0, 1500)], [col("#4b4f59"), col("#2a2d33")])))
    c.drawRect(skia.Rect.MakeLTRB(40, 1500, 1040, 1560), paint("#16171b"))
    c.drawLine(60, 1300, 1020, 1300, paint("#7a7e88", stroke=3))
    # porte monnayeur
    door = skia.Rect.MakeLTRB(150, 1640, 930, 1920)
    c.drawRRect(skia.RRect.MakeRectXY(door, 10, 10), paint("#121317"))
    for i, x in enumerate((420, 600)):
        r = skia.Rect.MakeXYWH(x, 1700, 60, 90)
        c.drawRRect(skia.RRect.MakeRectXY(r, 6, 6), paint("#26282e"))
        c.drawRect(skia.Rect.MakeXYWH(x + 26, 1715, 8, 50), paint("#050506"))
    return s.makeImageSnapshot()


def draw_joystick(c, x, y, tilt, ball="#b3261e"):
    c.drawOval(skia.Rect.MakeXYWH(x - 70, y - 18, 140, 44), paint("#0b0c0e"))
    c.drawOval(skia.Rect.MakeXYWH(x - 56, y - 12, 112, 32), paint("#3a3d44"))
    tx, ty = x + 60 * math.sin(tilt), y - 130 * math.cos(tilt)
    c.drawLine(x, y, tx, ty, paint("#9aa0aa", stroke=14))
    c.drawLine(x, y, tx, ty, paint("#e2e5ea", 0.6, stroke=4))
    # boule (forme « bat top » allongée comme sur la référence)
    r = skia.Rect.MakeXYWH(tx - 26, ty - 92, 52, 100)
    c.drawRRect(skia.RRect.MakeRectXY(r, 26, 26), skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeLinear(
        [(tx - 26, 0), (tx + 26, 0)], [col("#5a0f0b"), col(ball), col("#e0574b"), col("#5a0f0b")],
        [0, 0.35, 0.55, 1])))
    c.drawOval(skia.Rect.MakeXYWH(tx - 12, ty - 84, 10, 34), paint("#ffffff", 0.35))


def draw_button(c, x, y, color, pressed):
    dy = 6 if pressed else 0
    c.drawOval(skia.Rect.MakeXYWH(x - 34, y - 6, 68, 34), paint("#0b0c0e"))
    c.drawOval(skia.Rect.MakeXYWH(x - 28, y - 12 + dy, 56, 26), paint(color))
    c.drawOval(skia.Rect.MakeXYWH(x - 28, y - 18 + dy, 56, 26), skia.Paint(
        AntiAlias=True, Shader=skia.GradientShader.MakeRadial((x - 8, y - 12 + dy), 34,
                                                             [col("#ffffff", 0.5), col(color)])))
    if pressed:
        c.drawCircle(x, y - 5, 40, paint(color, 0.35, blur=14))


# ---------------------------------------------------------------- timeline d'événements
class Events:
    def __init__(self, events):
        self.ev = sorted(events, key=lambda e: e[0])

    def last(self, cmd, t):
        out = None
        for e in self.ev:
            if e[0] > t:
                break
            if e[1] == cmd:
                out = e
        return out

    def all(self, cmd, t=1e9):
        return [e for e in self.ev if e[1] == cmd and e[0] <= t]

    def since(self, cmd, t, default=1e9):
        e = self.last(cmd, t)
        return t - e[0] if e else default


# ---------------------------------------------------------------- écrans de jeu
class Screens:
    def __init__(self, G, portraits):
        self.G, self.P = G, portraits
        rng = np.random.default_rng(2)
        # foule pixelisée (fond de stade)
        h, w = SH // 4, SW // 4
        crowd = np.zeros((h, w, 4), np.uint8)
        base = np.array([[22, 32, 70], [40, 60, 120], [90, 110, 170], [200, 170, 80], [160, 40, 50]])
        for yy in range(h):
            for xx in range(w):
                if rng.random() < 0.55:
                    cc = base[rng.integers(0, len(base))] * (0.35 + 0.65 * yy / h)
                else:
                    cc = np.array([12, 16, 34]) * (0.5 + yy / h)
                crowd[yy, xx, :3] = cc.clip(0, 255)
        crowd[..., 3] = 255
        self.crowd = skia.Image.fromarray(crowd)
        # lignes de balayage
        sl = np.zeros((SH, 4, 4), np.uint8)
        sl[::4, :, 3] = 70
        sl[1::4, :, 3] = 25
        self.scan = skia.Image.fromarray(sl)
        self.surf = skia.Surface(SW, SH)

    # ------------------------------------------------------------ fonds
    def bg_stadium(self, c, t, dim=0.0):
        c.drawImageRect(self.crowd, skia.Rect.MakeXYWH(0, 0, SW, SH * 0.62), NEAREST, skia.Paint(Alphaf=0.55))
        c.drawRect(skia.Rect.MakeXYWH(0, SH * 0.55, SW, SH * 0.45), skia.Paint(Shader=skia.GradientShader.MakeLinear(
            [(0, SH * 0.55), (0, SH)], [col("#0a1430", 0.0), col("#060a18")])))
        for k in range(3):
            x = SW * (0.5 + 0.45 * math.sin(t * 0.6 + k * 2.1))
            p = paint("#9fc4ff", 0.10, blur=40)
            p.setBlendMode(skia.BlendMode.kScreen)
            path = skia.Path()
            path.moveTo(x, -20)
            path.lineTo(x - 140, SH)
            path.lineTo(x + 140, SH)
            path.close()
            c.drawPath(path, p)
        if dim:
            c.drawPaint(paint("#000000", dim))

    def frame_box(self, c, rect, color, w=6, glow=True, alpha=1.0):
        if glow:
            c.drawRect(rect, paint(color, 0.6 * alpha, stroke=w * 2.5, blur=10))
        c.drawRect(rect, paint(color, alpha, stroke=w))

    # ------------------------------------------------------------ rendu
    def render(self, t, ev, info):
        c = self.surf.getCanvas()
        c.clear(col("#05070d"))
        sc = ev.last("scene", t)
        name, t0 = (sc[2], sc[0]) if sc else ("boot", 0.0)
        getattr(self, "s_" + name)(c, t, t - t0, ev, info)
        return self.surf.makeImageSnapshot()

    # ------------------------------------------------------------ scènes
    def s_boot(self, c, t, lt, ev, info):
        rng = np.random.default_rng(int(t * 30))
        if lt < 0.35:  # allumage du CRT
            k = lt / 0.35
            c.drawRect(skia.Rect.MakeXYWH(0, SH / 2 - 2 - SH / 2 * k, SW, 4 + SH * k), paint("#dfe8ff", 1 - k * 0.8))
            return
        self.bg_stadium(c, t, 0.55)
        pixel_text(c, "FOFANA FÚTBOL", SW / 2, 150, 44, GOLD)
        pixel_text(c, "PRESENTA", SW / 2, 215, 24, "#ffffff")
        if int(t * 2.2) % 2 == 0:
            pixel_text(c, "INSERT COIN", SW / 2, 420, 52, "#ffffff")
        coin = ev.last("coin", t)
        pixel_text(c, "CREDIT 01" if coin else "CREDIT 00", SW - 30, SH - 40, 22, "#9fd0ff", align="right")
        pixel_text(c, "LONDRES · 26.10.2026", 30, SH - 40, 22, "#9fd0ff", align="left")

    def s_title(self, c, t, lt, ev, info):
        self.bg_stadium(c, t, 0.35)
        self.skyline(c, t)
        k = ease_back(lt / 0.5)
        c.save()
        c.translate(SW / 2, 200)
        c.scale(0.5 + 0.5 * k, 0.5 + 0.5 * k)
        pixel_text(c, "BALÓN DE ORO", 0, 0, 92, GOLD, px=5)
        c.restore()
        # reflet qui balaie le titre
        sx = (lt * 500) % (SW * 2) - SW / 2
        p = paint("#ffffff", 0.35, blur=12)
        p.setBlendMode(skia.BlendMode.kOverlay)
        c.drawRect(skia.Rect.MakeXYWH(sx, 140, 40, 120), p)
        if lt > 0.4:
            k2 = ease_back((lt - 0.4) / 0.4)
            c.save()
            c.translate(SW / 2, 330)
            c.scale(k2, k2)
            pixel_text(c, "2026", 0, 0, 120, "#ffffff", px=6)
            c.restore()
        if lt > 1.0:
            pixel_text(c, "70ª EDICIÓN · LONDRES", SW / 2, 450, 34, "#9fd0ff", alpha=clamp01((lt - 1) / 0.3))

    def skyline(self, c, t):
        y = SH - 120
        p = paint("#0b1124")
        # Big Ben
        c.drawRect(skia.Rect.MakeXYWH(120, y - 230, 50, 230), p)
        c.drawRect(skia.Rect.MakeXYWH(112, y - 250, 66, 24), p)
        tri = skia.Path()
        tri.moveTo(112, y - 250)
        tri.lineTo(145, y - 320)
        tri.lineTo(178, y - 250)
        c.drawPath(tri, p)
        c.drawCircle(145, y - 200, 16, paint(GOLD, 0.8))
        # London Eye
        c.drawCircle(640, y - 120, 110, paint("#0b1124", stroke=10))
        for i in range(12):
            a = i * math.pi / 6 + t * 0.2
            c.drawLine(640, y - 120, 640 + 110 * math.cos(a), y - 120 + 110 * math.sin(a), paint("#0b1124", stroke=3))
            c.drawCircle(640 + 110 * math.cos(a), y - 120 + 110 * math.sin(a), 6, paint("#9fd0ff", 0.7))
        # immeubles
        rng = np.random.default_rng(5)
        x = 0
        while x < SW:
            w_ = 30 + rng.integers(0, 50)
            h_ = 40 + rng.integers(0, 110)
            c.drawRect(skia.Rect.MakeXYWH(x, y - h_, w_, h_ + 130), p)
            for wy in range(int(y - h_ + 10), int(y), 18):
                for wx in range(int(x + 6), int(x + w_ - 6), 14):
                    if rng.random() < 0.35:
                        c.drawRect(skia.Rect.MakeXYWH(wx, wy, 6, 8), paint("#ffd27a", 0.5))
            x += w_ + 4
        c.drawRect(skia.Rect.MakeXYWH(0, y, SW, 130), paint("#070b18"))

    def s_champ(self, c, t, lt, ev, info):
        self.bg_stadium(c, t, 0.45)
        k = ease_out(lt / 0.5)
        r = skia.Rect.MakeXYWH(SW / 2 - 210, 120 + 40 * (1 - k), 420, 420)
        q = ev.last("qmark", t)
        gray = clamp01((t - q[0]) / 0.4) * 0.85 if q else 0
        c.drawRect(r.makeOutset(10, 10), paint(GOLD, 0.5 * k, blur=16))
        self.P.draw(c, "dembele", r, k, gray=gray)
        self.frame_box(c, r, GOLD, 6, alpha=k)
        # couronne
        cx, cy = SW / 2, r.top() - 18 + 6 * math.sin(t * 3)
        crown = skia.Path()
        for i, (dx, dy) in enumerate([(-60, 20), (-60, -30), (-30, 0), (0, -45), (30, 0), (60, -30), (60, 20)]):
            (crown.moveTo if i == 0 else crown.lineTo)(cx + dx, cy + dy)
        crown.close()
        c.drawPath(crown, paint(GOLD, k * (1 - gray)))
        pixel_text(c, "CAMPEÓN DEFENSOR", SW / 2, 40, 34, GOLD, alpha=k)
        if q:
            pixel_text(c, "¿SU SUCESOR?", SW / 2, 610, 56, GOLD)
        else:
            pixel_text(c, "OUSMANE DEMBÉLÉ", SW / 2, 600, 46, "#ffffff", alpha=k)
            pixel_text(c, "BALÓN DE ORO 2025", SW / 2, 660, 26, "#9fd0ff", alpha=k)
        if q:
            qa = clamp01((t - q[0]) / 0.25)
            s = 1 + 0.08 * math.sin(t * 8)
            c.save()
            c.translate(SW / 2, 330)
            c.scale(s, s)
            pixel_text(c, "?", 0, 0, 300, "#ffffff", px=10, alpha=qa)
            c.restore()

    # grille de sélection -------------------------------------------------
    def grid_rects(self):
        cw, ch, gap = 150, 128, 8
        x0 = (SW - (5 * cw + 4 * gap)) / 2
        out = {}
        for i, pid in enumerate(self.G.GRID):
            r, cc = divmod(i, 5)
            out[pid] = skia.Rect.MakeXYWH(x0 + cc * (cw + gap), 446 + r * (ch + gap), cw, ch)
        return out

    def draw_grid(self, c, t, lt, cur, other=None, dim_except=None, appear=1.0):
        rects = self.grid_rects()
        for i, pid in enumerate(self.G.GRID):
            r = rects[pid]
            k = ease_back((appear * 10 - i * 0.6) / 1.5) if appear < 1 else 1
            if k <= 0:
                continue
            rr = skia.Rect.MakeXYWH(r.centerX() - r.width() / 2 * k, r.centerY() - r.height() / 2 * k,
                                    r.width() * k, r.height() * k)
            c.drawRect(rr, paint("#0c1226"))
            gray = 0.0
            if dim_except is not None and pid not in dim_except:
                gray = 1.0
            self.P.draw(c, pid, rr, 1.0, pixel=True, gray=gray, zoom=1.35)
            c.drawRect(rr, paint("#2b3550", stroke=3))
        if cur:
            blink = 0.65 + 0.35 * math.sin(t * 14)
            self.frame_box(c, rects[cur].makeOutset(4, 4), P1, 6, alpha=blink)
            pixel_text(c, "1P", rects[cur].left() + 4, rects[cur].top() + 14, 22, P1, align="left")
        if other:
            blink = 0.65 + 0.35 * math.sin(t * 14 + 1)
            self.frame_box(c, rects[other].makeOutset(4, 4), P2, 6, alpha=blink)
            pixel_text(c, "2P", rects[other].right() - 4, rects[other].top() + 14, 22, P2, align="right")

    def preview(self, c, t, pid, since, side="left", color=P1, tag=None):
        info = self.G.PLAYERS[pid]
        k = ease_out(since / 0.35)
        x = 26 - 60 * (1 - k) if side == "left" else SW - 26 - 360 + 60 * (1 - k)
        r = skia.Rect.MakeXYWH(x, 70, 360, 360)
        c.drawRect(r.makeOutset(8, 8), paint(color, 0.35 * k, blur=18))
        self.P.draw(c, pid, r, k)
        self.frame_box(c, r, color, 5, alpha=k)
        tx = r.right() + 26 if side == "left" else r.left() - 26
        al = "left" if side == "left" else "right"
        name = info["name"]
        size = 50 if len(name) < 11 else 40
        pixel_text(c, name, tx, 120, size, "#ffffff", align=al, alpha=k)
        pixel_text(c, info["club"], tx, 180, 24, "#9fd0ff", align=al, alpha=k)
        if tag:
            pixel_text(c, tag, tx, 245, 26, GOLD, align=al, alpha=clamp01((since - 0.2) / 0.25))

    def s_grid(self, c, t, lt, ev, info):
        self.bg_stadium(c, t, 0.25)
        pixel_text(c, "SELECCIONA JUGADOR", SW / 2, 30, 26, "#ffffff")
        pk = ev.last("pick", t)
        if pk:
            pid = pk[2]
            self.preview(c, t, pid, t - pk[0], tag=self.G.PLAYERS[pid]["fact"])
            cur = pid
        else:
            # le curseur « cherche » au hasard avant le premier choix
            cur = self.G.GRID[int(t * 9) % 10]
            big, small = getattr(self.G, "GRID_TITLE", ("10 / 30", "NOMINADOS"))
            pixel_text(c, big, SW / 2, 230, 120, GOLD, px=6)
            pixel_text(c, small, SW / 2, 340, 40, "#ffffff")
        self.draw_grid(c, t, lt, cur, appear=clamp01(lt / 1.2))

    def s_finalists(self, c, t, lt, ev, info):
        self.bg_stadium(c, t, 0.3)
        pixel_text(c, "LOS 2 FINALISTAS", SW / 2, 30, 30, GOLD)
        k = ease_back(lt / 0.5)
        c.save()
        c.translate(SW / 2, 230)
        c.scale(k, k)
        pixel_text(c, "KANE", -160, 0, 70, P1)
        pixel_text(c, "VS", 0, 0, 60, "#ffffff")
        pixel_text(c, "YAMAL", 175, 0, 70, P2)
        c.restore()
        self.draw_grid(c, t, lt, "kane", "yamal", dim_except={"kane", "yamal"})

    def s_p1(self, c, t, lt, ev, info):
        self.duel(c, t, lt, ev, show_p2=False)

    def s_p2(self, c, t, lt, ev, info):
        self.duel(c, t, lt, ev, show_p2=True)

    def stat_list(self, c, t, x, ev, after, align, color):
        stats = [e for e in ev.all("stat", t) if e[0] >= after]
        for i, (ts, _, s) in enumerate(stats):
            k = ease_back((t - ts) / 0.3)
            y = 470 + i * 70
            f = font(28, "Black")
            tw = f.measureText(s) + 36
            xx = x if align == "left" else x - tw
            c.save()
            c.translate(xx + tw / 2, y)
            c.scale(k, k)
            r = skia.Rect.MakeXYWH(-tw / 2, -26, tw, 52)
            c.drawRect(r, paint(color))
            c.drawRect(r, paint("#ffffff", stroke=3))
            pixel_text(c, s, 0, 0, 28, "#ffffff")
            c.restore()

    def duel(self, c, t, lt, ev, show_p2):
        self.bg_stadium(c, t, 0.3)
        p1 = ev.last("scene_p1", t)
        p2 = ev.last("scene_p2", t)
        # P1 Kane
        t1 = p1[0] if p1 else t - 5
        k = ease_out((t - t1) / 0.4)
        r1 = skia.Rect.MakeXYWH(20 - 300 * (1 - k), 70, 400, 380)
        c.drawRect(r1.makeOutset(8, 8), paint(P1, 0.4, blur=18))
        self.P.draw(c, "kane", r1, 1, zoom=1.0)
        self.frame_box(c, r1, P1, 6)
        pixel_text(c, "1P", r1.left() + 14, r1.top() + 26, 34, P1, align="left")
        pixel_text(c, "HARRY KANE", r1.centerX(), r1.bottom() - 28, 36, "#ffffff")
        if show_p2:
            t2 = p2[0]
            k2 = ease_out((t - t2) / 0.4)
            r2 = skia.Rect.MakeXYWH(SW - 420 + 300 * (1 - k2), 70, 400, 380)
            c.drawRect(r2.makeOutset(8, 8), paint(P2, 0.4, blur=18))
            self.P.draw(c, "yamal", r2, 1)
            self.frame_box(c, r2, P2, 6)
            pixel_text(c, "2P", r2.right() - 14, r2.top() + 26, 34, P2, align="right")
            pixel_text(c, "LAMINE YAMAL", r2.centerX(), r2.bottom() - 28, 34, "#ffffff")
            self.stat_list(c, t, SW - 24, ev, t2, "right", P2)
            # stats de Kane estompées à gauche
            c.saveLayerAlpha(None, 90)
            self.stat_list(c, t2 - 0.01, 24, ev, t1, "left", P1)
            c.restore()
        else:
            r2 = skia.Rect.MakeXYWH(SW - 420, 70, 400, 380)
            c.drawRect(r2, paint("#0c1226"))
            self.frame_box(c, r2, "#2b3550", 4, glow=False)
            pixel_text(c, "?", r2.centerX(), r2.centerY(), 200, "#2b3550", px=8, shadow=False)
            self.stat_list(c, t, 24, ev, t1, "left", P1)
        # VS central
        s = 1 + 0.06 * math.sin(t * 9)
        c.save()
        c.translate(SW / 2, 260)
        c.scale(s, s)
        pixel_text(c, "VS", 0, 0, 80, GOLD, px=5)
        c.restore()

    def s_vs(self, c, t, lt, ev, info):
        self.bg_stadium(c, t, 0.2)
        # éclairs en fond
        rng = np.random.default_rng(int(t * 12))
        for _ in range(2):
            x = SW / 2 + rng.normal(0, 30)
            path = skia.Path()
            path.moveTo(x, 0)
            yy = 0
            while yy < SH:
                yy += 40
                x += rng.normal(0, 25)
                path.lineTo(x, yy)
            c.drawPath(path, paint("#bfe0ff", 0.7, stroke=5, blur=3))
        k = ease_out(lt / 0.4)
        r1 = skia.Rect.MakeXYWH(0, 40, SW / 2 - 10, 560)
        r2 = skia.Rect.MakeXYWH(SW / 2 + 10, 40, SW / 2 - 10, 560)
        c.save()
        c.translate(-200 * (1 - k), 0)
        self.P.draw(c, "kane", r1, 1, zoom=1.1)
        self.frame_box(c, r1, P1, 6)
        c.restore()
        c.save()
        c.translate(200 * (1 - k), 0)
        self.P.draw(c, "yamal", r2, 1, zoom=1.1)
        self.frame_box(c, r2, P2, 6)
        c.restore()
        s = 1.0 + 0.1 * math.sin(t * 10)
        c.save()
        c.translate(SW / 2, 320)
        c.scale(s * ease_back(lt / 0.5), s * ease_back(lt / 0.5))
        pixel_text(c, "VS", 0, 0, 150, GOLD, px=7)
        c.restore()
        pixel_text(c, "KANE", SW / 4, 650, 54, P1)
        pixel_text(c, "YAMAL", SW * 3 / 4, 650, 54, P2)
        fav = ev.last("fav", t)
        if fav:
            kf = ease_back((t - fav[0]) / 0.35)
            c.save()
            c.translate(SW / 4, 520)
            c.rotate(-8)
            c.scale(kf * 1.0, kf * 1.0)
            r = skia.Rect.MakeXYWH(-170, -40, 340, 80)
            c.drawRect(r, paint(GOLD))
            c.drawRect(r, paint("#000000", stroke=5))
            pixel_text(c, "FAVORITO", 0, 0, 44, INK, shadow=False)
            c.restore()

    def s_predict(self, c, t, lt, ev, info):
        self.bg_stadium(c, t, 0.6)
        pixel_text(c, "MI PREDICCIÓN", SW / 2, 40, 36, GOLD)
        win = ev.last("winner", t)
        # ruleta : alterne de plus en plus vite
        period = max(0.06, 0.45 - lt * 0.08)
        sel = int(lt / period) % 2
        r1 = skia.Rect.MakeXYWH(40, 120, 360, 360)
        r2 = skia.Rect.MakeXYWH(SW - 400, 120, 360, 360)
        self.P.draw(c, "kane", r1, 1, gray=0 if sel == 0 else 0.8)
        self.P.draw(c, "yamal", r2, 1, gray=0 if sel == 1 else 0.8)
        self.frame_box(c, r1, P1 if sel == 0 else "#333a4a", 6, glow=sel == 0)
        self.frame_box(c, r2, P2 if sel == 1 else "#333a4a", 6, glow=sel == 1)
        pixel_text(c, "?", SW / 2, 300, 120, "#ffffff", px=6, alpha=0.6 + 0.4 * math.sin(t * 12))
        pixel_text(c, "BALÓN DE ORO 2026", SW / 2, 600, 40, "#ffffff")

    def s_winner(self, c, t, lt, ev, info):
        # fond doré rayonnant
        c.drawPaint(skia.Paint(Shader=skia.GradientShader.MakeRadial(
            (SW / 2, 300), 600, [col("#ffe9a8"), col("#c8901f"), col("#3a2205")], [0, 0.35, 1])))
        c.save()
        c.translate(SW / 2, 300)
        c.rotate(t * 20)
        for i in range(16):
            c.rotate(360 / 16)
            path = skia.Path()
            path.moveTo(0, 0)
            path.lineTo(-40, -900)
            path.lineTo(40, -900)
            path.close()
            c.drawPath(path, paint("#ffffff", 0.12))
        c.restore()
        k = ease_back(lt / 0.5)
        r = skia.Rect.MakeXYWH(SW / 2 - 200 * k, 300 - 200 * k, 400 * k, 400 * k)
        if k > 0.05:
            c.drawRect(r.makeOutset(10, 10), paint("#ffffff", 0.8, blur=20))
            self.P.draw(c, "kane", r, 1)
            self.frame_box(c, r, GOLD, 8)
        k2 = ease_back((lt - 0.3) / 0.4)
        if k2 > 0:
            c.save()
            c.translate(SW / 2, 570)
            c.scale(k2, k2)
            pixel_text(c, "¡GANADOR!", 0, 0, 90, "#ffffff", px=5)
            c.restore()
            pixel_text(c, "HARRY KANE", SW / 2, 660, 48, INK, shadow=False, alpha=clamp01(k2))
        pixel_text(c, "PREDICCIÓN", SW / 2, 40, 28, INK, shadow=False)
        # confettis pixel
        rng = np.random.default_rng(9)
        for i in range(60):
            x0, sp, ph = rng.random() * SW, 120 + rng.random() * 200, rng.random() * 5
            y = ((lt + ph) * sp) % (SH + 40) - 20
            x = x0 + 20 * math.sin(lt * 3 + ph)
            cc = [GOLD, "#ffffff", P1, P2][i % 4]
            c.drawRect(skia.Rect.MakeXYWH(int(x / 4) * 4, int(y / 4) * 4, 12, 12), paint(cc))

    def s_cta(self, c, t, lt, ev, info):
        self.bg_stadium(c, t, 0.35)
        pixel_text(c, "¿Y TÚ?", SW / 2, 50, 50, GOLD)
        r1 = skia.Rect.MakeXYWH(40, 110, 360, 360)
        r2 = skia.Rect.MakeXYWH(SW - 400, 110, 360, 360)
        self.P.draw(c, "kane", r1, 1)
        self.P.draw(c, "yamal", r2, 1)
        self.frame_box(c, r1, P1, 6, alpha=0.6 + 0.4 * math.sin(t * 8))
        self.frame_box(c, r2, P2, 6, alpha=0.6 + 0.4 * math.sin(t * 8 + 3))
        pixel_text(c, "1P", r1.centerX(), r1.bottom() + 40, 44, P1)
        pixel_text(c, "2P", r2.centerX(), r2.bottom() + 40, 44, P2)
        pixel_text(c, "O", SW / 2, 290, 70, "#ffffff")
        if int(t * 2) % 2 == 0:
            pixel_text(c, "¡COMENTA TU ELECCIÓN!", SW / 2, 620, 40, "#ffffff")
        pixel_text(c, "SÍGUEME PARA MÁS", SW / 2, 680, 26, "#9fd0ff")


# ---------------------------------------------------------------- composition finale
class ArcadeRenderer:
    def __init__(self, G, ev, captions, cam_keys, duration):
        self.G, self.ev, self.captions, self.duration = G, ev, captions, duration
        self.cam_keys = cam_keys  # [(t, zoom, cy)]
        self.cab = make_cabinet(G.BRAND)
        self.P = Portraits(G.GRID)
        self.screens = Screens(G, self.P)
        self.surf = skia.Surface(W, H)
        rng = np.random.default_rng(11)
        g = (rng.normal(128, 40, (H // 2, W // 2))).clip(0, 255).astype(np.uint8)
        self.grain = skia.Image.fromarray(np.dstack([g, g, g, np.full_like(g, 255)]))

    def camera(self, t):
        z, cy = self.cam_keys[0][1], self.cam_keys[0][2]
        for tk, zk, cyk in self.cam_keys:
            if t < tk:
                break
            k = ease((t - tk) / 0.9)
            z, cy = lerp(z, zk, k), lerp(cy, cyk, k)
        # secousse sur les impacts
        sx = sy = 0.0
        for e in self.ev.all("shake", t):
            d = t - e[0]
            if d < 0.5:
                a = 14 * (1 - d / 0.5) * float(e[2])
                sx += a * math.sin(d * 90)
                sy += a * math.cos(d * 70)
        return z * (1 + 0.004 * math.sin(t * 0.8)), cy, sx, sy

    def frame(self, t):
        c = self.surf.getCanvas()
        z, cy, sx, sy = self.camera(t)
        scr = self.screens.render(t, self.ev, None)
        c.save()
        c.translate(W / 2 + sx, H / 2 + sy)
        c.scale(z, z)
        c.translate(-W / 2, -cy)
        c.drawImageRect(self.cab, skia.Rect.MakeWH(W, H), SAMP)
        self.draw_screen(c, scr, t)
        self.draw_controls(c, t)
        c.restore()
        # vignette
        c.drawPaint(skia.Paint(Shader=skia.GradientShader.MakeRadial(
            (W / 2, H * 0.48), H * 0.72, [col("#000000", 0), col("#000000", 0.6)], [0.55, 1])))
        self.draw_captions(c, t)
        gp = skia.Paint(Alphaf=0.05)
        gp.setBlendMode(skia.BlendMode.kOverlay)
        ox = (int(t * 30) * 37) % 200
        c.drawImageRect(self.grain, skia.Rect.MakeXYWH(-ox, -ox * 0.7, W + 200, H + 200), SAMP, gp)
        # fondu final
        if t > self.duration - 0.6:
            c.drawPaint(paint("#000000", clamp01((t - (self.duration - 0.6)) / 0.6)))
        return self.surf.makeImageSnapshot()

    def draw_screen(self, c, scr, t):
        rr = skia.RRect.MakeRectXY(SCR, 34, 34)
        c.save()
        c.clipRRect(rr, doAntiAlias=True)
        flick = 0.97 + 0.03 * math.sin(t * 50)
        c.drawImageRect(scr, SCR, SAMP, skia.Paint(Alphaf=flick))
        # lueur (bloom)
        bp = skia.Paint(Alphaf=0.35)
        bp.setImageFilter(skia.ImageFilters.Blur(10, 10))
        bp.setBlendMode(skia.BlendMode.kScreen)
        c.drawImageRect(scr, SCR, SAMP, bp)
        # lignes de balayage
        c.drawImageRect(self.screens.scan, SCR, NEAREST, skia.Paint(Alphaf=0.9))
        # bande de rafraîchissement qui défile
        by = SCR.top() + ((t * 160) % (SH + 200)) - 100
        c.drawRect(skia.Rect.MakeXYWH(SCR.left(), by, SW, 60), paint("#ffffff", 0.035, blur=20))
        # bords bombés + reflet de la vitre
        c.drawRRect(rr, skia.Paint(Shader=skia.GradientShader.MakeRadial(
            (SCR.centerX(), SCR.centerY()), SW * 0.72, [col("#000000", 0), col("#000000", 0.55)], [0.62, 1])))
        refl = skia.Path()
        refl.moveTo(SCR.left(), SCR.top())
        refl.lineTo(SCR.left() + SW * 0.55, SCR.top())
        refl.lineTo(SCR.left(), SCR.top() + SH * 0.45)
        refl.close()
        c.drawPath(refl, paint("#ffffff", 0.05))
        c.restore()
        # halo de l'écran sur le cabinet
        hp = paint("#7fb2ff", 0.10, blur=40)
        hp.setBlendMode(skia.BlendMode.kScreen)
        c.drawRRect(skia.RRect.MakeRectXY(SCR.makeOutset(10, 10), 40, 40), hp)

    def draw_controls(self, c, t):
        # inclinaison des manettes : à chaque sélection
        tilt1 = tilt2 = 0.0
        for e in self.ev.all("pick", t):
            d = t - e[0]
            if d < 0.5:
                tilt1 += 0.35 * math.sin(d * 18) * (1 - d / 0.5) * (1 if len(e[2]) % 2 else -1)
        for e in self.ev.all("scene_p2", t):
            d = t - e[0]
            if d < 0.6:
                tilt2 += 0.4 * math.sin(d * 16) * (1 - d / 0.6)
        tilt1 += 0.05 * math.sin(t * 1.3)
        tilt2 += 0.05 * math.sin(t * 1.1 + 1)
        draw_joystick(c, 250, 1395, tilt1)
        draw_joystick(c, 830, 1395, tilt2)
        pressed = {}
        for e in self.ev.all("pick", t) + self.ev.all("winner", t) + self.ev.all("coin", t):
            if 0 <= t - e[0] < 0.18:
                pressed["all"] = True
        for i, x in enumerate((420, 480, 540, 600, 660)):
            colr = "#2f6fe0" if i in (1, 3) else "#1a1b1f"
            draw_button(c, x, 1405 - (12 if i in (1, 3) else 0), colr, pressed.get("all", False) and i in (1, 3))

    def draw_captions(self, c, t):
        for ch in self.captions:
            if not (ch["t0"] <= t < ch["t1"]):
                continue
            size = 60
            f = font(size, "Black")
            words = ch["words"]
            space = f.measureText(" ")
            widths = [f.measureText(w["text"]) for w in words]
            total = sum(widths) + space * (len(words) - 1)
            scale = min(1.0, (W - 140) / total)
            k = ease_back((t - ch["t0"]) / 0.2)
            c.save()
            c.translate(W / 2, 1530)
            c.scale(scale * (0.85 + 0.15 * k), scale * (0.85 + 0.15 * k))
            bg = skia.Rect.MakeLTRB(-total / 2 - 28, -size * 0.85, total / 2 + 28, size * 0.7)
            c.drawRRect(skia.RRect.MakeRectXY(bg, 22, 22), paint("#000000", 0.62))
            x = -total / 2
            for w, wd in zip(words, widths):
                spoken = t >= w["t0"]
                if w["key"] and spoken:
                    r = skia.Rect.MakeLTRB(x - 10, -size * 0.62, x + wd + 10, size * 0.46)
                    c.drawRRect(skia.RRect.MakeRectXY(r.makeOffset(0, 5), 8, 8), paint("#000000", 0.5, blur=6))
                    c.drawRRect(skia.RRect.MakeRectXY(r, 8, 8), paint(GOLD))
                    c.drawString(w["text"], x, size * 0.3, f, paint(INK))
                else:
                    a = 1.0 if spoken else 0.6
                    c.drawString(w["text"], x, size * 0.3, f, paint("#000000", 0.9 * a, stroke=10))
                    c.drawString(w["text"], x, size * 0.3, f, paint("#ffffff", a))
                x += wd + space
            c.restore()
