"""Vidéo : « Luis Enrique es un genio » — analyse tactique du PSG, version espagnole.

Syntaxe des lignes :
  {cmd} ou {cmd:arg}  -> action déclenchée au début du mot suivant
  *mot*               -> mot-clé (surligné en doré dans les sous-titres)
  affiché=prononcé    -> texte affiché différent du texte lu par la voix (ex. 4-3-3=cuatro-tres-tres)
"""
import math

from engine import Camera, GOLD, RED, draw_arrow, draw_ring, draw_poly, draw_line_label, draw_qmark, pill, \
    circle_pts, ground_path, paint, dash, ease_out, clamp01

BRAND = "FOFANA FÚTBOL"
VOICE = "em_alex"
SPEED = 1.13
OUTRO_LEN = 4.2

LINES = [
    ("PSG · LUIS ENRIQUE", "{intro}Luis Enrique es un {genio}*genio*."),
    (None, "Y te voy a decir *por* *qué*."),
    ("LA ALINEACIÓN", "{cam:wide}{base}Sobre el papel, el PSG juega un {tag433}*4-3-3=cuatro-tres-tres* totalmente *normal*."),
    (None, "Pero en cuanto el *balón* circula, {fluid}*casi* *nadie* está donde debería estar en la {tint:on}*alineación*."),
    ("DEMBÉLÉ", "{tint:off}{base}Te lo explico, *hermano*."),
    (None, "{cam:dembele}{hl:DEM}Todo empieza con *Dembélé*."),
    (None, "En teoría es el *delantero*, pero {drop}*baja* al centro del campo."),
    ("EL DILEMA", "{cam:dilemma}Y ahí, el *central* rival {hl_cb}tiene un *problema*."),
    (None, "Si lo {follow}*sigue*, deja un {hole}*hueco* a su espalda."),
    (None, "Si se {stay}queda en su sitio, el PSG se encuentra de golpe con {4v3}*cuatro* jugadores *contra* *tres* en el medio,"),
    ("EL ROMBO", "{cam:rombo}porque {ring:VIT}*Vitinha*, {ring:RUI}*Ruiz* y {ring:ZAI}*Zaïre-Emery* forman un {rombo}*rombo* con Dembélé."),
    ("LOS LATERALES", "{cam:wide2}{clear}Al mismo tiempo, los *laterales*, {ring:HAK}*Hakimi* y {ring:MEN}*Mendes*, {fb_up}suben *muy* *arriba*, casi a la {height}altura de los *delanteros*."),
    (None, "Y a cambio, los {wingers_in}*extremos* se meten por *dentro*."),
    ("EL TRIÁNGULO", "{cam:right}{clear}Resultado: en cada banda, un {triangle}*triángulo*."),
    (None, "{ring:HAK}*Lateral*, {ring:ZAI}*interior* y {ring:DOU}*extremo*."),
    (None, "Y ese triángulo {spin}*gira* todo el tiempo."),
    (None, "El interior {r1}sale a la *banda*, el extremo {r2}se mete *por* *dentro*, y el lateral {r3}ataca la *espalda*."),
    ("EL RIVAL", "{cam:rival}{clear}Para el rival, todas las *marcas* {chaos}*saltan* por los aires,"),
    (None, "porque ya nadie sabe a quién {qmarks}tiene que pasarle la *marca*."),
    (None, "{tint:off}Siempre hay un jugador {free}*libre* en algún sitio."),
    ("CHAMPIONS 2025", "{cam:final}{clear}Y así es *exactamente* como el PSG {riser}ganó la {ucl}*Champions* *League* en {boom}*2025=dos-mil-veinticinco*."),
]

# ---------------------------------------------------------------- joueurs
HOME = [  # id, numéro, étiquette, position de base (x, y) — le PSG attaque vers le haut (+y)
    ("GK", 1, None, (0, -44)),
    ("MEN", 25, "MENDES", (-27, -13)),
    ("PAC", 51, "PACHO", (-10, -20)),
    ("MAR", 5, "MARQUINHOS", (10, -20)),
    ("HAK", 2, "HAKIMI", (27, -13)),
    ("VIT", 17, "VITINHA", (0, -3)),
    ("RUI", 8, "RUIZ", (-14, 6)),
    ("ZAI", 33, "ZAÏRE-EMERY", (14, 6)),
    ("KVA", 7, "KVARA", (-24, 26)),
    ("DEM", 10, "DEMBÉLÉ", (0, 30)),
    ("DOU", 14, "DOUÉ", (24, 26)),
]
AWAY = [
    ("o1", 1, (0, 49)), ("o3", 3, (-22, 36)), ("o4", 4, (-7.5, 38)), ("o5", 5, (7.5, 38)),
    ("o2", 2, (22, 36)), ("o8", 8, (-13, 23)), ("o6", 6, (0, 21.5)), ("o10", 10, (13, 23)),
    ("o11", 11, (-23, 11)), ("o9", 9, (0, 9)), ("o7", 7, (23, 11)),
]
BASE = {pid: pos for pid, _, _, pos in HOME} | {pid: pos for pid, _, pos in AWAY}

