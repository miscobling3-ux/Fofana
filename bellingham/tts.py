# Synthèse locale de la voix off (Kokoro), phrase par phrase, + timings mot à mot (words.json)
import sys, json, re, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
M='/home/user/Fofana/video/models'
voice=sys.argv[1]; speed=float(sys.argv[2]); out=sys.argv[3]
k=Kokoro(f'{M}/kokoro.onnx',f'{M}/voices.bin')
if '+' in voice:
    a,b=voice.split('+'); style=0.5*k.get_voice_style(a)+0.5*k.get_voice_style(b)
else: style=voice
text=open('/home/user/Fofana/bellingham/script.txt').read().replace('\n',' ')
# phrases
sents=[s.strip() for s in re.findall(r'[^.!?:]+[.!?:]?',text) if s.strip()]
# fusionne les bouts trop courts terminés par ':' avec la suite
merged=[];buf=''
for s in sents:
    if s.endswith(':'): buf+=s+' '; continue
    merged.append((buf+s).strip()); buf=''
SR=24000; GAP=int(0.06*SR); WIN=int(0.02*SR)
def trim(x):
    db=20*np.log10(np.sqrt(np.convolve(x**2,np.ones(WIN)/WIN,'same'))+1e-9)
    idx=np.where(db>-38)[0]; return x[max(0,idx[0]-240):idx[-1]+480] if len(idx) else x
def compress(x):
    # tout silence > 0,12 s ramené à 0,06 s (RMS 20 ms, seuil -38 dB)
    n=len(x)//WIN; rms=np.array([np.sqrt(np.mean(x[i*WIN:(i+1)*WIN]**2)) for i in range(n)])
    sil=20*np.log10(rms+1e-9)<-38; outp=[]; i=0
    while i<n:
        j=i
        while j<n and sil[j]==sil[i]: j+=1
        seg=x[i*WIN:j*WIN]
        if sil[i] and (j-i)*0.02>0.12: seg=seg[:int(0.06*SR)]
        outp.append(seg); i=j
    outp.append(x[n*WIN:]); return np.concatenate(outp)
def sylls(w): return max(1,len(re.findall(r'[aeiouyàâéèêëîïôûùœ]+',w.lower())))
def say(s):
    for a,b in [("l'AEK",'la eu ka'),('AEK','a eu ka'),('Real Madrid','Réal Madrid'),('le Real','le Réal'),('Cucurella','Koukourella')]: s=s.replace(a,b)
    return s
audio=[]; words=[]; t=0.0
for s in merged:
    x,_=k.create(say(s),voice=style,speed=speed,lang='fr-fr')
    x=compress(trim(x.astype(np.float32)))
    dur=len(x)/SR
    toks=s.split()
    # pauses internes (virgule) : détection des creux pour caler les groupes de mots
    groups=[]; g=[]
    for w in toks:
        g.append(w)
        if w.endswith(','): groups.append(g); g=[]
    if g: groups.append(g)
    n=len(x)//WIN; rms=np.array([np.sqrt(np.mean(x[i*WIN:(i+1)*WIN]**2)) for i in range(n)])
    sil=20*np.log10(rms+1e-9)<-38
    # creux candidats
    gaps=[];i=0
    while i<n:
        if sil[i]:
            j=i
            while j<n and sil[j]: j+=1
            if i>0 and j<n: gaps.append(((i+j)/2*0.02,(j-i)*0.02,i*0.02,j*0.02))
            i=j
        else: i+=1
    W=[sum(sylls(w) for w in g) for g in groups]; tot=sum(W)
    bounds=[0.0]; acc=0
    for gi in range(len(groups)-1):
        acc+=W[gi]; est=dur*acc/tot
        if gaps:
            best=min(gaps,key=lambda q:abs(q[0]-est)-0.5*q[1])
            if abs(best[0]-est)<0.6: bounds.append(best[0]); continue
        bounds.append(est)
    bounds.append(dur)
    for gi,g in enumerate(groups):
        a,b=bounds[gi],bounds[gi+1]; ws=[sylls(w)+0.3 for w in g]; ts=sum(ws); c=a
        for w,wt in zip(g,ws):
            d=(b-a)*wt/ts; words.append({'word':w,'start':round(t+c,3),'end':round(t+c+d,3)}); c+=d
    audio.append(x); audio.append(np.zeros(GAP,np.float32)); t+=dur+GAP/SR
y=np.concatenate(audio)
# limiteur de crête simple -2 dBFS
peak=np.max(np.abs(y)); y=y*(10**(-2/20)/peak)
sf.write(out,y,SR)
json.dump({'sentences':merged,'words':words,'duration':len(y)/SR},open(out.replace('.wav','.json'),'w'),ensure_ascii=False,indent=0)
print(out,len(y)/SR,'s',len(words),'mots')
