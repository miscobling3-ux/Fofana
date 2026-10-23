"""Remonte une vidéo verticale existante en TikTok 1080x1920 : nouvelle voix off (FR / ES), zooms et recadrages,
sous-titres animés mot par mot, badges, titres, musique et bruitages. Les anciens sous-titres incrustés et le
filigrane de la source sont effacés (inpainting) avant le montage.

Usage :
  python3 remix.py --script guion_ongles_fr                    # -> output/ongles_fr.mp4
  python3 remix.py --script guion_ongles_es                    # -> output/ongles_es.mp4
  python3 remix.py --script guion_ongles_fr --voice piper:fr-gilles-low --out output/ongles_fr_homme.mp4
  python3 remix.py --script guion_ongles_fr --stills 1,14,45   # aperçu : quelques PNG dans video/build/
"""
import argparse
import functools
import hashlib
import importlib
import json
import math
import multiprocessing as mp
import os
import re
import subprocess
import sys

import cv2
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
YELLOW, PINK, GREEN, RED, WHITE, BLACK = (255, 212, 0), (255, 46, 99), (22, 190, 90), (235, 40, 40), \
    (255, 255, 255), (0, 0, 0)
SUB_Y = 1395            # centre des sous-titres (là où étaient ceux de la source)
BADGE_Y, TITLE_Y = 330, 560
# zones de la source à effacer, en pixels pour une source 576x1024 (mises à l'échelle sinon)
BAND = (692, 802)                 # lignes des sous-titres + filigrane
WATERMARK = (222, 764, 356, 797)  # x0, y0, x1, y1


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def back_out(u):
    u = min(1.0, max(0.0, u))
    c = 1.9
    return 1 + (c + 1) * (u - 1) ** 3 + c * (u - 1) ** 2


def pulse(d, decay=5.0):
    return 0.0 if d < 0 else math.exp(-d * decay) * min(1.0, d / 0.06)


# ---------------------------------------------------------------- source
def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
                          "stream=width,height,r_frame_rate,nb_read_frames", "-of", "json", path],
                         capture_output=True, text=True, check=True)
    s = json.loads(out.stdout)["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    return int(s["width"]), int(s["height"]), float(num) / float(den), int(s["nb_read_frames"])


def clean(frame, k):
    """Efface les sous-titres incrustés (texte blanc à contour noir) et le filigrane."""
    y0, y1 = int(BAND[0] * k), int(BAND[1] * k)
    roi = frame[y0:y1]
    mx, mn = roi.max(2), roi.min(2)
    mask = (((mn > 215) | (mx < 75)) * 255).astype(np.uint8)
    x0, wy0, x1, wy1 = (int(v * k) for v in WATERMARK)
    mask[wy0 - y0:wy1 - y0, x0:x1] = 255
    mask = cv2.dilate(mask, np.ones((5, 5), np.uint8))
    fixed = cv2.inpaint(roi, mask, 5, cv2.INPAINT_TELEA)
    soft = cv2.GaussianBlur(fixed, (0, 0), 3)
    a = cv2.GaussianBlur(cv2.dilate(mask, np.ones((15, 15), np.uint8)), (0, 0), 6)[..., None] / 255.0
    frame[y0:y1] = (roi * (1 - a) + soft * a).astype(np.uint8)
    return frame


def load_source(path, build):
    w, h, fps, n = probe(path)
    st = os.stat(path)
    key = hashlib.md5(f"{os.path.abspath(path)}|{st.st_size}|{st.st_mtime}|{BAND}|{WATERMARK}".encode()).hexdigest()[:10]
    npy = os.path.join(build, f"source_{key}.npy")
    if os.path.exists(npy):
        return np.load(npy, mmap_mode="r"), fps
    print(f"   nettoyage de la source ({n} images)…", flush=True)
    arr = np.lib.format.open_memmap(npy + ".tmp", mode="w+", dtype=np.uint8, shape=(n, h, w, 3))
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                          stdout=subprocess.PIPE)
    k = h / 1024
    for i in range(n):
        buf = ff.stdout.read(w * h * 3)
        if len(buf) < w * h * 3:
            arr[i:] = arr[i - 1]
            break
        arr[i] = clean(np.frombuffer(buf, np.uint8).reshape(h, w, 3).copy(), k)
    ff.stdout.close()
    ff.wait()
    arr.flush()
    del arr
    os.replace(npy + ".tmp", npy)
    return np.load(npy, mmap_mode="r"), fps


