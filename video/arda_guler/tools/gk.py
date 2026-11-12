import cv2,numpy as np,sys,json
# gk.py P clip s e x y out  -> bbox per frame of GK (green shirt component near prev)
P,clip=sys.argv[1],sys.argv[2]; s,e=int(sys.argv[3]),int(sys.argv[4]); x,y=int(sys.argv[5]),int(sys.argv[6]); out=sys.argv[7]
res=json.load(open(out)) if len(sys.argv)>8 else {}
for k in range(s,e+1):
    im=cv2.imread(f'{P}/frames/{clip}/{k:04d}.jpg'); h=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
    m=((h[...,0]>=62)&(h[...,0]<=92)&(h[...,1]>=60)&(h[...,2]>=60)).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8)); m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
    n,l,st,c=cv2.connectedComponentsWithStats(m)
    best=None;bd=1e9
    for i in range(1,n):
        if st[i,4]<120: continue
        cx,cy=c[i]; d=np.hypot(cx-x,cy-y)-np.sqrt(st[i,4])
        if d<bd: bd=d;best=i
    if best is None: res[str(k)]=None; continue
    # merge components within 80px of best bbox
    bx,by,bw,bh,_=st[best]; X0,Y0,X1,Y1=bx,by,bx+bw,by+bh
    for i in range(1,n):
        if st[i,4]<60 or i==best: continue
        ix,iy,iw,ih,_=st[i]
        if ix<X1+60 and ix+iw>X0-60 and iy<Y1+60 and iy+ih>Y0-60: X0,Y0,X1,Y1=min(X0,ix),min(Y0,iy),max(X1,ix+iw),max(Y1,iy+ih)
    res[str(k)]=[int(X0),int(Y0),int(X1),int(Y1)]; x,y=(X0+X1)/2,(Y0+Y1)/2
json.dump(res,open(out,'w'))
