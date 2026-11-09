import cv2,numpy as np,sys
# grid.py dir out x0 y0 w h cols f...  -> crops with 50px grid labeled in source coords
d,out=sys.argv[1],sys.argv[2]; x0,y0,w,h,cols=map(int,sys.argv[3:8]); fr=list(map(int,sys.argv[8:]))
ims=[]
for f in fr:
  im=cv2.imread(f'{d}/{f:04d}.jpg')[y0:y0+h,x0:x0+w].copy()
  s=min(2.0,(1900/cols)/w); im=cv2.resize(im,None,fx=s,fy=s,interpolation=cv2.INTER_CUBIC)
  for gx in range((x0//50+1)*50,x0+w,50):
    X=int((gx-x0)*s); cv2.line(im,(X,0),(X,im.shape[0]),(255,255,255) if gx%100==0 else (120,120,120),1)
    if gx%100==0: cv2.putText(im,str(gx),(X+2,im.shape[0]-5),0,0.45,(255,255,0),1)
  for gy in range((y0//50+1)*50,y0+h,50):
    Y=int((gy-y0)*s); cv2.line(im,(0,Y),(im.shape[1],Y),(255,255,255) if gy%100==0 else (120,120,120),1)
    if gy%100==0: cv2.putText(im,str(gy),(2,Y-2),0,0.45,(255,255,0),1)
  cv2.putText(im,f'{d}{f} t={(f-1)/50:.2f}',(8,22),0,0.7,(0,255,255),2); ims.append(im)
while len(ims)%cols: ims.append(np.zeros_like(ims[0]))
cv2.imwrite(out,np.vstack([np.hstack(ims[i:i+cols]) for i in range(0,len(ims),cols)]))
