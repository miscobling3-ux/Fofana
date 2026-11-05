# Synthesized SFX (Mixkit host blocked by the session network): whoosh, freeze hit, pop, ball kick
import numpy as np,wave
sr=44100; rng=np.random.default_rng(7)
def save(n,y):
    y=y/np.max(np.abs(y))*0.7
    with wave.open(f"hf/assets/sfx/{n}.wav","wb") as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((y*32767).astype(np.int16).tobytes())
def lp(x,a):
    y=np.zeros_like(x);s=0
    for i,v in enumerate(x): s+=a*(v-s); y[i]=s
    return y
for k,(d,f0,f1) in enumerate([(.32,.04,.35),(.30,.06,.45),(.34,.03,.30),(.28,.05,.40)]):
    n=int(d*sr);t=np.arange(n)/sr;x=rng.standard_normal(n)
    a=np.interp(t,[0,d],[f0,f1]); y=np.zeros(n);s=0
    for i in range(n): s+=a[i]*(x[i]-s); y[i]=s
    env=np.sin(np.pi*t/d)**2; save(f"whoosh{k+1}",y*env)
n=int(.45*sr);t=np.arange(n)/sr
save("freeze",np.sin(2*np.pi*(90*t-40*t*t))*np.exp(-t*9)+0.35*rng.standard_normal(n)*np.exp(-t*60))
n=int(.12*sr);t=np.arange(n)/sr
save("pop",np.sin(2*np.pi*(520*t+2200*t*t))*np.exp(-t*38))
for k,f in enumerate([140,120,160]):
    n=int(.18*sr);t=np.arange(n)/sr
    save(f"kick{k+1}",np.sin(2*np.pi*f*t*np.exp(-t*6))*np.exp(-t*22)+0.5*lp(rng.standard_normal(n),.5)*np.exp(-t*120))
