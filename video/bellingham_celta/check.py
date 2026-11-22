import cv2,numpy as np,json,sys
# check.py track.json out.jpg r scale cols [step]
d={int(k):v for k,v in json.load(open(sys.argv[1])).items()}; out=sys.argv[2]; r=int(sys.argv[3]); sc=float(sys.argv[4]); cols=int(sys.argv[5]); step=int(sys.argv[6]) if len(sys.argv)>6 else 1
tiles=[]
for i in sorted(d)[::step]:
  x,y=d[i]; im=cv2.imread(f'frames/f{i:04d}.jpg')
  im=cv2.copyMakeBorder(im,r,r,r,r,cv2.BORDER_CONSTANT)
  c=im[int(y):int(y)+2*r,int(x):int(x)+2*r].copy(); c=cv2.resize(c,None,fx=sc,fy=sc,interpolation=cv2.INTER_NEAREST)
  C=int(r*sc); cv2.line(c,(C-12,C),(C+12,C),(0,0,255),1); cv2.line(c,(C,C-12),(C,C+12),(0,0,255),1)
  for g in range(-r,r+1,10):
    cv2.line(c,(C+int(g*sc),0),(C+int(g*sc),4),(0,255,255),1); cv2.line(c,(0,C+int(g*sc)),(4,C+int(g*sc)),(0,255,255),1)
  cv2.putText(c,str(i),(3,14),0,0.45,(255,255,0),1); tiles.append(c)
while len(tiles)%cols: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out,np.vstack([np.hstack(tiles[k:k+cols]) for k in range(0,len(tiles),cols)]))
