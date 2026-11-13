import json,sys,difflib,re,unicodedata
sys.path.insert(0,sys.argv[1]+'/tools'); import remap
S=sys.argv[1]
import json as _j
_m=_j.load(open(f'{S}/es/cutmap.json'))['map']
def f(t):
    for a,b,n in _m:
        if t<=b+1e-6: return n+max(0,t-a) if t>=a else n
    a,b,n=_m[-1]; return n+t-a
script=["Este tiro libre de Arda Güler.",
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
tw=json.load(open(f'{S}/es/tr_santa/transcript.json'))
# split transcript into sentences
ST=json.load(open(f'{S}/es/santa.json'))
sents=[[x for x in tw if a['start']-0.1 <= (x['start']+x['end'])/2 < (ST[n+1]['start'] if n+1<len(ST) else 1e9)] for n,a in enumerate(ST)]
assert len(sents)==len(script),(len(sents),len(script))
norm=lambda s: unicodedata.normalize('NFD',s.lower()).encode('ascii','ignore').decode().strip(".,!?:;'\"")
out=[]
for si,(txt,tr) in enumerate(zip(script,sents)):
    sw=[w for w in txt.replace(' !','!').split()]
    a=[norm(w) for w in sw]; b=[norm(x['text']) for x in tr]
    T0,T1=f(tr[0]['start']),f(tr[-1]['end'])
    st=[None]*len(sw); en=[None]*len(sw)
    for blk in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            st[blk.a+k]=f(tr[blk.b+k]['start']); en[blk.a+k]=f(tr[blk.b+k]['end'])
    # fill gaps by char-length interpolation
    i=0
    while i<len(sw):
        if st[i] is None:
            j=i
            while j<len(sw) and st[j] is None: j+=1
            g0=en[i-1] if i>0 else T0; g1=st[j] if j<len(sw) else T1
            L=[len(w)+2 for w in sw[i:j]]; tot=sum(L); t=g0
            for k in range(i,j):
                d=(g1-g0)*L[k-i]/tot; st[k]=t; en[k]=t+d; t+=d
            i=j
        else: i+=1
    for k,w in enumerate(sw):
        out.append({'text':w,'start':round(st[k],3),'end':round(en[k],3),'sent':si})
json.dump(out,open(f'{S}/proj/words_es.json','w'),ensure_ascii=False,indent=0)
for s in range(len(script)):
    ws=[w for w in out if w['sent']==s]; print(s,ws[0]['start'],ws[-1]['end'],' '.join(f"{w['text']}@{w['start']:.2f}" for w in ws))
