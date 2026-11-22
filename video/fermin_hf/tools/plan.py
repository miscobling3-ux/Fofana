"""Edit plan (EDL) for the Fermín López goal video (Barça 2-2 Villarreal, 60').

Every segment starts on the first word of its sentence (data/words.json).
Source clips are 50 fps: A = live broadcast angle, B = replay angles.
Frame numbers are 1-based (0001.jpg = first frame of the clip).
"""

# ---- key events measured frame by frame on the 50 fps source ---------------
EV = {
    "A_raphinha_pass": 51,   # Raphinha -> Lamine (contact)
    "A_lamine_recv": 105,    # first touch of Lamine on the wing
    "A_lamine_pass": 305,    # live angle, Lamine's low pass
    "A_fermin_shot": 363,    # live angle, Fermín's strike
    "A_ball_in_net": 388,
    "B_lamine_pass_wide": 219,   # high replay
    "B_fermin_shot_wide": 277,
    "B_lamine_pass_close": 428,  # close replay
    "B_fermin_shot_close": 597,
}

# Overlay boxes in the 1920x1080 source (score bug, channel watermark, hashtag),
# measured from per-pixel temporal variance + 10 px margin.
OVERLAYS = [
    (86, 48, 316, 181),      # score bug (x0, y0, x1, y1)
    (1511, 55, 1844, 198),   # LEGITS X STRONG watermark
    (1615, 995, 1865, 1052), # #BarçaVillarreal
]

NAMES = {
    "fermin": ("Fermín López", "barca"),
    "lamine": ("Lamine Yamal", "barca"),
    "raphinha": ("Raphinha", "barca"),
}

# Segment fields:
#  t0,t1 output seconds; clip 'a'/'b'; f0,f1 source frames (linear) or freeze=f
#  cam: list of (track, weight, dx, dy) targets; H: base crop height in source px
#  labels: (track, who, src_from, src_to_exclusive)
#  spots:  (track|('box',x0,y0,x1,y1), t_start, t_end)
SEGMENTS = [
    # 0 hook: the strike (close replay)
    dict(t0=0.00, t1=2.30, clip="b", f0=555, f1=610,
         cam=[("B2_fer", 1, 40, 120)], H=1000,
         labels=[("B2_fer", "fermin", 568, 597)],
         spots=[("B2_fer", 0.64, 2.30)]),
    # 1 hook: ball in the net (live wide)
    dict(t0=2.30, t1=5.08, clip="a", f0=375, f1=458,
         cam=[("goal", 1, 0, 0)], H=900),
    # 2 Raphinha -> Lamine
    dict(t0=5.08, t1=8.74, clip="a", f0=1, f1=144,
         cam=[("A_rafa", 1, 0, 30)], cam2=("A_lamine1", 70, 100), H=760,
         labels=[("A_rafa", "raphinha", 1, 51), ("A_lamine1", "lamine", 105, 145)],
         spots=[("A_rafa", 5.92, 6.70), ("A_lamine1", 7.40, 8.74)]),
    # 3 Lamine advances (close live)
    dict(t0=8.74, t1=10.62, clip="a", f0=145, f1=218,
         cam=[("A2_lam", 1, 0, 230)], H=1080,
         labels=[("A2_lam", "lamine", 145, 219)],
         spots=[("A2_lam", 8.74, 10.62)]),
    # 4 freeze: 1 v 2
    dict(t0=10.62, t1=14.96, clip="b", freeze=205,
         cam=[("B1_lam", 1, -60, 90)], H=620,
         labels=[("B1_lam", "lamine", 1, 999)],
         rings=[((1067, 402, 42, 15), 13.12), ((1185, 405, 44, 15), 13.12)]),
    # 5 the two defenders in front of him (high replay)
    dict(t0=14.96, t1=19.90, clip="b", f0=67, f1=140,
         cam=[("B1_lam", 1, -60, 140)], H=900,
         labels=[("B1_lam", "lamine", 67, 219)]),
    # 6 not many Barça players in the box (high replay, continues)
    dict(t0=19.90, t1=25.18, clip="b", f0=140, f1=206,
         cam=[("B1_lam", 1, -150, 200)], H=1000,
         labels=[("B1_lam", "lamine", 67, 219)]),
    # 7 he waits for Fermín (live wide)
    dict(t0=25.18, t1=32.92, clip="a", f0=219, f1=316,
         cam=[("A3_lam", 0.5, 0, 0), ("A3_fer", 0.5, 0, 0)], H=1000,
         labels=[("A3_lam", "lamine", 219, 305)],
         spots=[("A3_lam", 28.72, 30.46), ("A3_fer", 30.46, 32.92)]),
    # 8 freeze: the passing lane
    dict(t0=32.92, t1=42.78, clip="a", freeze=304,
         cam=[("A3_lam", 0.5, 0, 0), ("A3_fer", 0.5, 0, 0)], H=960,
         labels=[("A3_lam", "lamine", 1, 999)],
         lane=(("A3_lam", "A3_fer"), 39.72),
         spots=[("A3_lam", 40.82, 41.94), ("A3_fer", 41.94, 42.78)]),
    # 9 he spots the space (high replay)
    dict(t0=42.78, t1=45.48, clip="b", f0=180, f1=219,
         cam=[("B1_lam", 1, -40, 120)], H=900,
         labels=[("B1_lam", "lamine", 180, 219)],
         spots=[("B1_lam", 42.78, 45.48)]),
    # 10 the low pass (close replay)
    dict(t0=45.48, t1=48.82, clip="b", f0=411, f1=470,
         cam=[("B2_lam", 1, 150, 330)], H=1080,
         labels=[("B2_lam", "lamine", 411, 428)]),
    # 11 freeze: "mirad bien"
    dict(t0=48.82, t1=50.00, clip="b", freeze=568,
         cam=[("B2_fer", 1, 60, 150)], H=900,
         labels=[("B2_fer", "fermin", 568, 597)]),
    # 12 first-time strike (close replay)
    dict(t0=50.00, t1=52.90, clip="b", f0=568, f1=605,
         cam=[("B2_fer", 1, 60, 150)], H=900,
         labels=[("B2_fer", "fermin", 568, 597)],
         spots=[("B2_fer", 50.00, 52.90)]),
    # 13 freeze: Fermín sees the keeper's position, camera then pans to the keeper
    dict(t0=52.90, t1=59.30, clip="a", freeze=360,
         cam=[("A3_fer", 1, -60, -40)], cam2t=("keeper", 54.45, 55.15), H=1000,
         labels=[("A3_fer", "fermin", 342, 363)], label_until=54.45,
         spots=[(("box", 539, 451, 608, 555), 54.72, 59.30)]),
    # 14 strike, high replay
    dict(t0=59.30, t1=62.20, clip="b", f0=245, f1=284,
         cam=[("B1_fer", 1, -150, 60)], H=900,
         labels=[("B1_fer", "fermin", 262, 277)],
         spots=[("B1_fer", 60.98, 62.20)]),
    # 15 strike + trajectory, live wide
    dict(t0=62.20, t1=66.10, clip="a", f0=345, f1=403,
         cam=[("A3_fer", 1, -120, 0)], cam2=("goal", 363, 385), H=1000,
         labels=[("A3_fer", "fermin", 345, 363)]),
    # 16 celebration x1
    dict(t0=66.10, t1=67.88, clip="a", f0=459, f1=548,
         cam=[("celeb", 1, 0, 0)], H=1080),
    # 17 Lamine's vision (close replay)
    dict(t0=67.88, t1=70.14, clip="b", f0=411, f1=440,
         cam=[("B2_lam", 1, 150, 330)], H=1080,
         labels=[("B2_lam", "lamine", 411, 428)]),
    # 18 Fermín's finish: celebration, slow
    dict(t0=70.14, t1=72.50, clip="a", f0=548, f1=614,
         cam=[("celeb", 1, 0, 0)], H=1080),
]

