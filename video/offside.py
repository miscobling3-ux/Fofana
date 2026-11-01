"""Montage TikTok « pourquoi pas hors-jeu ? » — but de Lamine Yamal (Barça - Alavés), voix off en anglais.

Réutilise les outils de dessin de yamal.py (triangles, cercles, flèches, mise en lumière...).
Ajoute la ligne de hors-jeu tracée en perspective (point de fuite des lignes parallèles à la ligne de but).
Pas de sous-titres, pas de musique ; logos masqués par offside_clean.py.

    python3 offside_clean.py              # une fois
    python3 offside.py                    # -> ../output/lamine_yamal_offside_en.mp4
    python3 offside.py --stills 5,30,40   # aperçu PNG dans build/offside/
"""
import argparse
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
import yamal as Y  # noqa: E402
from yamal import (RED, WHITE, YELLOW, ORANGE, Shot, appear, back_out, cam_kf, draw_arrow, draw_cross,  # noqa: E402
                   draw_marker, draw_ring, ease, ease_out, flash, keyframes, line, poly_fill, red_tint,
                   spotlight, desaturate)

BUILD = os.path.join(HERE, "build", "offside")
Y.FRAMES = os.path.join(BUILD, "frames")
Y.SH = 960          # les sources sont ramenées à 1920x960
GREEN = (90, 220, 60)
CYAN = (255, 245, 170)

# ------------------------------------------------------------------ positions (pixels source 1920x960)
# B = plan large « télé », A = caméra tactique haute (+ 2e angle du lob)
VP = (20, -475)                 # point de fuite des lignes parallèles à la ligne de but (image B à 5.5 s)
B_PASS = 5.5                    # image B : la passe vient de partir
DEF_FOOT = (639, 543)           # pied du dernier défenseur à B_PASS
YAMAL_FOOT = (585, 437)         # pied de Yamal à B_PASS
BALL_PASS = (806, 527)
B_FREEZE = 1.5                  # image B (figée dans la source de 1.5 à 5.3 s) : Jesus contrôle
DEF_FOOT_15 = (630, 548)
YAMAL_15 = (540, 405)
NINE_15 = (850, 522)
BALL_15 = (828, 550)
YAMAL_00 = (410, 375)

TRACK_SEEDS = {   # nom : (clip, départ, x, y, fin)
    "a_header": ("a", 0.0, 714, 492, 0.9),
    "a_nine": ("a", 0.0, 762, 510, 2.6),
    "b_nine": ("b", 0.0, 830, 572, 1.55),
    "b_yamal0": ("b", 0.0, 410, 375, 1.55),
    "b_yamal": ("b", 5.5, 580, 408, 8.4),
    "b_keeper": ("b", 7.3, 480, 420, 8.4),
}


def compute_tracks():
    import json
    path = os.path.join(BUILD, "tracks.json")
    if os.path.exists(path):
        return {k: {float(t): tuple(v) for t, v in d.items()} for k, d in json.load(open(path)).items()}
    out = {}
    for name, (clip, t0, x, y, t1) in TRACK_SEEDS.items():
        f = cv2.imread(os.path.join(Y.FRAMES, clip, f"{int(t0 * 50):06d}.jpg"))
        tr = cv2.TrackerCSRT_create()
        tr.init(f, (x - 20, y - 45, 40, 90))
        d = {t0: (x, y)}
        for i in range(int(t0 * 50) + 1, int(t1 * 50) + 1):
            ok, b = tr.update(cv2.imread(os.path.join(Y.FRAMES, clip, f"{i:06d}.jpg")))
            if ok:
                d[i / 50] = (b[0] + b[2] / 2, b[1] + b[3] / 2)
        out[name] = d
        print(f"  suivi {name} : {len(d)} positions", flush=True)
    json.dump({k: {str(t): v for t, v in d.items()} for k, d in out.items()}, open(path, "w"))
    return out


def T(name, t):
    Y.TRACKS = TRACKS
    return Y.T(name, t)


TRACKS = None


def feet(p, dy=40):
    return (p[0], p[1] + dy)


def head(p, dy=-52):
    return (p[0], p[1] + dy)