FLUID = {"MEN": (-29, 31), "HAK": (29, 31), "KVA": (-13, 31), "DOU": (13, 31), "DEM": (0, 16),
         "RUI": (-21, 13), "ZAI": (20, 15), "VIT": (-3, 3), "PAC": (-14, -10), "MAR": (12, -10),
         "GK": (0, -38), "o4": (-5, 34), "o8": (-10, 21), "o10": (10, 22)}

CAMS = {
    "intro0": Camera(20, 20, 40, 38, 55, yaw=-14, oy=170),
    "intro": Camera(15, 18, 58, 44, 55, yaw=-9, oy=130),
    "wide": Camera(0, 4, 118, 60, 56, oy=70),
    "dembele": Camera(0, 22, 58, 42, 55, oy=140),
    "dilemma": Camera(-2, 26, 70, 47, 55, yaw=3, oy=120),
    "rombo": Camera(0, 13, 64, 50, 55, oy=110),
    "wide2": Camera(0, 13, 102, 55, 56, oy=80),
    "right": Camera(17, 22, 62, 44, 55, yaw=-10, oy=120),
    "rival": Camera(5, 30, 72, 47, 55, yaw=-5, oy=110),
    "final": Camera(-2, 22, 44, 33, 55, yaw=10, oy=150),
}


# ---------------------------------------------------------------- actions
class Ctx:
    def __init__(self, tl, chapter_end, sfx):
        self.tl, self.chapter_end, self.sfx = tl, chapter_end, sfx
        self.rings = []

    def P(self, pid):
        return self.tl.players[pid]

    def move(self, t, moves, dur=1.1):
        for pid, pos in moves.items():
            self.P(pid).pos.to(t, pos, dur)

    def ring(self, t, pid, gold=False):
        p = self.P(pid)
        p.ring.to(t, 1.0, 0.3)
        p.ring.to(self.chapter_end(t), 0.0, 0.3)
        if gold:
            p.gold.set(t, 1.0)
        self.sfx(t, "pop", 0.8)


def pos_at(ctx, pid, t):
    return ctx.P(pid).pos(t)


