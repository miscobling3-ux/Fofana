# words.json from known script + pause structure (no ASR model reachable)
import numpy as np,subprocess,json,re
sr=44100
x=np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i","voice/voice_user.mp3","-f","f32le","-ac","1","-ar",str(sr),"-"],capture_output=True).stdout,np.float32)
win=882;n=len(x)//win
db=20*np.log10(np.sqrt((x[:n*win].reshape(n,win)**2).mean(1)+1e-12))
sp=db>=-38
# speech intervals, merging gaps < 0.1 s
iv=[];i=0
while i<n:
    if sp[i]:
        j=i
        while j<n and sp[j]: j+=1
        iv.append([i*.02,j*.02]); i=j
    else: i+=1
m=[iv[0]]
for a,b in iv[1:]:
    if a-m[-1][1]<0.1: m[-1][1]=b
    else: m.append([a,b])
breaks=[5.88,12.68,16.9,21.9,27.94,31.44,35.3,40.02,42.54,50.0,54.22]
text=open('voice/script_es.txt').read().split()
sents=re.split(r'(?<=[.!?])\s+',open('voice/script_es.txt').read().strip())
bounds=[0]+breaks+[n*.02]
words=[]
def w8(w): return len(re.sub(r'[^\wáéíóúñü]','',w.lower()))+1.5
for k,s in enumerate(sents):
    lo,hi=bounds[k],bounds[k+1]
    sv=[[max(a,lo),min(b,hi)] for a,b in m if b>lo+0.05 and a<hi-0.05]
    tot=sum(b-a for a,b in sv)
    ws=s.split(); W=[w8(w) for w in ws]; S=sum(W)
    def at(f):
        r=f*tot
        for a,b in sv:
            if r<=b-a+1e-9: return a+r
            r-=b-a
        return sv[-1][1]
    c=0
    for w,ww in zip(ws,W):
        st=at(c/S); c+=ww; en=at(c/S)
        words.append({"text":w,"start":round(st,3),"end":round(en,3),"sentence":k})
json.dump(words,open('voice/words.json','w'),ensure_ascii=False,indent=0)
print(len(words), words[0], words[-1])
for k in range(len(sents)): 
    ws=[w for w in words if w['sentence']==k]; print(k,ws[0]['start'],ws[-1]['end'],' '.join(w['text'] for w in ws)[:40])
