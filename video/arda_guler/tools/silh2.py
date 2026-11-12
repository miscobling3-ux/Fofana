import cv2,numpy as np,sys,json
# Güler seul : pixels non pelouse reliés à la tête, limités à une bande autour de la tête
P,clip,trk,s,e,out,band=sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4]),int(sys.argv[5]),sys.argv[6],int(sys.argv[7])
d=json.load(open(trk)); res={}
for k in range(s,e+1):
    hx,hy=d[str(k)][:2]; im=cv2.imread(f'{P}/frames/{clip}/{k:04d}.jpg'); h=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
    g=(h[...,0]>=30)&(h[...,0]<=90)&(h[...,1]>=50)&(h[...,2]>=60)
    m=(~g).astype(np.uint8); X0,X1=max(0,hx-band),min(1920,hx+band); Y0,Y1=max(0,hy-160),min(1080,hy+640)
    w=np.zeros_like(m); w[Y0:Y1,X0:X1]=m[Y0:Y1,X0:X1]; w=cv2.morphologyEx(w,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
    n,l,st,c=cv2.connectedComponentsWithStats(w); lab=l[min(1079,hy+15),hx]
    x,y,ww,hh,_=st[lab]; res[str(k)]=[int(x),int(y),int(x+ww),int(y+hh)]
json.dump(res,open(out,'w'))
