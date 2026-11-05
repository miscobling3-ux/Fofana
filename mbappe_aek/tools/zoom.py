# zoom.py out clip:frame:cx:cy[:half] ...   -> zoomed crops with 10px grid, labels every 50
import cv2,sys,numpy as np
out=sys.argv[1]; tiles=[]
for spec in sys.argv[2:]:
    p=spec.split(':'); clip,f,cx,cy=p[0],int(p[1]),int(p[2]),int(p[3]); h=int(p[4]) if len(p)>4 else 80
    im=cv2.imread(f"src/{clip}/{f:04d}.jpg"); H,W=im.shape[:2]
    x0,y0=max(0,cx-h),max(0,cy-h); x1,y1=min(W,cx+h),min(H,cy+h)
    c=im[y0:y1,x0:x1]; sc=480/(2*h); c=cv2.resize(c,None,fx=sc,fy=sc,interpolation=cv2.INTER_CUBIC)
    for x in range((x0//10+1)*10,x1,10):
        X=int((x-x0)*sc); col=(255,0,255) if x%50==0 else (90,0,90); cv2.line(c,(X,0),(X,c.shape[0]),col,1)
        if x%50==0: cv2.putText(c,str(x),(X+2,12),0,.4,(255,255,255),1)
    for y in range((y0//10+1)*10,y1,10):
        Y=int((y-y0)*sc); col=(255,0,255) if y%50==0 else (90,0,90); cv2.line(c,(0,Y),(c.shape[1],Y),col,1)
        if y%50==0: cv2.putText(c,str(y),(2,Y-2),0,.4,(255,255,255),1)
    c=cv2.copyMakeBorder(c,0,480-c.shape[0],0,480-c.shape[1],cv2.BORDER_CONSTANT)
    cv2.putText(c,f"{clip}{f}",(5,470),0,.7,(0,255,255),2); tiles.append(c)
cols=4
while len(tiles)%cols: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out,np.vstack([np.hstack(tiles[i:i+cols]) for i in range(0,len(tiles),cols)]))
