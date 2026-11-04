"""Silences (RMS 20 ms, -38 dB, >0.12 s -> 0.06 s), limiteur -2 dBTP, words.json aligné sur le script."""
import json, re, sys, numpy as np, soundfile as sf
import scipy.signal as ss
t = sys.argv[1]
a, sr = sf.read(f"build/take{t}_raw.wav"); sents = json.load(open(f"build/take{t}_sent.json"))
W = int(0.02 * sr)
n = len(a) // W
rms = np.sqrt(np.mean(a[: n * W].reshape(n, W) ** 2, 1) + 1e-12)
db = 20 * np.log10(rms / 1.0)
quiet = db < -38
# construire le mapping temps source -> temps sortie
keep = np.ones(len(a), bool)
i = 0
runs = []
while i < n:
    if quiet[i]:
        j = i
        while j < n and quiet[j]: j += 1
        runs.append((i, j)); i = j
    else: i += 1
for i, j in runs:
    if (j - i) * 0.02 > 0.12:
        s0 = i * W + int(0.03 * sr); s1 = j * W - int(0.03 * sr)
        keep[s0:s1] = False
cum = np.cumsum(keep)
def tmap(ts): return cum[min(len(cum) - 1, int(ts * sr))] / sr
out = a[keep]
# limiteur de crête simple (-2 dBTP, suréchantillonnage x4)
up = ss.resample_poly(out, 4, 1); peak = np.max(np.abs(up)); lim = 10 ** (-2 / 20)
g = min(1.0, lim / peak) if peak > 0 else 1
out = out * g * 0.98
# normaliser vers ~ -16 LUFS approx (gain réglé au mixage)
sf.write(f"build/voice{t}.wav", out.astype(np.float32), sr)
VOW = re.compile(r"[aeiouyàâéèêëîïôûùœ]+", re.I)
def syl(w): return max(1, len(VOW.findall(w)))
words = []
qs = quiet  # silences internes pour ancrer les virgules
for s in sents:
    st, en = s["start"], s["end"]
    toks = s["text"].replace("’", "'").split()
    toks2 = []
    for tk in toks:
        if re.fullmatch(r"[:;!?]", tk) and toks2: toks2[-1] += tk
        else: toks2.append(tk)
    toks = toks2
    # chunks séparés par , : ;
    chunks, cur = [], []
    for tk in toks:
        cur.append(tk)
        if re.search(r"[,:;]$", tk): chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    i0, i1 = int(st / 0.02), min(n, int(en / 0.02))
    seg = quiet[i0:i1]
    # zone voisée
    v = np.where(~seg)[0]
    vs, ve = (i0 + v[0]) * 0.02, (i0 + v[-1] + 1) * 0.02
    # pauses internes
    pauses = []
    k2 = 0
    while k2 < len(seg):
        if seg[k2]:
            j = k2
            while j < len(seg) and seg[j]: j += 1
            if v[0] < k2 and j <= v[-1]: pauses.append(((i0 + k2) * 0.02, (i0 + j) * 0.02))
            k2 = j
        else: k2 += 1
    need = len(chunks) - 1
    pauses = sorted(sorted(pauses, key=lambda p: p[1] - p[0], reverse=True)[:need])
    bounds = [vs]
    for p in pauses: bounds += [p[0], p[1]]
    bounds.append(ve)
    if True:  # syllabes sur toute la phrase, pause de virgule = 1,5 syllabe
        chunks = [toks]; bounds = [vs, ve]
    for ci, ch in enumerate(chunks):
        cs, ce = bounds[2 * ci], bounds[2 * ci + 1]
        wt = [syl(w) + (1.5 if re.search(r"[,:;]$", w) else 0) for w in ch]
        tot = sum(wt); acc = 0
        for w, k in zip(ch, wt):
            ws = cs + (ce - cs) * acc / tot; we = cs + (ce - cs) * (acc + syl(w)) / tot; acc += k
            words.append({"w": w, "start": round(tmap(ws), 3), "end": round(tmap(we), 3), "sent": s["i"]})
json.dump(words, open(f"build/words{t}.json", "w"), ensure_ascii=False, indent=0)
print(t, "durée", len(out) / sr, "mots", len(words))
