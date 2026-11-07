import cv2,json,sys,numpy as np
# usage: track.py dir first last x y half search out.json [reverse]
d,f0,f1,x,y,h,sr,out=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),float(sys.argv[4]),float(sys.argv[5]),int(sys.argv[6]),int(sys.argv[7]),sys.argv[8]
rev=len(sys.argv)>9
rng=range(f1,f0-1,-1) if rev else range(f0,f1+1)
def load(i): return cv2.imread(f"{d}/{i:04d}.jpg")
res={}
im=load(rng[0]); cx,cy=x,y
tpl=im[int(cy-h):int(cy+h),int(cx-h):int(cx+h)].astype(np.float32)
tpl0=tpl.copy(); vx=vy=0
for i in rng:
    im=load(i)
    px,py=cx+vx,cy+vy
    x0,y0=int(px-h-sr),int(py-h-sr)
    x0=max(0,x0);y0=max(0,y0)
    win=im[y0:int(py+h+sr),x0:int(px+h+sr)].astype(np.float32)
    r=cv2.matchTemplate(win,tpl,cv2.TM_CCOEFF_NORMED)
    r2=cv2.matchTemplate(win,tpl0,cv2.TM_CCOEFF_NORMED)
    r=0.7*r+0.3*r2
    # prior: penalize distance
    yy,xx=np.mgrid[0:r.shape[0],0:r.shape[1]]
    dist=np.hypot(xx+x0+h-px,yy+y0+h-py)
    r=r-0.002*dist
    _,mv,_,ml=cv2.minMaxLoc(r)
    nx,ny=ml[0]+x0+h,ml[1]+y0+h
    if i!=rng[0]: vx,vy=0.6*(nx-cx)+0.4*vx,0.6*(ny-cy)+0.4*vy
    cx,cy=nx,ny
    res[i]=[cx,cy,round(float(mv),3)]
    new=im[int(cy-h):int(cy+h),int(cx-h):int(cx+h)].astype(np.float32)
    if new.shape==tpl.shape: tpl=0.8*tpl+0.2*new
json.dump(res,open(out,"w"))
print("ok",len(res),min(v[2] for v in res.values()))