# ------------------------------------------------------------------ lignes de hors-jeu
def offside_points(foot, up=330, down=260):
    """Deux extrémités (pixels source) de la ligne parallèle à la ligne de but passant par foot."""
    dx, dy = foot[0] - VP[0], foot[1] - VP[1]
    k = dx / dy
    y0, y1 = foot[1] - up, foot[1] + down
    return (foot[0] + k * (y0 - foot[1]), y0), (foot[0] + k * (y1 - foot[1]), y1)


def glow_line(img, a, b, prog, color=CYAN, th=7):
    """Ligne lumineuse qui se déploie depuis le milieu (style VAR)."""
    if prog <= 0:
        return img
    a, b = np.array(a, float), np.array(b, float)
    m = (a + b) / 2
    a2, b2 = m + (a - m) * ease_out(prog), m + (b - m) * ease_out(prog)
    glow = np.zeros_like(img)
    cv2.line(glow, tuple(np.int32(a2)), tuple(np.int32(b2)), color, th * 5, cv2.LINE_AA)
    glow = cv2.GaussianBlur(glow, (0, 0), 14)
    out = cv2.add(img, (glow * 0.9).astype(np.uint8))
    cv2.line(out, tuple(np.int32(a2)), tuple(np.int32(b2)), color, th + 4, cv2.LINE_AA)
    cv2.line(out, tuple(np.int32(a2)), tuple(np.int32(b2)), WHITE, max(2, th - 3), cv2.LINE_AA)
    img[:] = out
    return img


def dashed_line(img, a, b, prog, color=RED, th=8, dash=30, gap=18):
    a, b = np.array(a, float), np.array(b, float)
    L = np.linalg.norm(b - a)
    d = (b - a) / (L + 1e-6)
    s = 0.0
    while s < L * min(prog, 1):
        e = min(s + dash, L * min(prog, 1))
        line(img, a + d * s, a + d * e, (15, 15, 15), th + 6)
        line(img, a + d * s, a + d * e, color, th)
        s += dash + gap


def check_mark(img, p, k, size=40):
    if k <= 0:
        return
    s = size * back_out(k)
    pts = [(p[0] - s * 0.6, p[1]), (p[0] - s * 0.15, p[1] + s * 0.5), (p[0] + s * 0.75, p[1] - s * 0.55)]
    for th, c in ((22, (15, 15, 15)), (13, GREEN)):
        line(img, pts[0], pts[1], c, th)
        line(img, pts[1], pts[2], c, th)


