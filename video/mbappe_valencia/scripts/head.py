# head.py name clip [mode=grass|ratio:k]  -> tracks/name.json with [x,y,w,h,hx,hy] (body box incl head)
import cv2,sys,json,numpy as np
R="/tmp/claude-0/-home-user-Fofana/ee96c0df-7bfe-5d5b-8578-10ba5a54e09d/scratchpad"
name,clip=sys.argv[1],sys.argv[2]; mode=sys.argv[3] if len(sys.argv)>3 else "grass"
t=json.load(open(f"{R}/tracks/{name}.raw.json")); out={}
for k,v in t.items():
    if v is None: out[k]=None; continue
    x,y,w,h=v; f=int(k); cx=x+w/2
    if mode=="grass":
        im=cv2.imread(f"{R}/hfproj/frames/{clip}/{f:05d}.jpg"); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
        g=cv2.inRange(hsv,(30,70,60),(60,255,255))>0
        bw=max(4,w*0.45); yy=int(y); top=yy; xs=[]
        lim=int(y-max(12,h*0.9))
        for r in range(yy,max(lim,0),-1):
            band=~g[r,int(max(0,cx-bw)):int(cx+bw)+1]
            if band.sum()==0: break
            top=r; xs=np.where(band)[0]+int(max(0,cx-bw))
        hx=float(xs.mean()) if len(xs) else cx; hy=float(top)
    else:
        kf=float(mode.split(":")[1]); hy=y-kf*h; hx=cx
    out[k]=[x,min(y,hy),w,y+h-min(y,hy),hx,hy]
json.dump(out,open(f"{R}/tracks/{name}.json","w"))
