"""Moteur de rendu : terrain 3D en perspective, pions, annotations, textes (skia)."""
import math
import numpy as np
import skia

W, H = 1080, 1920
FPS = 30

FONT_DIR = "/usr/share/fonts/truetype/montserrat/"
_tf_cache = {}


def typeface(weight="ExtraBold"):
    if weight not in _tf_cache:
        _tf_cache[weight] = skia.Typeface.MakeFromFile(FONT_DIR + f"Montserrat-{weight}.ttf")
    return _tf_cache[weight]


def font(size, weight="ExtraBold"):
    f = skia.Font(typeface(weight), size)
    f.setEdging(skia.Font.Edging.kAntiAlias)
    f.setSubpixel(True)
    return f


def col(hexstr, a=1.0):
    hexstr = hexstr.lstrip("#")
    r, g, b = int(hexstr[0:2], 16), int(hexstr[2:4], 16), int(hexstr[4:6], 16)
    return skia.Color4f(r / 255, g / 255, b / 255, max(0.0, min(1.0, a)))


GOLD = "#f2c14e"
GOLD_DARK = "#b8862b"
WHITE = "#ffffff"
INK = "#14161a"
RED = "#e5383b"


def paint(c, a=1.0, stroke=0, aa=True, blur=0):
    p = skia.Paint(AntiAlias=aa)
    p.setColor4f(col(c, a) if isinstance(c, str) else c)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


# ---------------------------------------------------------------- easing
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def ease(x):
    x = clamp01(x)
    return 4 * x * x * x if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def ease_back(x):
    x = clamp01(x)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def lerp(a, b, t):
    return a + (b - a) * t


# ---------------------------------------------------------------- camera
class Camera:
    """Caméra perspective visant un point du terrain (mètres, y vers le but adverse)."""

    def __init__(self, tx, ty, dist, phi, fov=50.0, yaw=0.0, oy=0.0, roll=0.0):
        self.tx, self.ty, self.dist, self.phi, self.fov, self.yaw, self.oy, self.roll = (
            tx, ty, dist, phi, fov, yaw, oy, roll)
        p, yw = math.radians(phi), math.radians(yaw)
        d = np.array([math.sin(yw) * math.cos(p), math.cos(yw) * math.cos(p), -math.sin(p)])
        self.C = np.array([tx, ty, 0.0]) - dist * d
        r = np.cross(d, [0, 0, 1.0])
        r /= np.linalg.norm(r)
        u = np.cross(r, d)
        rl = math.radians(roll)
        r, u = r * math.cos(rl) + u * math.sin(rl), u * math.cos(rl) - r * math.sin(rl)
        self.R = np.stack([r, u, d])
        self.F = (H / 2) / math.tan(math.radians(fov) / 2)
        self.cx, self.cy = W / 2, H / 2 + oy
        K = np.array([[self.F, 0, self.cx], [0, -self.F, self.cy], [0, 0, 1.0]])
        self.Hg = K @ np.column_stack([self.R[:, 0], self.R[:, 1], -self.R @ self.C])

    @staticmethod
    def blend(a, b, t):
        keys = ("tx", "ty", "dist", "phi", "fov", "yaw", "oy", "roll")
        return Camera(*[lerp(getattr(a, k), getattr(b, k), t) for k in keys])

    def project(self, x, y, z=0.0):
        pc = self.R @ (np.array([x, y, z]) - self.C)
        zc = max(pc[2], 0.1)
        return self.cx + self.F * pc[0] / zc, self.cy - self.F * pc[1] / zc, zc

    def scale_at(self, x, y, z=0.0):
        """pixels par mètre à ce point."""
        return self.F / self.project(x, y, z)[2]

    def ground_matrix(self, ppm, x0, y1):
        S = np.array([[1 / ppm, 0, x0], [0, -1 / ppm, y1], [0, 0, 1.0]])
        M = self.Hg @ S
        M = M / M[2, 2]
        return skia.Matrix.MakeAll(*[float(v) for v in M.flatten()])


# ---------------------------------------------------------------- pitch texture
PITCH_L, PITCH_W = 105.0, 68.0
MARGIN = 7.0
PPM = 18


