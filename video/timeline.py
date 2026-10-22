"""Timeline : pistes animées (caméra, joueurs, overlays) et composition d'une image."""
import math
import numpy as np
import skia

from engine import (W, H, PPM, Camera, GOLD, INK, RED, col, paint, font, pill, ease, ease_out, ease_back,
                    clamp01, lerp, draw_token, draw_board, draw_goal, draw_qmark, make_pitch_texture,
                    make_board_texture)


class Track:
    def __init__(self, init):
        self.init = init
        self.keys = []  # (t0, dur, target, easing)

    def to(self, t0, target, dur=0.8, fn=ease):
        self.keys.append((t0, dur, target, fn))
        self.keys.sort(key=lambda k: k[0])

    def set(self, t0, target):
        self.to(t0, target, 0.0001)

    def __call__(self, t):
        v = self.init
        for t0, dur, target, fn in self.keys:
            if t < t0:
                break
            k = fn((t - t0) / dur)
            v = mix(v, target, k)
        return v


def mix(a, b, k):
    if isinstance(a, Camera):
        return Camera.blend(a, b, k)
    if isinstance(a, tuple):
        return tuple(lerp(x, y, k) for x, y in zip(a, b))
    return lerp(a, b, k)


class Player:
    def __init__(self, pid, num, team, label, pos):
        self.pid, self.num, self.team, self.label = pid, num, team, label
        self.pos = Track(pos)
        self.gold = Track(0.0)
        self.ring = Track(0.0)
        self.alpha = Track(1.0)
        self.show_label = Track(1.0 if label else 0.0)
        self.dim = Track(0.0)


class Timeline:
    def __init__(self, brand, chapters):
        self.brand = brand
        self.chapters = chapters  # [(t0, nom)]
        self.cam = None
        self.players = {}
        self.annots = []  # dict(t0, t1, fn)
        self.tint = Track(0.0)
        self.leaks = Track(0.0)
        self.punch = []  # (t, force)
        self.titles = []  # dict
        self.captions = []  # chunks
        self.duration = 0
        self.outro_t = None

    def add_player(self, *a):
        p = Player(*a)
        self.players[p.pid] = p
        return p

    def annot(self, t0, t1, fn, fade_in=0.25, fade_out=0.3):
        self.annots.append(dict(t0=t0, t1=t1, fn=fn, fi=fade_in, fo=fade_out))

    def title(self, t0, t1, text, y=520, size=150, color=GOLD, sub=None):
        self.titles.append(dict(t0=t0, t1=t1, text=text, y=y, size=size, color=color, sub=sub))


