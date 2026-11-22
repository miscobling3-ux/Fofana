"""Measures the final mix: no crowd / stadium bed anywhere.
Every 20 ms window where neither the voice nor a sound effect is playing must be silent (< -60 dBFS),
and the voice-only windows must not carry a broadband noise floor (crowd) between words.
python3 tools/audio_check.py renders/final.mp4
"""
import json, subprocess, sys, numpy as np
mp4 = sys.argv[1]
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp4, "-ac", "1", "-ar", "48000", "-f", "f32le", "-"],
                     capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.float32)
words = json.load(open("data/words.json")); sfx = json.load(open("data/sfx.json"))
SFX_DUR = {"166": .81, "174": 1.05, "168": .89, "3115": .61, "1492": 1.39, "3005": .21, "2112": 1.47, "2108": .97, "2099": 1.6}
busy = []
for w in words: busy.append((w["start"] - 0.08, w["end"] + 0.12))
for s in sfx: busy.append((s["t"] - 0.02, s["t"] + SFX_DUR[s["src"].split("/")[1][:-4]] + 0.05))
win = 960; n = len(x) // win; quiet = []
for i in range(n):
    t0, t1 = i * win / 48000, (i + 1) * win / 48000
    if any(a < t1 and t0 < b for a, b in busy): continue
    rms = np.sqrt(np.mean(x[i * win:(i + 1) * win] ** 2) + 1e-12)
    quiet.append((t0, 20 * np.log10(rms)))
lv = [q[1] for q in quiet]
print(f"silent-gap windows: {len(quiet)} ({len(quiet) * 0.02:.1f} s)  max {max(lv):.1f} dBFS  median {np.median(lv):.1f} dBFS")
loud = [q for q in quiet if q[1] > -60]
print("windows above -60 dBFS outside voice/sfx:", len(loud), [round(q[0], 2) for q in loud[:10]])

# ---- the clips' own sound (crowd, stadium) must not be in the mix: normalised cross-correlation
from scipy.signal import fftconvolve
def load(p, sr=8000):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(r, np.float32).astype(np.float64)
mix = load(mp4)
for clip in sys.argv[2:]:
    c = load(clip); c = c - c.mean()
    num = fftconvolve(mix, c[::-1], mode="valid")
    e = np.sqrt(fftconvolve(mix ** 2, np.ones(len(c)), mode="valid") * np.sum(c ** 2)) + 1e-9
    print(f"max correlation with original sound of {clip.split('/')[-1]}: {np.max(np.abs(num / e)):.3f}  (1.0 = clip audio present)")
# ---- same test on the voice file: shows the method detects a present source
v = load("assets/audio/voice_es.wav")[8000 * 10:8000 * 23]; v = v - v.mean()
num = fftconvolve(mix, v[::-1], mode="valid"); e = np.sqrt(fftconvolve(mix ** 2, np.ones(len(v)), mode="valid") * np.sum(v ** 2)) + 1e-9
print(f"control: max correlation with the voice-over itself: {np.max(np.abs(num / e)):.3f}")
