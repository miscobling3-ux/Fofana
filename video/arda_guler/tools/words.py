import json,sys,difflib,re,unicodedata
sys.path.insert(0,sys.argv[1]+'/tools'); from remap import loadmap
S=sys.argv[1]; f=loadmap(S)
script=["Ce coup franc d'Arda Güler.",
"Vous ne verrez jamais Lamine Yamal marquer un coup pareil dans toute sa carrière.",
"Tout commence quand la Turquie obtient un coup franc très loin de la surface.",
"À ce moment, on voit trois joueurs turcs placés près du ballon.",
"On pourrait penser qu'ils préparent une combinaison spéciale pour tromper la défense et surtout surprendre le gardien adverse.",
"Mais ce que Arda Güler fait ensuite est simplement incroyable.",
"Il lève la main droite, comme pour indiquer à ses coéquipiers qu'il va envoyer un centre vers les joueurs situés dans la surface.",
"Ce geste trompe complètement le gardien, convaincu que Güler est en train de préparer une combinaison ou un centre classique.",
"Et soudain, Arda Güler prend tout le monde au dépourvu.",
"Au lieu de centrer, il envoie le ballon directement vers le second poteau.",
"Le ballon trace alors une trajectoire absolument élevée, avec une courbe impressionnante qui surprend complètement le gardien.",
"Il croit d'abord qu'il peut se préparer pour le centre, mais il se rend compte trop tard que le ballon file directement vers sa cage.",
"Malgré son effort désespéré, il ne peut rien faire.",
"Le ballon continue sa trajectoire et termine au fond des filets.",
"Quel coup franc exceptionnel d'Arda Güler !"]
tw=json.load(open(f'{S}/vo/transcript.json'))
# split transcript into sentences
sents=[];cur=[]
for x in tw:
    cur.append(x)
    if x['text'][-1] in '.!?': sents.append(cur);cur=[]
if cur: sents[-1]+=cur
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
json.dump(out,open(f'{S}/proj/words.json','w'),ensure_ascii=False,indent=0)
for s in range(len(script)):
    ws=[w for w in out if w['sent']==s]; print(s,ws[0]['start'],ws[-1]['end'],' '.join(f"{w['text']}@{w['start']:.2f}" for w in ws))
