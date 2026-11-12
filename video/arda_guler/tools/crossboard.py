import cv2,numpy as np,sys,json
P,clip,trk,out=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4]; s,e=int(sys.argv[5]),int(sys.argv[6]); R=int(sys.argv[7]) if len(sys.argv)>7 else 80
d=json.load(open(trk)); tiles=[]
for k in range(s,e+1):
    if str(k) not in d: continue
    x,y=d[str(k)][:2]; im=cv2.imread(f'{P}/frames/{clip}/{k:04d}.jpg')
    pad=cv2.copyMakeBorder(im,300,300,300,300,cv2.BORDER_CONSTANT)
    c=pad[y+300-R:y+300+R,x+300-R:x+300+R].copy(); c=cv2.resize(c,(160,160))
    m=80; cv2.line(c,(m-12,m),(m+12,m),(255,0,255),1); cv2.line(c,(m,m-12),(m,m+12),(255,0,255),1)
    cv2.putText(c,str(k),(3,14),0,0.45,(0,255,255),1); tiles.append(c)
cols=12
while len(tiles)%cols: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out,np.vstack([np.hstack(tiles[i:i+cols]) for i in range(0,len(tiles),cols)]),[cv2.IMWRITE_JPEG_QUALITY,85])
