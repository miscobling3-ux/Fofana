"""Construit pep/index.html (HyperFrames) a partir de words.json et de l'EDL."""
import json, re, os, sys, math

S = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(S, "pep")
FPS = 30
words = json.load(open(os.path.join(S, "work", "words.json")))
VOICE_DUR = 90.84
TOTAL = round(VOICE_DUR + 0.25, 2)


def norm(w):
    return re.sub(r"[^\wáéíóúñü¿?-]", "", w.lower()).replace("¿", "").replace("?", "")


def find(phrase, after=0):
    toks = [norm(t) for t in phrase.split()]
    for i in range(after, len(words) - len(toks) + 1):
        if all(norm(words[i + j]["w"]) == toks[j] for j in range(len(toks))):
            return i
    sys.exit("introuvable: " + phrase)


# (debut = phrase de la voix, clip, src_in, src_out)  src_in == src_out -> arret sur image
EDL_SPEC = [
    ("Pero, ¿cómo tuvo", "c1", 0.30, 2.24),
    ("Fíjate en que Palmer", "c1", 2.80, 2.80),          # arret sur image "Fíjate"
    ("recibe este saque", "c1", 2.30, 5.66),
    ("Después, se quedó tocando", "c1", 5.74, 11.30),
    ("Pero nadie imaginaba", "c1", 17.45, 19.40),
    ("Guardiola lo mandaría", "c1", 19.46, 22.14),
    ("Lo más absurdo", "c1", 22.20, 25.06),
    ("A los 45,", "c1", 25.12, 26.78),
    ("Y a los 84", "c1", 26.84, 31.10),
    ("Después de que el Tottenham", "c2", 0.05, 3.30),
    ("pero recibió un rodillazo", "c2", 4.46, 6.40),
    ("Todos los jugadores", "c2", 3.30, 4.40),
    ("y Guardiola enseguida", "c2", 7.60, 8.20),
    ("Pero Ederson le dijo", "c2", 6.46, 7.54),
    ("solo que el tipo", "c2", 8.88, 9.60),
    ("y Guardiola, al ver", "c2", 8.24, 8.80),
    ("Ederson fue sustituido", "c2", 9.62, 10.85),
    ("Y cuando Son", "c2", 16.88, 20.54),
    ("Guardiola se llevó", "c2", 20.60, 21.60),
    ("Pero el portero suplente", "c2", 21.70, 24.80),
    ("y al técnico casi", "c2", 24.88, 26.44),
    ("da un infarto.", "c2", 26.56, 27.10),
    ("Cuando Bernardo Silva", "c3", 0.03, 3.86),
    ("y los jugadores del City y Guardiola", "c3", 3.94, 5.68),
    ("Pero el árbitro dijo", "c3", 5.74, 7.30),
    ("Diez minutos después,", "c3", 7.46, 10.10),
    ("y nuevamente la pelota", "c3", 11.20, 13.24),
    ("Pero fíjate en el juez", "c3", 10.45, 10.45),      # arret sur image "fíjate"
    ("haciendo el mismo gesto", "c3", 10.12, 11.14),
    ("Esto dejó a Guardiola", "c3", 13.30, 17.06),
    ("y después, fue", "c3", 17.14, 19.46),
]

shots, last = [], 0
for phrase, clip, a, b in EDL_SPEC:
    i = find(phrase, last)
    last = i
    shots.append(dict(start=words[i]["s"] if shots else 0.0, clip=clip, a=a, b=b, phrase=phrase))
for k, sh in enumerate(shots):
    sh["end"] = shots[k + 1]["start"] if k + 1 < len(shots) else TOTAL
    d = sh["end"] - sh["start"]
    sh["rate"] = (sh["b"] - sh["a"]) / d
    sh["freeze"] = sh["a"] == sh["b"]

# cadrage par plan : (scale de base, decalage x en %, decalage y en %)
FRAME = {"c1": (1.06, 0, -1.0), "c2": (1.04, 0, 0), "c3": (1.05, 0, -1.0)}
CLIP_FRAMES = {"c1": 990, "c2": 826, "c3": 585}

# ---------------------------------------------------------------- images
imgs = []  # (clip, frame_no, start, dur, shot_idx)
nout = int(round(TOTAL * FPS))
for k, sh in enumerate(shots):
    f0, f1 = int(round(sh["start"] * FPS)), int(round(sh["end"] * FPS))
    cur = None
    for f in range(f0, f1):
        t = (f + 0.5) / FPS - sh["start"]
        src = sh["a"] + t * sh["rate"]
        fr = min(CLIP_FRAMES[sh["clip"]], max(1, int(src * FPS) + 1))
        if cur and cur[1] == fr:
            cur[3] += 1
        else:
            if cur:
                imgs.append(cur)
            cur = [sh["clip"], fr, f, 1, k]
    imgs.append(cur)

used = {(c, fr) for c, fr, *_ in imgs}

img_html = []
for c, fr, f, n, k in imgs:
    st = max(0.0, (f - 0.25) / FPS)
    img_html.append(
        f'<img class="clip src {c}" src="assets/{c}/{fr:04d}.jpg" data-start="{st:.4f}" '
        f'data-duration="{n / FPS:.4f}" data-track-index="1">'
    )

