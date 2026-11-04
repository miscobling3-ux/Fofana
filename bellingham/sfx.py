# Bruitages synthétisés (Mixkit inaccessible depuis l'environnement) : whoosh x4, arrêt sur image, pop, frappe x3
import numpy as np, soundfile as sf
SR=48000; rng=np.random.default_rng(7); O='/home/user/Fofana/bellingham/hf/sfx/'
def env(n,a,d): t=np.arange(n)/SR; return np.minimum(1,t/a)*np.exp(-np.maximum(0,t-a)/d)
def bp(x,lo,hi):
    X=np.fft.rfft(x); f=np.fft.rfftfreq(len(x),1/SR); X[(f<lo)|(f>hi)]=0; return np.fft.irfft(X,len(x))
def norm(x,db=-6): return (x/np.max(np.abs(x))*10**(db/20)).astype(np.float32)
for i,(dur,lo,hi) in enumerate([(0.35,300,4000),(0.3,500,6000),(0.4,200,3000),(0.32,800,8000)]):
    n=int(dur*SR); t=np.arange(n)/SR; x=rng.standard_normal(n)
    sweep=np.sin(np.pi*t/dur)**2; x=bp(x,lo,hi)*sweep
    sf.write(O+f'whoosh{i+1}.wav',norm(x,-8),SR)
n=int(0.6*SR); t=np.arange(n)/SR
x=np.sin(2*np.pi*90*t)*env(n,0.002,0.12)+0.4*bp(rng.standard_normal(n),2000,9000)*env(n,0.001,0.05)
sf.write(O+'freeze.wav',norm(x,-6),SR)
n=int(0.15*SR); t=np.arange(n)/SR; f=600+900*np.exp(-t/0.02)
x=np.sin(2*np.pi*np.cumsum(f)/SR)*env(n,0.002,0.03); sf.write(O+'pop.wav',norm(x,-8),SR)
for i,(f0,d) in enumerate([(110,0.08),(140,0.06),(95,0.1)]):
    n=int(0.3*SR); t=np.arange(n)/SR
    x=np.sin(2*np.pi*f0*t*np.exp(-t/0.05))*env(n,0.001,d)+0.5*bp(rng.standard_normal(n),1000,6000)*env(n,0.0005,0.012)
    sf.write(O+f'kick{i+1}.wav',norm(x,-4),SR)
print('ok')
