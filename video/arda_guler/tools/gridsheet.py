import cv2,numpy as np,sys
# gridsheet.py P clip frames(x0:y0:w:h per frame via 'k@x0,y0') w h out cols scale
P,clip=sys.argv[1],sys.argv[2]; specs=sys.argv[3].split(';'); W,H=int(sys.argv[4]),int(sys.argv[5]); out=sys.argv[6]; cols=int(sys.argv[7]); sc=float(sys.argv[8])
tiles=[]
for sp in specs:
    k,xy=sp.split('@'); k=int(k); x0,y0=[int(v) for v in xy.split(',')]
    im=cv2.imread(f'{P}/frames/{clip}/{k:04d}.jpg')
    pad=cv2.copyMakeBorder(im,400,400,400,400,cv2.BORDER_CONSTANT)
    c=pad[y0+400:y0+400+H,x0+400:x0+400+W].copy()
    c=cv2.resize(c,(int(W*sc),int(H*sc)),interpolation=cv2.INTER_NEAREST if sc>=2 else cv2.INTER_AREA)
    for gx in range((x0//10+1)*10,x0+W,10):
        col=(0,255,255) if gx%50==0 else (90,90,90)
        if gx%50==0 or sc>=3: cv2.line(c,(int((gx-x0)*sc),0),(int((gx-x0)*sc),c.shape[0]),col,1)
        if gx%50==0: cv2.putText(c,str(gx),(int((gx-x0)*sc)+2,c.shape[0]-4),0,0.4,(0,255,255),1)
    for gy in range((y0//10+1)*10,y0+H,10):
        col=(255,255,0) if gy%50==0 else (90,90,90)
        if gy%50==0 or sc>=3: cv2.line(c,(0,int((gy-y0)*sc)),(c.shape[1],int((gy-y0)*sc)),col,1)
        if gy%50==0: cv2.putText(c,str(gy),(2,int((gy-y0)*sc)-2),0,0.4,(255,255,0),1)
    cv2.putText(c,str(k),(c.shape[1]-60,22),0,0.7,(0,0,255),2)
    tiles.append(c)
while len(tiles)%cols: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out,np.vstack([np.hstack(tiles[i:i+cols]) for i in range(0,len(tiles),cols)]),[cv2.IMWRITE_JPEG_QUALITY,85])
