import sys,json,numpy as np,soundfile as sf
from kokoro_onnx import Kokoro
S=sys.argv[1]; voice=sys.argv[2]; speed=float(sys.argv[3]); out=sys.argv[4]
SC=["Este tiro libre de Arda Güler.",
"Nunca verás a Lamine Yamal marcar uno igual en toda su carrera.",
"Todo empieza cuando Turquía consigue un tiro libre muy lejos del área.",
"En ese momento, vemos a tres jugadores turcos colocados junto al balón.",
"Uno podría pensar que preparan una jugada especial para engañar a la defensa y, sobre todo, sorprender al portero rival.",
"Pero lo que Arda Güler hace después es simplemente increíble.",
"Levanta la mano derecha, como para indicar a sus compañeros que va a mandar un centro hacia los jugadores situados en el área.",
"Ese gesto engaña por completo al portero, convencido de que Güler está preparando una jugada combinada o un centro clásico.",
"Y de repente, Arda Güler pilla a todo el mundo desprevenido.",
"En lugar de centrar, lanza el balón directamente al segundo palo.",
"El balón traza una trayectoria altísima, con una curva impresionante que sorprende por completo al portero.",
"Al principio cree que puede prepararse para el centro, pero se da cuenta demasiado tarde de que el balón va directo a su portería.",
"A pesar de su esfuerzo desesperado, no puede hacer nada.",
"El balón sigue su trayectoria y termina en el fondo de la red.",
"¡Qué tiro libre tan excepcional de Arda Güler!"]
k=Kokoro(f'{S}/kokoro/kokoro-v1.0.onnx',f'{S}/kokoro/voices-v1.0.bin')
parts=[];sents=[];t=0
for i,s in enumerate(SC):
    a,sr=k.create(s.replace('Güler','Guiler').replace('Lamine','Lamín'),voice=voice,speed=speed,lang='es')
    nz=np.where(np.abs(a)>0.01)[0]; a=a[max(0,nz[0]-240):nz[-1]+480]
    sents.append(dict(i=i,text=s,start=round(t,3),end=round(t+len(a)/sr,3))); parts.append(a); t+=len(a)/sr
    gap=0.22 if i<len(SC)-1 else 0.3
    parts.append(np.zeros(int(sr*gap),np.float32)); t+=gap
y=np.concatenate(parts); sf.write(out,y,sr)
json.dump(sents,open(out.replace('.wav','.json'),'w'),ensure_ascii=False)
print(voice,speed,'dur',round(len(y)/sr,2))
