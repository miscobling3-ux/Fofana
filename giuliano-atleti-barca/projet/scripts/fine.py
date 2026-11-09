import cv2,numpy as np,sys,json
# fine.py dir out "f:x:y,f:x:y,..." half=60 -> zoomed crops (4x) centered on approx points with 10px grid
d,out,spec=sys.argv[1],sys.argv[2],sys.argv[3]; hw=int(sys.argv[4]) if len(sys.argv)>4 else 50
ims=[]
for it in spec.split(','):
  f,x,y=map(int,it.split(':'))
  im=cv2.imread(f'{d}/{f:04d}.jpg')
  x0,y0=x-hw,y-hw; c=im[max(0,y0):y0+2*hw,max(0,x0):x0+2*hw]
  c=cv2.copyMakeBorder(c,0,2*hw-c.shape[0],0,2*hw-c.shape[1],cv2.BORDER_CONSTANT)
  s=400/(2*hw); c=cv2.resize(c,None,fx=s,fy=s,interpolation=cv2.INTER_CUBIC)
  for g in range((x0//10+1)*10,x0+2*hw,10):
    X=int((g-x0)*s); cv2.line(c,(X,0),(X,400),(255,255,255) if g%50==0 else (90,90,90),1)
    if g%50==0: cv2.putText(c,str(g),(X+2,395),0,0.4,(0,255,255),1)
  for g in range((y0//10+1)*10,y0+2*hw,10):
    Y=int((g-y0)*s); cv2.line(c,(0,Y),(400,Y),(255,255,255) if g%50==0 else (90,90,90),1)
    if g%50==0: cv2.putText(c,str(g),(2,Y-2),0,0.4,(0,255,255),1)
  cv2.putText(c,f'{d}{f}',(5,18),0,0.55,(0,255,255),2); ims.append(c)
while len(ims)%4: ims.append(np.zeros_like(ims[0]))
cv2.imwrite(out,np.vstack([np.hstack(ims[i:i+4]) for i in range(0,len(ims),4)]))
