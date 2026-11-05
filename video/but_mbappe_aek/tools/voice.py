"""Voix off locale (Kokoro) phrase par phrase -> voice_takeN.wav + words_takeN.json"""
import sys, re, json, numpy as np, soundfile as sf
sys.path.insert(0, '/home/user/Fofana/video')
import audio
P = sys.argv[1]; voice = sys.argv[2]; out = sys.argv[3]; speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
SUB = {"Jude": "Djoude", "Dumfries": "Doumfrisse", "Denzel": "Dènnzèl", "L'AEK": "L'A-E-K", "Real": "Réal",
       "Mbappé,": "Mbappé,", "timing.": "taïmingue."}
tts = audio.load_tts('/home/user/Fofana/video/models')
if '+' in voice:
    a, b, w = voice.split('+') if voice.count('+') == 2 else (*voice.split('+'), '0.55')
    style = (1 - float(w)) * tts.get_voice_style(a) + float(w) * tts.get_voice_style(b)
else:
    style = voice
SR = audio.SR
blocks = [l.strip() for l in open(f'{P}/script.txt', encoding='utf-8') if l.strip()]
pieces, words = [], []
t = 0.0
for bi, blk in enumerate(blocks):
    sents = re.findall(r'[^.!?]+[.!?]', blk)
    for si, sent in enumerate(sents):
        chunks = re.findall(r'[^,:;]+[,:;]?', sent)
        for ci, ch in enumerate(chunks):
            toks = ch.split()
            if not toks: continue
            spoken = [SUB.get(x, x) for x in toks if not re.fullmatch(r'[:;!?]', x)]
            a = audio.synth_line(tts, ' '.join(spoken), style, speed, 'fr-fr')
            syl = [audio.syllables(x) for x in spoken]; tot = sum(syl)
            d = len(a) / SR; t0 = 0.03; t1 = d - 0.06; acc = t0
            wi = 0
            for tok in toks:
                if re.fullmatch(r'[:;!?]', tok):
                    words[-1]['text'] += ' ' + tok; continue
                dd = (t1 - t0) * syl[wi] / tot; wi += 1
                words.append(dict(text=tok, start=t + acc, end=t + acc + dd, block=bi + 1)); acc += dd
            pieces.append(a); t += d
            g = 0.30 if ci == len(chunks) - 1 else 0.16
            pieces.append(np.zeros(int(g * SR))); t += g
v = np.concatenate(pieces)
# --- compression des silences : RMS 20 ms, seuil -38 dB, silence > 0.12 s -> 0.06 s
hop = int(0.02 * SR)
rms = np.array([np.sqrt(np.mean(v[i:i+hop]**2) + 1e-12) for i in range(0, len(v) - hop + 1, hop)])
quiet = 20 * np.log10(rms) < -38
segs = []  # (src0, src1) kept ranges
i = 0; n = len(quiet); keep = []; cur = 0
while i < n:
    if quiet[i]:
        j = i
        while j < n and quiet[j]: j += 1
        if (j - i) * 0.02 > 0.12:
            mid0 = i * hop + int(0.03 * SR); mid1 = j * hop - int(0.03 * SR)
            keep.append((cur, mid0)); cur = mid1
        i = j
    else:
        i += 1
keep.append((cur, len(v)))
outa = np.concatenate([v[a:b] for a, b in keep])
def remap(ts):
    s = int(ts * SR); acc = 0
    for a, b in keep:
        if s < a: return acc / SR
        if s <= b: return (acc + s - a) / SR
        acc += b - a
    return acc / SR
for w in words:
    w['start'] = round(remap(w['start']), 3); w['end'] = round(max(remap(w['end']), w['start'] + 0.04), 3)
# léger blanc au début / fin
lead = 0.15
outa = np.concatenate([np.zeros(int(lead * SR)), outa, np.zeros(int(0.6 * SR))])
for w in words: w['start'] += lead; w['end'] += lead
pk = np.max(np.abs(outa)); outa = outa / pk * 10 ** (-3 / 20)
sf.write(f'{P}/{out}.wav', outa, SR, subtype='PCM_16')
json.dump(words, open(f'{P}/{out}.json', 'w'), ensure_ascii=False, indent=0)
print(out, 'duration', round(len(outa) / SR, 2), 'words', len(words))
