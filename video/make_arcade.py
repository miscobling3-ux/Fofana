"""Génère une vidéo TikTok « borne d'arcade » (1080x1920, 30 fps).

Usage : python3 make_arcade.py [--script guion_balon_oro_es] [--out ...] [--stills 2,10,30]
"""
import argparse
import importlib
import multiprocessing as mp
import os
import re
import subprocess
import sys

import numpy as np
import skia
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio  # noqa: E402
from arcade import ArcadeRenderer, Events  # noqa: E402
from engine import W, H, FPS  # noqa: E402
from make_video import parse_line, tts_lines  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def build(G, cache_dir, model_dir):
    parsed = [parse_line(txt) for txt in G.LINES]
    clips = tts_lines(G, parsed, cache_dir, model_dir)

    t = 0.9  # laisse le temps à l'écran de s'allumer
    starts = []
    for words, clip in zip(parsed, clips):
        if any(c[0] == "scene" for w in words[:1] for c in w["cmds"]):
            t += 0.25
        if any(c[0] == "winner" for w in words[:1] for c in w["cmds"]):
            t += 0.4  # suspense avant le nom
        starts.append(t)
        times = audio.word_times([w["spoken"] for w in words], clip)
        for w, (a, b) in zip(words, times):
            w["t0"], w["t1"] = t + a, t + b
        t += len(clip) / audio.SR + 0.15
        if any(c[0] == "winner" for w in words for c in w["cmds"]):
            t += 2.0  # laisser respirer l'écran du vainqueur
    duration = t + G.OUTRO_LEN

    voice = np.zeros(int(duration * audio.SR) + audio.SR)
    for s, clip in zip(starts, clips):
        i = int(s * audio.SR)
        voice[i:i + len(clip)] += clip

    events = []
    sfx = []
    for words in parsed:
        line_end = words[-1]["t1"]
        for w in words:
            for cmd, arg in w["cmds"]:
                tt = w["t0"] - 0.05
                if cmd in ("winner", "shake") and any(c[0] == "winner" for c in w["cmds"]):
                    # la fanfare et l'impact arrivent juste après le nom, pour ne pas le couvrir
                    sfx_t = line_end + 0.05
                else:
                    sfx_t = tt
                if cmd == "scene":
                    tt = 0.0 if arg == "boot" else max(0.0, w["t0"] - 0.3)
                    events.append((tt, "scene", arg))
                    events.append((tt, "scene_" + arg, arg))
                    sfx.append((tt, "whoosh", 0.35))
                    if arg == "predict":
                        sfx.append((w["t0"] + 0.3, "roll", 0.8))
                elif cmd == "shake":
                    events.append((tt, "shake", float(arg)))
                    sfx.append((sfx_t, "boom", 0.35 * float(arg)))
                else:
                    arg = arg.replace("_", " ")
                    events.append((tt, cmd, arg))
                    sfx.append((sfx_t, {"coin": "coin", "pick": "blip", "stat": "select", "fav": "select",
                                     "qmark": "blip", "winner": "fanfare"}.get(cmd, "blip"),
                                 1.0 if cmd != "pick" else 0.8))
    ev = Events(events)

    # sous-titres
    all_words = [w for ws in parsed for w in ws]
    chunks, cur = [], []
    for w in all_words:
        cur.append(w)
        if len(cur) >= 3 or re.search(r"[,.:;?!]$", w["text"]) or len(" ".join(x["text"] for x in cur)) > 16:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    captions = []
    for i, ch in enumerate(chunks):
        t0 = ch[0]["t0"] - 0.04
        nxt = chunks[i + 1][0]["t0"] - 0.04 if i + 1 < len(chunks) else duration
        captions.append(dict(t0=t0, t1=min(nxt, ch[-1]["t1"] + 0.6), words=ch))

    # caméra et musique suivent les scènes
    scenes = ev.all("scene")
    cam = [(0.0, 0.92, 1010)] + [(s[0], *G.CAMERA[s[2]]) for s in scenes]
    secs = []
    for i, s in enumerate(scenes):
        t1 = scenes[i + 1][0] if i + 1 < len(scenes) else duration + 5
        secs.append((s[0], t1, G.MUSIC[s[2]]))
    music = audio.make_chiptune(duration, secs)
    mix = audio.mix_chip(voice, music, sfx, duration)
    return ArcadeRenderer(G, ev, captions, cam, duration), mix, duration


_R = None


def _render_range(args):
    i0, i1, path = args
    ff = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
         "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        img = _R.frame(i / FPS)
        ff.stdin.write(img.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).tobytes())
    ff.stdin.close()
    ff.wait()
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", default="guion_balon_oro_es")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "output", "balon_de_oro_2026_es.mp4"))
    ap.add_argument("--models", default=os.environ.get("MODELS_DIR", os.path.join(HERE, "models")))
    ap.add_argument("--build", default=os.path.join(HERE, "build"))
    ap.add_argument("--stills", default="")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()

    G = importlib.import_module(a.script)
    os.makedirs(a.build, exist_ok=True)
    print("1/3 voix + timeline…", flush=True)
    r, mix, duration = build(G, os.path.join(a.build, "tts_cache"), a.models)
    print(f"   durée : {duration:.1f}s", flush=True)
    for e in r.ev.all("scene"):
        print(f"   {e[0]:6.2f}s  {e[2]}")
    if a.stills:
        for ts in a.stills.split(","):
            r.frame(float(ts)).save(os.path.join(a.build, f"arc_{float(ts):05.1f}.png"))
        print("images exportées dans", a.build)
        return

    wav = os.path.join(a.build, "mix_arcade.wav")
    sf.write(wav, np.stack([mix, mix], 1).astype(np.float32), audio.SR)
    print("2/3 rendu des images…", flush=True)
    global _R
    _R = r
    n = int(duration * FPS)
    k = a.workers
    bounds = [round(n * i / k) for i in range(k + 1)]
    jobs = [(bounds[i], bounds[i + 1], os.path.join(a.build, f"apart{i}.mp4")) for i in range(k)]
    with mp.get_context("fork").Pool(k) as pool:
        parts = pool.map(_render_range, jobs)
    lst = os.path.join(a.build, "aparts.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)
    print("3/3 assemblage…", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", a.out], check=True)
    print("OK ->", os.path.abspath(a.out))


if __name__ == "__main__":
    main()
