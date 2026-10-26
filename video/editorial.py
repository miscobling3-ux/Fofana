"""Style « éditorial » (inspiré de la référence) : cadre photo octogonal qui s'ouvre, statistique dans un
disque relié par des lignes fines, transitions en zoom traversant, petit texte + grand mot, faisceaux de lumière."""
import math

import numpy as np
import skia

from engine import W, H, GOLD, INK, col, paint, font, ease, ease_out, ease_back, clamp01, lerp

SAMP = skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear)

LIGHT = dict(bg0="#efede8", bg1="#8f8c86", ink="#141414", sub="#5a5752", line="#3a3835", disc="#f7f6f2",
             disc_edge="#c9c6bf")
DARK = dict(bg0="#1a1a1a", bg1="#020202", ink="#f4f2ee", sub="#a8a49c", line="#d8d5ce", disc="#ecebe6",
            disc_edge="#8c8982")


def octagon(rect, cut):
    l, t, r, b = rect.left(), rect.top(), rect.right(), rect.bottom()
    p = skia.Path()
    p.moveTo(l + cut, t)
    p.lineTo(r - cut, t)
    p.lineTo(r, t + cut)
    p.lineTo(r, b - cut)
    p.lineTo(r - cut, b)
    p.lineTo(l + cut, b)
    p.lineTo(l, b - cut)
    p.lineTo(l, t + cut)
    p.close()
    return p


def bw_filter(amount=1.0):
    """Noir et blanc légèrement sépia, plus contrasté (comme la référence)."""
    g = amount
    r = [0.30, 0.59, 0.11]
    m = []
    for i, tint in enumerate((1.06, 1.0, 0.9)):
        row = [lerp(1 if j == i else 0, r[j] * tint * 1.15, g) for j in range(3)]
        m += row + [0, lerp(0, -0.06, g)]
    m += [0, 0, 0, 1, 0]
    return skia.ColorFilters.Matrix(m)


def draw_text(c, text, x, y, size, color, weight="Black", align="center", alpha=1.0, spacing=0.0):
    f = font(size, weight)
    tw = f.measureText(text) + spacing * max(0, len(text) - 1)
    x0 = x - tw / 2 if align == "center" else (x - tw if align == "right" else x)
    if spacing:
        xx = x0
        for ch in text:
            c.drawString(ch, xx, y, f, paint(color, alpha))
            xx += f.measureText(ch) + spacing
    else:
        c.drawString(text, x0, y, f, paint(color, alpha))
    return tw


def fit_size(text, size, maxw, weight="Black"):
    tw = font(size, weight).measureText(text)
    return size if tw <= maxw else size * maxw / tw


