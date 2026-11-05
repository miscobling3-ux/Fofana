# grid.py clip frames(comma) x0,y0,x1,y1 out [scale] [gridstep]
import cv2,sys,numpy as np
clip,frames,box,out=sys.argv[1],[int(f) for f in sys.argv[2].split(',')],[int(v) for v in sys.argv[3].split(',')],sys.argv[4]
sc=float(sys.argv[5]) if len(sys.argv)>5 else 2.0; st=int(sys.argv[6]) if len(sys.argv)>6 else 50
x0,y0,x1,y1=box; tiles=[]
for f in frames:
    im=cv2.imread(f"src/{clip}/{f:04d}.jpg")[y0:y1,x0:x1]
    im=cv2.resize(im,None,fx=sc,fy=sc,interpolation=cv2.INTER_CUBIC)
    for x in range((x0//st+1)*st,x1,st):
        X=int((x-x0)*sc); cv2.line(im,(X,0),(X,im.shape[0]),(255,0,255) if x%100==0 else (120,0,120),1)
        if x%100==0: cv2.putText(im,str(x),(X+2,14),0,.45,(255,0,255),1)
    for y in range((y0//st+1)*st,y1,st):
        Y=int((y-y0)*sc); cv2.line(im,(0,Y),(im.shape[1],Y),(255,0,255) if y%100==0 else (120,0,120),1)
        if y%100==0: cv2.putText(im,str(y),(2,Y-2),0,.45,(255,0,255),1)
    cv2.putText(im,f"{clip}{f}",(5,im.shape[0]-8),0,.8,(0,255,255),2); tiles.append(im)
cols=min(len(tiles),int(sys.argv[7]) if len(sys.argv)>7 else 3)
while len(tiles)%cols: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out,np.vstack([np.hstack(tiles[i:i+cols]) for i in range(0,len(tiles),cols)]))
