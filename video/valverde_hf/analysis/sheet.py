import cv2,json,sys,numpy as np
# sheet.py dir track.json out.jpg crop_half step [dy_top]
d,tj,out,ch,step=sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4]),int(sys.argv[5])
dy=float(sys.argv[6]) if len(sys.argv)>6 else 0
t=json.load(open(tj)); ks=sorted(t,key=int)[::step]
tiles=[]
for k in ks:
    im=cv2.imread(f"{d}/{int(k):04d}.jpg"); x,y=t[k][0],t[k][1]-dy
    x0,y0=int(x-ch),int(y-ch)
    pad=cv2.copyMakeBorder(im,ch,ch,ch,ch,cv2.BORDER_CONSTANT)
    c=pad[y0+ch:y0+3*ch,x0+ch:x0+3*ch].copy()
    c=cv2.resize(c,(200,200)); s=200/(2*ch)
    cv2.drawMarker(c,(100,100),(0,0,255),cv2.MARKER_CROSS,20,1)
    cv2.putText(c,k,(3,15),0,0.45,(0,255,255),1)
    tiles.append(c)
while len(tiles)%10: tiles.append(np.zeros((200,200,3),np.uint8))
rows=[np.hstack(tiles[i:i+10]) for i in range(0,len(tiles),10)]
cv2.imwrite(out,np.vstack(rows))
