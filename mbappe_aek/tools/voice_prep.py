# RMS 20 ms windows, -38 dB threshold; silences > 0.12 s -> 0.06 s; returns speech segments of the processed file
import numpy as np, subprocess, json, sys, wave
src, out = sys.argv[1], sys.argv[2]
sr=44100
raw=subprocess.run(["ffmpeg","-v","error","-i",src,"-f","f32le","-ac","1","-ar",str(sr),"-"],capture_output=True).stdout
x=np.frombuffer(raw,np.float32).copy()
win=int(.02*sr); n=len(x)//win
rms=np.sqrt((x[:n*win].reshape(n,win)**2).mean(1)+1e-12); db=20*np.log10(rms)
sil=db< -38
# runs
runs=[];i=0
while i<n:
    j=i
    while j<n and sil[j]==sil[i]: j+=1
    runs.append((sil[i],i,j)); i=j
pieces=[];segs=[];t=0.0
for s,a,b in runs:
    seg=x[a*win:b*win]
    if s and (b-a)*.02>0.12:
        keep=int(.03*sr)  # 30 ms each side = 60 ms total
        seg=np.concatenate([seg[:keep],seg[-keep:]])
    if not s: segs.append([round(t,3),round(t+len(seg)/sr,3)])
    pieces.append(seg); t+=len(seg)/sr
y=np.concatenate(pieces)
y=np.concatenate([y[n*win:] if False else y, x[n*win:]])
with wave.open(out,'wb') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr)
    w.writeframes((np.clip(y,-1,1)*32767).astype(np.int16).tobytes())
# merge segments separated by < 0.03 s? keep raw; report
json.dump(segs,open(out+'.segs.json','w'))
print(len(y)/sr, len(segs))
