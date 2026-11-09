import cv2,numpy as np,glob,json
res={}
for d in ['fA','fB']:
    fs=sorted(glob.glob(d+'/*.jpg')); out=[]; prev=None
    for f in fs:
        im=cv2.imread(f); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
        m=((hsv[...,0]>=25)&(hsv[...,0]<=42)&(hsv[...,1]>110)&(hsv[...,2]>170)).astype(np.uint8)
        m[:180]=0; m[880:]=0
        n,lab,st,cen=cv2.connectedComponentsWithStats(m)
        best=None;bs=-1e9
        for i in range(1,n):
            x,y,w,h,a=st[i]
            if a<12 or a>12000: continue
            fill=a/(w*h); asp=min(w,h)/max(w,h)
            if fill<0.45 or asp<0.5: continue
            sc=a*fill*asp
            if prev is not None: sc-=0.5*np.hypot(cen[i][0]-prev[0],cen[i][1]-prev[1])
            if sc>bs: bs=sc;best=(float(cen[i][0]),float(cen[i][1]),int(a))
        out.append(best)
        if best: prev=best
    res[d]=out
    print(d,sum(1 for o in out if o),len(out))
json.dump(res,open('ball.json','w'))
