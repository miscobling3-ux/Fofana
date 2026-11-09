import cv2,sys
# usage: grid.py out.jpg x0 y0 x1 y1 scale frame1 [frame2..]
out=sys.argv[1]; x0,y0,x1,y1=map(int,sys.argv[2:6]); sc=float(sys.argv[6]); fs=sys.argv[7:]
import numpy as np
ims=[]
for f in fs:
    im=cv2.imread(f)[y0:y1,x0:x1].copy()
    for x in range((x0//50+1)*50,x1,50): cv2.line(im,(x-x0,0),(x-x0,y1-y0),(0,255,255) if x%100==0 else (0,120,120),1)
    for y in range((y0//50+1)*50,y1,50): cv2.line(im,(0,y-y0),(x1-x0,y-y0),(0,255,255) if y%100==0 else (0,120,120),1)
    im=cv2.resize(im,None,fx=sc,fy=sc)
    for x in range((x0//100+1)*100,x1,100): cv2.putText(im,str(x),(int((x-x0)*sc)+2,14),0,0.45,(255,255,255),1)
    for y in range((y0//100+1)*100,y1,100): cv2.putText(im,str(y),(2,int((y-y0)*sc)-2),0,0.45,(255,255,255),1)
    cv2.putText(im,f.split('/')[-1],(5,int((y1-y0)*sc)-8),0,0.7,(0,0,255),2)
    ims.append(im)
while len(ims)%2: ims.append(np.zeros_like(ims[0]))
rows=[np.hstack(ims[i:i+2]) for i in range(0,len(ims),2)]
cv2.imwrite(out,np.vstack(rows))
