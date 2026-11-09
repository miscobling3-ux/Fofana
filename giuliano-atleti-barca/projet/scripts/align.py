import numpy as np,subprocess,re,json,sys
TEXT="""Este gol del Atlético de Madrid de hoy, demuestra claramente por qué la defensa del Barcelona tiene una enorme debilidad, y por qué va a encajar muchos goles esta temporada. Todo comienza cuando Marcos Llorente realiza un pase en profundidad hacia Kang-in Lee por la banda. Lee controla el balón y comienza a avanzar aprovechando los espacios en una situación de contraataque. A medida que sigue progresando, levanta la cabeza y observa cómo Julián Álvarez se desmarca a la espalda de la defensa. Sin pensarlo dos veces, Kang-in Lee ejecuta un espectacular pase de trivela hacia Álvarez, quien controla el balón y se encuentra frente a frente con un defensor. En ese momento, todo el mundo pensaba que iba a realizar un pase, ya fuera hacia Grimaldo o hacia Kang-in Lee, que se encontraban fuera del área. Pero Julián Álvarez descarta esas opciones y decide encarar directamente al defensor. Levanta la cabeza y descubre que Giuliano Simeone está completamente solo, sin ningún defensa que lo esté marcando. Entonces, le envía un pase espectacular, perfectamente ajustado, y Simeone solo tiene que rematar de primeras, sin necesidad de controlar el balón, para mandarlo directamente al fondo de la red."""
words=TEXT.split()
def syl(w):
    w=w.lower().replace('kang-in','kanguin')
    w=re.sub(r'[^a-záéíóúüñ]','',w)
    n=len(re.findall(r'[aeiouáéíóúü]+',w))
    # hiatus approx: strong-strong vowels
    n+=len(re.findall(r'(?<=[aeo])[aeo]|í[aeo]|[aeo]í|ú[aeo]',w))
    return max(1,n)
S=np.array([syl(w) for w in words],float)
P=np.array([2 if w.endswith('.') else 1 if w.endswith(',') else 0 for w in words])
a=np.frombuffer(subprocess.run(['ffmpeg','-v','error','-i',sys.argv[1],'-ar','16000','-ac','1','-f','s16le','-'],capture_output=True).stdout,np.int16).astype(float)/32768
w=320;n=len(a)//w;db=20*np.log10(np.sqrt((a[:n*w].reshape(n,w)**2).mean(1)+1e-12))
sp=db>-38;segs=[];s=None
for i,v in enumerate(sp):
  if v and s is None:s=i
  if not v and s is not None: segs.append([s,i]);s=None
if s is not None: segs.append([s,n])
m=[segs[0]]
for x in segs[1:]:
  if (x[0]-m[-1][1])*0.02<0.12: m[-1][1]=x[1]
  else: m.append(x)
segs=[(x[0]*.02,x[1]*.02) for x in m]
G=len(segs); N=len(words)
rate=S.sum()/sum(e-b for b,e in segs)
cs=np.concatenate([[0],np.cumsum(S)])
INF=1e18
# dp[g][j]: first g segments cover words[:j]
dp=np.full((G+1,N+1),INF);bk=np.zeros((G+1,N+1),int);dp[0][0]=0
for g in range(1,G+1):
  b,e=segs[g-1];d=e-b
  for j in range(1,N+1):
    best=INF;bi=0
    for i in range(max(0,j-40),j):
      if dp[g-1][i]>=INF:continue
      r=(cs[j]-cs[i])/d
      c=dp[g-1][i]+ (np.log(r/rate))**2*10*(cs[j]-cs[i])/4
      if g<G: c+= {2:0,1:0.3,0:6}[P[j-1]]
      if c<best:best=c;bi=i
    dp[g][j]=best;bk[g][j]=bi
j=N;bounds=[]
for g in range(G,0,-1): i=bk[g][j];bounds.append((i,j));j=i
bounds=bounds[::-1]
out=[]
for (i,j),(b,e) in zip(bounds,segs):
  tot=cs[j]-cs[i];t=b
  print(f"{b:6.2f}-{e:6.2f}",' '.join(words[i:j]))
  for k in range(i,j):
    dd=(e-b)*S[k]/tot; out.append({"text":words[k],"start":round(t,3),"end":round(t+dd,3)}); t+=dd
json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False,indent=0)
print(len(out),'words')
