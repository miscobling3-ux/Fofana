import cv2,numpy as np,sys,json
P,clip,f,out=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4]; s,e,st=int(sys.argv[5]),int(sys.argv[6]),int(sys.argv[7])
d=json.load(open(f)); tiles=[]
for k in range(s,e+1,st):
    im=cv2.imread(f'{P}/frames/{clip}/{k:04d}.jpg'); b=d.get(str(k))
    if b:
        if len(b)==4: cv2.rectangle(im,(b[0],b[1]),(b[2],b[3]),(0,0,255),3)
        else: cv2.circle(im,(int(b[0]),int(b[1])),int(b[2]),(255,255,255),4)
    cv2.putText(im,str(k),(20,80),0,2.5,(0,255,255),5); tiles.append(cv2.resize(im,(480,270)))
while len(tiles)%4: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out,np.vstack([np.hstack(tiles[i:i+4]) for i in range(0,len(tiles),4)]),[cv2.IMWRITE_JPEG_QUALITY,80])
