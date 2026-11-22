import cv2,numpy as np,sys,json
# zg2.py out.jpg sc half cols "f:x:y"... grid every 5px, labels every 10
out=sys.argv[1]; sc=int(sys.argv[2]); hf=int(sys.argv[3]); cols=int(sys.argv[4]); tiles=[]
for a in sys.argv[5:]:
  i,cx,cy=map(int,a.split(':')); x0,y0=cx-hf,cy-hf
  im=cv2.imread(f'frames/f{i:04d}.jpg'); im=cv2.copyMakeBorder(im,200,200,200,200,cv2.BORDER_CONSTANT)
  c=im[y0+200:y0+200+2*hf,x0+200:x0+200+2*hf]; c=cv2.resize(c,None,fx=sc,fy=sc,interpolation=cv2.INTER_NEAREST)
  for g in range((x0//5+1)*5,x0+2*hf,5):
    X=int((g-x0)*sc); cv2.line(c,(X,0),(X,c.shape[0]),(0,0,255) if g%10==0 else (0,200,255),1)
    if g%10==0: cv2.putText(c,str(g),(X+1,9),0,0.28,(255,255,255),1)
  for g in range((y0//5+1)*5,y0+2*hf,5):
    Y=int((g-y0)*sc); cv2.line(c,(0,Y),(c.shape[1],Y),(0,0,255) if g%10==0 else (0,200,255),1)
    if g%10==0: cv2.putText(c,str(g),(1,Y-1),0,0.28,(255,255,255),1)
  cv2.putText(c,f'f{i}',(3,c.shape[0]-4),0,0.45,(255,255,0),1); tiles.append(c)
while len(tiles)%cols: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out,np.vstack([np.hstack(tiles[k:k+cols]) for k in range(0,len(tiles),cols)]))
