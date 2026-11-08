# sheet.py track.json clip every out.jpg [crop]
import cv2,sys,json,numpy as np
R="/tmp/claude-0/-home-user-Fofana/ee96c0df-7bfe-5d5b-8578-10ba5a54e09d/scratchpad"
t=json.load(open(sys.argv[1])); clip=sys.argv[2]; ev=int(sys.argv[3]); cs=int(sys.argv[5]) if len(sys.argv)>5 else 0
tiles=[]
keys=sorted(int(k) for k in t)
for f in keys[::ev]:
    v=t[str(f)]; im=cv2.imread(f"{R}/hfproj/frames/{clip}/{f:05d}.jpg")
    if v is None:
        tiles.append(np.zeros((200,200,3),np.uint8)); cv2.putText(tiles[-1],f"{f} -",(3,15),0,0.5,(0,0,255),1); continue
    x,y,w,h=v[:4]
    if len(v)>4: hx,hy=v[4],v[5]
    else: hx,hy=x+w/2,y
    cv2.rectangle(im,(int(x),int(y)),(int(x+w),int(y+h)),(0,255,0),1)
    cv2.line(im,(int(hx)-10,int(hy)),(int(hx)+10,int(hy)),(0,0,255),1);cv2.line(im,(int(hx),int(hy)-10),(int(hx),int(hy)+10),(0,0,255),1)
    s=cs or max(w,h)*1.6; cx,cy=x+w/2,y+h/2
    X0=int(np.clip(cx-s/2,0,1920-s));Y0=int(np.clip(cy-s/2,0,1080-s))
    tl=cv2.resize(im[Y0:Y0+int(s),X0:X0+int(s)],(200,200),interpolation=cv2.INTER_NEAREST)
    cv2.putText(tl,str(f),(3,15),0,0.5,(255,255,0),1); tiles.append(tl)
while len(tiles)%10: tiles.append(np.zeros((200,200,3),np.uint8))
cv2.imwrite(sys.argv[4],np.vstack([np.hstack(tiles[i:i+10]) for i in range(0,len(tiles),10)]))
