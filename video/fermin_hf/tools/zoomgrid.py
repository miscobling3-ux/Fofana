import cv2,sys,numpy as np
# zoomgrid.py out cols folder:frame:cx:cy:half[:scale] ...
out=sys.argv[1]; cols=int(sys.argv[2]); tiles=[]
for spec in sys.argv[3:]:
    p=spec.split(":"); folder,f,cx,cy,h=p[0],int(p[1]),int(p[2]),int(p[3]),int(p[4]); sc=float(p[5]) if len(p)>5 else 4
    im=cv2.imread(f"{folder}/{f:04d}.jpg"); x0,y0=cx-h,cy-h
    crop=np.zeros((2*h,2*h,3),np.uint8); H,W=im.shape[:2]
    ax0,ay0=max(0,x0),max(0,y0); ax1,ay1=min(W,x0+2*h),min(H,y0+2*h)
    crop[ay0-y0:ay1-y0,ax0-x0:ax1-x0]=im[ay0:ay1,ax0:ax1]
    z=cv2.resize(crop,None,fx=sc,fy=sc,interpolation=cv2.INTER_NEAREST if sc>=3 else cv2.INTER_LINEAR)
    step=10 if sc>=3 else 50
    g0x=(-x0)%step; g0y=(-y0)%step
    for gx in range(g0x,2*h,step):
        X=x0+gx; c=(0,0,255) if X%50==0 else (90,90,90)
        cv2.line(z,(int(gx*sc),0),(int(gx*sc),z.shape[0]),c,1)
        if X%50==0: cv2.putText(z,str(X),(int(gx*sc)+2,14),0,0.45,(0,0,255),1)
    for gy in range(g0y,2*h,step):
        Y=y0+gy; c=(0,0,255) if Y%50==0 else (90,90,90)
        cv2.line(z,(0,int(gy*sc)),(z.shape[1],int(gy*sc)),c,1)
        if Y%50==0: cv2.putText(z,str(Y),(2,int(gy*sc)-2),0,0.45,(0,0,255),1)
    cv2.putText(z,f"{folder}{f}",(4,z.shape[0]-8),0,0.8,(0,255,255),2)
    tiles.append(z)
th=max(t.shape[0] for t in tiles); tw=max(t.shape[1] for t in tiles)
tiles=[cv2.copyMakeBorder(t,0,th-t.shape[0],0,tw-t.shape[1]+4,cv2.BORDER_CONSTANT) for t in tiles]
while len(tiles)%cols: tiles.append(tiles[0]*0)
cv2.imwrite(out,np.vstack([np.hstack(tiles[k:k+cols]) for k in range(0,len(tiles),cols)]))
