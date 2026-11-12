import cv2,numpy as np,sys,json
# track.py P clip start end x y out [manual.json]
P,clip=sys.argv[1],sys.argv[2]; s,e=int(sys.argv[3]),int(sys.argv[4]); x,y=int(sys.argv[5]),int(sys.argv[6]); out=sys.argv[7]
manual=json.load(open(sys.argv[8])) if len(sys.argv)>8 else {}
def grassmask(im):
    hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
    return (hsv[...,0]>=30)&(hsv[...,0]<=90)&(hsv[...,1]>=50)&(hsv[...,2]>=60)
def refine(im,x,y,band=10):
    g=grassmask(im); H,W=g.shape
    x0,x1=max(0,x-band),min(W,x+band+1)
    best=None
    for yy in range(max(0,y-30),min(H-12,y+30)):
        col=~g[yy:yy+12,x0:x1]
        if col.mean()>0.6: best=yy;break
    return best
res={}; prev=None; tpl=None
for k in range(s,e+1):
    im=cv2.imread(f'{P}/frames/{clip}/{k:04d}.jpg')
    if str(k) in manual:
        x,y=manual[str(k)]; src='m'
    else:
        if tpl is not None:
            sx0,sy0=max(0,x-60-35),max(0,y-25-35)
            win=im[sy0:y+60+35,sx0:x+60+35]
            r=cv2.matchTemplate(win,tpl,cv2.TM_CCOEFF_NORMED); _,mv,_,ml=cv2.minMaxLoc(r)
            x,y=sx0+ml[0]+60,sy0+ml[1]+25
        ry=refine(im,x,y); 
        if ry is not None: y=ry
        src='a'
    res[k]=(int(x),int(y),src)
    tpl=im[y-25:y+95,x-60:x+60].copy()
json.dump(res,open(out,'w'))
