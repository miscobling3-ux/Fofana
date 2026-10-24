"""Voix off (Kokoro, hors-ligne), estimation du timing des mots, musique et bruitages synthétisés."""
import re
import numpy as np

SR = 48000


# ---------------------------------------------------------------- voix
def load_tts(model_dir):
    from kokoro_onnx import Kokoro
    return Kokoro(f"{model_dir}/kokoro.onnx", f"{model_dir}/voices.bin")


def synth_line(tts, text, voice, speed, lang="es"):
    import scipy.signal as ss
    a, sr = tts.create(text, voice=voice, speed=speed, lang=lang)
    a = ss.resample_poly(a.astype(np.float64), SR, sr)
    return trim(a)


def trim(a, thr=0.008):
    env = np.convolve(np.abs(a), np.ones(480) / 480, "same")
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return a
    s, e = max(0, idx[0] - 960), min(len(a), idx[-1] + 2400)
    return a[s:e]


VOWELS = re.compile(r"[aeiouáéíóúüyàâèêëîïôùûœAEIOUÁÉÍÓÚÜYÀÂÈÊËÎÏÔÙÛŒ]+")


def syllables(word):
    return max(1, len(VOWELS.findall(word)))


def silences(a, min_len=0.09, thr=0.012):
    """Pauses à l'intérieur de la phrase (début, fin) en secondes."""
    hop = int(0.01 * SR)
    env = np.array([np.sqrt(np.mean(a[i:i + hop] ** 2)) for i in range(0, len(a) - hop, hop)])
    quiet = env < thr
    out, start = [], None
    for i, q in enumerate(quiet):
        if q and start is None:
            start = i
        elif not q and start is not None:
            if (i - start) * 0.01 >= min_len and start > 5:
                out.append((start * 0.01, i * 0.01))
            start = None
    return out


def word_times(words_spoken, audio):
    """Répartit les mots sur l'audio : ancrage sur les pauses de ponctuation, puis au prorata des syllabes."""
    dur = len(audio) / SR
    gaps = silences(audio)
    punct = [i for i, w in enumerate(words_spoken[:-1]) if re.search(r"[,.:;?!]$", w)]
    if gaps and len(gaps) >= len(punct) > 0:
        # garder les pauses les plus longues, dans l'ordre
        gaps = sorted(sorted(gaps, key=lambda g: g[0] - g[1])[:len(punct)])
        bounds = [(0.02, None)]
        segs = []
        prev_w, prev_t = 0, 0.02
        for p, (g0, g1) in zip(punct, gaps):
            segs.append((prev_w, p + 1, prev_t, g0))
            prev_w, prev_t = p + 1, g1
        segs.append((prev_w, len(words_spoken), prev_t, dur - 0.05))
    else:
        segs = [(0, len(words_spoken), 0.02, dur - 0.05)]
    times = []
    for w0, w1, t0, t1 in segs:
        ws = [syllables(w) for w in words_spoken[w0:w1]]
        tot = sum(ws)
        acc = t0
        for k in ws:
            d = (t1 - t0) * k / tot
            times.append((acc, acc + d))
            acc += d
    return times


# ---------------------------------------------------------------- synthèse musique
def _env(n, a, d, sr=SR):
    t = np.arange(n) / sr
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def _lowpass(x, cutoff):
    alpha = 1 - np.exp(-2 * np.pi * cutoff / SR)
    from scipy.signal import lfilter
    return lfilter([alpha], [1, alpha - 1], x)


def _highpass(x, cutoff):
    return x - _lowpass(x, cutoff)


def note_hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def kick(rng):
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 45 + 95 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 7) * 0.9 + rng.normal(0, 1, n) * np.exp(-t * 300) * 0.15


def clap(rng):
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    x = _highpass(rng.normal(0, 1, n), 1200)
    e = np.exp(-t * 18) + 0.6 * np.exp(-((t - 0.012) % 0.011) * 400) * (t < 0.035)
    return x * e * 0.35


def hat(rng, open_=False):
    n = int((0.25 if open_ else 0.06) * SR)
    t = np.arange(n) / SR
    return _highpass(rng.normal(0, 1, n), 7000) * np.exp(-t * (14 if open_ else 70)) * 0.22


def saw(f, n, detune=0.0):
    t = np.arange(n) / SR
    out = 0
    for d in (-detune, 0, detune):
        ph = (t * f * (1 + d)) % 1.0
        out = out + (2 * ph - 1)
    return out / 3


