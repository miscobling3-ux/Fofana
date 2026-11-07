#!/usr/bin/env python3
"""Writes the HyperFrames composition (index.html) from plan.json."""
import json, math
S = "/tmp/claude-0/-home-user-Fofana/0dc10ad3-8ae5-5d3f-b08b-3b4d72bae3e6/scratchpad"
P = S + "/proj"
plan = json.load(open(S + "/plan.json"))
FPS, DUR = plan["fps"], plan["dur"]
fr = plan["frames"]
EDL = plan["edl"]
words = plan["words"]
VOICE_VOL = float(open(S + "/voice_vol.txt").read()) if __import__("os").path.exists(S + "/voice_vol.txt") else 1.0

import wave
VDUR = round(wave.open(P + "/assets/voice.wav").getnframes() / 48000, 3)
def wlen(n):
    w = wave.open(f"{P}/assets/sfx/{n}.wav"); return round(w.getnframes() / w.getframerate(), 3)
def sec(i): return i / FPS
imgs = []
for name, a, b in plan["runs"]:
    st = max(0.0, sec(a) - 1 / (4 * FPS))
    du = sec(b) - st
    imgs.append(f'<img class="clip src" src="assets/frames/{name}" data-start="{st:.5f}" data-duration="{du:.5f}" data-track-index="1" alt="">')

# captions: one word at a time, script text, lowercase
caps = []
ds = []
for w in words:
    ds.append(max(w["start"], ds[-1] + 0.12) if ds else w["start"])
for j, w in enumerate(words):
    txt = w["text"].lower().strip(",.")
    st = ds[j]
    nxt = ds[j + 1] if j + 1 < len(words) else VDUR
    en = min(nxt, max(w["end"], st + 0.12) + 0.35) if j + 1 < len(words) else VDUR
    caps.append(f'<div class="clip cap" data-start="{st:.3f}" data-duration="{en - st:.3f}" data-track-index="9">{txt}</div>')

# ---------------------------------------------------------------- sound effects
sfx = []
def add(name, t, dur, vol):
    sfx.append((name, max(0.0, t), wlen(name), vol))
cuts = [e[0] for e in EDL[1:]]
freezes = [e[0] for e in EDL if e[3] == e[4]]
for j, c in enumerate(cuts):
    add(f"whoosh{j % 4}", c - 0.12, 0.42, 0.30)
for c in freezes:
    add("freeze", c, 0.45, 0.45)
# label pops
prev = None
for r in fr:
    cur = r.get("lab", [None])[0]
    if cur and cur != prev: add("pop", r["t"], 0.14, 0.45)
    prev = cur
add("pop", 4.96, 0.14, 0.45)
# ball contact: first output frame showing the contact source frame
contacts = [("A", 334, (0, 16)), ("B", 592, (8,)), ]
kick_i = 0
for clip, cf, ks in contacts:
    for k in ks:
        for r in fr:
            if r["k"] == k and r["c"] == clip and r["n"] >= cf:
                add(f"kick{kick_i % 3}", r["t"], 0.40, 0.55); kick_i += 1; break
add("flip", 73.12, 0.2, 0.4)
aud = [f'<audio id="voice" class="clip" src="assets/voice.wav" data-start="0" data-duration="{VDUR:.3f}" data-volume="{VOICE_VOL:.3f}" data-track-index="20"></audio>']
for j, (n, t, d, v) in enumerate(sfx):
    aud.append(f'<audio id="sfx{j}" class="clip" src="assets/sfx/{n}.wav" data-start="{t:.3f}" data-duration="{d:.3f}" data-volume="{v}" data-track-index="{21 + j}"></audio>')
json.dump(sfx, open(S + "/sfx.json", "w"))

# compact per-frame data for the timeline
data = []
for r in fr:
    lab = r.get("lab"); sp = r.get("spot")
    data.append([r["s"], r["x"], r["y"],
                 (lab[0][0], lab[1], lab[2]) if lab else 0,
                 (sp[1], sp[2], sp[3], sp[4]) if sp else 0])

