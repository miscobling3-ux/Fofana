"""Vidéo « hors-jeu de Lamine Yamal » : efface les logos des deux sources et les met au format 1920x960.

Logos masqués : score (en haut à gauche), gros bandeau « BAR 4 LALIGA 0 ALA » (en bas, début du clip A),
#BarçaAlavés, filigrane « x.com/marfawe » qui défile.

python3 offside_clean.py  ->  build/offside/frames/{a,b}/000123.jpg  (50 i/s)
"""
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from yamal_clean import find_pieces  # noqa: E402

OUT = os.path.join(HERE, "build", "offside", "frames")
W, H = 1920, 960
CLIPS = {
    # nom : (fichier, hauteur source, bande du filigrane (y0, y1), image + x du gabarit du filigrane)
    "a": ("sources/off_a.mov", 958, (760, 800), (1.0, 625)),
    "b": ("sources/off_b.mov", 964, (764, 804), (1.0, 902)),
}
FIXED = [(84, 0, 314, 58),          # score en haut à gauche
         (1650, 872, 1866, 924)]    # #BarçaAlavés
A_BANNER = ((466, 782, 1234, 888), 6.0)   # bandeau du score en bas du clip A, jusqu'à t = 6 s


def read_frames(path, h):
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-i", os.path.join(HERE, path), "-f", "rawvideo",
                           "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    while True:
        buf = ff.stdout.read(W * h * 3)
        if len(buf) < W * h * 3:
            break
        yield np.frombuffer(buf, np.uint8).reshape(h, W, 3).copy()
    ff.wait()


def clean(frame, tpl, band_y, extra):
    mask = np.zeros(frame.shape[:2], np.uint8)
    for x0, y0, x1, y1 in FIXED + extra:
        mask[y0:y1, x0:x1] = 255
    y0, y1 = band_y
    band = cv2.cvtColor(frame[y0:y1], cv2.COLOR_BGR2GRAY)
    bright = cv2.dilate((band > 150).astype(np.uint8) * 255, np.ones((11, 11), np.uint8))
    for x, w in find_pieces(band, tpl):
        a, b = max(0, x - 6), min(W, x + w + 6)
        mask[y0:y1, a:b] |= bright[:, a:b]
    for a, b in ((0, 40), (W - 40, W)):
        if (band[:, a:b] > 200).sum() > 25:
            lo, hi = max(0, a - 80), min(W, b + 80)
            mask[y0:y1, lo:hi] |= bright[:, lo:hi]
    h = frame.shape[0]
    small = cv2.resize(frame, (W // 2, h // 2), interpolation=cv2.INTER_AREA)
    msmall = cv2.dilate(cv2.resize(mask, (W // 2, h // 2), interpolation=cv2.INTER_NEAREST), np.ones((3, 3), np.uint8))
    fill = cv2.GaussianBlur(cv2.inpaint(small, msmall, 6, cv2.INPAINT_TELEA), (0, 0), 2.0)
    fill = cv2.resize(fill, (W, h), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    fill += np.random.default_rng(0).normal(0, 3, frame.shape).astype(np.float32)
    soft = cv2.GaussianBlur(mask, (0, 0), 3).astype(np.float32)[..., None] / 255.0
    out = np.clip(frame.astype(np.float32) * (1 - soft) + fill * soft, 0, 255).astype(np.uint8)
    return cv2.resize(out, (W, H), interpolation=cv2.INTER_AREA)


def main():
    for name, (path, h, band_y, (tt, tx)) in CLIPS.items():
        d = os.path.join(OUT, name)
        os.makedirs(d, exist_ok=True)
        if os.listdir(d) and "--force" not in sys.argv:
            print(f"{name}: déjà fait")
            continue
        cap = cv2.VideoCapture(os.path.join(HERE, path))
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(tt * 50))
        ref = cap.read()[1]
        tpl = cv2.cvtColor(ref[band_y[0]:band_y[1], tx:tx + 246], cv2.COLOR_BGR2GRAY)
        n = 0
        for i, fr in enumerate(read_frames(path, h)):
            n += 1
            extra = [A_BANNER[0]] if name == "a" and i / 50 < A_BANNER[1] else []
            cv2.imwrite(os.path.join(d, f"{i:06d}.jpg"), clean(fr, tpl, band_y, extra), [cv2.IMWRITE_JPEG_QUALITY, 93])
        print(f"{name}: {n} images")


if __name__ == "__main__":
    main()