# ---------------------------------------------------------------- composition
class Renderer:
    def __init__(self, tl):
        self.tl = tl
        self.tex, (self.x0, self.y1) = make_pitch_texture(tl.brand)
        self.board = make_board_texture(tl.brand)
        rng = np.random.default_rng(11)
        g = (rng.normal(128, 40, (H // 2, W // 2))).clip(0, 255).astype(np.uint8)
        rgba = np.dstack([g, g, g, np.full_like(g, 255)])
        self.grain = skia.Image.fromarray(rgba)
        self.samp = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)
        self.surf = skia.Surface(W, H)

    def camera(self, t):
        cam = self.tl.cam(t)
        # punch-in (zoom sec sur les impacts)
        z = 0.0
        for tp, force in self.tl.punch:
            if tp <= t < tp + 0.6:
                k = (t - tp) / 0.6
                z += force * math.sin(math.pi * min(1, k * 2.5)) * (1 - k) ** 1.5
        # léger flottement permanent
        d = cam.dist * (1 - 0.12 * z) + 0.6 * math.sin(t * 0.7)
        return Camera(cam.tx + 0.4 * math.sin(t * 0.5), cam.ty, d, cam.phi, cam.fov, cam.yaw, cam.oy,
                      cam.roll + 0.25 * math.sin(t * 0.4))

    def frame(self, t):
        tl = self.tl
        c = self.surf.getCanvas()
        cam = self.camera(t)
        # fond
        c.drawPaint(skia.Paint(Shader=skia.GradientShader.MakeLinear(
            [(0, 0), (0, H)], [col("#08140d"), col("#123020"), col("#0b1a11")], [0, 0.45, 1])))
        c.save()
        c.concat(cam.ground_matrix(PPM, self.x0, self.y1))
        c.drawImage(self.tex, 0, 0, self.samp)
        c.restore()
        draw_board(c, cam, self.board, (-37, 56.5), (37, 56.5), offset=t * 0.6)
        draw_board(c, cam, self.board, (37, 56.5), (37, -56.5), offset=t * 0.6)
        draw_board(c, cam, self.board, (-37, -56.5), (-37, 56.5), offset=t * 0.6)
        draw_goal(c, cam, 52.5)

        # annotations au sol (sous les pions)
        top_layer = []
        for a in tl.annots:
            if a["t0"] <= t < a["t1"] + a["fo"]:
                al = clamp01((t - a["t0"]) / a["fi"]) * clamp01((a["t1"] + a["fo"] - t) / a["fo"])
                pr = (t - a["t0"])
                res = a["fn"](c, cam, t, pr, al)
                if callable(res):
                    top_layer.append(res)

        # pions triés par profondeur
        items = []
        for p in tl.players.values():
            x, y = p.pos(t)
            items.append((cam.project(x, y)[2], p, x, y))
        items.sort(key=lambda q: -q[0])
        tok_scale = max(1.0, cam.dist / 62) ** 0.85
        for _, p, x, y in items:
            g = p.gold(t)
            style = "gold" if g > 0.5 else ("home" if p.team == "home" else "away")
            dim = p.dim(t)
            draw_token(c, cam, x, y, p.num, style, p.label, alpha=p.alpha(t) * (1 - 0.55 * dim),
                       label_gold=g > 0.5, ring=p.ring(t), t=t, label_alpha=p.show_label(t), scale=tok_scale)
        for fn in top_layer:
            fn(c, cam, t)

        self.overlays(c, t)
        self.header(c, t)
        self.draw_titles(c, t)
        self.draw_captions(c, t)
        if tl.outro_t is not None and t >= tl.outro_t:
            self.outro(c, t - tl.outro_t)
        # grain
        gp = skia.Paint(Alphaf=0.045)
        gp.setBlendMode(skia.BlendMode.kOverlay)
        ox = (int(t * 30) * 37) % 200
        c.drawImageRect(self.grain, skia.Rect.MakeXYWH(-ox, -ox * 0.7, W + 200, H + 200), self.samp, gp)
        return self.surf.makeImageSnapshot()

    # ------------------------------------------------------------ overlays
    def overlays(self, c, t):
        tl = self.tl
        # vignette
        c.drawPaint(skia.Paint(Shader=skia.GradientShader.MakeRadial(
            (W / 2, H * 0.55), H * 0.75, [col("#000000", 0), col("#000000", 0.55)], [0.55, 1])))
        # assombrir le haut pour l'en-tête
        c.drawRect(skia.Rect.MakeWH(W, 420), skia.Paint(Shader=skia.GradientShader.MakeLinear(
            [(0, 0), (0, 420)], [col("#061009", 0.9), col("#061009", 0)])))
        tint = tl.tint(t)
        if tint > 0.01:
            p = skia.Paint(Shader=skia.GradientShader.MakeRadial(
                (W / 2, H * 0.5), H * 0.7, [col("#ff1a1a", 0.0), col("#c01010", 0.55 * tint)], [0.25, 1]))
            c.drawPaint(p)
            c.drawPaint(paint("#7a0000", 0.12 * tint))
        lk = tl.leaks(t)
        if lk > 0.01:
            for i, (cc, ph) in enumerate((("#19d3c5", 0.0), ("#ff3fa4", 2.1), ("#3fa2ff", 4.2), ("#ff3fa4", 5.5))):
                x = W * (0.15 + 0.7 * (0.5 + 0.5 * math.sin(t * 0.9 + ph)))
                p = paint(cc, 0.42 * lk, blur=120)
                p.setBlendMode(skia.BlendMode.kScreen)
                c.drawRect(skia.Rect.MakeXYWH(x - 110, -100, 220, H + 200), p)
            # confettis dorés
            rng = np.random.default_rng(4)
            for k in range(70):
                x0, sp, ph, sz = rng.random() * W, 250 + rng.random() * 350, rng.random() * 10, 6 + rng.random() * 10
                tt = (t + ph) * sp
                y = (tt % (H + 100)) - 50
                x = x0 + 30 * math.sin(tt / 80 + ph)
                c.save()
                c.translate(x, y)
                c.rotate(tt * 0.8)
                c.drawRect(skia.Rect.MakeXYWH(-sz / 2, -sz / 4, sz, sz / 2),
                           paint(GOLD if k % 3 else "#ffffff", 0.9 * lk))
                c.restore()

    # ------------------------------------------------------------ en-tête
    def header(self, c, t):
        tl = self.tl
        a = 1.0
        if tl.outro_t is not None:
            a = clamp01(1 - (t - tl.outro_t) / 0.4)
        if a <= 0:
            return
        x0, y0 = 54, 150
        # mini logo
        draw_badge(c, x0 + 28, y0, 28, a, small=True, brand=tl.brand)
        f = font(30, "Black")
        parts = self.tl.brand.split(" ", 1)
        c.drawString(parts[0], x0 + 72, y0 + 11, f, paint("#ffffff", a))
        w0 = f.measureText(parts[0] + " ")
        if len(parts) > 1:
            c.drawString(parts[1], x0 + 72 + w0, y0 + 11, f, paint(GOLD, a))
        # barre de progression segmentée
        n = len(tl.chapters)
        bx, by, bw = x0, y0 + 48, W - 2 * x0
        gap = 8
        sw = (bw - gap * (n - 1)) / n
        for i, (ct, name) in enumerate(tl.chapters):
            ct1 = tl.chapters[i + 1][0] if i + 1 < n else (tl.outro_t or tl.duration)
            fill = clamp01((t - ct) / max(0.01, ct1 - ct))
            r = skia.Rect.MakeXYWH(bx + i * (sw + gap), by, sw, 7)
            c.drawRRect(skia.RRect.MakeRectXY(r, 3.5, 3.5), paint("#ffffff", 0.18 * a))
            if fill > 0:
                r2 = skia.Rect.MakeXYWH(r.left(), by, sw * fill, 7)
                c.drawRRect(skia.RRect.MakeRectXY(r2, 3.5, 3.5), paint(GOLD, a))
        # chapitre courant
        cur, ct0 = None, 0
        for ct, name in tl.chapters:
            if t >= ct:
                cur, ct0 = name, ct
        if cur:
            k = ease_out((t - ct0) / 0.45)
            f2 = font(26, "ExtraBold")
            yy = by + 52
            c.drawRect(skia.Rect.MakeXYWH(bx, yy - 17, 10, 10), paint(GOLD, a * k))
            c.save()
            c.clipRect(skia.Rect.MakeXYWH(bx + 20, yy - 40, W, 60))
            c.drawString(cur, bx + 22 - 40 * (1 - k), yy - 6, f2, paint(GOLD, a * k))
            c.restore()

    # ------------------------------------------------------------ titres
    def draw_titles(self, c, t):
        for d in self.tl.titles:
            if not (d["t0"] <= t < d["t1"] + 0.3):
                continue
            k = ease_back((t - d["t0"]) / 0.35)
            a = clamp01((t - d["t0"]) / 0.12) * clamp01((d["t1"] + 0.3 - t) / 0.3)
            f = font(d["size"], "Black")
            tw = f.measureText(d["text"])
            if tw > W - 80:
                f = font(d["size"] * (W - 80) / tw, "Black")
                tw = f.measureText(d["text"])
            c.save()
            c.translate(W / 2, d["y"])
            s = 0.4 + 0.6 * k
            c.scale(s, s)
            c.rotate(-3 * (1 - k))
            sz = f.getSize()
            c.drawString(d["text"], -tw / 2 + 6, sz * 0.36 + 8, f, paint("#000000", 0.6 * a, blur=8))
            stroke = paint("#000000", a, stroke=sz * 0.08)
            c.drawString(d["text"], -tw / 2, sz * 0.36, f, stroke)
            c.drawString(d["text"], -tw / 2, sz * 0.36, f, paint(d["color"], a))
            if d["sub"]:
                pill(c, 0, sz * 0.36 + 60, d["sub"], 34, a, bg="#0d0f10", fg="#ffffff", border=GOLD)
            c.restore()

    # ------------------------------------------------------------ sous-titres
    def draw_captions(self, c, t):
        for ch in self.tl.captions:
            if not (ch["t0"] <= t < ch["t1"]):
                continue
            size = 62
            f = font(size, "ExtraBold")
            words = ch["words"]
            space = f.measureText(" ")
            widths = [f.measureText(w["text"]) for w in words]
            total = sum(widths) + space * (len(words) - 1)
            scale = min(1.0, (W - 160) / total)
            k = ease_back((t - ch["t0"]) / 0.22)
            y = 1320
            c.save()
            c.translate(W / 2, y)
            c.scale(scale * (0.85 + 0.15 * k), scale * (0.85 + 0.15 * k))
            x = -total / 2
            for w, wd in zip(words, widths):
                spoken = t >= w["t0"]
                active = w["t0"] <= t < w["t1"]
                if w["key"] and spoken:
                    pk = ease_back((t - w["t0"]) / 0.18)
                    r = skia.Rect.MakeLTRB(x - 10, -size * 0.62, x + wd + 10, size * 0.46)
                    c.save()
                    c.translate(x + wd / 2, 0)
                    c.scale(0.9 + 0.1 * pk, 0.9 + 0.1 * pk)
                    c.translate(-(x + wd / 2), 0)
                    c.drawRRect(skia.RRect.MakeRectXY(r.makeOffset(0, 5), 10, 10), paint("#000000", 0.5, blur=6))
                    c.drawRRect(skia.RRect.MakeRectXY(r, 10, 10), paint(GOLD))
                    c.drawString(w["text"], x, size * 0.3, f, paint(INK))
                    c.restore()
                else:
                    a = 1.0 if spoken else 0.55
                    c.drawString(w["text"], x + 3, size * 0.3 + 5, f, paint("#000000", 0.55 * a, blur=5))
                    c.drawString(w["text"], x, size * 0.3, f, paint("#000000", 0.85 * a, stroke=9))
                    c.drawString(w["text"], x, size * 0.3, f,
                                 paint(GOLD if (active and not w["key"]) else "#ffffff", a))
                x += wd + space
            c.restore()

    # ------------------------------------------------------------ outro
    def outro(self, c, tt):
        a = clamp01(tt / 0.5)
        c.drawPaint(paint("#030605", 0.82 * a))
        c.drawPaint(skia.Paint(Shader=skia.GradientShader.MakeRadial(
            (W / 2, H * 0.42), 600, [col(GOLD, 0.16 * a), col(GOLD, 0)])))
        k = ease_back(tt / 0.6)
        c.save()
        c.translate(W / 2, H * 0.42)
        c.scale(0.6 + 0.4 * k, 0.6 + 0.4 * k)
        draw_badge(c, 0, 0, 230, a, brand=self.tl.brand)
        c.restore()
        k2 = ease_out((tt - 0.4) / 0.5)
        f = font(56, "Black")
        y = H * 0.42 + 330 + 30 * (1 - k2)
        t1, t2 = "LUIS ENRIQUE, ", "¿UN GENIO?"
        w1, w2 = f.measureText(t1), f.measureText(t2)
        x = W / 2 - (w1 + w2) / 2
        c.drawString(t1, x, y, f, paint("#ffffff", k2))
        c.drawString(t2, x + w1, y, f, paint(GOLD, k2))
        f2 = font(34, "SemiBold")
        s = "Dímelo en los comentarios"
        c.drawString(s, W / 2 - f2.measureText(s) / 2, y + 62, f2, paint("#d9d9d9", k2))
        k3 = ease_back((tt - 0.9) / 0.4)
        if k3 > 0:
            pill(c, W / 2, y + 160, "SÍGUEME PARA MÁS ANÁLISIS", 30, clamp01(k3), bg=GOLD, fg=INK,
                 pad=(26, 16))


def draw_badge(c, x, y, r, a=1.0, small=False, brand="FOFANA FÚTBOL"):
    """Écusson rond de la chaîne : ballon + couronne + nom."""
    c.save()
    c.translate(x, y)
    c.drawCircle(0, 6 if not small else 2, r * 1.04, paint("#000000", 0.6 * a, blur=r * 0.12))
    c.drawCircle(0, 0, r, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (0, -r * 0.3), r * 1.2, [col("#2b3d2f", a), col("#0b0f0c", a)])))
    if not small:
        # rayons de projecteurs
        for i in range(-3, 4):
            p = paint("#ffffff", 0.06 * a, blur=6)
            path = skia.Path()
            path.moveTo(i * r * 0.25, -r * 0.9)
            path.lineTo(i * r * 0.25 - r * 0.08, r * 0.6)
            path.lineTo(i * r * 0.25 + r * 0.08, r * 0.6)
            path.close()
            c.drawPath(path, p)
        # pelouse
        c.save()
        c.clipPath(skia.Path.Circle(0, 0, r))
        c.drawRect(skia.Rect.MakeLTRB(-r, r * 0.45, r, r), paint("#3d7a34", a))
        c.drawLine(-r, r * 0.45, r, r * 0.45, paint("#ffffff", 0.5 * a, stroke=3))
        c.restore()
    # ballon
    br = r * (0.36 if not small else 0.5)
    by = -r * 0.12 if not small else 0
    c.drawCircle(0, by, br, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
        (-br * 0.3, by - br * 0.4), br * 1.4, [col("#ffffff", a), col("#9a9a9a", a)])))
    pent = skia.Path()
    for i in range(5):
        ang = -math.pi / 2 + i * 2 * math.pi / 5
        px, py = br * 0.38 * math.cos(ang), by + br * 0.38 * math.sin(ang)
        (pent.moveTo if i == 0 else pent.lineTo)(px, py)
    pent.close()
    c.drawPath(pent, paint("#151515", a))
    for i in range(5):
        ang = -math.pi / 2 + i * 2 * math.pi / 5
        c.drawLine(br * 0.38 * math.cos(ang), by + br * 0.38 * math.sin(ang),
                   br * 0.95 * math.cos(ang), by + br * 0.95 * math.sin(ang), paint("#151515", a, stroke=br * 0.08))
    # couronne
    cw, chh = r * (0.42 if not small else 0.6), r * (0.2 if not small else 0.3)
    cy = by - br - chh * 0.2
    crown = skia.Path()
    crown.moveTo(-cw / 2, cy)
    crown.lineTo(-cw / 2, cy - chh)
    crown.lineTo(-cw / 4, cy - chh * 0.45)
    crown.lineTo(0, cy - chh * 1.25)
    crown.lineTo(cw / 4, cy - chh * 0.45)
    crown.lineTo(cw / 2, cy - chh)
    crown.lineTo(cw / 2, cy)
    crown.close()
    c.drawPath(crown, paint(GOLD, a))
    # anneau
    c.drawCircle(0, 0, r, paint(GOLD, a, stroke=max(2, r * 0.05)))
    if not small:
        f = font(r * 0.26, "BlackItalic")
        for i, (txt, cc) in enumerate(zip(brand.split(" ", 1), ("#ffffff", GOLD))):
            tw = f.measureText(txt)
            yy = r * 0.42 + i * r * 0.27
            c.drawString(txt, -tw / 2 + 3, yy + 4, f, paint("#000000", 0.7 * a, blur=3))
            c.drawString(txt, -tw / 2, yy, f, paint(cc, a))
    c.restore()
