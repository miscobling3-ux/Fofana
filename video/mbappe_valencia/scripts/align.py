import numpy as np, subprocess, re, json, sys
wd=sys.argv[1]
x=np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i",wd+"/voice.mp3","-ac","1","-ar","16000","-f","s16le","-"],capture_output=True).stdout,np.int16).astype(float)/32768
w=320; n=len(x)//w; r=np.sqrt((x[:n*w].reshape(n,w)**2).mean(1)+1e-12); db=20*np.log10(r)
sil=db<-38
pauses=[];i=0
while i<n:
    if sil[i]:
        j=i
        while j<n and sil[j]: j+=1
        pauses.append((i*0.02,j*0.02)); i=j
    else: i+=1
start=pauses[0][1] if pauses[0][0]==0 else 0
end=pauses[-1][0] if pauses[-1][1]>=n*0.02-0.03 else n*0.02
P=[p for p in pauses if p[0]>start and p[1]<end and p[1]-p[0]>=0.10]
words=open(wd+"/script_es.txt").read().split()
def syl(wd):
    wd=wd.lower(); g=re.findall(r"[aeiouáéíóúü]+",wd)
    c=0
    for s in g:
        # hiatus with strong vowels
        c+=1+len(re.findall(r"[aeoáéó](?=[aeoáéó])",s))+len(re.findall(r"[íú]",s))*(len(s)>1)
    return max(c,1)
S=np.cumsum([0]+[syl(wd)+0.35 for wd in words])  # boundary k = before word k
punct=[False]+[bool(re.search(r"[,.;:?!]$",wd)) for wd in words[:-1]]+[False]
# speech time mapping
def speech_before(t):
    s=t-start
    for a,b in P:
        if b<=t: s-=(b-a)
        elif a<t: s-=(t-a)
    return s
T=speech_before(end)
exp=S/S[-1]*T
K=len(words)
# DP: pauses in order to boundaries 1..K-1, or skipped
INF=1e18
m=len(P)
sp=[speech_before(a) for a,b in P]
dp=np.full((m+1,K+1),INF); bk={}
dp[0,0]=0
for pi in range(m+1):
    for k in range(K+1):
        if dp[pi,k]>=INF: continue
        if pi==m: continue
        # skip pause
        c=dp[pi,k]+3.0
        if c<dp[pi+1,k]: dp[pi+1,k]=c; bk[(pi+1,k)]=(pi,k,None)
        for k2 in range(k+1,K):
            c=dp[pi,k]+((exp[k2]-sp[pi])/0.6)**2+(0 if punct[k2] else 2.5)
            if c<dp[pi+1,k2]: dp[pi+1,k2]=c; bk[(pi+1,k2)]=(pi,k,k2)
kbest=int(np.argmin(dp[m])); assign={}
pi,k=m,kbest
while pi>0:
    a,b,k2=bk[(pi,k)]
    if k2 is not None: assign[k2]=P[pi-1]
    pi,k=a,b
# anchors: boundary k -> (end of prev word, start of next)
anchors=[(0,start,start)]+sorted((k,a,b) for k,(a,b) in assign.items())+[(K,end,end)]
out=[]
for (k0,_,t0),(k1,t1,_) in zip(anchors,anchors[1:]):
    seg=S[k0:k1+1]-S[k0]; tot=seg[-1]
    for j in range(k0,k1):
        s=t0+(t1-t0)*seg[j-k0]/tot; e=t0+(t1-t0)*(seg[j-k0+1]-0.35*0.5)/tot
        out.append({"word":words[j],"start":round(s,3),"end":round(e,3)})
json.dump(out,open(wd+"/words.json","w"),ensure_ascii=False,indent=0)
print("unassigned pauses:",[p for i,p in enumerate(P) if p not in assign.values()])
line="";
for o in out:
    line+=f"{o['word']}[{o['start']:.2f}] "
    if re.search(r"[.]$",o['word']): print(line); line=""
print(line)
