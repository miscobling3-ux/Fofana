import cv2,numpy as np,json,sys
d=sys.argv[1]; f0,f1=int(sys.argv[2]),int(sys.argv[3]); seed=tuple(map(float,sys.argv[4].split(','))); out=sys.argv[5]
gate=float(sys.argv[6]) if len(sys.argv)>6 else 45
res={}; prev=np.array(seed); vel=np.zeros(2); miss=0
for f in range(f0,f1+1):
  im=cv2.imread(f'{d}/{f:04d}.jpg'); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
  m=cv2.inRange(hsv,(28,120,215),(38,255,255)); m=cv2.dilate(m,np.ones((3,3),np.uint8)); m[:295]=0; m[:,:5]=0
  n,l,st,c=cv2.connectedComponentsWithStats(m)
  pred=prev+vel
  best=None;bd=1e9
  for i in range(1,n):
    x,y,w,h,a=st[i]
    if 6<=a<=200 and w<22 and h<22:
      dd=np.hypot(*(c[i]-pred))
      if dd<bd: bd=dd;best=c[i]
  if best is not None and bd<gate*(1+miss):
    vel=0.6*vel+0.4*(best-prev); prev=best; miss=0; res[f]=[round(best[0],1),round(best[1],1)]
  else:
    miss+=1; prev=pred
json.dump(res,open(out,'w'))
