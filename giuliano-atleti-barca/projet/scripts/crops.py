import cv2,numpy as np,sys
# usage: crops.py dir out x0 y0 w h f1 f2 ...
d,out=sys.argv[1],sys.argv[2]; x0,y0,w,h=map(int,sys.argv[3:7]); fr=list(map(int,sys.argv[7:]))
ims=[]
for f in fr:
  im=cv2.imread(f'{d}/{f:04d}.jpg')[y0:y0+h,x0:x0+w].copy()
  s=960/w; im=cv2.resize(im,None,fx=s,fy=s)
  cv2.putText(im,f'{f} t={(f-1)/50:.2f}',(8,30),0,0.9,(0,255,255),2); ims.append(im)
while len(ims)%2: ims.append(np.zeros_like(ims[0]))
cv2.imwrite(out,np.vstack([np.hstack(ims[i:i+2]) for i in range(0,len(ims),2)]))