class Editorial:
    """Rend les segments joueur, la séquence « finalistes » et le pronostic."""

    def __init__(self, G, portraits, brand):
        self.G, self.P, self.brand = G, portraits, brand
        rng = np.random.default_rng(21)
        g = (rng.normal(128, 30, (H // 2, W // 2))).clip(0, 255).astype(np.uint8)
        self.paper = skia.Image.fromarray(np.dstack([g, g, g, np.full_like(g, 255)]))

    # ------------------------------------------------------------ fonds
    def background(self, c, th, t, beam=0.0, beam_ang=0.0, beam_c=(W / 2, 820)):
        c.drawPaint(skia.Paint(Shader=skia.GradientShader.MakeRadial(
            (W / 2, H * 0.42), H * 0.75, [col(th["bg0"]), col(th["bg1"])], [0.15, 1])))
        p = skia.Paint(Alphaf=0.07)
        p.setBlendMode(skia.BlendMode.kOverlay)
        c.drawImageRect(self.paper, skia.Rect.MakeWH(W, H), SAMP, p)
        if beam > 0:
            self.light_beam(c, beam_c, beam_ang, beam)

    def light_beam(self, c, center, ang, alpha, length=1500, spread=0.16):
        cx, cy = center
        path = skia.Path()
        path.moveTo(cx, cy)
        path.lineTo(cx + length * math.cos(ang - spread), cy + length * math.sin(ang - spread))
        path.lineTo(cx + length * math.cos(ang + spread), cy + length * math.sin(ang + spread))
        path.close()
        sh = skia.GradientShader.MakeRadial((cx, cy), length, [col("#ffffff", 0.55 * alpha), col("#ffffff", 0)])
        p = skia.Paint(AntiAlias=True, Shader=sh)
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
        c.drawPath(path, p)

    def watermark(self, c, th, alpha=1.0):
        draw_text(c, "@" + self.brand.lower().replace(" ", "").replace("ú", "u"), 70, 175, 26, th["ink"],
                  "Bold", "left", 0.75 * alpha)

    # ------------------------------------------------------------ titre cinétique
    def kinetic(self, c, th, small, big, t, t0, y, alpha=1.0, big_size=110):
        """Petite ligne qui s'écrit mot à mot, puis le grand mot qui tombe (comme « he plays with his / mind »)."""
        if t < t0:
            return
        words = small.split()
        n = clamp01((t - t0) / 0.45) * len(words)
        shown = " ".join(words[:max(0, int(math.ceil(n)))])
        f_small = 34
        draw_text(c, shown, W / 2, y - big_size * 0.92, f_small, th["ink"], "SemiBold", alpha=alpha)
        k = ease_back((t - t0 - 0.3) / 0.35)
        if k > 0:
            size = fit_size(big, big_size, W - 140)
            c.save()
            c.translate(W / 2, y)
            c.scale(1, 0.6 + 0.4 * k)
            draw_text(c, big, 0, 0, size, th["ink"], "Black", alpha=alpha * clamp01(k))
            c.restore()

    # ------------------------------------------------------------ cadre photo
    def frame_photo(self, c, th, pid, rect, t, appear, split, color_amount=0.0, alpha=1.0):
        """Photo dans un octogone ; split (0..1) écarte les deux moitiés comme des portes."""
        cut = rect.width() * 0.13
        dx = split * rect.width() * 0.4
        halves = ((rect.left(), rect.centerX(), -dx), (rect.centerX(), rect.right(), dx))
        oct_ = octagon(rect, cut)
        k = ease_back(appear)
        if k <= 0:
            return
        c.save()
        c.translate(rect.centerX(), rect.centerY())
        c.scale(0.7 + 0.3 * k, 0.7 + 0.3 * k)
        c.translate(-rect.centerX(), -rect.centerY())
        for x0, x1, off in halves:
            c.save()
            c.translate(off, 0)
            clip = skia.Path(oct_)
            c.clipRect(skia.Rect.MakeLTRB(x0, rect.top() - 10, x1, rect.bottom() + 10))
            # ombre portée
            shadow = skia.Path(oct_)
            shadow.offset(0, 18)
            c.drawPath(shadow, paint("#000000", 0.28 * alpha, blur=26))
            c.clipPath(clip, doAntiAlias=True)
            p = skia.Paint(Alphaf=alpha)
            p.setColorFilter(bw_filter(1 - color_amount))
            im = self.P.img[pid]
            iw = im.width()
            c.drawImageRect(im, skia.Rect.MakeXYWH(iw * 0.04, 0, iw * 0.92, iw * 0.92 * rect.height() / rect.width()),
                            rect, SAMP, p)
            c.restore()
            c.save()
            c.translate(off, 0)
            c.clipRect(skia.Rect.MakeLTRB(x0, rect.top() - 10, x1, rect.bottom() + 10))
            c.drawPath(oct_, paint(th["disc_edge"], alpha, stroke=7))
            c.drawPath(oct_, paint("#ffffff", 0.7 * alpha, stroke=2))
            c.restore()
        c.restore()
        return dx

    # ------------------------------------------------------------ disque de statistique
    def stat_disc(self, c, th, center, r, value, label, k, alpha=1.0, gold=False):
        cx, cy = center
        if k <= 0.01:
            return
        c.save()
        c.translate(cx, cy)
        c.scale(k, k)
        c.drawCircle(0, 16, r, paint("#000000", 0.35 * alpha, blur=24))
        c.drawCircle(0, 0, r, skia.Paint(AntiAlias=True, Shader=skia.GradientShader.MakeRadial(
            (-r * 0.3, -r * 0.4), r * 1.5, [col("#ffffff", alpha), col(th["disc"], alpha), col("#cfccc4", alpha)],
            [0, 0.55, 1])))
        c.drawCircle(0, 0, r, paint(GOLD if gold else th["disc_edge"], alpha, stroke=6))
        vs = fit_size(value, r * (0.95 if len(value) <= 3 else 0.62), r * 1.6)
        f = font(vs, "Black")
        tw = f.measureText(value)
        c.drawString(value, -tw / 2, vs * 0.32 - (r * 0.08 if label else 0), f, paint(INK, alpha))
        if label:
            ls = fit_size(label, r * 0.17, r * 1.55, "ExtraBold")
            draw_text(c, label, 0, r * 0.46, ls, "#5a5752", "ExtraBold", alpha=alpha)
        c.restore()

    def connector_lines(self, c, th, center, rect, dx, alpha):
        """Lignes fines du disque vers les coins intérieurs des deux moitiés de la photo."""
        cx, cy = center
        p = paint(th["line"], 0.8 * alpha, stroke=2.2)
        for x, y in ((rect.centerX() - dx, rect.top()), (rect.centerX() - dx, rect.bottom()),
                     (rect.centerX() + dx, rect.top()), (rect.centerX() + dx, rect.bottom())):
            c.drawLine(cx, cy, x, y, p)
        c.drawLine(cx, rect.top() - 140, cx, rect.top() + 20, paint(th["line"], 0.5 * alpha, stroke=3))
        c.drawLine(cx, rect.bottom() - 20, cx, rect.bottom() + 120, paint(th["line"], 0.5 * alpha, stroke=3))

    # ------------------------------------------------------------ segment joueur
    def player(self, c, t, seg, stats, dark=False):
        th = DARK if dark else LIGHT
        pid, rank, t0, t1 = seg["pid"], seg["rank"], seg["t0"], seg["t1"]
        lt = t - t0
        info = self.G.PLAYERS[pid]
        # zoom traversant : entrée (1.3 -> 1) et sortie (1 -> 2.2)
        zin = 1 + 0.3 * (1 - ease_out(lt / 0.55))
        zout = 1 + 1.2 * ease(clamp01((t - (t1 - 0.4)) / 0.4)) ** 2
        z = zin * zout
        fade_out = 1 - clamp01((t - (t1 - 0.2)) / 0.2)
        beam = 0.0
        ang = -math.pi / 2 - 0.9 + 0.35 * math.sin(lt * 0.9)
        if dark:
            beam = 0.9 * clamp01(lt / 0.6)
        self.background(c, th, t, beam, ang, (W / 2, 800))
        c.save()
        c.translate(W / 2, 800)
        c.scale(z, z)
        c.translate(-W / 2, -800)
        # grand rang en filigrane
        draw_text(c, f"#{rank}", W - 60, 330, 220, th["ink"], "Black", "right", 0.07)
        # titre cinétique
        self.kinetic(c, th, f"número {self.G.RANK_WORDS[rank]}", info["name"], t, t0 + 0.05, 395)
        draw_text(c, info["club"], W / 2, 452, 30, th["sub"], "Bold", alpha=clamp01((lt - 0.6) / 0.3), spacing=3)
        rect = skia.Rect.MakeXYWH(W / 2 - 270, 520, 540, 560)
        ps = [s for s in stats if t0 <= s["t"] < t1]
        first = ps[0]["t"] if ps else t1 + 1
        split = ease(clamp01((t - first + 0.1) / 0.55))
        dx = self.frame_photo(c, th, pid, rect, t, clamp01(lt / 0.45), split) or 0
        center = (rect.centerX(), rect.centerY())
        cur = None
        for i, s in enumerate(ps):
            if t >= s["t"]:
                cur = i
        if cur is not None:
            self.connector_lines(c, th, center, rect, dx, clamp01(split * 1.5))
            # disque précédent qui « traverse » l'écran
            if cur > 0:
                prev = ps[cur - 1]
                k = (t - ps[cur]["t"]) / 0.35
                if k < 1:
                    self.stat_disc(c, th, center, 190, prev["value"], prev["label"], 1 + 1.6 * ease(k), 1 - k)
            s = ps[cur]
            self.stat_disc(c, th, center, 190, s["value"], s["label"], ease_back((t - s["t"]) / 0.35),
                           gold=dark)
        # liste des stats déjà citées
        for i, s in enumerate(ps):
            if t < s["t"]:
                break
            k = ease_out((t - s["t"]) / 0.3)
            y = 1185 + i * 62
            txt = f"{s['value']} {s['label']}" if s["value"][:1].isdigit() else s["label"]
            f = font(34, "ExtraBold")
            tw = f.measureText(txt)
            x = W / 2 - tw / 2 + 40 * (1 - k)
            c.drawRect(skia.Rect.MakeXYWH(x - 34, y - 21, 14, 14), paint(GOLD, k))
            c.drawString(txt, x, y - 2, f, paint(th["ink"], k))
        c.restore()
        self.watermark(c, th)
        if fade_out < 1:
            c.drawPaint(paint(th["bg0"], 1 - fade_out))

    # ------------------------------------------------------------ « deux joueurs » : disque -> rond central
    def two(self, c, t, t0, t1):
        th = DARK
        lt = t - t0
        self.background(c, th, t)
        zoom_out = ease(clamp01((lt - 1.2) / 1.4))
        r = lerp(250, 120, zoom_out)
        cx, cy = W / 2, 820
        # terrain qui apparaît en dézoomant (le disque devient le rond central)
        if zoom_out > 0:
            a = zoom_out
            p = paint("#d8d5ce", 0.85 * a, stroke=4)
            s = lerp(3.0, 1.0, a)
            pw, ph = 900 * s, 1500 * s
            c.drawRect(skia.Rect.MakeXYWH(cx - pw / 2, cy - ph / 2, pw, ph), p)
            c.drawLine(cx - pw / 2, cy, cx + pw / 2, cy, p)
            for sgn in (-1, 1):
                by = cy + sgn * ph / 2
                bh = 260 * s
                c.drawRect(skia.Rect.MakeXYWH(cx - 270 * s, by - (bh if sgn > 0 else 0), 540 * s, bh), p)
        else:
            c.drawLine(cx, 0, cx, H, paint("#d8d5ce", 0.6, stroke=4))
        self.light_beam(c, (cx, cy), -math.pi / 2 + 0.8 * math.sin(lt * 1.2), 0.8 * (1 - zoom_out))
        k = ease_back(lt / 0.4)
        c.drawCircle(cx, cy, r * k, paint("#ecebe6"))
        draw_text(c, "2", cx, cy + r * 0.38, r * 1.1 * k, INK, "Black")
        # petit texte + grand mot
        self.kinetic(c, th, "todo se decide entre", "DOS", t, t0 + 0.2, 420,
                     alpha=1 - clamp01((zoom_out - 0.2) / 0.3))
        if zoom_out > 0.3:
            a = clamp01((zoom_out - 0.3) / 0.5)
            for pid, y in (("yamal", cy - 430), ("kane", cy + 430)):
                rect = skia.Rect.MakeXYWH(cx - 150, y - 150, 300, 300)
                c.save()
                c.clipPath(octagon(rect, 40), doAntiAlias=True)
                pp = skia.Paint(Alphaf=a)
                pp.setColorFilter(bw_filter(1.0))
                c.drawImageRect(self.P.img[pid], rect, SAMP, pp)
                c.restore()
                c.drawPath(octagon(rect, 40), paint("#ecebe6", a, stroke=5))
        self.watermark(c, th)
        fo = clamp01((t - (t1 - 0.2)) / 0.2)
        if fo > 0:
            c.drawPaint(paint(th["bg0"], fo))

    # ------------------------------------------------------------ favori / pronostic / vainqueur
    def finale(self, c, t, ev):
        th = DARK
        fav = ev.last("fav", t)
        pred = ev.last("predict", t)
        win = ev.last("winner", t)
        base = fav[0] if fav else t
        lt = t - base
        self.background(c, th, t)
        if win:
            self.winner(c, t, t - win[0])
            return
        swing = 0.0
        if pred:
            pl = t - pred[0]
            swing = math.sin(pl * (3 + pl * 2.2))
        ang = -math.pi / 2 + 0.55 * swing if pred else -math.pi / 2 - 0.5
        self.light_beam(c, (W / 2, H + 40), ang, 0.9, length=2200, spread=0.13)
        for pid, x, name in (("kane", W / 2 - 245, "KANE"), ("yamal", W / 2 + 245, "YAMAL")):
            rect = skia.Rect.MakeXYWH(x - 210, 560, 420, 470)
            lit = 1.0
            if pred:
                lit = 0.35 + 0.65 * clamp01((swing * (-1 if pid == "kane" else 1) + 0.3) / 0.6)
            k = ease_back(lt / 0.45)
            c.save()
            c.translate(rect.centerX(), rect.centerY())
            c.scale(k, k)
            c.translate(-rect.centerX(), -rect.centerY())
            oc = octagon(rect, 55)
            c.drawPath(oc, paint("#000000", 0.4, blur=20))
            c.save()
            c.clipPath(oc, doAntiAlias=True)
            pp = skia.Paint(Alphaf=lit)
            pp.setColorFilter(bw_filter(1.0))
            c.drawImageRect(self.P.img[pid], rect, SAMP, pp)
            c.restore()
            c.drawPath(oc, paint("#ecebe6", lit, stroke=5))
            c.restore()
            draw_text(c, name, x, 1110, 64, "#f4f2ee", "Black", alpha=lit)
        if fav and not pred:
            kf = ease_back((t - fav[0] - 0.9) / 0.35)
            if kf > 0:
                c.save()
                c.translate(W / 2 - 245, 610)
                c.rotate(-7)
                c.scale(kf, kf)
                r = skia.Rect.MakeXYWH(-175, -42, 350, 84)
                c.drawRect(r, paint(GOLD))
                draw_text(c, "FAVORITO", 0, 18, 50, INK, "Black")
                c.restore()
            self.kinetic(c, th, "las casas de apuestas", "KANE vs YAMAL", t, base + 0.1, 400, big_size=100)
        if pred:
            self.kinetic(c, th, "mi predicción para el", "BALÓN DE ORO", t, pred[0], 400, big_size=110)
        self.watermark(c, th)

    def winner(self, c, t, lt):
        th = DARK
        for i in range(3):
            self.light_beam(c, (W / 2, H + 60), -math.pi / 2 + (i - 1) * 0.42 + 0.1 * math.sin(t * 1.5 + i),
                            0.8, length=2300, spread=0.1)
        c.drawPaint(skia.Paint(Shader=skia.GradientShader.MakeRadial(
            (W / 2, 800), 700, [col(GOLD, 0.35 * clamp01(lt / 0.5)), col(GOLD, 0)])))
        rect = skia.Rect.MakeXYWH(W / 2 - 300, 470, 600, 660)
        k = ease_back(lt / 0.5)
        color_in = clamp01((lt - 0.4) / 0.8)
        c.save()
        c.translate(rect.centerX(), rect.centerY())
        c.scale(0.6 + 0.4 * k, 0.6 + 0.4 * k)
        c.translate(-rect.centerX(), -rect.centerY())
        oc = octagon(rect, 80)
        c.drawPath(oc, paint(GOLD, 0.6, blur=40))
        c.save()
        c.clipPath(oc, doAntiAlias=True)
        pp = skia.Paint()
        pp.setColorFilter(bw_filter(1 - color_in))
        c.drawImageRect(self.P.img["kane"], rect, SAMP, pp)
        c.restore()
        c.drawPath(oc, paint(GOLD, 1, stroke=8))
        c.restore()
        self.kinetic(c, th, "balón de oro 2026", "HARRY KANE", t, t - lt + 0.05, 390, big_size=120)
        draw_text(c, "PREDICCIÓN", W / 2, 1210, 34, GOLD, "Black", alpha=clamp01((lt - 0.8) / 0.3), spacing=8)
        rng = np.random.default_rng(3)
        for i in range(90):
            x0, sp, ph, sz = rng.random() * W, 260 + rng.random() * 380, rng.random() * 9, 8 + rng.random() * 10
            y = ((lt + ph) * sp) % (H + 80) - 40
            x = x0 + 30 * math.sin(lt * 2 + ph)
            c.save()
            c.translate(x, y)
            c.rotate((lt + ph) * 200)
            c.drawRect(skia.Rect.MakeXYWH(-sz / 2, -sz / 4, sz, sz / 2),
                       paint(GOLD if i % 3 else "#ffffff", 0.9 * clamp01(lt / 0.3)))
            c.restore()
        self.watermark(c, th)
