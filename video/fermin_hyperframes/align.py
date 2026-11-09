import numpy as np, wave, re, json
w=wave.open('voice16.wav'); x=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16)/32768.
win=320; n=len(x)//win
r=20*np.log10(np.sqrt((x[:n*win].reshape(n,win)**2).mean(1))+1e-9)
sil=r<-38
S=[];i=0
while i<n:
    if sil[i]:
        j=i
        while j<n and sil[j]: j+=1
        S.append((i*0.02,j*0.02)); i=j
    else: i+=1
speech_start=S[0][1] if S[0][0]==0 else 0
speech_end=S[-1][0]
words=open('script_es.txt').read().split()
def syl(wd):
    wd=wd.lower()
    if wd=='fc': return 2
    return max(1,len(re.findall(r'[aeiouáéíóúü]+',wd)))+0.3
wt=np.array([syl(x) for x in words])
brk=[k for k,wd in enumerate(words) if wd[-1] in ',.'][:-1]
strength={k:(2 if words[k][-1]=='.' else 1) for k in brk}
# DP: map each break to a silence (index) or none, monotonic; cost = rate variance
cands=[s for s in S if s[1]-s[0]>=0.08 and s[0]>speech_start and s[1]<speech_end]
# iterative snapping
times=None
cum=np.concatenate([[0],np.cumsum(wt)])
def place(anchors):
    # anchors: dict word_index_boundary -> (t_end_prev, t_start_next)
    pts=[(0,speech_start,speech_start)]+sorted((k+1,a,b) for k,(a,b) in anchors.items())+[(len(words),speech_end,speech_end)]
    st=np.zeros(len(words)); en=np.zeros(len(words))
    for (k0,_,t0),(k1,t1,_) in zip(pts[:-1],pts[1:]):
        tot=cum[k1]-cum[k0]
        for k in range(k0,k1):
            st[k]=t0+(t1-t0)*(cum[k]-cum[k0])/tot
            en[k]=t0+(t1-t0)*(cum[k+1]-cum[k0])/tot
    return st,en
anchors={}
used=set()
for it in range(6):
    st,en=place(anchors)
    new={}
    usedc=set()
    for k in brk:
        t=en[k]
        best=None;bd=9
        for ci,c in enumerate(cands):
            m=(c[0]+c[1])/2; d=abs(m-t)-0.15*(c[1]-c[0])
            if d<bd and ci not in usedc: bd=d;best=ci
        if best is not None and abs((cands[best][0]+cands[best][1])/2-t)<1.2:
            new[k]=cands[best]; usedc.add(best)
    # enforce monotonic
    ks=sorted(new); ok={};last=-1
    for k in ks:
        if new[k][0]>last: ok[k]=new[k]; last=new[k][1]
    anchors=ok
for k in brk:
    if words[k]=='pase,' and abs(en[k]-47.84)<0.3: anchors[k]=(48.56,48.84)
st,en=place(anchors)
out=[dict(w=words[k],s=round(st[k],3),e=round(en[k],3)) for k in range(len(words))]
json.dump(out,open('words.json','w'),ensure_ascii=False,indent=0)
unused=[c for c in cands if c not in anchors.values() and c[1]-c[0]>0.25]
print("breaks",len(brk),"anchored",len(anchors),"unused long silences",unused)
for k in brk: print(words[k], f"{en[k]:.2f}", anchors.get(k))
