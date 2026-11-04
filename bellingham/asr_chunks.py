# Segments séparés par des silences (RMS 20 ms, -38 dB) + transcription Whisper de chaque segment
import sys, json, numpy as np, soundfile as sf, sherpa_onnx, scipy.signal as ss
D='/home/user/Fofana/video/models/sherpa-onnx-whisper-small'
r=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f'{D}/small-encoder.int8.onnx',decoder=f'{D}/small-decoder.int8.onnx',tokens=f'{D}/small-tokens.txt',language='es',task='transcribe')
x,sr=sf.read(sys.argv[1]); x=x.mean(1) if x.ndim>1 else x
W=int(0.02*sr); n=len(x)//W
db=np.array([20*np.log10(np.sqrt(np.mean(x[i*W:(i+1)*W]**2))+1e-9) for i in range(n)])
sil=db<-38
segs=[];i=0
while i<n:
    if not sil[i]:
        j=i
        while j<n and not sil[j]: j+=1
        segs.append([i*0.02,j*0.02]); i=j
    else: i+=1
# fusionne les segments séparés par < 0,12 s
m=[]
for a,b in segs:
    if m and a-m[-1][1]<0.12: m[-1][1]=b
    else: m.append([a,b])
out=[]
for a,b in m:
    seg=x[int(a*sr):int(b*sr)]
    if b-a<0.15: continue
    y=ss.resample_poly(seg,16000,sr).astype(np.float32)
    s=r.create_stream(); s.accept_waveform(16000,np.concatenate([np.zeros(1600,np.float32),y,np.zeros(1600,np.float32)])); r.decode_stream(s)
    out.append(dict(start=round(a,3),end=round(b,3),text=s.result.text.strip())); print(f'{a:6.2f}-{b:6.2f} {s.result.text.strip()}')
json.dump(dict(segments=out,duration=len(x)/sr),open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