# ------------------------------------------------------------------ plans
def build_shots():
    S = []

    def R(v, r):  # rayon de cercle adapté au zoom
        return r * v.s / 2.0

    # 0 — accroche : le lob, puis l'image figée où il « semble » hors-jeu
    def d0(img, v, u, st, dur):
        if u < 2.2:
            return
        w = u - 2.2
        top, bot = (DEF_FOOT_15[0], DEF_FOOT_15[1] - 330), (DEF_FOOT_15[0], DEF_FOOT_15[1] + 200)
        glow_line(img, v.P(top), v.P(bot), appear(w, 0.6, 0.7), color=(80, 80, 255))
        draw_ring(img, v.P(feet(YAMAL_15, 32)), R(v, 70), u, appear(w, 0.3), color=RED, dashed=True)
        draw_marker(img, v.P(head(YAMAL_15)), u, appear(w, 0.4))
        y = v.P(YAMAL_15)
        draw_arrow(img, (y[0] - 230, y[1] + 40), (y[0] - 70, y[1] + 10), ease_out((w - 1.6) / 0.5), color=RED,
                   bend=0.0, th=12)
    def p0(img, u, dur):
        return flash(img, max(0, 1 - abs(u - 1.25) / 0.15) * 0.8 + max(0, 1 - abs(u - 2.2) / 0.15) * 0.9)
    s = Shot(0, None, None, None)
    s.multi = [
        ("b", [(2.2, "play", 7.75, 9.5)],
         lambda u, st: (*keyframes([(0, (560, 420)), (1.0, (420, 380)), (2.2, (300, 340))], u),
                        keyframes([(0, 1.25), (2.2, 1.45)], u))),
        ("b", [(None, "freeze", B_FREEZE)],
         lambda u, st: (*keyframes([(0, (700, 480)), (2.5, (610, 470))], u), keyframes([(0, 1.2), (2.5, 1.6), (6, 1.75)], u))),
    ]
    s.draw, s.post = d0, p0
    S.append(s)

    # 1 — un défenseur tente de dégager de la tête
    def d1(img, v, u, st, dur):
        p = T("a_header", st)
        a = appear(u, 1.2)
        img[:] = spotlight(img, [(v.P(p), R(v, 70), R(v, 110))], 0.75 * a)
        draw_ring(img, v.P(feet(p, 28)), R(v, 55), u, a, color=RED, dashed=False)
        draw_marker(img, v.P(head(p, -42)), u, appear(u, 1.3))
    S.append(Shot(1, "a", [(1.4, "play", 0.0, 0.3), (None, "freeze", 0.3)],
                  cam_kf([(0, (720, 470, 1.6)), (1.4, (705, 480, 1.85)), (3.4, (705, 480, 2.0))]), d1))

    # 2 — tête mal maîtrisée, le ballon tombe dans les pieds de « Jesus »
    def d2(img, v, u, st, dur):
        fr = 2.6
        nine = T("a_nine", st)
        if u < fr:
            draw_marker(img, v.P(head(T("a_header", min(st, 0.9)))), u, 1 - appear(u, 0.6, 0.4))
            return
        hp = T("a_header", 0.3)
        draw_arrow(img, v.P(head(hp, -40)), v.P(feet(nine, 10)), ease_out((u - fr) / 0.6), bend=0.35, dashed=True)
        a = appear(u, fr + 0.5)
        img[:] = spotlight(img, [(v.P(nine), R(v, 70), R(v, 110))], 0.7 * a)
        draw_ring(img, v.P(feet(nine, 28)), R(v, 55), u, a, color=YELLOW)
        draw_marker(img, v.P(head(nine, -42)), u, a, color=YELLOW)
    S.append(Shot(2, "a", [(2.6, "play", 0.3, 2.4), (None, "freeze", 2.4)],
                  cam_kf([(0, (705, 480, 2.0)), (1.2, (670, 460, 1.7)), (2.6, (650, 490, 1.75)), (4.8, (650, 495, 2.0))]), d2))

    # 3 — il contrôle et voit Yamal partir dans l'espace
    def d3(img, v, u, st, dur):
        fr = 1.9
        nine = T("b_nine", st)
        yam = T("b_yamal0", st)
        draw_ring(img, v.P(feet(nine)), R(v, 50), u, 1, color=YELLOW)
        draw_marker(img, v.P(head(nine)), u, 1, color=YELLOW)
        if u < fr:
            return
        a = appear(u, fr + 0.2)
        img[:] = spotlight(img, [(v.P(yam), R(v, 75), R(v, 110)), (v.P(nine), R(v, 60), R(v, 95))], 0.7 * a)
        # regard de Jesus vers Yamal
        e = v.P(head(nine, -30))
        y = v.P(yam)
        dx, dy = y[0] - e[0], y[1] - e[1]
        n = (-dy * 0.12, dx * 0.12)
        poly_fill(img, [e, (y[0] + n[0], y[1] + n[1]), (y[0] - n[0], y[1] - n[1])], (180, 255, 255),
                  0.18 * appear(u, fr + 0.3))
        draw_marker(img, v.P(head(yam)), u, appear(u, fr + 0.6))
        draw_arrow(img, v.P(feet(yam, 25)), v.P((300, 470)), ease_out((u - fr - 1.0) / 0.7), color=YELLOW,
                   bend=0.12, dashed=True, th=9)
    S.append(Shot(3, "b", [(1.9, "play", 0.0, B_FREEZE), (None, "freeze", B_FREEZE)],
                  cam_kf([(0, (700, 490, 1.3)), (1.9, (690, 480, 1.25)), (4.6, (660, 470, 1.3))]), d3))

    # 4 — « regarde bien l'action »
    def p4(img, u, dur):
        return flash(img, max(0, 1 - u / 0.2) * 0.6)
    S.append(Shot(4, "b", [(None, "freeze", B_FREEZE)],
                  cam_kf([(0, (660, 470, 1.3)), (1.85, (600, 470, 1.9))]), None, p4))

    # 5 — au début de l'action, Yamal était en position régulière
    def d5(img, v, u, st, dur):
        a = appear(u, 0.5)
        img[:] = spotlight(img, [(v.P(YAMAL_00), R(v, 75), R(v, 110))], 0.75 * a)
        draw_ring(img, v.P(feet(YAMAL_00, 35)), R(v, 60), u, a, color=GREEN)
        draw_marker(img, v.P(head(YAMAL_00)), u, appear(u, 0.6), color=GREEN)
        p = v.P(YAMAL_00)
        check_mark(img, (p[0] + R(v, 95), p[1] - R(v, 80)), appear(u, 3.2, 0.4))
    def p5(img, u, dur):
        return desaturate(img, 0.35 * (1 - appear(u, 0.0, 0.5))) if u < 0.5 else img
    S.append(Shot(5, "b", [(None, "freeze", 0.0)],
                  cam_kf([(0, (620, 460, 1.35)), (1.0, (520, 430, 1.6)), (5.8, (500, 420, 1.75))]), d5, p5))

    # 6 — au moment où Jesus reçoit, contrôle et prépare la passe
    def d6(img, v, u, st, dur):
        a = appear(u, 0.3)
        img[:] = spotlight(img, [(v.P(NINE_15), R(v, 70), R(v, 105)), (v.P(BALL_15), R(v, 30), R(v, 30))], 0.7 * a)
        draw_ring(img, v.P(feet(NINE_15, 28)), R(v, 55), u, a, color=YELLOW)
        draw_marker(img, v.P(head(NINE_15)), u, a, color=YELLOW)
        b = v.P(BALL_15)
        pulse = 0.5 + 0.5 * math.sin(u * 9)
        cv2.circle(img, (int(b[0]), int(b[1])), int(R(v, 22) * (1 + 0.15 * pulse)), YELLOW, 4, cv2.LINE_AA)
    S.append(Shot(6, "b", [(None, "freeze", B_FREEZE)],
                  cam_kf([(0, (600, 470, 1.9)), (0.9, (830, 520, 2.1)), (4.0, (820, 515, 2.2)),
                          (5.45, (700, 490, 1.7))]), d6))

    # 7 — à première vue, Yamal semble hors-jeu (ligne « naïve », verticale à l'écran)
    def d7(img, v, u, st, dur):
        top, bot = (DEF_FOOT_15[0], DEF_FOOT_15[1] - 330), (DEF_FOOT_15[0], DEF_FOOT_15[1] + 200)
        dashed_line(img, v.P(bot), v.P(top), appear(u, 0.3, 0.8), color=RED, th=8)
        draw_ring(img, v.P(feet(DEF_FOOT_15, -5)), R(v, 50), u, appear(u, 0.2), color=ORANGE)
        draw_ring(img, v.P(feet(YAMAL_15, 32)), R(v, 60), u, appear(u, 1.2), color=RED, dashed=False)
        draw_marker(img, v.P(head(YAMAL_15)), u, appear(u, 1.3))
        y = v.P(YAMAL_15)
        draw_arrow(img, (y[0] - 220, y[1] + 50), (y[0] - 65, y[1] + 12), ease_out((u - 1.6) / 0.5), color=RED,
                   bend=0.0, th=12)
    def p7(img, u, dur):
        return red_tint(img, 0.3 * appear(u, 1.2, 0.4))
    S.append(Shot(7, "b", [(None, "freeze", B_FREEZE)],
                  cam_kf([(0, (700, 490, 1.7)), (1.0, (600, 470, 1.65)), (4.9, (590, 470, 1.8))]), d7, p7))

    # 8 — en regardant de plus près : il n'est pas hors-jeu (vraie ligne, en perspective)
    def d8(img, v, u, st, dur):
        fr = 1.2
        if u < fr:
            top, bot = (DEF_FOOT_15[0], DEF_FOOT_15[1] - 330), (DEF_FOOT_15[0], DEF_FOOT_15[1] + 200)
            dashed_line(img, v.P(bot), v.P(top), 1, color=RED, th=8)
            return
        a, b = offside_points(DEF_FOOT)
        glow_line(img, v.P(a), v.P(b), appear(u, fr + 0.3, 0.9))
        draw_ring(img, v.P(DEF_FOOT), R(v, 40), u, appear(u, fr + 1.2), color=ORANGE)
        draw_ring(img, v.P(YAMAL_FOOT), R(v, 40), u, appear(u, fr + 2.2), color=GREEN)
    def p8(img, u, dur):
        return flash(img, max(0, 1 - abs(u - 1.2) / 0.15) * 0.5)
    S.append(Shot(8, "b", [(1.2, "play", 5.3, B_PASS), (None, "freeze", B_PASS)],
                  cam_kf([(0, (590, 470, 1.8)), (1.2, (620, 480, 1.45)), (5.1, (615, 480, 1.6))]), d8, p8))

    # 9 — exactement sur la même ligne que le dernier défenseur
    def d9(img, v, u, st, dur):
        a, b = offside_points(DEF_FOOT)
        glow_line(img, v.P(a), v.P(b), 1)
        img[:] = spotlight(img, [(v.P((DEF_FOOT[0], DEF_FOOT[1] - 35)), R(v, 60), R(v, 90)),
                                 (v.P((YAMAL_FOOT[0], YAMAL_FOOT[1] - 30)), R(v, 60), R(v, 85))], 0.6 * appear(u, 0.2))
        draw_ring(img, v.P(DEF_FOOT), R(v, 40), u, 1, color=ORANGE)
        draw_ring(img, v.P(YAMAL_FOOT), R(v, 40), u, 1, color=GREEN)
        # deux flèches qui pointent les pieds sur la ligne
        for p, c in ((YAMAL_FOOT, GREEN), (DEF_FOOT, ORANGE)):
            q = v.P(p)
            draw_arrow(img, (q[0] + 170, q[1] + 30), (q[0] + 45, q[1] + 8), ease_out((u - 0.6) / 0.5), color=c,
                       bend=0.0, th=9)
        q = v.P(YAMAL_FOOT)
        check_mark(img, (q[0] - 20, q[1] - R(v, 150)), appear(u, 1.8, 0.4))
    S.append(Shot(9, "b", [(None, "freeze", B_PASS)],
                  cam_kf([(0, (615, 480, 1.6)), (1.2, (610, 485, 2.2)), (3.5, (610, 485, 2.35))]), d9))

    # 10 — passe en profondeur pour Yamal
    def d10(img, v, u, st, dur):
        fr = 1.3
        if u < fr:
            a, b = offside_points(DEF_FOOT)
            glow_line(img, v.P(a), v.P(b), 1 - appear(u, 0.8, 0.4))
            draw_arrow(img, v.P(BALL_PASS), v.P((430, 480)), ease_out((u - 0.1) / 0.7), bend=-0.1, dashed=True)
            return
        draw_marker(img, v.P(head(T("b_yamal", st))), u, 1)
    def cam10(u, st):
        p = T("b_yamal", st)
        return (p[0] - 40, p[1] + 20, keyframes([(0, 1.6), (1.3, 1.45), (3.2, 1.3)], u))
    S.append(Shot(10, "b", [(1.3, "freeze", B_PASS), (None, "play", B_PASS, 6.7)], cam10, d10))

    # 11 — il contrôle et oblige le gardien à sortir
    def d11(img, v, u, st, dur):
        fr = 2.5
        yam = T("b_yamal", st)
        draw_marker(img, v.P(head(yam)), u, 1)
        if u < fr:
            return
        kp = T("b_keeper", st)
        a = appear(u, fr)
        img[:] = spotlight(img, [(v.P(yam), R(v, 70), R(v, 105)), (v.P(kp), R(v, 70), R(v, 105))], 0.65 * a)
        draw_ring(img, v.P(feet(kp)), R(v, 55), u, a, color=YELLOW)
        k0 = T("b_keeper", 7.3)
        draw_arrow(img, v.P(feet(k0, 20)), v.P(feet(kp, 20)), ease_out((u - fr - 0.3) / 0.6), color=YELLOW,
                   bend=0.0, th=9)
    S.append(Shot(11, "b", [(2.5, "play", 6.7, 7.95), (None, "freeze", 7.95)],
                  lambda u, st: (*(lambda p: (p[0] - 90, p[1] + 10))(T("b_yamal", st)),
                                 keyframes([(0, 1.3), (2.5, 1.35), (4.8, 1.55)], u)), d11))

    # 12 — il avance et réussit un lob magnifique
    def d12(img, v, u, st, dur):
        if u < 1.9:
            yam = T("b_yamal", min(st, 8.4))
            draw_marker(img, v.P(head(yam)), u, 1 - appear(u, 1.5, 0.3))
    def p12(img, u, dur):
        return flash(img, max(0, 1 - abs(u - 3.0) / 0.2) * 0.8)
    s = Shot(12, None, None, None)
    s.multi = [
        ("b", [(1.9, "play", 7.95, 8.35)],
         lambda u, st: (*keyframes([(0, (720, 430)), (1.9, (640, 400))], u), keyframes([(0, 1.55), (1.9, 1.75)], u))),
        ("b", [(1.5, "play", 8.35, 9.6)],
         lambda u, st: (*keyframes([(0, (600, 390)), (1.0, (380, 340)), (1.5, (330, 330))], u),
                        keyframes([(0, 1.6), (1.5, 1.5)], u))),
        ("a", [(None, "play", 6.0, 7.6)],
         lambda u, st: (*keyframes([(0, (760, 420)), (2.5, (640, 360)), (4.5, (560, 320))], u),
                        keyframes([(0, 1.05), (4.5, 1.3)], u))),
    ]
    s.draw, s.post = d12, p12
    S.append(s)

    # fin : célébration
    S.append(Shot(None, "b", [(2.6, "play", 10.8, 13.4)], cam_kf([(0, (CELEB_X, 470, 1.0)), (2.6, (CELEB_X, 450, 1.12))])))
    return S


