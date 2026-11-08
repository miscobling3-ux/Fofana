# ptrack.py name clip f0 f1 seedx seedy [color=pink|keeper] [kf frame:x:y ...]
# Follows a colored blob (Real Madrid pink kit / keeper green) frame by frame.
import cv2, sys, json, numpy as np, os
R="/tmp/claude-0/-home-user-Fofana/ee96c0df-7bfe-5d5b-8578-10ba5a54e09d/scratchpad"
a=sys.argv; name,clip,f0,f1,sx,sy=a[1],a[2],int(a[3]),int(a[4]),float(a[5]),float(a[6])
color="pink"; kfs={}
for s in a[7:]:
    if s.startswith("color="): color=s[6:]
    else:
        f,x,y=s.split(":"); kfs[int(f)]=(float(x),float(y))
def mask(im):
    h=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
    if color=="pink": m=cv2.inRange(h,(150,45,50),(174,235,255))
    else: m=cv2.inRange(h,(26,110,170),(40,255,255))
    m[:175,:330]=0  # scoreboard
    k=np.ones((5,5),np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,k)
    return m
step=1 if f1>=f0 else -1
c=np.array([sx,sy]); prev=None; out={}
for f in range(f0,f1+step,step):
    if f in kfs: c=np.array(kfs[f]); prev=None
    im=cv2.imread(f"{R}/hfproj/frames/{clip}/{f:05d}.jpg")
    m=mask(im)
    n,lab,st,cen=cv2.connectedComponentsWithStats(m)
    best=None;bd=1e9
    for i in range(1,n):
        x,y,w,h,ar=st[i]
        if ar<15: continue
        # distance from current center to the component box
        dx=max(x-c[0],0,c[0]-(x+w)); dy=max(y-c[1],0,c[1]-(y+h))
        d=np.hypot(dx,dy)
        if prev is not None: d+=0.002*abs(ar-prev[4])
        if d<bd: bd=d;best=i
    lim = 60 if prev is None else max(25,0.6*prev[3])
    if best is None or bd>lim:
        out[f]=None; continue
    x,y,w,h,ar=st[best]
    # gather nearby components belonging to same player (gap < 0.25 h) e.g. socks split
    bx0,by0,bx1,by1=x,y,x+w,y+h
    for i in range(1,n):
        if i==best: continue
        X,Y,W,H,A=st[i]
        if A<10: continue
        if X<bx1+0.15*h and X+W>bx0-0.15*h and Y<by1+0.3*h and Y+H>by0-0.1*h and A>0.01*ar:
            bx0,by0,bx1,by1=min(bx0,X),min(by0,Y),max(bx1,X+W),max(by1,Y+H)
    cur=np.array([bx0,by0,bx1-bx0,by1-by0,ar],float)
    if prev is not None and (cur[2]>1.5*prev[2]+6 or cur[3]>1.4*prev[3]+6):
        # merge with someone else: keep previous size, move with the component center of mass near previous
        ys,xs=np.where(lab==best)
        sel=(xs>prev[0]-0.3*prev[2])&(xs<prev[0]+1.3*prev[2])
        if sel.sum()>10:
            cx=xs[sel].mean(); cur=np.array([cx-prev[2]/2,min(ys[sel].min(),prev[1]+prev[3]),prev[2],prev[3],prev[4]])
        else: cur=prev.copy()
    prev=cur; c=np.array([cur[0]+cur[2]/2,cur[1]+cur[3]/2])
    out[f]=[float(v) for v in cur[:4]]
os.makedirs(R+"/tracks",exist_ok=True)
json.dump({int(k):v for k,v in out.items()},open(f"{R}/tracks/{name}.raw.json","w"))
miss=[k for k,v in out.items() if v is None]
print(name,"frames",len(out),"missing",len(miss),miss[:10])