def make_music(duration, bpm=96, seed=7, sections=None):
    """Beat tendu (la mineur). sections: liste (t0, t1, niveau 0..1) pour l'intensité."""
    rng = np.random.default_rng(seed)
    n = int(duration * SR) + SR
    mix = np.zeros(n)
    beat = 60 / bpm
    bar = 4 * beat
    prog = [(57, [57, 60, 64]), (53, [53, 57, 60]), (50, [50, 53, 57]), (52, [52, 56, 59])]  # Am F Dm E
    k, cl, hh, oh = kick(rng), clap(rng), hat(rng), hat(rng, True)

    def level(t):
        if not sections:
            return 1.0
        v = 0.4
        for a, b, l in sections:
            if a <= t < b:
                v = l
        return v

    def add(sig, t, g=1.0):
        i = int(t * SR)
        if i >= n:
            return
        e = min(n, i + len(sig))
        mix[i:e] += sig[:e - i] * g

    nbars = int(duration / bar) + 1
    pad = np.zeros(n)
    bass = np.zeros(n)
    for b in range(nbars):
        t0 = b * bar
        root, chord = prog[b % 4]
        L = level(t0)
        # pad
        ln = int(bar * SR)
        seg = sum(saw(note_hz(m), ln, 0.004) for m in chord) / 3
        env = np.minimum(1, np.arange(ln) / (0.4 * SR)) * np.minimum(1, (ln - np.arange(ln)) / (0.3 * SR))
        i = int(t0 * SR)
        e = min(n, i + ln)
        pad[i:e] += (seg * env)[:e - i] * 0.22
        # basse 808
        for off in ([0, 2.5] if L > 0.5 else [0]):
            bn = int(beat * 1.8 * SR)
            tt = np.arange(bn) / SR
            f = note_hz(root - 24)
            sig = np.tanh(2.2 * np.sin(2 * np.pi * f * tt)) * np.exp(-tt * 1.6) * 0.5
            j = int((t0 + off * beat) * SR)
            e2 = min(n, j + bn)
            bass[j:e2] += sig[:e2 - j] * (1 if L > 0.3 else 0)
        # batterie
        for s in range(16):
            ts = t0 + s * beat / 4
            if L >= 0.5:
                if s in (0, 10) or (s == 7 and b % 2):
                    add(k, ts)
                if s in (4, 12):
                    add(cl, ts)
                add(hh, ts, 0.9 if s % 2 == 0 else 0.5)
                if s == 14 and b % 2:
                    add(oh, ts, 0.6)
            elif L > 0.2:
                if s in (0, 8):
                    add(k, ts, 0.7)
                if s % 4 == 2:
                    add(hh, ts, 0.5)
        # arpège pluck
        if L >= 0.75:
            notes = chord + [chord[0] + 12]
            for s in range(8):
                ts = t0 + s * beat / 2
                m = notes[[0, 2, 1, 3, 2, 1, 3, 2][s]] + 12
                pn = int(0.3 * SR)
                tt = np.arange(pn) / SR
                sig = np.sign(np.sin(2 * np.pi * note_hz(m) * tt)) * np.exp(-tt * 14) * 0.06
                add(_lowpass(sig, 2500), ts)
    pad = _lowpass(pad, 1400)
    mix += pad + _lowpass(bass, 400)
    # sidechain sur le kick
    sc = np.ones(n)
    for b in range(nbars):
        for s in (0, 10):
            j = int((b * bar + s * beat / 4) * SR)
            L = int(0.18 * SR)
            if j < n:
                e = min(n, j + L)
                sc[j:e] = np.minimum(sc[j:e], 0.45 + 0.55 * np.linspace(0, 1, L)[:e - j])
    mix *= sc
    return mix[:int(duration * SR)]


# ---------------------------------------------------------------- bruitages
def sfx(kind, rng=None):
    rng = rng or np.random.default_rng(1)
    if kind == "whoosh":
        n = int(0.55 * SR)
        t = np.arange(n) / SR
        x = rng.normal(0, 1, n)
        cut = 300 + 5000 * np.sin(np.pi * t / t[-1]) ** 2
        y = np.zeros(n)
        st = 0.0
        for i in range(n):
            a = 1 - np.exp(-2 * np.pi * cut[i] / SR)
            st += a * (x[i] - st)
            y[i] = st
        return y * np.sin(np.pi * t / t[-1]) ** 1.5 * 0.55
    if kind == "pop":
        n = int(0.12 * SR)
        t = np.arange(n) / SR
        f = 380 + 900 * np.exp(-t * 40)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 35) * 0.35
    if kind == "boom":
        n = int(2.2 * SR)
        t = np.arange(n) / SR
        f = 32 + 70 * np.exp(-t * 6)
        low = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
        noise = _lowpass(rng.normal(0, 1, n), 900) * np.exp(-t * 4) * 0.6
        return np.tanh(1.5 * (low + noise)) * 0.8
    if kind == "riser":
        n = int(2.0 * SR)
        t = np.arange(n) / SR
        f = 200 * 2 ** (t * 2.2)
        tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.15
        noise = _highpass(rng.normal(0, 1, n), 2000) * 0.25
        return (tone + noise) * (t / t[-1]) ** 2
    if kind == "tick":
        n = int(0.05 * SR)
        t = np.arange(n) / SR
        return np.sin(2 * np.pi * 2200 * t) * np.exp(-t * 120) * 0.25
    if kind == "error":
        n = int(0.35 * SR)
        t = np.arange(n) / SR
        return np.tanh(3 * np.sin(2 * np.pi * 110 * t) * np.sign(np.sin(2 * np.pi * 7 * t))) * \
            np.exp(-t * 6) * 0.25
    raise ValueError(kind)


def mix_all(voice, music, events, duration):
    """voice/music: tableaux mono SR. events: (t, kind, gain)."""
    n = int(duration * SR)
    v = np.zeros(n)
    v[:min(n, len(voice))] = voice[:n]
    m = np.zeros(n)
    m[:min(n, len(music))] = music[:n]
    # ducking
    env = np.convolve(np.abs(v), np.ones(4800) / 4800, "same")
    env = np.convolve(env, np.ones(9600) / 9600, "same")
    duck = 1 - 0.55 * np.clip(env / 0.05, 0, 1)
    m = m / (np.max(np.abs(m)) + 1e-9) * 0.42 * duck
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
        e = min(n, i + len(s))
        fx[i:e] += s[:e - i] * g
    out = v + m + fx * 0.8
    out = np.tanh(out * 1.1) / np.tanh(1.1)
    fade = int(0.8 * SR)
    out[-fade:] *= np.linspace(1, 0, fade)
    return out