# ---------------------------------------------------------------- voix
def parse(text):
    words = []
    for tok in text.split():
        if re.fullmatch(r"[?!:;»]+", tok) and words:  # ponctuation française détachée : collée au mot précédent
            words[-1]["text"] += "\u00a0" + tok
            continue
        words.append(dict(text=tok.replace("*", ""), key="*" in tok))
    return words


@functools.lru_cache(maxsize=1)
def _kokoro(models):
    return audio.load_tts(models)


def synth(G, voice, text, cache, models):
    h = hashlib.md5(f"{voice}|{G.SPEED}|{G.LANG}|{text}".encode()).hexdigest()[:12]
    path = os.path.join(cache, f"{h}.wav")
    if not os.path.exists(path):
        import scipy.signal as ss
        if voice.startswith("piper:"):
            from piper import PiperVoice, SynthesisConfig
            v = PiperVoice.load(os.path.join(models, voice[6:] + ".onnx"))
            chunks = v.synthesize(text, syn_config=SynthesisConfig(length_scale=1 / G.SPEED))
            a = np.concatenate([c.audio_float_array for c in chunks]).astype(np.float64)
            a = audio.trim(ss.resample_poly(a, audio.SR, v.config.sample_rate))
        else:
            tts = _kokoro(models)
            style = voice
            if "+" in voice:  # mélange de deux voix Kokoro (55 % de la seconde)
                v1, v2 = voice.split("+")
                style = 0.45 * tts.get_voice_style(v1) + 0.55 * tts.get_voice_style(v2)
            a = audio.synth_line(tts, text, style, G.SPEED, G.LANG)
        sf.write(path, a, audio.SR)
        print(f"  voix : {text}", flush=True)
    a, _ = sf.read(path)
    return a


# ---------------------------------------------------------------- timeline
def build(G, voice, build_dir, models):
    cache = os.path.join(build_dir, "tts_cache")
    os.makedirs(cache, exist_ok=True)
    segs, words_all, sfx = [], [], []
    t = 0.25
    clips = []
    for i, ln in enumerate(G.LINES):
        words = parse(ln["text"])
        clip = synth(G, voice, " ".join(w["text"] for w in words), cache, models)
        if ln["chapter"] and i > 0:
            t += 0.35
        start = t
        for w, (a, b) in zip(words, audio.word_times([w["text"] for w in words], clip)):
            w["t0"], w["t1"] = start + a, start + b
        clips.append((start, clip))
        segs.append(dict(ln, t0=0.0 if i == 0 else start - 0.08, words=words))
        words_all += words
        t = start + len(clip) / audio.SR + (0.22 if re.search(r"[.?!]$", ln["text"]) else 0.08)
    duration = t + 0.9
    for i, s in enumerate(segs):
        s["t1"] = segs[i + 1]["t0"] if i + 1 < len(segs) else duration
    cta_t = segs[-1]["t0"]

    voice_track = np.zeros(int(duration * audio.SR) + audio.SR)
    for s, clip in clips:
        j = int(s * audio.SR)
        voice_track[j:j + len(clip)] += clip

    # sous-titres : 1 à 3 mots, coupés à la ponctuation
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
    sfx.append((0.05, "boom", 0.45))
    for s in segs[1:]:
        sfx.append((s["t0"] - 0.12, "whoosh", 0.35))
        if s["chapter"]:
            sfx.append((s["t0"] - 1.9, "riser", 0.4))
            sfx.append((s["t0"], "boom", 0.35))
    prev_tag = None
    for s in segs:
        if s["tag"] and s["tag"] != prev_tag:
            sfx.append((s["t0"] + 0.05, "error" if s["tag"] == "bad" else "tick", 0.45))
        prev_tag = s["tag"]
    sfx += [(k, "pop", 0.3) for k in keys]
    sfx.append((cta_t + 0.05, "pop", 0.8))

    music = audio.make_music(duration, bpm=100, seed=11,
                             sections=[(0, segs[1]["t0"], 0.8), (segs[1]["t0"], cta_t, 0.55), (cta_t, duration + 5, 0.8)])
    mix = audio.mix_all(voice_track, music, sfx, duration)
    tl = dict(segs=segs, caps=caps, keys=keys, duration=duration, cta_t=cta_t)
    return tl, mix, duration


