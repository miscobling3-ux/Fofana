import numpy as np, wave, sys
SR=48000; out=sys.argv[1]
rng=np.random.default_rng(7)
def save(name,x):
    x=x/ (np.abs(x).max()+1e-9) * 0.8
    st=np.stack([x,x],1)
    w=wave.open(f'{out}/{name}.wav','wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st*32767).astype(np.int16).tobytes()); w.close()
def bp(x,lo,hi):
    X=np.fft.rfft(x); f=np.fft.rfftfreq(len(x),1/SR); X[(f<lo)|(f>hi)]=0; return np.fft.irfft(X,len(x))
def whoosh(seed,dur=0.42,lo=300,hi=4000):
    n=int(SR*dur); t=np.arange(n)/SR
    noise=np.random.default_rng(seed).standard_normal(n)
    # sweep: sum of bands with moving envelope
    y=np.zeros(n)
    bands=np.geomspace(lo,hi,9)
    for i in range(8):
        b=bp(noise,bands[i],bands[i+1])
        c=(i+0.5)/8
        env=np.exp(-((t/dur-c*0.8-0.1)**2)/(2*0.12**2))
        y+=b*env
    env=np.sin(np.pi*np.clip(t/dur,0,1))**1.5
    return y*env
for i,s in enumerate([1,2,3,4]): save(f'w{i+1}',whoosh(s,lo=250+60*i,hi=3500+300*i))
# freeze: low thump + reversed shimmer tail
n=int(SR*0.7); t=np.arange(n)/SR
thump=np.sin(2*np.pi*(70+60*np.exp(-t*25))*t)*np.exp(-t*7)
shim=bp(rng.standard_normal(n),3000,9000)*np.exp(-t*9)*0.35
save('freeze',thump+shim)
# pop
n=int(SR*0.16); t=np.arange(n)/SR
f=900*np.exp(-t*12)+380
pop=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t*30)*(1-np.exp(-t*800))
save('pop',pop)
# kick (ball contact)
n=int(SR*0.25); t=np.arange(n)/SR
k=np.sin(2*np.pi*(95+140*np.exp(-t*40))*t)*np.exp(-t*22)+bp(rng.standard_normal(n),1500,6000)*np.exp(-t*90)*0.6
save('kick',k)
n=int(SR*0.45); t=np.arange(n)/SR
k=np.sin(2*np.pi*(80+200*np.exp(-t*35))*t)*np.exp(-t*12)+bp(rng.standard_normal(n),1200,7000)*np.exp(-t*60)*0.8
save('shot',k)
print('ok')
