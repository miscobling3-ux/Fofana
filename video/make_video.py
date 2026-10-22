"""Génère la vidéo TikTok (1080x1920, 30 fps) à partir d'un script.

Usage : python3 make_video.py [--script guion_psg_es] [--out output/video.mp4] [--preview]
"""
import argparse
import hashlib
import importlib
import json
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
from engine import W, H, FPS  # noqa: E402
from timeline import Timeline, Track, Renderer  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CMD_RE = re.compile(r"\{([^}:]+)(?::([^}]*))?\}")


def parse_line(text):
    """-> liste de mots {text, spoken, key, cmds}"""
    words = []
    for tok in text.split():
        cmds = CMD_RE.findall(tok)
        tok = CMD_RE.sub("", tok)
        if not tok:
            continue
        key = "*" in tok
        tok = tok.replace("*", "")
        if "=" in tok:
            disp, spoken = tok.split("=", 1)
            punct = re.search(r"[,.:;?!]+$", spoken)
            if punct and not re.search(r"[,.:;?!]+$", disp):
                disp += punct.group(0)
            spoken = spoken.replace("-", " ")
        else:
            disp = spoken = tok
        words.append(dict(text=disp, spoken=spoken, key=key, cmds=cmds))
    return words


def tts_lines(G, lines, cache_dir, model_dir):
    os.makedirs(cache_dir, exist_ok=True)
    tts = None
    out = []
    for words in lines:
        text = " ".join(w["spoken"] for w in words)
        h = hashlib.md5(f"{G.VOICE}|{G.SPEED}|{text}".encode()).hexdigest()[:12]
        path = os.path.join(cache_dir, f"{h}.wav")
        if not os.path.exists(path):
            if tts is None:
                tts = audio.load_tts(model_dir)
            a = audio.synth_line(tts, text, G.VOICE, G.SPEED)
            sf.write(path, a, audio.SR)
            print(f"  voix : {text}", flush=True)
        a, _ = sf.read(path)
        out.append(a)
    return out


def build(G, cache_dir, model_dir):
    parsed = [(ch, parse_line(txt)) for ch, txt in G.LINES]
    clips = tts_lines(G, [w for _, w in parsed], cache_dir, model_dir)

    # placement temporel
    t = 0.3
    starts, chapters = [], []
    for i, ((ch, words), clip) in enumerate(zip(parsed, clips)):
        if ch and i > 0:
            t += 0.35
        if ch:
            chapters.append((max(0.0, t - 0.15) if i > 0 else 0.0, ch))
        starts.append(t)
        times = audio.word_times([w["spoken"] for w in words], clip)
        for w, (a, b) in zip(words, times):
            w["t0"], w["t1"] = t + a, t + b
        t += len(clip) / audio.SR + 0.12
    outro_t = t + 0.5
    duration = outro_t + G.OUTRO_LEN

    voice = np.zeros(int(duration * audio.SR) + audio.SR)
    for s, clip in zip(starts, clips):
        i = int(s * audio.SR)
        voice[i:i + len(clip)] += clip

    tl = Timeline(G.BRAND, chapters)
    tl.duration, tl.outro_t = duration, outro_t
    tl.cam = Track(G.CAMS["wide"])
    for pid, num, label, pos in G.HOME:
        tl.add_player(pid, num, "home", label, pos)
    for pid, num, pos in G.AWAY:
        tl.add_player(pid, num, "away", None, pos)

    sfx_events = []
    ch_times = [c[0] for c in chapters] + [outro_t]

    def chapter_end(tt):
        for c in ch_times:
            if c > tt + 0.05:
                return c
        return outro_t

    ctx = G.Ctx(tl, chapter_end, lambda tt, kind, g=1.0: sfx_events.append((max(0, tt), kind, g)))
    for ch, words in parsed:
        for w in words:
            for cmd, arg in w["cmds"]:
                G.run_command(ctx, w["t0"] - 0.05, cmd, arg)
    for ct, _ in chapters[1:]:
        sfx_events.append((ct, "whoosh", 0.6))
        tl.punch.append((ct, 0.35))
    sfx_events.append((outro_t, "boom", 0.5))
    sfx_events.append((outro_t + 0.9, "pop", 0.9))

    # sous-titres : groupes de 1 à 3 mots, coupés à la ponctuation
    all_words = [w for _, ws in parsed for w in ws]
    chunks, cur = [], []
    for w in all_words:
        cur.append(w)
        if len(cur) >= 3 or re.search(r"[,.:;?!]$", w["text"]) or len(" ".join(x["text"] for x in cur)) > 18:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    for i, ch in enumerate(chunks):
        t0 = ch[0]["t0"] - 0.04
        nxt = chunks[i + 1][0]["t0"] - 0.04 if i + 1 < len(chunks) else outro_t
        t1 = min(nxt, ch[-1]["t1"] + 0.6)
        tl.captions.append(dict(t0=t0, t1=t1, words=ch))

    # musique
    secs = []
    for i, (ct, name) in enumerate(chapters):
        c1 = chapters[i + 1][0] if i + 1 < len(chapters) else outro_t
        secs.append((ct, c1, G.MUSIC_LEVELS.get(name, 0.6)))
    secs.append((outro_t, duration + 5, 0.15))
    music = audio.make_music(duration, sections=secs)
    mix = audio.mix_all(voice, music, sfx_events, duration)
    return tl, mix, duration


# ---------------------------------------------------------------- rendu parallèle
_TL = None


def _render_range(args):
    i0, i1, path = args
    r = Renderer(_TL)
    ff = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
         "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for i in range(i0, i1):
        img = r.frame(i / FPS)
        ff.stdin.write(img.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType).tobytes())
    ff.stdin.close()
    ff.wait()
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", default="guion_psg_es")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "output", "psg_luis_enrique_es.mp4"))
    ap.add_argument("--models", default=os.environ.get("MODELS_DIR", os.path.join(HERE, "models")))
    ap.add_argument("--build", default=os.path.join(HERE, "build"))
    ap.add_argument("--stills", default="", help="temps (s) séparés par des virgules : n'exporte que ces images")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()

    G = importlib.import_module(a.script)
    os.makedirs(a.build, exist_ok=True)
    print("1/3 voix + timeline…", flush=True)
    tl, mix, duration = build(G, os.path.join(a.build, "tts_cache"), a.models)
    print(f"   durée : {duration:.1f}s", flush=True)

    if a.stills:
        r = Renderer(tl)
        for ts in a.stills.split(","):
            r.frame(float(ts)).save(os.path.join(a.build, f"still_{float(ts):05.1f}.png"))
        print("images exportées dans", a.build)
        return

    wav = os.path.join(a.build, "mix.wav")
    sf.write(wav, np.stack([mix, mix], 1).astype(np.float32), audio.SR)

    print("2/3 rendu des images…", flush=True)
    global _TL
    _TL = tl
    n = int(duration * FPS)
    k = a.workers
    bounds = [round(n * i / k) for i in range(k + 1)]
    jobs = [(bounds[i], bounds[i + 1], os.path.join(a.build, f"part{i}.mp4")) for i in range(k)]
    with mp.get_context("fork").Pool(k) as pool:
        parts = pool.map(_render_range, jobs)
    lst = os.path.join(a.build, "parts.txt")
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