CELEB_X = 1000


# ------------------------------------------------------------------ montage + audio (même logique que yamal.py)
def plan(G):
    Y.build_shots = build_shots
    cache = os.path.join(BUILD, "voice")
    os.makedirs(cache, exist_ok=True)
    G.LINES = list(G.LINES)
    # Y.plan lit build/yamal/voice : on lui donne notre cache
    Y.BUILD = BUILD
    return Y.plan(G)


def sfx_events(shots):
    ev = []
    for sh in shots:
        if sh.t0 > 0.1:
            ev.append((sh.t0 - 0.08, "whoosh", 0.3))
        if getattr(sh, "parts", None):
            continue
        acc = sh.t0
        for d, kind, *r in sh.tl:
            if kind == "freeze" and acc > sh.t0 + 0.05:
                ev.append((acc, "tick", 0.5))
            acc += d
    s0, s12 = shots[0], shots[12]
    ev += [(s0.t0 + 1.25, "boom", 0.6), (s0.t0 + 2.2, "pop", 0.5), (shots[7].t0 + 1.2, "error", 0.5),
           (shots[8].t0 + 1.5, "riser", 0.4), (shots[9].t0 + 1.8, "tick", 0.6), (s12.t0 + 3.0, "boom", 0.7)]
    return ev


