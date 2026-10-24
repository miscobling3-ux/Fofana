"""Musique et bruitages façon console 16 bits (carrés, triangle, bruit), synthétisés en numpy."""
import numpy as np
from scipy.signal import lfilter

SR = 48000


def _lowpass(x, cutoff):
    a = 1 - np.exp(-2 * np.pi * cutoff / SR)
    return lfilter([a], [1, a - 1], x)


def note_hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def pulse(f, n, duty=0.5):
    ph = (np.arange(n) * np.asarray(f) / SR) % 1.0 if np.isscalar(f) else np.cumsum(f) / SR % 1.0
    return np.where(ph < duty, 1.0, -1.0)


def tri(f, n):
    ph = (np.arange(n) * f / SR) % 1.0 if np.isscalar(f) else np.cumsum(f) / SR % 1.0
    return 4 * np.abs(ph - 0.5) - 1


def noise(n, rng, period=1):
    x = rng.choice([-1.0, 1.0], n // period + 1)
    return np.repeat(x, period)[:n]


def env(n, attack=0.002, decay=0.2, sustain=0.0, release=0.02):
    t = np.arange(n) / SR
    e = np.minimum(1, t / attack) * (sustain + (1 - sustain) * np.exp(-t / decay))
    r = int(release * SR)
    if 0 < r < n:
        e[-r:] *= np.linspace(1, 0, r)
    return e


# ---------------------------------------------------------------- musique
def make_music(duration, sections, bpm=100, seed=3):
    """Ré mineur, i-VI-iv-V. sections : (t0, t1, niveau 0..1) pour l'intensité."""
    rng = np.random.default_rng(seed)
    n = int(duration * SR) + SR
    out = np.zeros(n)
    beat = 60 / bpm
    bar = 4 * beat
    prog = [(50, [62, 65, 69]), (46, [58, 62, 65]), (43, [55, 58, 62]), (45, [57, 61, 64])]

    def level(t):
        v = 0.4
        for a, b, l in sections:
            if a <= t < b:
                v = l
        return v

    def add(sig, t, g):
        i = int(t * SR)
        if i >= n:
            return
        e = min(n, i + len(sig))
        out[i:e] += sig[:e - i] * g

    kick_n = int(0.18 * SR)
    kick_f = 140 * np.exp(-np.arange(kick_n) / SR * 30) + 45
    kick = tri(kick_f, kick_n) * env(kick_n, decay=0.08)
    snare = noise(int(0.14 * SR), rng, 3) * env(int(0.14 * SR), decay=0.05)
    hat = noise(int(0.04 * SR), rng, 1) * env(int(0.04 * SR), decay=0.012)

    for b in range(int(duration / bar) + 1):
        t0 = b * bar
        root, chord = prog[b % 4]
        L = level(t0)
        # basse triangle
        steps = [0, 2, 4, 6] if L > 0.3 else [0]
        for s in steps:
            ln = int(beat * (0.9 if L > 0.3 else 3.8) * SR)
            m = root - 12 + (12 if s == 4 and L > 0.6 else 0)
            add(tri(note_hz(m), ln) * env(ln, decay=0.5, sustain=0.6), t0 + s * beat / 2, 0.32)
        # arpège en carré 25 %
        div = 4 if L >= 0.7 else 2
        notes = chord + [chord[0] + 12]
        for s in range(4 * div):
            m = notes[[0, 1, 2, 3, 2, 1][s % 6]] + (12 if L >= 0.85 else 0)
            ln = int(beat / div * 0.9 * SR)
            add(pulse(note_hz(m), ln, 0.25) * env(ln, decay=0.09), t0 + s * beat / div, 0.07 + 0.05 * L)
        # mélodie
        if L >= 0.8:
            mel = [chord[2] + 12, chord[1] + 12, chord[0] + 12, chord[1] + 12]
            for s, m in enumerate(mel):
                ln = int(beat * 0.85 * SR)
                tt = np.arange(ln) / SR
                f = note_hz(m) * (1 + 0.006 * np.sin(2 * np.pi * 6 * tt))
                add(pulse(f, ln, 0.5) * env(ln, decay=0.4, sustain=0.5), t0 + s * beat, 0.07)
        # batterie
        for s in range(8):
            ts = t0 + s * beat / 2
            if L >= 0.4:
                add(hat, ts, 0.12 if s % 2 == 0 else 0.07)
            if L >= 0.65 and s in (0, 4, 5 if b % 2 else 0):
                add(kick, ts, 0.5)
            if L >= 0.8 and s in (2, 6):
                add(snare, ts, 0.18)
    return _lowpass(out, 6000)[:int(duration * SR)]


# ---------------------------------------------------------------- bruitages
def sfx(kind, rng=None):
    rng = rng or np.random.default_rng(1)

    def seq(notes, d, duty=0.5, dec=0.06):
        parts = []
        for m in notes:
            ln = int(d * SR)
            parts.append(pulse(note_hz(m), ln, duty) * env(ln, decay=dec))
        return np.concatenate(parts)

    if kind == "blip":
        return seq([88], 0.05, 0.5, 0.03) * 0.25
    if kind == "tick":
        return seq([96], 0.025, 0.25, 0.01) * 0.18
    if kind == "coin":
        return np.concatenate([seq([83], 0.06), seq([88], 0.22, dec=0.1)]) * 0.25
    if kind == "thud":
        n = int(0.35 * SR)
        f = 110 * np.exp(-np.arange(n) / SR * 12) + 40
        body = tri(f, n) * env(n, decay=0.12)
        hit = _lowpass(noise(n, rng, 2), 2500) * env(n, decay=0.04)
        return np.tanh(2 * (body + hit)) * 0.6
    if kind == "sweep":
        n = int(0.32 * SR)
        f = 1400 * np.exp(-np.arange(n) / SR * 6)
        return pulse(f, n, 0.25) * env(n, decay=0.15) * 0.08
    if kind == "jingle":
        return np.concatenate([seq([72, 76, 79], 0.07), seq([84], 0.5, dec=0.25)]) * 0.25
    if kind == "sparkle":
        return seq([96, 100, 103, 108], 0.05, 0.25, 0.04) * 0.15
    if kind == "alarm":
        return np.concatenate([seq([81], 0.14, dec=1), seq([76], 0.14, dec=1)] * 3) * 0.12
    if kind == "bark":
        n = int(0.1 * SR)
        f = 620 * np.exp(-np.arange(n) / SR * 9)
        b = (pulse(f, n, 0.3) * 0.6 + noise(n, rng, 4) * 0.4) * env(n, decay=0.05)
        return np.concatenate([b, np.zeros(int(0.06 * SR)), b]) * 0.3
    if kind == "boom":
        n = int(1.2 * SR)
        f = 120 * np.exp(-np.arange(n) / SR * 3) + 35
        return np.tanh(2 * (tri(f, n) + 0.4 * _lowpass(noise(n, rng, 2), 800))) * env(n, decay=0.4) * 0.5
    raise ValueError(kind)


def mix_all(voice, music, events, duration):
    """voice/music : mono SR. events : (t, kind, gain)."""
    n = int(duration * SR)
    v = np.zeros(n)
    v[:min(n, len(voice))] = voice[:n]
    m = np.zeros(n)
    m[:min(n, len(music))] = music[:n]
    e = np.convolve(np.abs(v), np.ones(4800) / 4800, "same")
    e = np.convolve(e, np.ones(9600) / 9600, "same")
    m = m / (np.max(np.abs(m)) + 1e-9) * 0.36 * (1 - 0.5 * np.clip(e / 0.05, 0, 1))
    v = v / (np.max(np.abs(v)) + 1e-9) * 0.92
    fx = np.zeros(n)
    rng = np.random.default_rng(5)
    cache = {}
    for t, kind, g in events:
        if kind not in cache:
            cache[kind] = sfx(kind, rng)
        s = cache[kind]
        i = int(t * SR)
        if i >= n:
            continue
        j = min(n, i + len(s))
        fx[i:j] += s[:j - i] * g
    out = np.tanh((v + m + fx) * 1.1) / np.tanh(1.1)
    fade = int(0.8 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)
    return out
