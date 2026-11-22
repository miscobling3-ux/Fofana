import cv2,numpy as np,sys
# usage: grid.py out.jpg x0 y0 x1 y1 step scale cols frames...
out=sys.argv[1]; x0,y0,x1,y1,step=map(int,sys.argv[2:7]); sc=float(sys.argv[7]); cols=int(sys.argv[8]); fr=[int(a) for a in sys.argv[9:]]
tiles=[]
for i in fr:
  im=cv2.imread(f'frames/f{i:04d}.jpg')[y0:y1,x0:x1].copy()
  im=cv2.resize(im,None,fx=sc,fy=sc,interpolation=cv2.INTER_CUBIC)
  for gx in range((x0//step+1)*step,x1,step):
    X=int((gx-x0)*sc); cv2.line(im,(X,0),(X,im.shape[0]),(0,0,255) if gx%(step*5)==0 else (0,200,255),1); cv2.putText(im,str(gx),(X+2,12),0,0.35,(0,0,255),1)
  for gy in range((y0//step+1)*step,y1,step):
    Y=int((gy-y0)*sc); cv2.line(im,(0,Y),(im.shape[1],Y),(0,0,255) if gy%(step*5)==0 else (0,200,255),1); cv2.putText(im,str(gy),(2,Y-2),0,0.35,(0,0,255),1)
  cv2.putText(im,f'f{i}',(5,im.shape[0]-8),0,0.7,(255,255,0),2); tiles.append(im)
while len(tiles)%cols: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out,np.vstack([np.hstack(tiles[r:r+cols]) for r in range(0,len(tiles),cols)]))
