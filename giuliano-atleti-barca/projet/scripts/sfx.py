import numpy as np,wave,sys
SR=48000
rng=np.random.default_rng(7)
def save(name,x):
    x=x/ (np.abs(x).max()+1e-9)*0.7
    d=(np.clip(x,-1,1)*32767).astype(np.int16)
    w=wave.open(f'{sys.argv[1]}/{name}.wav','wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(d.tobytes()); w.close()
def env(n,a,r):
    t=np.arange(n)/SR; e=np.minimum(t/a,1)*np.exp(-np.maximum(t-a,0)/r); return e
def lp(x,c):
    y=np.zeros_like(x); k=c
    for i in range(1,len(x)): y[i]=y[i-1]+k*(x[i]-y[i-1])
    return y
# whooshes (4 variants)
for i,(dur,f0,f1) in enumerate([(0.38,0.02,0.25),(0.32,0.03,0.3),(0.42,0.015,0.2),(0.30,0.04,0.35)]):
    n=int(SR*dur); t=np.arange(n)/n
    noise=rng.standard_normal(n)
    k=f0+(f1-f0)*np.sin(np.pi*t)  # sweep up/down
    y=np.zeros(n)
    for j in range(1,n): y[j]=y[j-1]+k[j]*(noise[j]-y[j-1])
    e=np.sin(np.pi*t)**1.5
    save(f'whoosh{i+1}',y*e)
# freeze: shutter click + short low hit
n=int(SR*0.45); t=np.arange(n)/SR
click=rng.standard_normal(n)*np.exp(-t/0.006)
click2=np.roll(rng.standard_normal(n)*np.exp(-t/0.005),int(0.05*SR))
boom=np.sin(2*np.pi*(90*t-40*t**2))*np.exp(-t/0.12)
save('freeze',0.6*click+0.4*click2+0.9*boom)
# pop
n=int(SR*0.12); t=np.arange(n)/SR
f=900*np.exp(-t/0.03)+500; ph=2*np.pi*np.cumsum(f)/SR
save('pop',np.sin(ph)*np.exp(-t/0.03)*np.minimum(t/0.002,1))
# kicks (3 variants)
for i,(f0,dec) in enumerate([(150,0.06),(130,0.08),(170,0.05)]):
    n=int(SR*0.25); t=np.arange(n)/SR
    f=f0*np.exp(-t/0.04)+55; ph=2*np.pi*np.cumsum(f)/SR
    body=np.sin(ph)*np.exp(-t/dec)
    tr=lp(rng.standard_normal(n),0.5)*np.exp(-t/0.004)
    save(f'kick{i+1}',body+0.5*tr)
print('ok')
