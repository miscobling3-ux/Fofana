"""Vidéo TikTok « top 10 Balón de Oro » : intro borne d'arcade + segments joueur style éditorial.

Usage : python3 make_top10.py [--script guion_top10_es] [--stills 3,20,40]
Si video/<ELEVEN_VOICE_DIR>/NN.wav existe (une piste par ligne du script), cette voix remplace Kokoro.
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
from editorial import Editorial  # noqa: E402
from engine import W, H, FPS, paint, clamp01, ease  # noqa: E402
from make_video import parse_line, tts_lines  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SPLIT_CMDS = {"dive", "player", "two", "fav", "scene"}


def load_voice(G, parsed, cache_dir, model_dir):
    vdir = os.path.join(HERE, getattr(G, "ELEVEN_VOICE_DIR", "") or "_none_")
    files = [os.path.join(vdir, f"{i:02d}.wav") for i in range(len(parsed))]
    if all(os.path.exists(f) for f in files):
        print("   voix : ElevenLabs (" + vdir + ")")
        import scipy.signal as ss
        out = []
        for f in files:
            a, sr = sf.read(f)
            if a.ndim > 1:
                a = a.mean(1)
            if sr != audio.SR:
                a = ss.resample_poly(a, audio.SR, sr)
            out.append(audio.trim(a))
        return out
    return tts_lines(G, parsed, cache_dir, model_dir)


def build(G, cache_dir, model_dir):
    parsed = [parse_line(txt) for txt in G.LINES]
    clips = load_voice(G, parsed, cache_dir, model_dir)

    t = 0.9
    starts = []
    for words, clip in zip(parsed, clips):
        first = [c[0] for c in words[0]["cmds"]]
        if any(c in SPLIT_CMDS for c in first):
            t += 0.35
        if "winner" in first:
            t += 0.4
        starts.append(t)
        times = audio.word_times([w["spoken"] for w in words], clip)
        for w, (a, b) in zip(words, times):
            w["t0"], w["t1"] = t + a, t + b
        t += len(clip) / audio.SR + 0.15
        if "winner" in first:
            t += 2.2
    duration = t + G.OUTRO_LEN

    voice = np.zeros(int(duration * audio.SR) + audio.SR)
    for s, clip in zip(starts, clips):
        i = int(s * audio.SR)
        voice[i:i + len(clip)] += clip

    events, sfx, stats, segs = [], [], [], []
    for words in parsed:
        line_end = words[-1]["t1"]
        for w in words:
            for cmd, arg in w["cmds"]:
                tt = w["t0"] - 0.05
                if cmd == "scene":
                    ts = 0.0 if arg == "boot" else max(0.0, w["t0"] - 0.3)
                    events.append((ts, "scene", arg))
                    events.append((ts, "scene_" + arg, arg))
                    sfx.append((ts, "whoosh", 0.35))
                    if arg == "cta":
                        segs.append(dict(kind="arcade", t0=ts))
                elif cmd == "dive":
                    ts = w["t0"] - 0.3
                    events.append((ts, "dive", ""))
                    sfx.append((ts - 0.5, "riser", 0.5))
                    sfx.append((ts, "boom", 0.45))
                elif cmd == "player":
                    pid, rank = arg.split(":")
                    ts = w["t0"] - 0.3
                    segs.append(dict(kind="player", pid=pid, rank=int(rank), t0=ts))
                    events.append((ts, "player", pid))
                    sfx.append((ts, "whoosh", 0.5))
                elif cmd == "stat":
                    value, label = arg.split("|")
                    stats.append(dict(t=tt, value=value.replace("_", " "), label=label.replace("_", " ")))
                    sfx.append((tt, "pop", 0.7))
                elif cmd == "two":
                    ts = w["t0"] - 0.3
                    segs.append(dict(kind="two", t0=ts))
                    sfx.append((ts, "boom", 0.6))
                elif cmd == "fav":
                    ts = w["t0"] - 0.3
                    segs.append(dict(kind="finale", t0=ts))
                    events.append((ts, "fav", ""))
                    sfx.append((ts, "whoosh", 0.5))
                    sfx.append((ts + 0.9, "select", 0.9))
                elif cmd == "predict":
                    events.append((tt, "predict", ""))
                    sfx.append((tt + 0.2, "roll", 0.8))
                elif cmd == "winner":
                    events.append((tt, "winner", ""))
                    sfx.append((line_end + 0.05, "boom", 0.6))
                    sfx.append((line_end + 0.1, "fanfare", 1.0))
                else:
                    events.append((tt, cmd, arg))
                    sfx.append((tt, {"coin": "coin", "qmark": "blip"}.get(cmd, "blip"), 0.9))
    ev = Events(events)
    segs.sort(key=lambda s: s["t0"])
    for i, s in enumerate(segs):
        s["t1"] = segs[i + 1]["t0"] if i + 1 < len(segs) else duration
    dive = ev.last("dive", 1e9)[0]

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

    # caméra de la borne : scènes, plongée dans l'écran, puis retour pour la fin
    scenes = ev.all("scene")
    cam = [(0.0, 0.92, 1010)]
    for s in scenes:
        if s[2] == "cta":
            cam.append((s[0] - 0.01, 3.2, 814))
        cam.append((s[0], *G.CAMERA[s[2]]))
        if s[2] == "grid":
            cam.append((dive - 0.75, 3.2, 814))
    cam.sort(key=lambda k: k[0])

    # musique : chiptune sur la borne, beat tendu pendant le top 10
    cta_t = ev.last("scene", 1e9)[0]
    chip = audio.make_chiptune(duration, [(s[0], 1e9, G.MUSIC[s[2]]) for s in scenes])
    beat = audio.make_music(duration, sections=[(dive, cta_t, 1.0)])
    chip /= np.max(np.abs(chip)) + 1e-9
    beat /= np.max(np.abs(beat)) + 1e-9
    tt = np.arange(len(chip)) / audio.SR
    w_beat = np.clip((tt - dive + 0.3) / 0.6, 0, 1) * np.clip((cta_t + 0.3 - tt) / 0.6, 0, 1)
    music = chip * (1 - w_beat) + beat * w_beat
    mix = audio.mix_chip(voice, music, sfx, duration)

    arcade = ArcadeRenderer(G, ev, captions, cam, duration)
    return Top10Renderer(G, ev, segs, stats, arcade, dive), mix, duration


class Top10Renderer:
    def __init__(self, G, ev, segs, stats, arcade, dive):
        self.G, self.ev, self.segs, self.stats, self.arcade, self.dive = G, ev, segs, stats, arcade, dive
        self.ed = Editorial(G, arcade.P, G.BRAND)
        self.surf = skia.Surface(W, H)
        self.duration = arcade.duration

    def frame(self, t):
        seg = None
        for s in self.segs:
            if s["t0"] <= t < s["t1"]:
                seg = s
        if t < self.dive or (seg and seg["kind"] == "arcade") or seg is None:
            img = self.arcade.frame(t)
            if t < self.dive and t > self.dive - 0.2:  # éclair blanc à l'entrée dans l'écran
                c = skia.Surface(W, H)
                cc = c.getCanvas()
                cc.drawImage(img, 0, 0)
                cc.drawPaint(paint("#f2f0ea", clamp01((t - (self.dive - 0.2)) / 0.2)))
                return c.makeImageSnapshot()
            if seg and seg["kind"] == "arcade" and t < seg["t0"] + 0.25:
                c = skia.Surface(W, H)
                cc = c.getCanvas()
                cc.drawImage(img, 0, 0)
                cc.drawPaint(paint("#000000", 1 - clamp01((t - seg["t0"]) / 0.25)))
                return c.makeImageSnapshot()
            return img
        c = self.surf.getCanvas()
        if seg["kind"] == "player":
            self.ed.player(c, t, seg, self.stats, dark=seg["rank"] <= 2)
        elif seg["kind"] == "two":
            self.ed.two(c, t, seg["t0"], seg["t1"])
        elif seg["kind"] == "finale":
            self.ed.finale(c, t, self.ev)
        if t < self.dive + 0.25:
            c.drawPaint(paint("#f2f0ea", 1 - clamp01((t - self.dive) / 0.25)))
        self.arcade.draw_captions(c, t)
        return self.surf.makeImageSnapshot()


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
    ap.add_argument("--script", default="guion_top10_es")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "output", "balon_de_oro_2026_top10_es.mp4"))
    ap.add_argument("--models", default=os.environ.get("MODELS_DIR", os.path.join(HERE, "models")))
    ap.add_argument("--build", default=os.path.join(HERE, "build"))
    ap.add_argument("--stills", default="")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()

    G = importlib.import_module(a.script)
    os.makedirs(a.build, exist_ok=True)
    print("1/3 voix + timeline…", flush=True)
    r, mix, duration = build(G, os.path.join(a.build, "tts_cache"), a.models)
    print(f"   durée : {duration:.1f}s   plongée : {r.dive:.1f}s", flush=True)
    for s in r.segs:
        print(f"   {s['t0']:6.2f}–{s['t1']:6.2f}  {s['kind']} {s.get('pid', '')}")
    if a.stills:
        for ts in a.stills.split(","):
            r.frame(float(ts)).save(os.path.join(a.build, f"top_{float(ts):05.1f}.png"))
        print("images exportées dans", a.build)
        return
    wav = os.path.join(a.build, "mix_top10.wav")
    sf.write(wav, np.stack([mix, mix], 1).astype(np.float32), audio.SR)
    print("2/3 rendu des images…", flush=True)
    global _R
    _R = r
    n = int(duration * FPS)
    k = a.workers
    bounds = [round(n * i / k) for i in range(k + 1)]
    jobs = [(bounds[i], bounds[i + 1], os.path.join(a.build, f"tpart{i}.mp4")) for i in range(k)]
    with mp.get_context("fork").Pool(k) as pool:
        parts = pool.map(_render_range, jobs)
    lst = os.path.join(a.build, "tparts.txt")
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
