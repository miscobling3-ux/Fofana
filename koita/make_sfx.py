"""Bruitages synthétisés (Mixkit inaccessible depuis cet environnement) : coupes, arrêt sur image, pop, frappe de balle."""
import sys, numpy as np, soundfile as sf
sys.path.insert(0, "/home/user/Fofana/video")
from audio import sfx, _lowpass, _highpass, SR
rng = np.random.default_rng(3)
def save(name, y):
    y = y / (np.max(np.abs(y)) + 1e-9) * 0.7
    fade = int(0.004 * SR); y[:fade] *= np.linspace(0, 1, fade); y[-fade:] *= np.linspace(1, 0, fade)
    sf.write(f"hf/assets/sfx/{name}.wav", y.astype(np.float32), SR)
# 4 coupes (whoosh courts, variantes)
for i, (dur, lo, hi) in enumerate([(0.32, 400, 6000), (0.28, 600, 7000), (0.36, 300, 5000), (0.30, 500, 8000)]):
    n = int(dur * SR); t = np.arange(n) / SR
    x = rng.normal(0, 1, n); cut = lo + hi * np.sin(np.pi * t / t[-1]) ** 2
    y = np.zeros(n); st = 0.0
    for k in range(n):
        a = 1 - np.exp(-2 * np.pi * cut[k] / SR); st += a * (x[k] - st); y[k] = st
    save(f"cut{i+1}", y * np.abs(np.sin(np.pi * t / t[-1])) ** 1.3)
# arrêt sur image : "shutter" (clic + souffle descendant)
n = int(0.45 * SR); t = np.arange(n) / SR
click = np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 90)
air = _lowpass(rng.normal(0, 1, n), 3000) * np.exp(-t * 7) * 0.5
tone = np.sin(2 * np.pi * np.cumsum(900 * np.exp(-t * 5) + 120) / SR) * np.exp(-t * 6) * 0.4
save("freeze", click + air + tone)
save("pop", sfx("pop"))
# frappes de balle (3 variantes) : impact sourd + claquement
for i, f0 in enumerate([95, 110, 85]):
    n = int(0.3 * SR); t = np.arange(n) / SR
    thump = np.sin(2 * np.pi * np.cumsum(f0 + 120 * np.exp(-t * 60)) / SR) * np.exp(-t * 22)
    snap = _highpass(rng.normal(0, 1, n), 1500) * np.exp(-t * 140) * 0.7
    save(f"kick{i+1}", np.tanh(2.2 * (thump + snap)))
print("ok")