def render(shots, t):
    Y.TRACKS = TRACKS
    return Y.render_frame(shots, t)


def _worker(args):
    script, a, b, path = args
    global TRACKS
    TRACKS = compute_tracks()
    G = __import__(script)
    shots, _, _ = plan(G)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{Y.OW}x{Y.OH}",
                           "-r", str(Y.FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                           "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for k in range(a, b):
        ff.stdin.write(render(shots, k / Y.FPS).tobytes())
    ff.stdin.close()
    ff.wait()
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", default="guion_offside_en")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "output", "lamine_yamal_offside_en.mp4"))
    ap.add_argument("--stills", default="")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    args = ap.parse_args()
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
            cv2.imwrite(os.path.join(BUILD, f"still_{t:05.1f}.png"), render(shots, t))
        print("images dans", BUILD)
        return
    n = int(duration * Y.FPS)
    w = max(1, args.workers)
    bounds = [(n * i // w, n * (i + 1) // w) for i in range(w)]
    parts = [os.path.join(BUILD, f"part{i}.mp4") for i in range(w)]
    with ProcessPoolExecutor(w) as ex:
        list(ex.map(_worker, [(args.script, a, b, p) for (a, b), p in zip(bounds, parts)]))
    lst = os.path.join(BUILD, "parts.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    mix = audio.mix_all(voice, np.zeros_like(voice), sfx_events(shots), duration)
    wav = os.path.join(BUILD, "mix.wav")
    sf.write(wav, mix, audio.SR)
    out = os.path.abspath(args.out)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
                    "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-shortest", "-movflags", "+faststart", out], check=True)
    print("OK :", out)


if __name__ == "__main__":
    main()