# ---------------------------------------------------------------- sous-titres
sub_html = []
for i, w in enumerate(words):
    txt = re.sub(r"[.,¿?!]", "", w["w"]).lower()
    st = w["s"]
    en = words[i + 1]["s"] if i + 1 < len(words) else VOICE_DUR
    if i + 1 == len(words):
        en = TOTAL
    elif en - st > 0.9:
        en = st + 0.9
    shk = max(j for j, sh in enumerate(shots) if sh["start"] <= st + 1e-6)
    hi = shots[shk]["clip"] == "c3" and shots[shk]["a"] >= 10.0 and shots[shk]["a"] < 17.1
    sub_html.append(
        f'<div class="clip sub{" hi" if hi else ""}" data-start="{st:.3f}" data-duration="{en - st:.3f}" data-track-index="5">{txt}</div>'
    )

# ---------------------------------------------------------------- sons
aud = [f'<audio id="a-voz" class="clip" src="assets/voz.wav" data-start="0" data-duration="{VOICE_DUR}" data-volume="0.93" data-track-index="10"></audio>']
tr = 11
for k, sh in enumerate(shots[1:], 1):
    t = max(0, sh["start"] - 0.12)
    aud.append(f'<audio id="a-w{k}" class="clip" src="assets/sfx/whoosh{k % 4 + 1}.wav" data-start="{t:.3f}" data-duration="0.32" data-volume="0.205" data-track-index="{tr}"></audio>')
    tr += 1
    if sh["freeze"]:
        aud.append(f'<audio id="a-f{k}" class="clip" src="assets/sfx/freeze.wav" data-start="{sh["start"]:.3f}" data-duration="0.45" data-volume="0.325" data-track-index="{tr}"></audio>')
        tr += 1

# ---------------------------------------------------------------- animations camera
js = ['tl.set("#flash",{opacity:0},0);']
c3s = [sh["start"] for sh in shots if sh["clip"] == "c3"]
js.append(f'tl.set("#band",{{opacity:1}},{min(c3s):.3f});')
for k, sh in enumerate(shots):
    sc, dx, dy = FRAME[sh["clip"]]
    d = sh["end"] - sh["start"]
    end_sc = sc * (1.0 if sh["freeze"] else 1.04)
    js.append(f'tl.set("#cam",{{scale:{sc * 1.07:.4f},xPercent:{dx},yPercent:{dy}}},{sh["start"]:.3f});')
    js.append(f'tl.to("#cam",{{scale:{sc:.4f},duration:0.1,ease:"power2.out"}},{sh["start"]:.3f});')
    if d > 0.2:
        js.append(f'tl.to("#cam",{{scale:{end_sc:.4f},duration:{d - 0.1:.3f},ease:"none"}},{sh["start"] + 0.1:.3f});')
    if sh["freeze"]:
        js.append(f'tl.fromTo("#flash",{{opacity:0.55}},{{opacity:0,duration:0.25}},{sh["start"]:.3f});')
        js.append(f'tl.set("#freeze-tag",{{opacity:1}},{sh["start"]:.3f});tl.set("#freeze-tag",{{opacity:0}},{sh["end"]:.3f});')

html = f"""<!doctype html>
<html lang="es" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="gsap.min.js"></script>
<style>
@font-face {{ font-family: Poppins; font-weight: 500; src: url(assets/fonts/Poppins-500.ttf); }}
@font-face {{ font-family: Poppins; font-weight: 800; src: url(assets/fonts/Poppins-800.ttf); }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#000; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:#000; }}
#cam {{ position:absolute; inset:0; transform-origin:50% 45%; }}
#cam img.src {{ position:absolute; inset:0; width:1080px; height:1920px; object-fit:cover; }}
#cam img.src.c1 {{ width:1440px; height:2560px; left:-180px; top:-320px; object-fit:fill; }}
#band {{ position:absolute; left:0; right:0; top:1425px; height:170px; z-index:30; opacity:0;
  backdrop-filter:blur(18px) brightness(.8); -webkit-backdrop-filter:blur(18px) brightness(.8);
  mask-image:linear-gradient(transparent,#000 22%,#000 78%,transparent); -webkit-mask-image:linear-gradient(transparent,#000 22%,#000 78%,transparent); }}
.sub {{ position:absolute; left:0; right:0; top:1600px; text-align:center; z-index:50;
  font-family:Poppins; font-weight:500; font-size:46px; color:#fff;
  text-shadow:0 2px 4px rgba(0,0,0,.85), 0 0 14px rgba(0,0,0,.7), 0 0 4px rgba(0,0,0,.9); }}
.sub.hi {{ top:1290px; }}
#flash {{ position:absolute; inset:0; background:#fff; opacity:0; z-index:40; }}
#freeze-tag {{ position:absolute; top:150px; left:50%; transform:translateX(-50%); z-index:45; opacity:0;
  font-family:Poppins; font-weight:800; font-size:44px; color:#fff; background:#ff1f1f;
  padding:6px 22px; border-radius:10px; letter-spacing:2px; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
<div id="cam">
{chr(10).join(img_html)}
</div>
<div id="band"></div>
<div id="flash"></div>
<div id="freeze-tag">FÍJATE</div>
{chr(10).join(sub_html)}
{chr(10).join(aud)}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js)}
tl.set({{}}, {{}}, {TOTAL});
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = tl;
tl.seek(0);
</script>
</body>
</html>
"""
open(os.path.join(P, "index.html"), "w").write(html)
json.dump(shots, open(os.path.join(S, "work", "edl.json"), "w"), ensure_ascii=False, indent=1)
for k, sh in enumerate(shots):
    print(f'{k:2d} {sh["start"]:6.2f}-{sh["end"]:6.2f} {sh["clip"]} {sh["a"]:5.2f}-{sh["b"]:5.2f} x{sh["rate"]:.2f} {sh["phrase"]}')
print("images:", len(imgs), "frames used:", len(used))