# ---------------------------------------------------------------- graphismes
FONT_DIR = os.path.join(HERE, "models", "fonts")


@functools.lru_cache(maxsize=16)
def font(size, black=True):
    for name in (("Montserrat-Black.ttf",) if black else ()) + ("Montserrat-ExtraBold.ttf",):
        p = os.path.join(FONT_DIR, name)
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)


def text_size(txt, f, stroke=0):
    b = f.getbbox(txt, stroke_width=stroke)
    return b[2] - b[0], b[3] - b[1], b


@functools.lru_cache(maxsize=512)
def caption_img(cap_id, active, texts, keyflags):
    f = font(88)
    stroke = 9
    widths = [f.getlength(t) for t in texts]
    asc, desc = f.getmetrics()
    space = 22
    img = Image.new("RGBA", (int(sum(widths) + space * (len(texts) - 1)) + 60, asc + desc + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 30
    for i, (t, tw) in enumerate(zip(texts, widths)):
        if i == active:
            d.rounded_rectangle((x - 14, 10, x + tw + 14, img.height - 10), 22, fill=PINK + (235,))
        fill = YELLOW if keyflags[i] and i != active else WHITE
        d.text((x, 20 + asc), t, font=f, fill=fill, stroke_width=stroke, stroke_fill=BLACK, anchor="ls")
        x += tw + space
    if img.width > W - 60:
        r = (W - 60) / img.width
        img = img.resize((int(img.width * r), int(img.height * r)), Image.LANCZOS)
    return img


def pill(txt, size, bg, fg=WHITE, icon=None, pad=(34, 18)):
    f = font(size)
    tw, th, b = text_size(txt, f)
    iw = int(size * 1.0) if icon else 0
    img = Image.new("RGBA", (tw + iw + pad[0] * 2 + 8, th + pad[1] * 2 + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((4, 4, img.width - 4, img.height - 4), (th + pad[1] * 2) // 2, fill=bg + (245,),
                        outline=WHITE + (255,), width=5)
    x = pad[0] + 4
    cy = img.height / 2
    if icon == "check":
        s = size * 0.42
        d.line([(x, cy), (x + s * 0.7, cy + s * 0.7), (x + s * 1.8, cy - s * 0.8)], fill=fg, width=int(size * 0.16),
               joint="curve")
    elif icon == "warn":
        s = size * 0.5
        d.polygon([(x + s, cy - s), (x + 2 * s, cy + s * 0.85), (x, cy + s * 0.85)], fill=fg)
        d.line([(x + s, cy - s * 0.35), (x + s, cy + s * 0.3)], fill=bg, width=int(size * 0.12))
        d.ellipse((x + s - 4, cy + s * 0.45, x + s + 4, cy + s * 0.65 + 4), fill=bg)
    d.text((x + iw - b[0], pad[1] + 4 - b[1]), txt, font=f, fill=fg)
    return img


@functools.lru_cache(maxsize=64)
def cached_pill(txt, size, bg, fg, icon):
    return pill(txt, size, bg, fg, icon)


@functools.lru_cache(maxsize=16)
def outlined(txt, size, fill):
    f = font(size)
    tw, th, b = text_size(txt, f, 8)
    img = Image.new("RGBA", (tw + 20, th + 20), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((10 - b[0], 10 - b[1]), txt, font=f, fill=fill, stroke_width=8, stroke_fill=BLACK)
    return img


def paste(canvas, img, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    s = round(scale, 2)
    if s != 1.0:
        img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BILINEAR)
    if rot:
        img = img.rotate(rot, Image.BICUBIC, expand=True)
    if alpha < 1:
        a = img.getchannel("A").point(lambda v: int(v * alpha))
        img = img.copy()
        img.putalpha(a)
    canvas.alpha_composite(img, (int(cx - img.width / 2), int(cy - img.height / 2)))


@functools.lru_cache(maxsize=1)
def vignette():
    y, x = np.mgrid[0:H, 0:W]
    r = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    return np.clip((r - 0.55) / 0.75, 0, 1)[..., None].astype(np.float32)


# ---------------------------------------------------------------- rendu
class Renderer:
    def __init__(self, tl, src, src_fps):
        self.tl, self.src, self.fps = tl, src, src_fps
        self.n = len(src)
        self.sh, self.sw = src.shape[1:3]

    def seg_at(self, t):
        for i, s in enumerate(self.tl["segs"]):
            if s["t0"] <= t < s["t1"]:
                return i, s
        return len(self.tl["segs"]) - 1, self.tl["segs"][-1]

    def source_frame(self, st):
        f = min(max(st * self.fps, 0), self.n - 1)
        i0 = int(f)
        i1 = min(i0 + 1, self.n - 1)
        u = f - i0
        if u < 0.15 or i0 == i1:
            return np.asarray(self.src[i0])
        if u > 0.85:
            return np.asarray(self.src[i1])
        return cv2.addWeighted(np.asarray(self.src[i0]), 1 - u, np.asarray(self.src[i1]), u, 0)

    def frame(self, t):
        tl = self.tl
        i, s = self.seg_at(t)
        u = (t - s["t0"]) / max(1e-3, s["t1"] - s["t0"])
        a, b = s["src"]
        img = self.source_frame(a + u * (b - a))

        # caméra : zoom lent sur la zone utile + « punch » sur les mots-clés et à chaque coupe
        z0, z1, cx, cy = s["zoom"]
        z = z0 + (z1 - z0) * ease(u)
        p = sum(0.06 * pulse(t - k) for k in tl["keys"] if -0.1 < t - k < 1.5)
        if i > 0:
            p += 0.09 * pulse(t - s["t0"], 6)
        z *= 1 + p
        cx += 0.006 * math.sin(t * 0.9)
        cy += 0.005 * math.cos(t * 0.7)
        cx = min(max(cx, 0.5 / z), 1 - 0.5 / z)
        cy = min(max(cy, 0.5 / z), 1 - 0.5 / z)
        k = W * z / self.sw
        M = np.float32([[k, 0, W / 2 - cx * self.sw * k], [0, k, H / 2 - cy * self.sh * k]])
        out = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        out = cv2.addWeighted(out, 1.45, cv2.GaussianBlur(out, (0, 0), 2.0), -0.45, 0)

        # étalonnage : contraste léger, vignette, teinte rouge sur les moments « danger », flash aux coupes
        f = out.astype(np.float32)
        f = (f - 128) * 1.06 + 131
        v = vignette()
        f *= 1 - 0.35 * v
        if s["tag"] == "bad":
            red = 0.22 + 0.12 * math.sin(t * 6)
            f = f * (1 - red * v) + np.float32([235, 30, 40]) * (red * v)
        if i > 0:
            fl = 0.45 * max(0.0, 1 - (t - s["t0"]) / 0.13)
            f = f * (1 - fl) + 255 * fl
        canvas = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).convert("RGBA")

        self.overlays(canvas, t, i, s)
        return np.asarray(canvas.convert("RGB"))

    def overlays(self, canvas, t, i, s):
        tl, G = self.tl, self.G
        d = ImageDraw.Draw(canvas)
        # barre de progression
        d.rounded_rectangle((40, 40, W - 40, 52), 6, fill=(255, 255, 255, 90))
        d.rounded_rectangle((40, 40, 40 + (W - 80) * min(1, t / tl["duration"]), 52), 6, fill=YELLOW + (255,))

        cta = t >= tl["cta_t"]
        # accroche
        hook_end = tl["segs"][1]["t0"]
        if t < hook_end + 0.2:
            out = 1 - ease((t - hook_end) / 0.2)
            paste(canvas, cached_pill(G.HOOK[0], 104, RED, WHITE, None), W / 2, TITLE_Y,
                  back_out(t / 0.35) * out, out, rot=-3)
            paste(canvas, outlined(G.HOOK[1], 62, YELLOW), W / 2, TITLE_Y + 140, back_out((t - 0.25) / 0.35) * out, out)
        # titre de chapitre
        if s["chapter"] and i > 0 and t - s["t0"] < 2.4:
            dt = t - s["t0"]
            out = 1 - ease((dt - 2.1) / 0.3)
            paste(canvas, cached_pill(s["chapter"], 96, PINK, WHITE, None), W / 2, TITLE_Y,
                  back_out(dt / 0.35) * out, out, rot=2)
        # badges
        if s["tag"] and not cta:
            prev = tl["segs"][i - 1]["tag"] if i > 0 else None
            dt = t - s["t0"] if prev != s["tag"] else 9
            nxt = tl["segs"][i + 1]["tag"] if i + 1 < len(tl["segs"]) else None
            out = 1 - ease((t - (s["t1"] - 0.2)) / 0.2) if nxt != s["tag"] else 1
            ok = s["tag"] == "ok"
            img = cached_pill(G.TAGS[s["tag"]], 62, GREEN if ok else RED, WHITE, "check" if ok else "warn")
            paste(canvas, img, W / 2, BADGE_Y, back_out(dt / 0.3) * out, out)
        # sous-titres
        for ci, c in enumerate(tl["caps"]):
            if c["t0"] <= t < c["t1"]:
                active = max([j for j, w in enumerate(c["words"]) if w["t0"] - 0.04 <= t] or [0])
                img = caption_img(ci, active, tuple(w["text"] for w in c["words"]),
                                  tuple(w["key"] for w in c["words"]))
                paste(canvas, img, W / 2, SUB_Y if not cta else SUB_Y + 80, 0.8 + 0.2 * back_out((t - c["t0"]) / 0.14))
                break
        # appel à l'action
        if cta:
            dt = t - tl["cta_t"]
            ov = Image.new("RGBA", canvas.size, (0, 0, 0, int(110 * ease(dt / 0.3))))
            canvas.alpha_composite(ov)
            beat = 1 + 0.04 * math.sin(dt * 9) * ease((dt - 0.4) / 0.3)
            paste(canvas, cached_pill(G.CTA[0], 120, PINK, WHITE, None), W / 2, 820, back_out(dt / 0.4) * beat)
            paste(canvas, outlined(G.CTA[1], 60, WHITE), W / 2, 990, back_out((dt - 0.2) / 0.4))
            if G.BRAND:
                paste(canvas, outlined("@" + G.BRAND.lower().replace(" ", ""), 56, YELLOW), W / 2, 1090,
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
    ap.add_argument("--script", default="guion_ongles_fr")
    ap.add_argument("--out", default=None)
    ap.add_argument("--voice", default=None, help="remplace VOICE du script (ex. piper:fr-gilles-low)")
    ap.add_argument("--models", default=os.environ.get("MODELS_DIR", os.path.join(HERE, "models")))
    ap.add_argument("--build", default=os.path.join(HERE, "build"))
    ap.add_argument("--stills", default="", help="temps (s) séparés par des virgules : n'exporte que ces images")
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()

    G = importlib.import_module(a.script)
    voice = a.voice or G.VOICE
    out = a.out or os.path.join(HERE, "..", "output", a.script.replace("guion_", "") + ".mp4")
    os.makedirs(a.build, exist_ok=True)
    print("1/3 source + voix + timeline…", flush=True)
    src, src_fps = load_source(os.path.join(HERE, G.SOURCE), a.build)
    tl, mix, duration = build(G, voice, a.build, a.models)
    print(f"   durée : {duration:.1f}s", flush=True)

    global _R
    _R = Renderer(tl, src, src_fps)
    _R.G = G
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
    jobs = [(bounds[i], bounds[i + 1], os.path.join(a.build, f"remix_part{i}.mp4")) for i in range(k)]
    with mp.get_context("fork").Pool(k) as pool:
        parts = pool.map(_render_range, jobs)
    lst = os.path.join(a.build, "remix_parts.txt")
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