def make_pitch_texture(brand):
    w_m, h_m = PITCH_W + 2 * MARGIN, PITCH_L + 2 * MARGIN
    tw, th = int(w_m * PPM), int(h_m * PPM)
    surf = skia.Surface(tw, th)
    c = surf.getCanvas()
    c.clear(col("#172e1b"))
    # bandes de tonte
    ox, oy = MARGIN * PPM, MARGIN * PPM
    n = 18
    sh = PITCH_L * PPM / n
    for i in range(n):
        c.drawRect(skia.Rect.MakeXYWH(ox, oy + i * sh, PITCH_W * PPM, sh + 1),
                   paint("#3f6834" if i % 2 == 0 else "#375e2d"))
    # bruit / texture herbe
    rng = np.random.default_rng(3)
    noise = (rng.random((th // 4, tw // 4)) * 255).astype(np.uint8)
    rgba = np.zeros((th // 4, tw // 4, 4), np.uint8)
    rgba[..., :3] = noise[..., None]
    rgba[..., 3] = 255
    nimg = skia.Image.fromarray(rgba)
    np_ = skia.Paint(Alphaf=0.06)
    np_.setBlendMode(skia.BlendMode.kOverlay)
    c.drawImageRect(nimg, skia.Rect.MakeWH(tw, th), skia.SamplingOptions(skia.FilterMode.kLinear), np_)
    # vignette au centre plus clair
    shader = skia.GradientShader.MakeRadial(
        (tw / 2, th / 2), max(tw, th) * 0.7,
        [col("#ffffff", 0.07), col("#000000", 0.0), col("#000000", 0.35)], [0, 0.6, 1])
    c.drawPaint(skia.Paint(Shader=shader))

    def P(x, y):
        return (ox + (x + PITCH_W / 2) * PPM, oy + (PITCH_L / 2 - y) * PPM)

    lp = paint("#e9f1e4", 0.8, stroke=0.13 * PPM)
    lp.setStrokeCap(skia.Paint.kButt_Cap)

    def rect(x0, y0, x1, y1):
        a, b = P(x0, y1), P(x1, y0)
        c.drawRect(skia.Rect.MakeLTRB(a[0], a[1], b[0], b[1]), lp)

    rect(-34, -52.5, 34, 52.5)
    c.drawLine(*P(-34, 0), *P(34, 0), lp)
    c.drawCircle(*P(0, 0), 9.15 * PPM, lp)
    c.drawCircle(*P(0, 0), 0.3 * PPM, paint("#e9f1e4", 0.8))
    for s in (1, -1):
        for half_w, depth in ((20.16, 16.5), (9.16, 5.5)):
            y_in = s * (52.5 - depth)
            rect(-half_w, min(y_in, s * 52.5), half_w, max(y_in, s * 52.5))
        c.drawCircle(*P(0, s * 41.5), 0.3 * PPM, paint("#e9f1e4", 0.8))
        # arc de surface
        cx, cy = P(0, s * 41.5)
        r = 9.15 * PPM
        oval = skia.Rect.MakeLTRB(cx - r, cy - r, cx + r, cy + r)
        if s > 0:
            c.drawArc(oval, 37, 106, False, lp)
        else:
            c.drawArc(oval, 217, 106, False, lp)
    # logo watermark au rond central
    cx, cy = P(0, 0)
    c.drawCircle(cx, cy, 8.6 * PPM, paint("#6b4a2a", 0.28))
    f = font(2.1 * PPM, "BlackItalic")
    words = brand.split(" ", 1)
    for i, wd in enumerate(words):
        tw_ = f.measureText(wd)
        c.save()
        c.translate(cx, cy + (i - 0.35) * 2.4 * PPM)
        c.rotate(-8)
        c.drawString(wd, -tw_ / 2, 0, f, paint("#e8d3b0", 0.18))
        c.restore()
    return surf.makeImageSnapshot(), (-(PITCH_W / 2 + MARGIN), PITCH_L / 2 + MARGIN)


def make_board_texture(brand):
    text = f"{brand}  •  "
    f = font(46, "ExtraBold")
    unit = f.measureText(text)
    w, h = int(unit * 8), 64
    surf = skia.Surface(w, h)
    c = surf.getCanvas()
    c.clear(col("#0d0f10"))
    c.drawRect(skia.Rect.MakeXYWH(0, 0, w, 4), paint(GOLD, 0.9))
    x = 0
    i = 0
    while x < w:
        c.drawString(text, x, 50, f, paint(GOLD if i % 2 else "#f5f5f5", 0.95))
        x += unit
        i += 1
    return surf.makeImageSnapshot()


# ---------------------------------------------------------------- drawing helpers
def ground_path(cam, pts, close=False):
    path = skia.Path()
    for i, (x, y) in enumerate(pts):
        sx, sy, _ = cam.project(x, y)
        if i == 0:
            path.moveTo(sx, sy)
        else:
            path.lineTo(sx, sy)
    if close:
        path.close()
    return path


def circle_pts(x, y, r, n=48, a0=0.0, a1=2 * math.pi):
    return [(x + r * math.cos(a0 + (a1 - a0) * i / n), y + r * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def dash(p, on, off, phase=0.0):
    p.setPathEffect(skia.DashPathEffect.Make([on, off], phase))
    return p


def bezier_pts(a, b, bend=0.0, n=40):
    (x0, y0), (x1, y1) = a, b
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    cx, cy = mx - dy / L * bend, my + dx / L * bend
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(((1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1,
                    (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1))
    return out


def draw_arrow(c, cam, a, b, progress=1.0, color=GOLD, bend=0.0, width=0.45, dashed=True, alpha=1.0):
    """Flèche au sol (coordonnées terrain)."""
    if progress <= 0.01 or alpha <= 0:
        return
    pts = bezier_pts(a, b, bend)
    k = max(2, int(len(pts) * clamp01(progress)))
    pts = pts[:k]
    s = cam.scale_at(*pts[-1])
    sw = max(2.5, width * s)
    shadow = paint("#000000", 0.35 * alpha, stroke=sw * 1.6, blur=3)
    p = paint(color, alpha, stroke=sw)
    if dashed:
        dash(p, sw * 2.2, sw * 1.6)
        dash(shadow, sw * 2.2, sw * 1.6)
    path = ground_path(cam, pts[:-2] if len(pts) > 4 else pts)
    c.drawPath(path, shadow)
    c.drawPath(path, p)
    # pointe
    (x1, y1), (x0, y0) = pts[-1], pts[-3] if len(pts) > 3 else pts[0]
    ang = math.atan2(y1 - y0, x1 - x0)
    hl = 2.2
    tri = [(x1, y1),
           (x1 - hl * math.cos(ang - 0.5), y1 - hl * math.sin(ang - 0.5)),
           (x1 - hl * math.cos(ang + 0.5), y1 - hl * math.sin(ang + 0.5))]
    c.drawPath(ground_path(cam, tri, True), paint(color, alpha))


def draw_ring(c, cam, x, y, r, color=GOLD, alpha=1.0, width=0.35, dashed=False, fill=0.0, glow=False):
    if alpha <= 0:
        return
    path = ground_path(cam, circle_pts(x, y, r), True)
    s = cam.scale_at(x, y)
    if fill > 0:
        c.drawPath(path, paint(color, fill * alpha))
    if glow:
        c.drawPath(path, paint(color, 0.6 * alpha, stroke=width * s * 3, blur=width * s * 2))
    p = paint(color, alpha, stroke=max(2, width * s))
    if dashed:
        dash(p, width * s * 2.5, width * s * 1.8)
    c.drawPath(path, p)


def draw_poly(c, cam, pts, color=GOLD, alpha=1.0, fill=0.22, width=0.3, dashed=False):
    if alpha <= 0:
        return
    path = ground_path(cam, pts, True)
    s = cam.scale_at(*np.mean(pts, axis=0))
    c.drawPath(path, paint(color, fill * alpha))
    p = paint(color, 0.9 * alpha, stroke=max(2, width * s))
    if dashed:
        dash(p, width * s * 3, width * s * 2)
    c.drawPath(path, p)


def draw_line_label(c, cam, y, x0, x1, text, alpha=1.0, color=GOLD):
    if alpha <= 0:
        return
    p = paint(color, alpha, stroke=max(2, 0.25 * cam.scale_at(0, y)))
    dash(p, 14, 10)
    c.drawPath(ground_path(cam, [(x0, y), (x1, y)]), p)
    sx, sy, _ = cam.project(0, y + 1.6)
    pill(c, sx, sy, text, 26, alpha, bg="#0d0f10", fg=color)


def pill(c, x, y, text, size, alpha=1.0, bg=GOLD, fg=INK, pad=(14, 8), weight="ExtraBold",
         radius=None, border=None, shadow=True):
    if alpha <= 0:
        return
    f = font(size, weight)
    tw = f.measureText(text)
    w, h = tw + 2 * pad[0], size + 2 * pad[1]
    r = skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h)
    rad = h / 2 if radius is None else radius
    if shadow:
        c.drawRRect(skia.RRect.MakeRectXY(r.makeOffset(0, 4), rad, rad), paint("#000000", 0.45 * alpha, blur=6))
    c.drawRRect(skia.RRect.MakeRectXY(r, rad, rad), paint(bg, alpha))
    if border:
        c.drawRRect(skia.RRect.MakeRectXY(r, rad, rad), paint(border, alpha, stroke=2))
    c.drawString(text, x - tw / 2, y + size * 0.36, f, paint(fg, alpha))
    return w, h


# ---------------------------------------------------------------- tokens
STYLES = {
    "home": dict(top="#f4f4f2", top2="#c9cac6", side="#9a9b97", num="#1a1c20", rim="#ffffff"),
    "away": dict(top="#3a3f48", top2="#1e2228", side="#101215", num="#f2f2f2", rim="#5a616c"),
    "gold": dict(top="#f7d77a", top2="#c9952e", side="#8a6216", num="#2a1d05", rim="#fff1c4"),
}


def draw_token(c, cam, x, y, num, style="home", label=None, alpha=1.0, scale=1.0, label_gold=False,
               ring=0.0, t=0.0, label_alpha=1.0):
    if alpha <= 0.01:
        return
    R, Th = 1.45 * scale, 0.55 * scale
    st = STYLES[style]
    s = cam.scale_at(x, y)
    rp = R * s
    if rp < 3:
        return
    # aplatissement selon l'angle de vue local
    sx0, sy0, _ = cam.project(x, y, 0)
    sx1, sy1, _ = cam.project(x, y, Th)
    ex, ey, _ = cam.project(x, y + R, 0)
    flat = clamp01(abs(ey - sy0) / rp)
    flat = max(0.38, min(0.95, flat))
    ry = rp * flat
    # anneau doré au sol
    if ring > 0:
        pulse = 0.5 + 0.5 * math.sin(t * 5.0)
        draw_ring(c, cam, x, y, R * (1.55 + 0.12 * pulse), GOLD, ring * alpha, width=0.28, glow=True,
                  fill=0.18)
    # ombre
    c.drawOval(skia.Rect.MakeLTRB(sx0 - rp * 1.05, sy0 - ry * 0.8, sx0 + rp * 1.15, sy0 + ry * 1.25),
               paint("#000000", 0.5 * alpha, blur=rp * 0.25))
    # tranche
    side = skia.Path()
    side.addOval(skia.Rect.MakeLTRB(sx0 - rp, sy0 - ry, sx0 + rp, sy0 + ry))
    c.drawPath(side, paint(st["side"], alpha))
    c.drawRect(skia.Rect.MakeLTRB(sx0 - rp, sy1, sx0 + rp, sy0), paint(st["side"], alpha))
    # dessus
    top = skia.Rect.MakeLTRB(sx1 - rp, sy1 - ry, sx1 + rp, sy1 + ry)
    sh = skia.GradientShader.MakeLinear([(sx1, sy1 - ry), (sx1, sy1 + ry)],
                                       [col(st["top"], alpha), col(st["top2"], alpha)])
    c.drawOval(top, skia.Paint(AntiAlias=True, Shader=sh))
    c.drawOval(top, paint(st["rim"], 0.8 * alpha, stroke=max(1.5, rp * 0.06)))
    inner = top.makeInset(rp * 0.16, ry * 0.16)
    c.drawOval(inner, paint("#000000", 0.08 * alpha, stroke=max(1, rp * 0.04)))
    # numéro (face caméra)
    fs = rp * 0.95
    f = font(fs, "BlackItalic")
    txt = str(num)
    tw = f.measureText(txt)
    c.save()
    c.translate(sx1, sy1)
    c.scale(1, 0.62 + 0.38 * flat)
    c.drawString(txt, -tw / 2, fs * 0.36, f, paint(st["num"], alpha))
    c.restore()
    # étiquette
    if label and label_alpha > 0:
        ls = max(15, min(34, rp * 0.62))
        ly = sy1 - ry - ls * 1.05
        bg, fg = (GOLD, INK) if label_gold else ("#111316", "#ffffff")
        pill(c, sx1, ly, label, ls, alpha * label_alpha, bg=bg, fg=fg, pad=(ls * 0.38, ls * 0.25),
             radius=ls * 0.18, border="#ffffff" if not label_gold else None, shadow=True)
        tri = skia.Path()
        tri.moveTo(sx1 - ls * 0.25, ly + ls * 0.75)
        tri.lineTo(sx1 + ls * 0.25, ly + ls * 0.75)
        tri.lineTo(sx1, ly + ls * 1.05)
        tri.close()
        c.drawPath(tri, paint(bg, alpha * label_alpha))


def draw_qmark(c, cam, x, y, alpha, t):
    if alpha <= 0:
        return
    sx, sy, _ = cam.project(x, y, 3.2 + 0.4 * math.sin(t * 6 + x))
    s = cam.scale_at(x, y)
    fs = 2.6 * s
    f = font(fs, "Black")
    tw = f.measureText("?")
    c.drawString("?", sx - tw / 2 + 3, sy + 4, f, paint("#000000", 0.5 * alpha))
    c.drawString("?", sx - tw / 2, sy, f, paint("#ff6b6b", alpha))


def draw_goal(c, cam, y, alpha=1.0):
    gw, gh, gd = 7.32 / 2, 2.44, 2.0 * (1 if y > 0 else -1)
    p = paint("#ffffff", 0.9 * alpha, stroke=max(2, 0.14 * cam.scale_at(0, y)))
    net = paint("#ffffff", 0.25 * alpha, stroke=1)
    pts = lambda L: [cam.project(*q)[:2] for q in L]
    front = pts([(-gw, y, 0), (-gw, y, gh), (gw, y, gh), (gw, y, 0)])
    back = pts([(-gw, y + gd, 0), (-gw, y + gd, gh * 0.8), (gw, y + gd, gh * 0.8), (gw, y + gd, 0)])
    for i in range(1, 9):
        a = front[1][0] + (front[2][0] - front[1][0]) * i / 9
        b = back[1][0] + (back[2][0] - back[1][0]) * i / 9
        c.drawLine(a, front[1][1], b, back[1][1], net)
    for A, B in ((front, back),):
        for i in range(4):
            c.drawLine(*A[i], *B[i], net)
    path = skia.Path()
    path.addPoly([skia.Point(*q) for q in front], False)
    c.drawPath(path, p)


def draw_board(c, cam, img, p0, p1, height=1.1, offset=0.0, alpha=1.0):
    """Panneau publicitaire vertical entre p0 et p1 (au sol)."""
    (x0, y0), (x1, y1) = p0, p1
    quad = [cam.project(x0, y0, height)[:2], cam.project(x1, y1, height)[:2],
            cam.project(x1, y1, 0)[:2], cam.project(x0, y0, 0)[:2]]
    L = math.hypot(x1 - x0, y1 - y0)
    iw = L * img.height() / height
    u0 = offset * 60
    src = [skia.Point(u0, 0), skia.Point(u0 + iw, 0), skia.Point(u0 + iw, img.height()),
           skia.Point(u0, img.height())]
    m = skia.Matrix()
    if not m.setPolyToPoly(src, [skia.Point(*q) for q in quad]):
        return
    shader = img.makeShader(skia.TileMode.kRepeat, skia.TileMode.kClamp,
                            skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear), m)
    path = skia.Path()
    path.addPoly([skia.Point(*q) for q in quad], True)
    c.drawPath(path, skia.Paint(AntiAlias=True, Shader=shader, Alphaf=alpha))
