"""Mixage de l'histoire : voix ElevenLabs + bruitages synchronisés, SANS musique -> build/mix.wav"""
import subprocess
from pathlib import Path
import numpy as np

ROOT = Path(__file__).parent
A, OUT = ROOT / "assets", ROOT / "build"
SR, DUR = 48000, 62.5
OUT.mkdir(exist_ok=True)


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


N = int(DUR * SR)


def smooth(x, w):
    c = np.cumsum(np.insert(x.astype(np.float64), 0, 0))
    y = (c[w:] - c[:-w]) / w
    pad = len(x) - len(y)
    return np.pad(y, (pad // 2, pad - pad // 2), mode="edge").astype(np.float32)
mix = np.zeros((N, 2), np.float32)


def put(buf, t, gain=1.0, max_len=None):
    s = int(t * SR)
    if max_len:
        buf = buf[: int(max_len * SR)].copy()
        fade = min(len(buf), int(.08 * SR))
        buf[-fade:] *= np.linspace(1, 0, fade)[:, None]
    e = min(N, s + len(buf))
    if e > s:
        mix[s:e] += buf[: e - s] * gain


# ---- voix
voice = load(A / "voix.mp3")
voice *= .9 / np.abs(voice).max()
put(voice, 0.0, 1.0)

# ---- bruitages (packs CC0 : Kenney via soundcn, crafter-station/elements) — pas de musique
SFX = {p.stem: load(p) for p in (A / "sfx").glob("*.wav")}
for k, b in SFX.items():
    SFX[k] = b * (.8 / max(1e-6, np.abs(b).max()))


def loop(name, t0, t1, gain, fade=.4):
    """Répète un son d'ambiance entre t0 et t1 avec fondu."""
    b = SFX[name]
    n = int((t1 - t0) * SR)
    buf = np.tile(b, (n // len(b) + 1, 1))[:n].copy()
    f = int(fade * SR)
    buf[:f] *= np.linspace(0, 1, f)[:, None]
    buf[-f:] *= np.linspace(1, 0, f)[:, None]
    put(buf, t0, gain)


# ambiances
loop("hum", 6.0, 21.9, .16)            # ascenseur qui monte
loop("neon", 21.9, 50.5, .07)          # néon qui grésille dans le couloir
loop("neon", 57.35, 59.7, .1)
loop("hum", 50.5, 55.4, .1)
# battements de cœur qui accélèrent
t, step = 39.4, .95
while t < 50.4:
    put(SFX["coeur1"], t, .5)
    put(SFX["coeur2"], t + .22, .35)
    t += step
    step = max(.42, step * .93)

CUES = [
    ("whoosh-alt1", 0.0, .5), ("pas0", .6, .35), ("pas1", 1.1, .35), ("pas2", 1.6, .35), ("pas3", 2.1, .35), ("pas0", 2.6, .35),
    ("pas1", 3.1, .35), ("porte_bois", 3.8, .4), ("whoosh", 3.85, .5), ("pas2", 4.3, .35), ("pas3", 4.8, .35), ("pas0", 5.3, .35),
    ("porte_ouvre", 5.95, .55), ("bouton", 8.16, .9), ("pop", 8.16, .25), ("metal", 10.4, .35),
    ("bouton", 11.84, .25), ("bouton", 12.8, .25), ("bouton", 13.68, .25),
    ("riser", 12.2, .4), ("glitch", 15.0, .45), ("ding", 16.08, 1.0), ("ding2", 16.1, .5), ("lowboom", 16.08, .7),
    ("whoosh-alt2", 18.3, .5), ("glitch2", 19.6, .7), ("glitch2", 19.9, .6),
    ("porte_ouvre", 21.75, .8), ("whoosh", 21.8, .4), ("pop", 27.0, .3), ("pop", 28.4, .3), ("neon", 29.6, .35), ("glitch2", 29.7, .5),
    ("whoosh-alt1", 31.1, .45), ("grince", 32.6, .7), ("pop", 32.7, .3),
    ("lowboom", 35.44, .8), ("glitch", 35.44, .4), ("pop", 37.05, .35), ("glitch", 40.5, .5), ("boom", 40.52, .5),
    ("whoosh-alt2", 41.25, .45), ("lowboom", 42.88, .6),
    ("porte_ferme", 44.7, .55), ("metal", 46.4, .3), ("bouton", 47.4, .3), ("pop", 47.84, .4), ("pop", 48.6, .35), ("pop", 49.0, .4),
    ("whoosh", 50.45, .5), ("pop", 55.5, .35), ("pop", 55.75, .35), ("notification", 55.8, .45),
    ("whoosh-alt1", 57.25, .5), ("riser", 57.4, .45), ("boom", 59.0, .9), ("lowboom", 59.0, .7), ("glitch", 59.7, .6), ("porte_ferme", 59.75, .9),
    ("magic-reveal", 60.0, .4),
]
LIM = {"riser": 1.9, "boom": 2.5, "glitch": .6, "neon": 1.2, "magic-reveal": 2.0}
for name, tt, g in CUES:
    put(SFX[name], tt, g * .6, LIM.get(name))

mix = np.tanh(mix * 1.1) / 1.1
mix.astype(np.float32).tofile(OUT / "mix.f32")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(OUT / "mix.f32"),
                "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-ar", str(SR), str(OUT / "mix.wav")], check=True)
(OUT / "mix.f32").unlink()
print("OK -> build/mix.wav")
