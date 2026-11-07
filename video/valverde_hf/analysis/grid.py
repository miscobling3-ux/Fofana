import cv2,sys
src,out,x0,y0,x1,y1=sys.argv[1],sys.argv[2],*map(int,sys.argv[3:7])
im=cv2.imread(src)[y0:y1,x0:x1].copy()
s=2 if (x1-x0)<700 else 1
im=cv2.resize(im,None,fx=s,fy=s)
for x in range((x0//20+1)*20,x1,20):
    c=(0,255,255) if x%100==0 else (80,80,80)
    cv2.line(im,((x-x0)*s,0),((x-x0)*s,im.shape[0]),c,1)
    if x%100==0: cv2.putText(im,str(x),((x-x0)*s+2,15),0,0.5,(0,255,255),1)
for y in range((y0//20+1)*20,y1,20):
    c=(0,255,255) if y%100==0 else (80,80,80)
    cv2.line(im,(0,(y-y0)*s),(im.shape[1],(y-y0)*s),c,1)
    if y%100==0: cv2.putText(im,str(y),(2,(y-y0)*s-2),0,0.5,(0,255,255),1)
cv2.imwrite(out,im)
