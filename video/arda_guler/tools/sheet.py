import cv2,numpy as np,sys
# usage: sheet.py clipdir start end step out [cols] [w]
d,s,e,st,out=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4]),sys.argv[5]
cols=int(sys.argv[6]) if len(sys.argv)>6 else 6; w=int(sys.argv[7]) if len(sys.argv)>7 else 320
tiles=[]
for i in range(s,e+1,st):
    im=cv2.imread(f'{d}/{i:04d}.jpg')
    if im is None: break
    im=cv2.resize(im,(w,w*9//16)); cv2.putText(im,str(i),(5,22),0,0.7,(0,0,0),4); cv2.putText(im,str(i),(5,22),0,0.7,(0,255,255),2); tiles.append(im)
while len(tiles)%cols: tiles.append(np.zeros_like(tiles[0]))
rows=[np.hstack(tiles[r:r+cols]) for r in range(0,len(tiles),cols)]
cv2.imwrite(out,np.vstack(rows),[cv2.IMWRITE_JPEG_QUALITY,80])
