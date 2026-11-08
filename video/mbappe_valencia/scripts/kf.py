# kf.py out.jpg clip size f:cx:cy ...  -> tiles 450px with 10px grid (labels every 50)
import cv2,sys,numpy as np
R="/tmp/claude-0/-home-user-Fofana/ee96c0df-7bfe-5d5b-8578-10ba5a54e09d/scratchpad"
out,clip,S=sys.argv[1],sys.argv[2],int(sys.argv[3]); T=450
tiles=[]
for s in sys.argv[4:]:
    f,cx,cy=map(int,s.split(":"))
    im=cv2.imread(f"{R}/hfproj/frames/{clip}/{f:05d}.jpg")
    x0=int(np.clip(cx-S//2,0,im.shape[1]-S)); y0=int(np.clip(cy-S//2,0,im.shape[0]-S))
    t=cv2.resize(im[y0:y0+S,x0:x0+S],(T,T),interpolation=cv2.INTER_CUBIC); sc=T/S
    st=10 if S<=300 else 20
    for g in range((x0//st+1)*st,x0+S,st):
        X=int((g-x0)*sc); big=g%50==0 if st==10 else g%100==0
        cv2.line(t,(X,0),(X,T),(0,255,255) if big else (0,110,110),1)
        if big: cv2.putText(t,str(g),(X+2,10),0,0.33,(0,255,255),1)
    for g in range((y0//st+1)*st,y0+S,st):
        Y=int((g-y0)*sc); big=g%50==0 if st==10 else g%100==0
        cv2.line(t,(0,Y),(T,Y),(255,0,255) if big else (110,0,110),1)
        if big: cv2.putText(t,str(g),(2,Y-2),0,0.33,(255,0,255),1)
    cv2.putText(t,f"{clip}{f}",(4,T-6),0,0.6,(255,255,255),2)
    tiles.append(t)
while len(tiles)%3: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out,np.vstack([np.hstack(tiles[i:i+3]) for i in range(0,len(tiles),3)]))
