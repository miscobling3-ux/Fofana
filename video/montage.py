"""Montage TikTok 1080x1920 à partir de PLUSIEURS vidéos sources : chaque phrase de la voix off reçoit ses propres
plans (vidéo, début, fin). Même habillage que remix.py : sous-titres mot par mot, zooms, « punch » sur les mots-clés,
flash + whoosh aux coupes, étiquettes, musique, et écran final. Les sources qui ne sont pas en 9:16 sont posées sur
un fond flouté de la même image.

Usage :
  python3 montage.py --script guion_ronaldo_es                      # -> output/ronaldo_es.mp4
  python3 montage.py --script guion_ronaldo_es --stills 2,20,60      # aperçu : quelques PNG dans video/build/
  python3 montage.py --script guion_ronaldo_es --voice-dir voz_eleven  # voix externe : un fichier par phrase
                                                                      #   (01.mp3, 02.mp3… dans l'ordre de LINES)
"""
import argparse
import glob
import importlib
import math
import multiprocessing as mp
import os
import re
import subprocess

import cv2
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw

import audio
from remix import (BLACK, FPS, GREEN, H, PINK, RED, SUB_Y, TITLE_Y, BADGE_Y, W, WHITE, YELLOW, back_out,  # noqa: F401
                   cached_pill, caption_img, ease, outlined, parse, paste, pulse, synth, vignette)

HERE = os.path.dirname(os.path.abspath(__file__))
FG_CY = 900  # centre vertical de la vidéo quand elle n'est pas en 9:16


# ---------------------------------------------------------------- voix + timeline
def load_external(path):
    """Fichier audio externe (ex. ElevenLabs) -> mono SR, silences coupés."""
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(audio.SR), "-"],
                         capture_output=True, check=True).stdout
    return audio.trim(np.frombuffer(out, np.float32).astype(np.float64))


def build(G, voice, build_dir, models, voice_dir=None):
    cache = os.path.join(build_dir, "tts_cache")
    os.makedirs(cache, exist_ok=True)
    ext = sorted(glob.glob(os.path.join(voice_dir, "*"))) if voice_dir else []
    if ext and len(ext) != len(G.LINES):
        raise SystemExit(f"{voice_dir} : {len(ext)} fichiers pour {len(G.LINES)} phrases")
    segs, words_all, clips = [], [], []
    t = 0.2
    for i, ln in enumerate(G.LINES):
        words = parse(ln["text"])
        spoken = " ".join(w["text"] for w in words)
        clip = load_external(ext[i]) if ext else synth(G, voice, spoken, cache, models)
        if ln["chapter"] and i > 0:
            t += 0.3
        start = t
        for w, (a, b) in zip(words, audio.word_times([w["text"] for w in words], clip)):
            w["t0"], w["t1"] = start + a, start + b
        clips.append((start, clip))
        segs.append(dict(ln, t0=0.0 if i == 0 else start - 0.08, words=words))
        words_all += words
        t = start + len(clip) / audio.SR + (0.18 if re.search(r"[.?!»”]$", ln["text"]) else 0.06)
    duration = t + 1.6
    for i, s in enumerate(segs):
        s["t1"] = segs[i + 1]["t0"] if i + 1 < len(segs) else duration
        # répartition des plans de la phrase au prorata de leur longueur
        tot = sum(b - a for _, a, b in s["shots"])
        acc = s["t0"]
        s["cuts"] = []
        for src, a, b in s["shots"]:
            d = (s["t1"] - s["t0"]) * (b - a) / tot
            s["cuts"].append(dict(src=src, a=a, b=b, t0=acc, t1=acc + d))
            acc += d
    cta_t = segs[-1]["t0"]

    voice_track = np.zeros(int(duration * audio.SR) + audio.SR)
    for s, clip in clips:
        j = int(s * audio.SR)
        voice_track[j:j + len(clip)] += clip

    chunks, cur = [], []
    for w in words_all:
        cur.append(w)
        if len(cur) >= 3 or re.search(r"[,.:;?!]$", w["text"]) or len(" ".join(x["text"] for x in cur)) > 15:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    caps = []
    for i, ch in enumerate(chunks):
        t0 = ch[0]["t0"] - 0.04
        nxt = chunks[i + 1][0]["t0"] - 0.04 if i + 1 < len(chunks) else duration
        caps.append(dict(t0=t0, t1=min(nxt, ch[-1]["t1"] + 0.5), words=ch))

    keys = [w["t0"] for w in words_all if w["key"]]
    cuts = [c["t0"] for s in segs for c in s["cuts"]][1:]
    sfx = [(0.05, "boom", 0.45)]
    sfx += [(c - 0.12, "whoosh", 0.3) for c in cuts]
    for s in segs[1:]:
        if s["chapter"]:
            sfx.append((s["t0"] - 1.9, "riser", 0.4))
            sfx.append((s["t0"], "boom", 0.4))
    prev = None
    for s in segs:
        if s["tag"] and s["tag"] != prev:
            sfx.append((s["t0"] + 0.05, "tick", 0.4))
        prev = s["tag"]
    sfx += [(k, "pop", 0.3) for k in keys]
    sfx.append((cta_t + 0.05, "pop", 0.8))

    music = audio.make_music(duration, bpm=G.BPM, seed=G.SEED,
                             sections=[(0, segs[1]["t0"], 0.8), (segs[1]["t0"], cta_t, 0.55), (cta_t, duration + 5, 0.8)])
    mix = audio.mix_all(voice_track, music, sfx, duration)
    tl = dict(segs=segs, caps=caps, keys=keys, cuts=cuts, duration=duration, cta_t=cta_t)
    return tl, mix, duration


