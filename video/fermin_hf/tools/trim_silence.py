import numpy as np, soundfile as sf, sys, json
x,sr=sf.read(sys.argv[1],dtype="float32")
if x.ndim>1: x=x.mean(1)
win=int(0.02*sr); n=len(x)//win
rms=np.array([np.sqrt(np.mean(x[i*win:(i+1)*win]**2)+1e-12) for i in range(n)])
db=20*np.log10(rms); sil=db< -38
# runs of silence
segs=[];i=0
while i<n:
    if sil[i]:
        j=i
        while j<n and sil[j]: j+=1
        segs.append((i,j)); i=j
    else: i+=1
keep=[];cur=0;removed=[]
for a,b in segs:
    dur=(b-a)*0.02
    if dur>0.12:
        s=a*win; e=b*win
        if a==0: cut_s, cut_e = 0, max(0,e-int(0.06*sr))   # leading: keep 0.06
        elif b==n: cut_s, cut_e = s+int(0.06*sr), len(x)
        else:
            half=int(0.03*sr); cut_s, cut_e = s+half, e-half
        if cut_e>cut_s: removed.append((cut_s,cut_e))
out=[];mp=[];pos=0;t_out=0
for cs,ce in removed:
    out.append(x[pos:cs]); mp.append((pos/sr,t_out)); t_out+= (cs-pos)/sr; pos=ce
out.append(x[pos:]); mp.append((pos/sr,t_out))
y=np.concatenate(out)
# 5 ms crossfade not needed at silence; write
sf.write(sys.argv[2],y,sr,subtype="PCM_24")
json.dump({"removed":[(a/sr,b/sr) for a,b in removed]},open(sys.argv[3],"w"))
print("in",len(x)/sr,"out",len(y)/sr,"cuts",len(removed))