html = f"""<!doctype html>
<html lang="es" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="assets/gsap.min.js"></script>
<style>
@font-face {{ font-family: "Poppins"; font-weight: 500; src: url("assets/fonts/poppins-latin-500-normal.woff2") format("woff2"); }}
@font-face {{ font-family: "Poppins"; font-weight: 800; src: url("assets/fonts/poppins-latin-800-normal.woff2") format("woff2"); }}
@font-face {{ font-family: "Montserrat"; font-weight: 800; src: url("assets/fonts/montserrat-latin-800-normal.woff2") format("woff2"); }}
:root {{ --ground: #000; --ink: #fff; --red: #ff1f1f; }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: var(--ground); }}
#root {{ position: relative; width: 1080px; height: 1920px; overflow: hidden; background: #000; font-family: "Poppins", sans-serif; }}
#world {{ position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; transform-origin: 0 0; }}
#world img.src {{ position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; }}
#spot {{ position: absolute; inset: 0; opacity: 0; z-index: 5; --sx: 540px; --sy: 960px; --sr: 300px; pointer-events: none; }}
#spot .dim {{ position: absolute; inset: 0;
  background: radial-gradient(circle var(--sr) at var(--sx) var(--sy), rgba(0,0,0,0) 0, rgba(0,0,0,0) calc(var(--sr) - 1px), rgba(0,0,0,.58) var(--sr));
  backdrop-filter: blur(5px); -webkit-backdrop-filter: blur(5px);
  -webkit-mask-image: radial-gradient(circle var(--sr) at var(--sx) var(--sy), transparent 0, transparent calc(var(--sr) - 1px), #000 calc(var(--sr) + 1px));
          mask-image: radial-gradient(circle var(--sr) at var(--sx) var(--sy), transparent 0, transparent calc(var(--sr) - 1px), #000 calc(var(--sr) + 1px)); }}
#spot .ring {{ position: absolute; left: 0; top: 0; border: 5px solid #fff; border-radius: 50%;
  box-shadow: 0 0 14px rgba(255,255,255,.65), inset 0 0 10px rgba(255,255,255,.35); }}
.lab {{ position: absolute; left: 0; top: 0; z-index: 8; visibility: hidden; }}
.lab .pop {{ position: absolute; left: 0; bottom: 0; transform-origin: 0 100%; }}
.lab .stack {{ position: absolute; left: 0; bottom: 0; transform: translateX(-50%); display: flex; flex-direction: column; align-items: center; gap: 8px; }}
.lab .logo {{ width: 84px; height: 84px; border-radius: 50%; background: #fff; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 3px 8px rgba(0,0,0,.45); overflow: hidden; }}
.lab .logo img {{ width: 72px; height: 72px; border-radius: 50%; object-fit: cover; }}
.lab .name {{ font-family: "Montserrat", sans-serif; font-weight: 800; font-size: 38px; color: #fff; white-space: nowrap;
  background: rgba(12,12,16,.86); padding: 4px 18px 6px; border-radius: 14px; box-shadow: 0 3px 8px rgba(0,0,0,.4); }}
.lab svg {{ display: block; filter: drop-shadow(0 3px 3px rgba(0,0,0,.45)); }}
.cap {{ position: absolute; left: 0; width: 1080px; top: 1600px; text-align: center; z-index: 12;
  font-family: "Poppins", sans-serif; font-weight: 500; font-size: 46px; line-height: 1.15; color: #fff;
  text-shadow: 0 2px 4px rgba(0,0,0,.85); }}
#score {{ position: absolute; top: 170px; left: 50%; transform: translateX(-50%); z-index: 11; display: flex; align-items: stretch;
  font-family: "Poppins", sans-serif; font-weight: 800; color: #fff; font-size: 40px; visibility: hidden;
  filter: drop-shadow(0 4px 10px rgba(0,0,0,.55)); }}
#score .team {{ background: rgba(10,10,14,.9); padding: 6px 20px; display: flex; align-items: center; }}
#score .team.l {{ border-radius: 14px 0 0 14px; }} #score .team.r {{ border-radius: 0 14px 14px 0; }}
#score .box {{ background: var(--red); padding: 6px 18px; display: flex; align-items: center; gap: 12px; perspective: 300px; }}
#score .dig {{ position: relative; width: 28px; height: 52px; }}
#score .dig span {{ position: absolute; left: 0; top: 0; width: 28px; text-align: center; line-height: 52px; backface-visibility: hidden; }}
#score .min {{ background: #fff; color: #111; padding: 6px 14px; margin-left: 10px; border-radius: 12px; font-size: 34px; display: flex; align-items: center; }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{DUR:.2f}" data-width="1080" data-height="1920">
  <div id="world">
    {chr(10).join(imgs)}
  </div>
  <div id="spot"><div class="dim"></div><div class="ring"></div></div>
  {''.join(f'''<div class="lab" id="lab_{p}"><div class="pop"><div class="stack">
    <div class="logo"><img src="assets/rm_crest.png" alt=""></div>
    <div class="name">{nm}</div>
    <svg width="64" height="86" viewBox="0 0 64 86"><path d="M20 2 H44 V46 H62 L32 84 L2 46 H20 Z" fill="#ff1f1f" stroke="#3a0000" stroke-width="3" stroke-linejoin="round"/></svg>
  </div></div></div>''' for p, nm in (("valverde", "Federico Valverde"), ("mbappe", "Kylian Mbappé")))}
  <div id="score"><div class="team l">VAL</div><div class="box"><div class="dig"><span>0</span></div><span>–</span>
    <div class="dig" id="rm"><span id="rm0">0</span><span id="rm1">1</span></div></div><div class="team r">RMA</div><div class="min">27'</div></div>
  {chr(10).join(caps)}
  {chr(10).join(aud)}
</div>
<script>
const FPS = {FPS};
const D = {json.dumps(data, separators=(',', ':'))};
const tl = gsap.timeline({{ paused: true }});
const world = document.getElementById("world");
const spot = document.getElementById("spot");
const ring = spot.querySelector(".ring");
const labs = {{ v: document.getElementById("lab_valverde"), m: document.getElementById("lab_mbappe") }};
let prevLab = null, prevSpot = false;
for (let i = 0; i < D.length; i++) {{
  const t = i / FPS, d = D[i];
  tl.set(world, {{ x: d[1], y: d[2], scale: d[0] }}, t);
  const L = d[3];
  const cur = L ? L[0] : null;
  if (cur !== prevLab) {{
    if (prevLab) tl.set(labs[prevLab], {{ visibility: "hidden" }}, t);
    if (cur) {{
      tl.set(labs[cur], {{ visibility: "visible" }}, t);
      tl.fromTo(labs[cur].querySelector(".pop"), {{ scale: 0 }}, {{ scale: 1, duration: 0.12, ease: "back.out(2)" }}, t);
    }}
    prevLab = cur;
  }}
  if (L) {{
    const bounce = 5 * Math.abs(Math.sin(2 * Math.PI * 1.4 * t));
    tl.set(labs[cur], {{ x: L[1], y: L[2] - 6 - bounce }}, t);
  }}
  const P = d[4];
  if (P) {{
    tl.set(spot, {{ opacity: P[3], "--sx": P[0] + "px", "--sy": P[1] + "px", "--sr": P[2] + "px" }}, t);
    tl.set(ring, {{ x: P[0] - P[2], y: P[1] - P[2], width: 2 * P[2], height: 2 * P[2] }}, t);
    prevSpot = true;
  }} else if (prevSpot) {{ tl.set(spot, {{ opacity: 0 }}, t); prevSpot = false; }}
}}
// score banner
const score = document.getElementById("score");
tl.set(score, {{ visibility: "visible" }}, 4.96);
tl.fromTo(score, {{ scale: 0 }}, {{ scale: 1, duration: 0.12, ease: "back.out(2)" }}, 4.96);
tl.set("#rm1", {{ rotationX: -90 }}, 0);
tl.to("#rm0", {{ rotationX: 90, duration: 0.14, ease: "power2.in" }}, 73.12);
tl.to("#rm1", {{ rotationX: 0, duration: 0.16, ease: "power2.out" }}, 73.26);
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = tl;
tl.seek(0);
</script>
</body>
</html>
"""
open(P + "/index.html", "w").write(html)
print("ok", len(imgs), "imgs", len(caps), "caps", len(sfx), "sfx")
