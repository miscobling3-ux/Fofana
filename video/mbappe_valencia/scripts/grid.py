# usage: grid.py out.jpg  clip:frame:x0:y0:w:h:step  [more...]  -> tiles stacked horizontally
import cv2, sys, numpy as np
root="/tmp/claude-0/-home-user-Fofana/ee96c0df-7bfe-5d5b-8578-10ba5a54e09d/scratchpad/hfproj/frames"
tiles=[]
for spec in sys.argv[2:]:
    c,f,x0,y0,w,h,st=spec.split(":"); f=int(f);x0,y0,w,h,st=map(int,(x0,y0,w,h,st))
    im=cv2.imread(f"{root}/{c}/{f:05d}.jpg")[y0:y0+h,x0:x0+w]
    sc=max(1,int(640/max(w,h)*1.0)) if max(w,h)<640 else 1
    sc=int(__import__("os").environ.get("TILE","640"))/max(w,h)
    im=cv2.resize(im,None,fx=sc,fy=sc,interpolation=cv2.INTER_NEAREST if sc>1 else cv2.INTER_AREA)
    for gx in range((x0//st+1)*st,x0+w,st):
        X=int((gx-x0)*sc); big=gx%(st*5)==0
        cv2.line(im,(X,0),(X,im.shape[0]),(0,255,255) if big else (0,140,140),1)
        if big: cv2.putText(im,str(gx),(X+2,12),cv2.FONT_HERSHEY_SIMPLEX,0.4,(0,255,255),1)
    for gy in range((y0//st+1)*st,y0+h,st):
        Y=int((gy-y0)*sc); big=gy%(st*5)==0
        cv2.line(im,(0,Y),(im.shape[1],Y),(255,0,255) if big else (140,0,140),1)
        if big: cv2.putText(im,str(gy),(2,Y-2),cv2.FONT_HERSHEY_SIMPLEX,0.4,(255,0,255),1)
    cv2.putText(im,f"{c}{f}",(5,im.shape[0]-6),cv2.FONT_HERSHEY_SIMPLEX,0.6,(255,255,255),2)
    tiles.append(im)
H=max(t.shape[0] for t in tiles)
tiles=[cv2.copyMakeBorder(t,0,H-t.shape[0],0,4,cv2.BORDER_CONSTANT) for t in tiles]
cv2.imwrite(sys.argv[1],np.hstack(tiles) if len(tiles)<4 else np.vstack([np.hstack(tiles[i:i+3]) if len(tiles[i:i+3])==3 else np.hstack(tiles[i:i+3]+[np.zeros_like(tiles[0])]*(3-len(tiles[i:i+3]))) for i in range(0,len(tiles),3)]))
