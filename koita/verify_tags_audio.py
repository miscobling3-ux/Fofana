"""Re-mesure : (a) pointe rouge mesurée dans la vidéo rendue vs haut de la tête mesuré indépendamment dans
l'image source (affinage sur pixels sombres, ramené en coordonnées de sortie) ; (b) absence de son de foule
dans les pauses de la voix (voix < -50 dBFS) hors bruitages."""
import json, re, subprocess, sys, cv2, numpy as np, soundfile as sf
sys.path.insert(0, "analysis")
from heads import refine
SRC = "/tmp/claude-0/-home-user-Fofana/daca3ac7-e701-5674-9337-1a49ad094954/scratchpad/src"
plan = json.load(open("build/plan.json")); frames, cams = plan["frames"], plan["cams"]
LAB = [("A", "jovic_A"), ("A", "koita_A"), ("B", "koita_Bh"), ("B", "koita_Bl")]
H = {k: {int(n): v for n, v in json.load(open(f"analysis/head_{k}.json")).items()} for _, k in LAB}
firsts, prev = set(), {}
for k, li, *_ in plan["tags"]:
    if prev.get(li) != k - 1: firsts.update({(li, k + d) for d in range(4)})
    prev[li] = k
want = {}
for k, li, ox, tip, oy in plan["tags"]:
    if 40 < ox < 1040 and (li, k) not in firsts: want.setdefault(k, []).append((li, ox, tip))
cap = cv2.VideoCapture("out/koita_but_fr.mp4"); k = 0; rows = []; bad = []
while True:
    ok, img = cap.read()
    if not ok: break
    for li, ox, tip in want.get(k, []):
        x1, y1 = int(ox - 50), int(tip - 120)
        sub = img[max(0, y1):int(tip + 20), max(0, x1):int(ox + 50)].astype(int)
        m = (sub[..., 2] > 200) & (sub[..., 1] < 90) & (sub[..., 0] < 90)
        ys, xs = np.nonzero(m)
        if len(ys) < 50: bad.append((k, li, "pointe introuvable")); continue
        ty = max(0, y1) + ys.max(); tx = max(0, x1) + xs[ys >= ys.max() - 2].mean()
        _, clip, n, _ = frames[k]; x0, y0, s = cams[k]
        src = cv2.imread(f"{SRC}/{clip}/{n + 1:04d}.jpg")
        gx, gy = H[LAB[li][1]][n]["interp"]
        hx, hy, okr = refine(src, gx, gy, wx=4, up=8, down=10)
        hox, hoy = (hx - x0) * s, (hy - y0) * s
        gap, dx = hoy - ty, hox - tx
        rows.append((k, li, gap, dx))
        if not (0 <= gap <= 16 and abs(dx) <= 6): bad.append((k, li, round(gap, 1), round(dx, 1), "affinage" if okr else "interp"))
    k += 1
g = np.array([r[2] for r in rows]); d = np.array([r[3] for r in rows])
print(f"étiquettes : {len(rows)} images ; écart pointe→haut de tête {g.min():.1f}..{g.max():.1f} px (médiane {np.median(g):.1f}) ; dx {d.min():.1f}..{d.max():.1f} ; hors tolérance {len(bad)}")
for b in bad[:60]: print("  ", b)
json.dump({"rows": rows, "bad": bad}, open("build/verif_tags.json", "w"))
# --- (b) foule
v, sr = sf.read("hf/assets/voice.wav"); v = v if v.ndim == 1 else v.mean(1)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "out/koita_but_fr.mp4", "-ac", "1", "-ar", str(sr), "build/final_audio.wav"])
a, _ = sf.read("build/final_audio.wav")
W = int(0.02 * sr); n = min(len(a), len(v)) // W
vr = 20 * np.log10(np.sqrt((v[:n * W].reshape(n, W) ** 2).mean(1)) + 1e-12)
ar = 20 * np.log10(np.sqrt((a[:n * W].reshape(n, W) ** 2).mean(1)) + 1e-12)
html = open("hf/index.html").read()
busy = np.zeros(n, bool)
for m in re.finditer(r'<audio id="sfx\d+" class="clip" src="[^"]+" data-start="([\d.]+)" data-duration="([\d.]+)"', html):
    t0, du = float(m.group(1)), float(m.group(2)); busy[int((t0 - 0.04) / 0.02):int((t0 + du + 0.04) / 0.02) + 1] = True
q = (vr < -38) & ~busy
q[1:-1] &= q[:-2] & q[2:]
exp = vr + 20 * np.log10(0.76)
print(f"pauses de la voix mesurées : {q.sum() * 0.02:.1f} s ; mix final : médiane {np.median(ar[q]):.1f} dBFS ; voix seule x0,76 : médiane {np.median(exp[q]):.1f} dBFS ; excès médian {np.median(ar[q] - exp[q]):+.1f} dB, max {np.max(ar[q] - exp[q]):+.1f} dB")
# corrélation avec le son d'origine des clips (doit être ~0)
for nm, f in (("A", "7039da82-2856010787559304523.mp4"), ("B", "dc00cf60-5539309054204298804.mov")):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "/root/.claude/uploads/daca3ac7-e701-5674-9337-1a49ad094954/" + f, "-ac", "1", "-ar", "8000", f"build/orig_{nm}.wav"])
    o, _ = sf.read(f"build/orig_{nm}.wav"); fa = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", "build/final_audio.wav", "-ar", "8000", "build/final_8k.wav"])
    x, _ = sf.read("build/final_8k.wav")
    o = (o - o.mean()) / (o.std() + 1e-9); x = (x - x.mean()) / (x.std() + 1e-9)
    L = 1 << int(np.ceil(np.log2(len(o) + len(x))))
    c = np.fft.irfft(np.fft.rfft(x, L) * np.conj(np.fft.rfft(o, L)), L)
    win = 8000 * 2
    best = np.max(np.abs(c)) / np.sqrt(len(o) * len(x)) * np.sqrt(len(x) / len(o)) if len(o) < len(x) else np.max(np.abs(c)) / len(x)
    print(f"corrélation max avec le son d'origine {nm} : {np.max(np.abs(c)) / min(len(o), len(x)):.3f}")