FREEZE_TIMES = [s["t0"] for s in SEGMENTS if "freeze" in s]

# strike / pass contacts -> kick sound (output time computed from source frame)
CONTACTS = [(0, "B_fermin_shot_close"), (2, "A_raphinha_pass"),
            (7, "A_lamine_pass"), (9, "B_lamine_pass_wide"), (10, "B_lamine_pass_close"),
            (12, "B_fermin_shot_close"), (14, "B_fermin_shot_wide"), (15, "A_fermin_shot"),
            (17, "B_lamine_pass_close")]

SCORE = dict(show=59.30, flip=65.76, hide=67.80, home="BAR", away="VIL", before=(1, 2), after=(2, 2), minute="60'")
END_CARD = dict(t0=70.30, title="¿MEJOR QUE\nBELLINGHAM?", sub="DÍMELO EN LOS COMENTARIOS")
DURATION = 72.50
FPS = 30

# Hand-placed silhouette boxes (x0,y0,x1,y1) for close-ups where the automatic
# non-grass silhouette merges with nearby players (keyframes, linearly interpolated).
MANUAL_BOXES = {
    "B2_fer": {556: (320, 190, 515, 500), 568: (320, 260, 550, 585), 580: (396, 320, 675, 745),
               592: (445, 375, 685, 790), 600: (390, 395, 785, 830), 608: (370, 405, 700, 830)},
    "A2_lam": {145: (1035, 468, 1310, 840), 170: (1020, 472, 1335, 855), 195: (1090, 432, 1340, 835),
               218: (1078, 488, 1340, 865)},
}
NOZOOM_SPOTS = {"B2_fer", "A2_lam"}   # circle already ~screen wide: no +22 % zoom (body would leave the frame)
