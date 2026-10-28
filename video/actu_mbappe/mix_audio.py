"""Mixage : voix ElevenLabs + musique (ducking sous la voix) + bruitages synchronisés -> build/mix.wav"""
import subprocess
from pathlib import Path
import numpy as np

ROOT = Path(__file__).parent
A, OUT = ROOT / "assets", ROOT / "build"
SR, DUR = 48000, 84.5
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

# ---- musique (« Ominosity », Tanner Helland, CC-BY 4.0) avec ducking sous la voix
music = load(A / "musique_ominosity.mp3")
music *= .9 / np.abs(music).max()
music = np.concatenate([music, music])[:N]
env = np.abs(np.pad(voice.mean(1), (0, max(0, N - len(voice))))[:N])
win = int(.25 * SR)
env = smooth(env, win)
duck = np.where(env > .02, .13, .3).astype(np.float32)
duck = smooth(duck, int(.3 * SR))
t = np.arange(N) / SR
fade = np.clip(t / .6, 0, 1) * np.clip((DUR - t) / 2.2, 0, 1)
mix[: len(music)] += music * (duck * fade)[:, None]

# ---- bruitages (packs CC0 : Kenney via soundcn, crafter-station/elements)
SFX = {p.stem: load(p) for p in (A / "sfx").glob("*.wav")}
for k, b in SFX.items():
    SFX[k] = b * (.8 / max(1e-6, np.abs(b).max()))

CUES = [
    # accroche
    ("riser", .2, .35), ("pop", .12, .6), ("pop", 1.2, .6), ("click", 1.2, .4), ("whoosh", 1.95, .7), ("pop", 2.5, .45),
    ("boom", 4.1, .9), ("lowboom", 4.12, .6), ("punch", 4.48, .6),
    # The Bridge
    ("whoosh-alt1", 5.05, .7), ("tick", 5.5, .5), ("glitch", 6.62, .35), ("notification", 7.6, .55),
    ("pop", 8.44, .5), ("pop", 8.62, .45), ("pop", 8.8, .45), ("pop", 8.98, .4),
    # le mème
    ("whoosh-alt2", 9.95, .6), ("pop", 10.85, .55), ("swoosh", 12.05, .55), ("scratch", 12.35, .7), ("scratch", 12.55, .7),
    ("whoosh", 12.6, .6), ("punch", 13.0, .8), ("tick", 13.05, .6), ("tick", 13.2, .6), ("boom", 14.06, .8), ("glitch2", 14.1, .8),
    # Mao
    ("whoosh-alt1", 15.35, .7), ("pop", 15.5, .6), ("whoosh", 16.8, .6), ("bell", 16.86, .55), ("pop", 17.2, .45),
    ("swoosh", 18.8, .6), ("click", 20.9, .6), ("punch", 21.2, .8), ("lowboom", 21.2, .55),
    # la vidéo explose
    ("whoosh-alt2", 22.15, .7), ("notification", 23.76, .6), ("pop", 23.8, .4), ("pop", 23.95, .4), ("pop", 24.1, .4),
    ("pop", 24.25, .4), ("whoosh", 25.45, .7), ("boom", 25.78, .9), ("punch", 25.8, .7),
    # Dongpeng
    ("whoosh-alt1", 26.68, .6), ("paper", 26.8, .7), ("whoosh-alt2", 27.25, .6), ("pop", 27.6, .4), ("pop", 28.6, .5),
    ("swoosh", 29.5, .6), ("scratch", 29.95, .8), ("paper", 29.97, .8), ("punch", 30.0, .7), ("uierror", 30.0, .5),
    ("click", 30.85, .5), ("whoosh", 32.45, .6), ("punch", 33.16, .5), ("tick", 34.37, .6), ("boom", 35.05, .85), ("uierror", 35.1, .5),
    # Mengniu
    ("whoosh-alt1", 35.7, .6), ("whoosh-alt2", 36.35, .6), ("pop", 36.7, .4), ("pop", 37.9, .5), ("swoosh", 38.3, .6),
    ("scratch", 38.9, .8), ("paper", 38.92, .8), ("punch", 39.2, .7), ("pop", 39.9, .45), ("pop", 40.02, .45), ("pop", 40.14, .45),
    ("uierror", 40.2, .55), ("uierror", 40.35, .55), ("error", 40.95, .5),
    # Pékin
    ("whoosh-alt2", 41.58, .7), ("drone", 41.7, .45), ("bell", 42.88, .6), ("whoosh", 43.75, .6), ("punch", 43.9, .5),
    ("pop", 44.05, .45), ("pop", 47.55, .5), ("punch", 48.72, .55),
    # télé d'État
    ("whoosh-alt1", 50.75, .7), ("punch", 51.56, .55), ("static", 54.05, .45), ("glitch", 54.08, .6), ("lowboom", 54.08, .7),
    # LaLiga / Real
    ("whoosh-alt2", 55.15, .7), ("paper", 55.3, .6), ("pop", 56.95, .5), ("whoosh", 58.35, .6), ("lowboom", 59.2, .7),
    ("tick", 59.4, .5), ("coins", 60.6, .7), ("coins2", 60.75, .7), ("coins", 61.0, .6),
    # excuses
    ("whoosh-alt1", 61.5, .7), ("reverse-whoosh", 61.9, .35), ("swoosh", 62.9, .6), ("click", 63.76, .6), ("pop", 63.78, .45),
    ("click", 64.56, .6), ("pop", 64.58, .45), ("click", 65.52, .6), ("pop", 65.54, .5), ("tick", 67.1, .5), ("tick", 68.3, .5),
    ("tick", 70.2, .5), ("magic-reveal", 71.1, .55), ("punch", 71.2, .6),
    # ça suffira ?
    ("whoosh-alt2", 71.9, .7), ("pop", 72.0, .6), ("pop", 73.6, .55), ("pop", 74.75, .4), ("pop", 74.95, .4), ("pop", 75.15, .4),
    ("whoosh-alt1", 75.7, .6), ("whoosh", 75.9, .55), ("coins2", 75.8, .5),
    # appel aux commentaires + abonnement
    ("swoosh", 76.4, .7), ("punch", 76.6, .6), ("pop", 77.2, .5), ("pop", 78.3, .5), ("whoosh", 80.35, .6),
    ("notification", 80.45, .6), ("success", 81.6, .6), ("pop", 81.6, .5),
]
LIM = {"drone": 6.5, "static": 1.2, "reverse-whoosh": 1.4, "keyboard": 1.5, "swoosh": 1.6, "boom": 2.6, "riser": 3.9}
for name, tt, g in CUES:
    put(SFX[name], tt, g * .55, LIM.get(name))

mix = np.tanh(mix * 1.1) / 1.1
mix.astype(np.float32).tofile(OUT / "mix.f32")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(OUT / "mix.f32"),
                "-af", "loudnorm=I=-14:TP=-1.0:LRA=11", "-ar", str(SR), str(OUT / "mix.wav")], check=True)
(OUT / "mix.f32").unlink()
print("OK -> build/mix.wav")
