import json, difflib, re, unicodedata, sys
S=sys.argv[1]
d=json.load(open(f'{S}/src/transcript.json')); tw=d if isinstance(d,list) else d['words']
script=open(f'{S}/work/script_es.txt').read().split()
norm=lambda s: unicodedata.normalize('NFD',re.sub(r"[^\w]","",s.lower())).encode('ascii','ignore').decode()
A=[norm(w) for w in script]; B=[norm(w['text']) for w in tw]
# merge fix: 'yahi' -> 'y','ahi'
sm=difflib.SequenceMatcher(None,A,B,autojunk=False)
res=[None]*len(script)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal' or (i2-i1==j2-j1):
        for k in range(i2-i1): res[i1+k]=(tw[j1+k]['start'],tw[j1+k]['end'])
    elif j2>j1:
        t0,t1=tw[j1]['start'],tw[j2-1]['end']; n=i2-i1
        for k in range(n): res[i1+k]=(t0+(t1-t0)*k/n,t0+(t1-t0)*(k+1)/n)
        print('approx',tag,script[i1:i2],[tw[j]['text'] for j in range(j1,j2)])
for i,r in enumerate(res):
    if r is None:
        p=res[i-1]; res[i]=(p[1],p[1]+0.15); print('missing',script[i])
out=[{'text':w,'start':round(a,3),'end':round(b,3)} for w,(a,b) in zip(script,res)]
json.dump(out,open(f'{S}/work/words.json','w'),ensure_ascii=False,indent=0)
print(len(out), out[-1])
