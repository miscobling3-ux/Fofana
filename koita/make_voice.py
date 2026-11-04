"""Voix off : 2 prises Kokoro (hors-ligne), phrase par phrase -> take{1,2}.wav + sentences.json"""
import json, re, sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
M = "/home/user/Fofana/video/models"
k = Kokoro(f"{M}/kokoro.onnx", f"{M}/voices.bin")
SPOKEN = [("Jović", "Yovitch"), ("Koita", "Koïta"), ("Cucurella", "Coucouréya"), ("l'AEK", "l'A.E.K."), ("L'AEK", "L'A.E.K.")]
text = open("script_fr.txt").read().replace("\n", " ")
sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
def spoken(s):
    for a, b in SPOKEN: s = s.replace(a, b)
    return s
TAKES = {1: (0.45, "am_onyx", 1.12), 2: (0.40, "am_eric", 1.12)}
for t, (w, v2, sp) in TAKES.items():
    style = w * k.get_voice_style("ff_siwis") + (1 - w) * k.get_voice_style(v2)
    out, meta, pos = [], [], 0
    sr = 24000
    for i, s in enumerate(sents):
        a, sr = k.create(spoken(s), voice=style, speed=sp, lang="fr-fr")
        a = a.astype(np.float32)
        out.append(a); meta.append({"i": i, "text": s, "start": pos / sr, "end": (pos + len(a)) / sr})
        pos += len(a)
        gap = np.zeros(int(sr * (0.18 if i == 0 and t == 2 else 0.08)), np.float32)  # prise 2 : pause plus longue après la 1re phrase
        out.append(gap); pos += len(gap)
    sf.write(f"build/take{t}_raw.wav", np.concatenate(out), sr)
    json.dump(meta, open(f"build/take{t}_sent.json", "w"), ensure_ascii=False, indent=1)
    print(t, pos / sr)
