import cv2,numpy as np,json,sys
d=sys.argv[1]; f0,f1=int(sys.argv[2]),int(sys.argv[3]); out=sys.argv[4]
res={}
prev=None
for f in range(f0,f1+1):
  im=cv2.imread(f'{d}/{f:04d}.jpg'); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
  m=cv2.inRange(hsv,(28,125,225),(38,255,255)); m=cv2.dilate(m,np.ones((3,3),np.uint8)); m[:250]=0; m[900:]=0
  n,l,st,c=cv2.connectedComponentsWithStats(m)
  cands=[]
  for i in range(1,n):
    x,y,w,h,a=st[i]
    if 8<=a<=160 and 0.4<w/h<2.5 and w<20 and h<20:
      # roundness / fill
      if a/(w*h)>0.45: cands.append((c[i][0],c[i][1],a))
  if not cands: continue
  if prev is not None:
    cands.sort(key=lambda p:(p[0]-prev[0])**2+(p[1]-prev[1])**2)
    if (cands[0][0]-prev[0])**2+(cands[0][1]-prev[1])**2>90**2 and len(cands)>0: 
      pass
  b=cands[0]; prev=b; res[f]=[round(b[0],1),round(b[1],1),int(b[2]),len(cands)]
json.dump(res,open(out,'w'))