def run_command(ctx, t, cmd, arg):
    tl = ctx.tl
    end = ctx.chapter_end(t)

    if cmd == "intro":
        tl.cam.set(0, CAMS["intro0"])
        tl.cam.to(0, CAMS["intro"], 2.6)
        ctx.P("DEM").gold.set(0, 1.0)
        ctx.P("DEM").ring.set(0, 1.0)

        def tri(c, cam, tt, pr, al):
            pts = [pos_at(ctx, i, tt) for i in ("HAK", "ZAI", "DOU")]
            draw_poly(c, cam, pts, GOLD, al * 0.8, fill=0.18, dashed=True)
            spin_arrows(c, cam, centroid(pts), 5.0, tt, al)
        tl.annot(0, 2.6, tri)
    elif cmd == "genio":
        tl.title(t, t + 1.5, "GENIO", y=560, size=190)
        tl.punch.append((t, 1.0))
        ctx.sfx(t - 0.05, "boom", 0.45)
    elif cmd == "cam":
        tl.cam.to(t, CAMS[arg], 1.4)
        ctx.sfx(t, "whoosh", 0.5)
    elif cmd == "base":
        ctx.move(t, {k: v for k, v in BASE.items()}, 1.0)
        ctx.P("DEM").ring.to(t, 0.0, 0.3)
        ctx.P("DEM").gold.set(t, 0.0)
    elif cmd == "tag433":
        def tag(c, cam, tt, pr, al):
            sx, sy, _ = cam.project(-25, 45)
            pill(c, sx, sy, "4-3-3", 40, al, bg=GOLD, fg="#14161a", pad=(18, 10))
            for a, b in (("MEN", "PAC"), ("PAC", "MAR"), ("MAR", "HAK"), ("RUI", "VIT"), ("VIT", "ZAI"),
                         ("KVA", "DEM"), ("DEM", "DOU")):
                p = paint("#ffffff", 0.35 * al, stroke=3)
                c.drawPath(ground_path(cam, [pos_at(ctx, a, tt), pos_at(ctx, b, tt)]), p)
        tl.annot(t, end - 1.2, tag)
        ctx.sfx(t, "pop", 0.8)
    elif cmd == "fluid":
        ghosts = {k: BASE[k] for k in FLUID if not k.startswith("o")}

        def gh(c, cam, tt, pr, al):
            for pid, (x, y) in ghosts.items():
                draw_ring(c, cam, x, y, 1.6, "#ffffff", 0.55 * al, width=0.18, dashed=True)
                draw_arrow(c, cam, (x, y), pos_at(ctx, pid, tt), clamp01(pr / 0.9), "#ffb347", 0.0, 0.25,
                           alpha=0.8 * al)
        tl.annot(t, end - 0.4, gh)
        ctx.move(t, FLUID, 1.3)
    elif cmd == "tint":
        if arg == "on":
            tl.tint.to(t, 1.0, 0.4)
            ctx.sfx(t, "error", 0.7)
        else:
            tl.tint.to(t, 0.0, 0.5)
    elif cmd == "hl":
        p = ctx.P(arg)
        p.gold.set(t, 1.0)
        p.ring.to(t, 1.0, 0.3)  # l'anneau reste jusqu'à la fin du chapitre suivant
        p.ring.to(ctx.chapter_end(end + 0.1), 0.0, 0.3)
        ctx.sfx(t, "pop", 0.8)
    elif cmd == "drop":
        ctx.move(t, {"DEM": (0, 16)}, 1.3)

        def arr(c, cam, tt, pr, al):
            draw_arrow(c, cam, (0, 29), (0, 18.5), ease_out(pr / 0.9), GOLD, 0.0, 0.45, alpha=al)
        tl.annot(t, end + 0.1, arr)
        ctx.sfx(t, "whoosh", 0.4)
    elif cmd == "hl_cb":
        p = ctx.P("o4")
        p.ring.to(t, 1.0, 0.3)
        p.ring.to(end, 0.0, 0.3)

        def lab(c, cam, tt, pr, al):
            x, y = pos_at(ctx, "o4", tt)
            sx, sy, _ = cam.project(x, y, 0)
            pill(c, sx, sy - 85, "CENTRAL", 26, al, bg=RED, fg="#ffffff")
            draw_ring(c, cam, x, y, 2.3, RED, al, width=0.3, glow=True, fill=0.15)
        tl.annot(t, end, lab)
        ctx.sfx(t, "pop", 0.8)
    elif cmd == "follow":
        ctx.move(t, {"o4": (-1.5, 20)}, 1.0)
    elif cmd == "hole":
        def hole(c, cam, tt, pr, al):
            draw_ring(c, cam, -7.5, 38, 5.5, RED, al, width=0.35, dashed=True, fill=0.22)
            sx, sy, _ = cam.project(-7.5, 38)
            pill(c, sx, sy, "HUECO", 30, al, bg=RED, fg="#ffffff")
            draw_arrow(c, cam, pos_at(ctx, "KVA", t), (-10, 37), ease_out((pr - 0.3) / 0.8), GOLD, -3.0, 0.4,
                       alpha=al)
        tl.annot(t, t + 2.6, hole)
        tl.tint.to(t, 0.55, 0.3)
        tl.tint.to(t + 2.4, 0.0, 0.4)
        ctx.sfx(t, "error", 0.6)
    elif cmd == "stay":
        ctx.move(t, {"o4": (-7.5, 38)}, 0.9)
        ctx.move(t + 0.3, {"VIT": (0, 3), "RUI": (-12, 11), "ZAI": (12, 11)}, 1.0)
    elif cmd == "4v3":
        tl.title(t, t + 2.0, "4 vs 3", y=560, size=150, sub="SUPERIORIDAD EN EL MEDIO")
        tl.punch.append((t, 0.6))
        ctx.sfx(t, "pop", 0.8)
        for pid in ("DEM", "VIT", "RUI", "ZAI"):
            ctx.P(pid).ring.to(t, 1.0, 0.3)
            ctx.P(pid).ring.to(ctx.chapter_end(end + 0.1), 0.0, 0.3)

        def opp(c, cam, tt, pr, al):
            for pid in ("o8", "o6", "o10"):
                x, y = pos_at(ctx, pid, tt)
                draw_ring(c, cam, x, y, 2.2, RED, al, width=0.25, fill=0.12)
        tl.annot(t, end, opp)
    elif cmd == "ring":
        ctx.ring(t, arg)
    elif cmd == "rombo":
        def rb(c, cam, tt, pr, al):
            pts = [pos_at(ctx, i, tt) for i in ("VIT", "RUI", "DEM", "ZAI")]
            k = ease_out(pr / 0.6)
            cx, cy = centroid(pts)
            pts = [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in pts]
            draw_poly(c, cam, pts, GOLD, al, fill=0.28, width=0.35)
        tl.annot(t, end, rb)
        tl.title(t, t + 1.4, "ROMBO", y=560, size=140)
        ctx.sfx(t, "boom", 0.2)
    elif cmd == "clear":
        for p in tl.players.values():
            if p.ring(t) > 0:
                p.ring.to(t, 0.0, 0.3)
    elif cmd == "fb_up":
        ctx.move(t, {"MEN": (-29, 31), "HAK": (29, 31), "PAC": (-11, -6), "MAR": (11, -6)}, 1.4)

        def arr(c, cam, tt, pr, al):
            for x in (-27, 27):
                xs = 29 if x > 0 else -29
                draw_arrow(c, cam, (x, -11), (xs, 28.5), ease_out(pr / 1.2), GOLD, 0.0, 0.45, alpha=al)
        tl.annot(t, end, arr)
        ctx.sfx(t, "whoosh", 0.5)
    elif cmd == "height":
        tl.annot(t, end, lambda c, cam, tt, pr, al: draw_line_label(
            c, cam, 31, -33, 33, "ALTURA DE LOS DELANTEROS", al * clamp01(pr / 0.4)))
    elif cmd == "wingers_in":
        ctx.move(t, {"KVA": (-12, 27), "DOU": (12, 27)}, 1.2)

        def arr(c, cam, tt, pr, al):
            draw_arrow(c, cam, (-23, 26.5), (-13.5, 27.5), ease_out(pr / 0.9), GOLD, 2.0, 0.4, alpha=al)
            draw_arrow(c, cam, (23, 26.5), (13.5, 27.5), ease_out(pr / 0.9), GOLD, -2.0, 0.4, alpha=al)
        tl.annot(t, end, arr)
    elif cmd == "triangle":
        def tri(c, cam, tt, pr, al):
            for ids in (("HAK", "ZAI", "DOU"), ("MEN", "RUI", "KVA")):
                pts = [pos_at(ctx, i, tt) for i in ids]
                draw_poly(c, cam, pts, GOLD, al * clamp01(pr / 0.5), fill=0.25, width=0.35)
        tl.annot(t, end, tri)
        tl.title(t, t + 1.4, "TRIÁNGULO", y=560, size=130)
        ctx.sfx(t, "boom", 0.2)
    elif cmd == "spin":
        def sp(c, cam, tt, pr, al):
            pts = [pos_at(ctx, i, tt) for i in ("HAK", "ZAI", "DOU")]
            spin_arrows(c, cam, centroid(pts), 4.5, tt, al)
        tl.annot(t, end, sp)
    elif cmd == "r1":
        ctx.move(t, {"ZAI": (26, 19)}, 1.2)
        tl.annot(t, end, lambda c, cam, tt, pr, al: draw_arrow(
            c, cam, (13, 12), (25, 18), ease_out(pr / 0.9), "#ffffff", -2.5, 0.35, alpha=al))
    elif cmd == "r2":
        ctx.move(t, {"DOU": (7, 26)}, 1.2)
        tl.annot(t, end, lambda c, cam, tt, pr, al: draw_arrow(
            c, cam, (12, 28), (8, 26.5), ease_out(pr / 0.9), "#ffffff", 0, 0.35, alpha=al))
    elif cmd == "r3":
        ctx.move(t, {"HAK": (23, 44)}, 1.3)
        tl.annot(t, end, lambda c, cam, tt, pr, al: draw_arrow(
            c, cam, (29, 32), (23.5, 42.5), ease_out(pr / 1.0), GOLD, 3.0, 0.45, alpha=al))
        ctx.sfx(t, "whoosh", 0.5)
    elif cmd == "chaos":
        tl.tint.to(t, 1.0, 0.4)
        ctx.sfx(t, "error", 0.7)
        pairs = (("o2", "HAK"), ("o10", "ZAI"), ("o5", "DOU"), ("o3", "MEN"), ("o8", "RUI"))

        def broken(c, cam, tt, pr, al):
            for a, b in pairs:
                (x0, y0), (x1, y1) = pos_at(ctx, a, tt), pos_at(ctx, b, tt)
                p = paint("#ff5c5c", 0.85 * al, stroke=max(2, 0.22 * cam.scale_at(x0, y0)))
                dash(p, 12, 9)
                c.drawPath(ground_path(cam, [(x0, y0), (x1, y1)]), p)
                mx, my = (x0 + x1) / 2, (y0 + y1) / 2
                sx, sy, _ = cam.project(mx, my)
                k = ease_out((pr - 0.25) / 0.3) * 16
                xp = paint("#ff5c5c", al, stroke=7)
                c.drawLine(sx - k, sy - k, sx + k, sy + k, xp)
                c.drawLine(sx - k, sy + k, sx + k, sy - k, xp)
        tl.annot(t, end, broken)
        for pid, d in (("o2", (2, -3)), ("o5", (-2, -2)), ("o10", (3, 1)), ("o4", (-1, 2))):
            x, y = BASE[pid]
            ctx.move(t, {pid: (x + d[0], y + d[1])}, 0.8)
    elif cmd == "qmarks":
        def qm(c, cam, tt, pr, al):
            for i, pid in enumerate(("o2", "o5", "o4", "o10", "o3")):
                x, y = pos_at(ctx, pid, tt)
                draw_qmark(c, cam, x, y, al * clamp01((pr - 0.12 * i) / 0.3), tt)
        tl.annot(t, end, qm)
        ctx.sfx(t, "pop", 0.7)
    elif cmd == "free":
        ctx.move(t, {"HAK": (24, 44)}, 0.8)
        p = ctx.P("HAK")
        p.gold.set(t, 1.0)
        p.ring.to(t, 1.0, 0.3)

        def lib(c, cam, tt, pr, al):
            x, y = pos_at(ctx, "HAK", tt)
            sx, sy, _ = cam.project(x, y, 0)
            pill(c, sx, sy + 70, "LIBRE", 34, al * clamp01(pr / 0.3), bg=GOLD, fg="#14161a", pad=(20, 10))
        tl.annot(t, end, lib)
        ctx.sfx(t, "pop", 0.9)
    elif cmd == "riser":
        ctx.sfx(t - 0.4, "riser", 0.6)
        ctx.move(t, {k: v for k, v in BASE.items() if k != "DEM"} | {"DEM": (0, 26)}, 1.6)
        ctx.P("HAK").gold.set(t, 0.0)
        ctx.P("DEM").gold.set(t, 1.0)
        ctx.P("DEM").ring.to(t, 1.0, 0.3)
        tl.tint.to(t, 0.0, 0.3)
    elif cmd == "ucl":
        tl.leaks.to(t, 1.0, 0.6)
        tl.title(t, end, "CHAMPIONS LEAGUE 2025", y=340, size=58, color=GOLD)
    elif cmd == "boom":
        tl.punch.append((t, 1.2))
        ctx.sfx(t - 0.03, "boom", 0.6)
        tl.title(t, end, "2025", y=640, size=230, color="#ffffff")
    else:
        raise ValueError(f"commande inconnue : {cmd}")


