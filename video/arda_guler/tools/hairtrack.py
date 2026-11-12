import cv2,numpy as np,sys,json
P,clip,trk=sys.argv[1],sys.argv[2],sys.argv[3]; s,e=int(sys.argv[4]),int(sys.argv[5])
d=json.load(open(trk)); x,y=d[str(s)][:2]
for k in range(s,e+1):
    im=cv2.imread(f'{P}/frames/{clip}/{k:04d}.jpg'); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
    x0,y0=max(0,x-80),max(0,y-50); win=hsv[y0:y+90,x0:x+80]
    m=((win[...,2]<95)&~((win[...,0]>=30)&(win[...,0]<=90)&(win[...,1]>60)&(win[...,2]>60))).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    n,l,st,c=cv2.connectedComponentsWithStats(m)
    if n<=1: d[str(k)]=[x,y,'h?'];continue
    # choose component closest to previous head point with area>150
    best=None;bd=1e9
    for i in range(1,n):
        if st[i,4]<150: continue
        ty=st[i,1]; ys,xs=np.where(l[:ty+12-0,:]==i) if False else np.where(l==i)
        top=ys.min(); xt=xs[ys<top+12].mean()
        dd=abs(x0+xt-x)+abs(y0+top-y)
        if dd<bd: bd=dd;best=(int(x0+xt),int(y0+top))
    if best: x,y=best
    d[str(k)]=[x,y,'h']
json.dump(d,open(trk,'w'))
