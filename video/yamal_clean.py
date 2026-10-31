"""Efface les logos des vidéos sources (score, beIN SPORTS, #BarçaAlavés, filigrane « x.com/marfawe » qui défile).

python3 yamal_clean.py  ->  build/yamal/frames/{wide,close}/000123.jpg  (50 i/s, 1920x1080, logos masqués)
"""
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "build", "yamal", "frames")
SOURCES = {
    "wide": (os.path.join(HERE, "sources", "yamal_wide.mp4"), 9.6),
    "close": (os.path.join(HERE, "sources", "yamal_close.mp4"), 16.4),
}
W, H = 1920, 1080
# logos fixes (x0, y0, x1, y1) en pixels source
FIXED = [(88, 34, 312, 176),        # tableau de score
         (1606, 50, 1834, 114),     # beIN SPORTS / LIVE
         (1652, 996, 1862, 1046)]   # #BarçaAlavés
BAND = (874, 924)                   # bande verticale du filigrane qui défile


def text_mask(gray):
    m = (gray > 170).astype(np.uint8) * 255
    return cv2.dilate(m, np.ones((7, 7), np.uint8))


def find_pieces(band, tpl, n=4, thr=0.55):
    """Cherche chaque morceau du filigrane séparément : il peut être coupé par le bord de l'image."""
    tw = tpl.shape[1]
    step = tw // n
    found = []
    for k in range(n):
        piece = tpl[:, k * step:(k + 1) * step]
        r = cv2.matchTemplate(band, piece, cv2.TM_CCOEFF_NORMED)[0]
        for _ in range(3):  # jusqu'à 3 occurrences
            x = int(np.argmax(r))
            if r[x] < thr:
                break
            found.append((x, step))
            r[max(0, x - step):x + step] = -1
    return found


def clean(frame, tpl, tpl_mask):
    mask = np.zeros(frame.shape[:2], np.uint8)
    for x0, y0, x1, y1 in FIXED:
        mask[y0:y1, x0:x1] = 255
    y0, y1 = BAND
    band = cv2.cvtColor(frame[y0:y1], cv2.COLOR_BGR2GRAY)
    bright = cv2.dilate((band > 150).astype(np.uint8) * 255, np.ones((11, 11), np.uint8))
    for x, w in find_pieces(band, tpl):
        a, b = max(0, x - 6), min(W, x + w + 6)
        mask[y0:y1, a:b] |= bright[:, a:b]
    # morceau de texte coupé par les bords gauche/droit
    for a, b in ((0, 40), (W - 40, W)):
        edge = band[:, a:b]
        if (edge > 200).sum() > 25:
            mask[y0:y1, max(0, a - 80):min(W, b + 80)] |= bright[:, max(0, a - 80):min(W, b + 80)]
    # inpainting à demi-résolution (plus lisse et plus rapide), recollé seulement dans le masque
    small = cv2.resize(frame, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
    msmall = cv2.resize(mask, (W // 2, H // 2), interpolation=cv2.INTER_NEAREST)
    msmall = cv2.dilate(msmall, np.ones((3, 3), np.uint8))
    fill = cv2.inpaint(small, msmall, 6, cv2.INPAINT_TELEA)
    fill = cv2.GaussianBlur(fill, (0, 0), 2.0)
    fill = cv2.resize(fill, (W, H), interpolation=cv2.INTER_CUBIC)
    # léger grain pour ne pas avoir une tache trop lisse
    noise = np.random.default_rng(len(frame)).normal(0, 3, frame.shape).astype(np.float32)
    fill = np.clip(fill.astype(np.float32) + noise, 0, 255)
    soft = cv2.GaussianBlur(mask, (0, 0), 3).astype(np.float32)[..., None] / 255.0
    out = frame.astype(np.float32) * (1 - soft) + fill * soft
    return out.astype(np.uint8)


def main():
    ref = None
    for name, (path, dur) in SOURCES.items():
        d = os.path.join(OUT, name)
        os.makedirs(d, exist_ok=True)
        if len(os.listdir(d)) > 0 and "--force" not in sys.argv:
            print(f"{name}: déjà fait")
            continue
        ff = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-t", str(dur), "-f", "rawvideo",
                               "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
        i = 0
        while True:
            buf = ff.stdout.read(W * H * 3)
            if len(buf) < W * H * 3:
                break
            fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
            if ref is None:
                ref = cv2.imread(os.path.join(HERE, "sources", "yamal_watermark.png"), cv2.IMREAD_GRAYSCALE)
                ref_mask = text_mask(ref)
            cv2.imwrite(os.path.join(d, f"{i:06d}.jpg"), clean(fr, ref, ref_mask), [cv2.IMWRITE_JPEG_QUALITY, 93])
            i += 1
        ff.wait()
        print(f"{name}: {i} images")


if __name__ == "__main__":
    main()