def centroid(pts):
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def spin_arrows(c, cam, center, r, t, al):
    """Deux flèches circulaires qui tournent au sol (rotation du triangle)."""
    x, y = center
    for k in range(2):
        a0 = t * 2.2 + k * math.pi
        pts = circle_pts(x, y, r, 24, a0, a0 + 2.2)
        p = paint(GOLD, al, stroke=max(3, 0.35 * cam.scale_at(x, y)))
        c.drawPath(ground_path(cam, pts), p)
        (x1, y1), (x0, y0) = pts[-1], pts[-3]
        ang = math.atan2(y1 - y0, x1 - x0)
        tri = [(x1 + 1.2 * math.cos(ang), y1 + 1.2 * math.sin(ang)),
               (x1 + 1.4 * math.cos(ang + 2.2), y1 + 1.4 * math.sin(ang + 2.2)),
               (x1 + 1.4 * math.cos(ang - 2.2), y1 + 1.4 * math.sin(ang - 2.2))]
        c.drawPath(ground_path(cam, tri, True), paint(GOLD, al))


MUSIC_LEVELS = {  # chapitre -> intensité de la musique
    "PSG · LUIS ENRIQUE": 0.4, "LA ALINEACIÓN": 0.5, "DEMBÉLÉ": 0.75, "EL DILEMA": 0.75,
    "EL ROMBO": 1.0, "LOS LATERALES": 1.0, "EL TRIÁNGULO": 1.0, "EL RIVAL": 0.3, "CHAMPIONS 2025": 1.0,
}
