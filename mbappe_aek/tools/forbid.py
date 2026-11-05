import json,numpy as np
wm=json.load(open("work/wm.json")); out={}
for clip in "AB":
    r=wm[clip]; n=len(r); rects=[]
    good=[(i,x) for i,(c,x,y,w,h) in enumerate(r) if c>0.5]
    for i in range(n):
        R=[[1500,0,1920,118]]                       # LIVE bug + grey bar, top right
        if clip=="B": R.append([0,0,630,112])        # TV score bug, top left
        # watermark: interpolate confident detections within 30 frames, else forbid whole band
        prev=[g for g in good if g[0]<=i]; nxt=[g for g in good if g[0]>=i]
        x=None
        if prev and nxt and nxt[0][0]-prev[-1][0]<=30:
            a,b=prev[-1],nxt[0]; t=0 if b[0]==a[0] else (i-a[0])/(b[0]-a[0]); x=a[1]+t*(b[1]-a[1])
            if abs(b[1]-a[1])>200: x=None
        if x is None: R.append([0,885,1920,960])
        else: R.append([int(x)-25,885,int(x)+335+25,960])
        rects.append(R)
    out[clip]=rects
json.dump(out,open("work/forbid.json","w"))
print({c:sum(1 for R in out[c] if any(r[0]==0 and r[1]==885 for r in R)) for c in out})
