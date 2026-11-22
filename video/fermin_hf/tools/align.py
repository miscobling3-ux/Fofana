import json,difflib,re,sys,unicodedata
def norm(w):
    w=unicodedata.normalize("NFD",w.lower()); w="".join(c for c in w if unicodedata.category(c)!="Mn")
    return re.sub(r"[^a-z0-9]","",w)
script=open(sys.argv[1]).read().strip().split("\n")
tr=json.load(open(sys.argv[2]))
sw=[];sent=[]
for si,line in enumerate(script):
    for w in line.split(): sw.append(w); sent.append(si)
# expand transcript tokens; map numerals
num={"1":"uno","2":"dos"}
tt=[]
for t in tr:
    n=norm(t["text"]); n=num.get(n,n); tt.append(n)
sn=[norm(w) for w in sw]
# fix "la min yamal" variants: let difflib handle on char-level fallback
sm=difflib.SequenceMatcher(None,sn,tt,autojunk=False)
res=[None]*len(sw)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=="equal":
        for k in range(i2-i1): res[i1+k]=(tr[j1+k]["start"],tr[j1+k]["end"])
    elif j2>j1:
        a=tr[j1]["start"]; b=tr[j2-1]["end"]; n=i2-i1
        L=[len(sn[i]) or 1 for i in range(i1,i2)]; tot=sum(L); t=a
        for k,i in enumerate(range(i1,i2)):
            d=(b-a)*L[k]/tot; res[i]=(t,t+d); t+=d
        print("REPLACE",sw[i1:i2],"<-",[tr[j]["text"] for j in range(j1,j2)])
# fill None by interpolation
for i in range(len(res)):
    if res[i] is None:
        p=res[i-1][1]; q=next(res[j][0] for j in range(i+1,len(res)) if res[j])
        res[i]=(p,q); print("FILL",sw[i])
out=[{"i":i,"text":sw[i],"sent":sent[i],"start":round(res[i][0],3),"end":round(res[i][1],3)} for i in range(len(sw))]
json.dump(out,open(sys.argv[3],"w"),ensure_ascii=False,indent=1)
for s in range(len(script)):
    ws=[o for o in out if o["sent"]==s]; print(s,ws[0]["start"],ws[-1]["end"],script[s][:50])
