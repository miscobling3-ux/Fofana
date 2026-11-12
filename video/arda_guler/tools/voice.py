import wave,numpy as np,json,sys
S=sys.argv[1]
w=wave.open(f'{S}/vo/vo48.wav');sr=w.getframerate();x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
n=int(sr*0.02);nw=len(x)//n
r=np.array([20*np.log10(np.sqrt(np.mean(x[i*n:(i+1)*n]**2))+1e-9) for i in range(nw)])
sil=[];s=None
for i,v in enumerate(list(r)+[0]):
    if v<-38: s=i if s is None else s
    else:
        if s is not None and (i-s)*0.02>0.12: sil.append((s*0.02,i*0.02))
        s=None
# keep 0.03s on each side
segs=[];cur=0.0;cmap=[]  # cmap: (orig_start, orig_end, new_start)
out=[];t_new=0.0
for a,b in sil:
    ka,kb=a+0.03,b-0.03
    out.append(x[int(cur*sr):int(ka*sr)]); cmap.append((cur,ka,t_new)); t_new+=ka-cur; cur=kb
out.append(x[int(cur*sr):]); cmap.append((cur,len(x)/sr,t_new)); t_new+=len(x)/sr-cur
y=np.concatenate(out)
json.dump({'map':cmap,'dur':len(y)/sr},open(f'{S}/vo/cutmap.json','w'))
wo=wave.open(f'{S}/vo/vo_cut.wav','wb');wo.setnchannels(1);wo.setsampwidth(2);wo.setframerate(sr);wo.writeframes((np.clip(y,-1,1)*32767).astype(np.int16).tobytes())
print('new dur',len(y)/sr)