# ---------------------------------------------------------------- sources
class Sources:
    """Lecture image par image, à la demande, de plusieurs vidéos (une capture par source et par processus)."""

    def __init__(self, paths):
        self.paths = paths
        self.caps, self.last = {}, {}

    def info(self, key):
        cap = self._cap(key)
        return cap.get(cv2.CAP_PROP_FPS), int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def _cap(self, key):
        if key not in self.caps:
            self.caps[key] = cv2.VideoCapture(self.paths[key])
            self.last[key] = (-10, None)
        return self.caps[key]

    def frame(self, key, ts):
        cap = self._cap(key)
        fps, n = self.info(key)
        idx = int(min(max(ts * fps, 0), n - 1))
        li, img = self.last[key]
        if idx == li:
            return img
        if not (li < idx <= li + 4):
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            li = idx - 1
        while li < idx:
            ok, bgr = cap.read()
            if not ok:
                break
            img = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
            li += 1
        self.last[key] = (idx, img)
        return img


# ---------------------------------------------------------------- rendu
class Renderer:
    def __init__(self, G, tl, sources):
        self.G, self.tl, self.src = G, tl, sources

    def seg_at(self, t):
        for i, s in enumerate(self.tl["segs"]):
            if s["t0"] <= t < s["t1"]:
                return i, s
        return len(self.tl["segs"]) - 1, self.tl["segs"][-1]

    def frame(self, t):
        tl = self.tl
        i, s = self.seg_at(t)
        c = next((c for c in s["cuts"] if c["t0"] <= t < c["t1"]), s["cuts"][-1])
        u = (t - c["t0"]) / max(1e-3, c["t1"] - c["t0"])
        img = self.src.frame(c["src"], c["a"] + u * (c["b"] - c["a"]))
        sh, sw = img.shape[:2]

        # caméra : zoom lent + « punch » sur les mots-clés et à chaque coupe
        us = (t - s["t0"]) / max(1e-3, s["t1"] - s["t0"])
        z0, z1, cx, cy = s["zoom"]
        z = z0 + (z1 - z0) * ease(us)
        p = sum(0.05 * pulse(t - k) for k in tl["keys"] if -0.1 < t - k < 1.5)
        p += 0.08 * pulse(t - c["t0"], 6) if c["t0"] > 0 else 0
        z *= 1 + p
        cx += 0.005 * math.sin(t * 0.9)
        cy += 0.004 * math.cos(t * 0.7)
        cx = min(max(cx, 0.5 / z), 1 - 0.5 / z)
        k = W * z / sw
        fh = sh * k
        if fh >= H:  # la vidéo couvre tout l'écran
            cy = min(max(cy, H / 2 / fh), 1 - H / 2 / fh)
            oy = H / 2 - cy * fh
        else:        # moins haute que l'écran : on garde le point visé vers FG_CY, fond flouté derrière
            oy = min(max(FG_CY - cy * fh, 0), H - fh)
        M = np.float32([[k, 0, W / 2 - cx * sw * k], [0, k, oy]])
        fg = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
        fg = cv2.addWeighted(fg, 1.4, cv2.GaussianBlur(fg, (0, 0), 2.0), -0.4, 0)
        if fh < H:
            kb = max(W / sw, H / sh) * 1.1
            small = cv2.resize(img, (sw // 4, sh // 4))
            Mb = np.float32([[kb * 4, 0, W / 2 - sw * kb / 2], [0, kb * 4, H / 2 - sh * kb / 2]])
            bg = cv2.warpAffine(small, Mb, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            bg = cv2.GaussianBlur(bg, (0, 0), 30).astype(np.float32) * 0.45
            mask = cv2.warpAffine(np.ones((sh, sw), np.float32), M, (W, H), flags=cv2.INTER_LINEAR)[..., None]
            f = fg.astype(np.float32) * mask + bg * (1 - mask)
        else:
            f = fg.astype(np.float32)

        # étalonnage : contraste, vignette, flash blanc aux coupes
        f = (f - 128) * 1.07 + 130
        f *= 1 - 0.38 * vignette()
        if c["t0"] > 0:
            fl = 0.42 * max(0.0, 1 - (t - c["t0"]) / 0.12)
            f = f * (1 - fl) + 255 * fl
        canvas = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).convert("RGBA")
        self.overlays(canvas, t, i, s)
        return np.asarray(canvas.convert("RGB"))

    def overlays(self, canvas, t, i, s):
        tl, G = self.tl, self.G
        d = ImageDraw.Draw(canvas)
        d.rounded_rectangle((40, 40, W - 40, 52), 6, fill=(255, 255, 255, 90))
        d.rounded_rectangle((40, 40, 40 + (W - 80) * min(1, t / tl["duration"]), 52), 6, fill=YELLOW + (255,))
        cta = t >= tl["cta_t"]
        # accroche
        hook_end = tl["segs"][1]["t0"]
        if t < hook_end + 0.2:
            out = 1 - ease((t - hook_end) / 0.2)
            paste(canvas, cached_pill(G.HOOK[0], 104, RED, WHITE, None), W / 2, TITLE_Y - 120,
                  back_out(t / 0.35) * out, out, rot=-3)
            paste(canvas, outlined(G.HOOK[1], 62, YELLOW), W / 2, TITLE_Y + 20, back_out((t - 0.25) / 0.35) * out, out)
        # titre de chapitre
        if s["chapter"] and i > 0 and t - s["t0"] < 2.2:
            dt = t - s["t0"]
            out = 1 - ease((dt - 1.9) / 0.3)
            paste(canvas, cached_pill(s["chapter"], 92, PINK, WHITE, None), W / 2, TITLE_Y - 120,
                  back_out(dt / 0.35) * out, out, rot=2)
        # étiquette du moment (nom du joueur, lieu…)
        if s["tag"] and not cta:
            prev = tl["segs"][i - 1]["tag"] if i > 0 else None
            nxt = tl["segs"][i + 1]["tag"] if i + 1 < len(tl["segs"]) else None
            dt = t - s["t0"] if prev != s["tag"] else 9
            out = 1 - ease((t - (s["t1"] - 0.2)) / 0.2) if nxt != s["tag"] else 1
            paste(canvas, cached_pill(s["tag"], 58, YELLOW, BLACK, None), W / 2, BADGE_Y - 120,
                  back_out(dt / 0.3) * out, out)
        # sous-titres
        for ci, c in enumerate(tl["caps"]):
            if c["t0"] <= t < c["t1"]:
                active = max([j for j, w in enumerate(c["words"]) if w["t0"] - 0.04 <= t] or [0])
                img = caption_img(ci, active, tuple(w["text"] for w in c["words"]),
                                  tuple(w["key"] for w in c["words"]))
                paste(canvas, img, W / 2, SUB_Y + 60 if not cta else SUB_Y + 140,
                      0.8 + 0.2 * back_out((t - c["t0"]) / 0.14))
                break
        # appel à l'action
        if cta:
            dt = t - tl["cta_t"]
            ov = Image.new("RGBA", canvas.size, (0, 0, 0, int(110 * ease(dt / 0.3))))
            canvas.alpha_composite(ov)
            beat = 1 + 0.04 * math.sin(dt * 9) * ease((dt - 0.4) / 0.3)
            paste(canvas, cached_pill(G.CTA[0], 110, PINK, WHITE, None), W / 2, 760, back_out(dt / 0.4) * beat)
            paste(canvas, outlined(G.CTA[1], 60, WHITE), W / 2, 920, back_out((dt - 0.2) / 0.4))
            if G.BRAND:
                paste(canvas, outlined("@" + G.BRAND.lower().replace(" ", ""), 56, YELLOW), W / 2, 1020,
                      back_out((dt - 0.35) / 0.4))


_R = None


def _render_range(args):
    i0, i1, path = args
    ff = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", path],
        stdin=subprocess.PIPE)
    for i in range(i0, i1):
        ff.stdin.write(_R.frame(i / FPS).tobytes())
    ff.stdin.close()
    ff.wait()
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", default="guion_ronaldo_es")
    ap.add_argument("--out", default=None)
    ap.add_argument("--voice", default=None, help="remplace VOICE du script (ex. em_santa)")
    ap.add_argument("--voice-dir", default=None, help="dossier avec un fichier audio par phrase (ex. ElevenLabs)")
    ap.add_argument("--models", default=os.environ.get("MODELS_DIR", os.path.join(HERE, "models")))
    ap.add_argument("--build", default=os.path.join(HERE, "build"))
    ap.add_argument("--stills", default="", help="temps (s) séparés par des virgules : n'exporte que ces images")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()

    G = importlib.import_module(a.script)
    out = a.out or os.path.join(HERE, "..", "output", a.script.replace("guion_", "") + ".mp4")
    os.makedirs(a.build, exist_ok=True)
    print("1/3 voix + timeline…", flush=True)
    tl, mix, duration = build(G, a.voice or G.VOICE, a.build, a.models, a.voice_dir)
    print(f"   durée : {duration:.1f}s", flush=True)

    global _R
    _R = Renderer(G, tl, Sources({k: os.path.join(HERE, p) for k, p in G.SOURCES.items()}))
    if a.stills:
        for ts in a.stills.split(","):
            Image.fromarray(_R.frame(float(ts))).save(os.path.join(a.build, f"still_{float(ts):05.1f}.png"))
        print("images exportées dans", a.build)
        return

    wav = os.path.join(a.build, "mix.wav")
    sf.write(wav, np.stack([mix, mix], 1).astype(np.float32), audio.SR)
    print("2/3 rendu des images…", flush=True)
    n = int(duration * FPS)
    k = a.workers
    bounds = [round(n * i / k) for i in range(k + 1)]
    jobs = [(bounds[i], bounds[i + 1], os.path.join(a.build, f"montage_part{i}.mp4")) for i in range(k)]
    with mp.get_context("fork").Pool(k) as pool:
        parts = pool.map(_render_range, jobs)
    lst = os.path.join(a.build, "montage_parts.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in parts)

    print("3/3 assemblage…", flush=True)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-movflags", "+faststart", "-shortest", out], check=True)
    print("OK ->", os.path.abspath(out))


if __name__ == "__main__":
    main()
