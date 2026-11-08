# Synthesized sound effects (Mixkit host is blocked in this environment).
import numpy as np, wave, os, sys
SR=48000; out=sys.argv[1]; os.makedirs(out,exist_ok=True)
rng=np.random.default_rng(3)
def save(n,x):
    x=x/ (np.abs(x).max()+1e-9)*0.89
    with wave.open(f"{out}/{n}.wav","wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes((x*32767).astype(np.int16).tobytes())
def t(d): return np.arange(int(SR*d))/SR
def lp(x,a):  # one-pole lowpass, a in (0,1)
    y=np.zeros_like(x); s=0
    for i,v in enumerate(x): s+=a*(v-s); y[i]=s
    return y
# whoosh: band-swept noise 0.42s
d=0.42; tt=t(d); n=rng.standard_normal(len(tt))
env=np.sin(np.pi*np.clip(tt/d,0,1))**2
sw=np.zeros_like(n); s=0; s2=0
for i,v in enumerate(n):
    a=0.02+0.25*(i/len(n)); s+=a*(v-s); s2+=a*(s-s2); sw[i]=s-s2*0.6
save("whoosh1",sw*env)
sw2=sw[::-1].copy(); save("whoosh2",sw2*env)
# freeze: camera shutter click + short high tone
d=0.35; tt=t(d); cl=rng.standard_normal(len(tt))*np.exp(-tt*90)
tone=np.sin(2*np.pi*1800*tt)*np.exp(-tt*14)*0.35
save("freeze",cl+tone+np.roll(cl,int(0.045*SR))*0.6)
# pop: pitch-dropping sine blip
d=0.14; tt=t(d); f=900*np.exp(-tt*18)+300
ph=2*np.pi*np.cumsum(f)/SR; save("pop",np.sin(ph)*np.exp(-tt*28))
# kick (ball strike): low thump + leather click
d=0.32; tt=t(d); f=140*np.exp(-tt*25)+48
ph=2*np.pi*np.cumsum(f)/SR; th=np.sin(ph)*np.exp(-tt*11)
ck=lp(rng.standard_normal(len(tt)),0.5)*np.exp(-tt*160)*0.8
save("kick",th+ck)
print("ok")
