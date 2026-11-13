import cv2,numpy as np,json,sys
ROOT='/tmp/claude-0/-home-user-Fofana/adbce7f5-53e3-54dc-bd95-fa9317b2d1f9/scratchpad/olise/assets'
def load(c,f): return cv2.imread(f'{ROOT}/{c}/{f:04d}.jpg')
def nongrass(p):
    p=p.astype(int);B,G,R=p[...,0],p[...,1],p[...,2]
    grass=(G>R+12)&(G>B+12)&(G>75)
    return (~grass).astype(np.uint8)
def refine(im,bb,prev):
    x,y,w,h=bb;m=14
    X0,Y0=max(0,x-m),max(0,y-m);X1,Y1=min(im.shape[1],x+w+m),min(im.shape[0],y+h+m)
    ng=nongrass(im[Y0:Y1,X0:X1])
    ng=cv2.morphologyEx(ng,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
    n,lab,st,_=cv2.connectedComponentsWithStats(ng)
    cx,cy=x+w/2-X0,y+h/2-Y0
    keep=np.zeros_like(ng)
    for i in range(1,n):
        sx,sy,sw,sh,a=st[i]
        if a<6: continue
        # component must intersect the central part of bbox and not be a long thin line
        if sx<=cx+w*0.35 and sx+sw>=cx-w*0.35 and sy<=cy+h*0.4 and sy+sh>=cy-h*0.4 and not (sw>3*w or sh>3*h):
            keep[lab==i]=1
    ys,xs=np.nonzero(keep)
    if len(xs)<20: return bb,None
    nb=[int(xs.min()+X0),int(ys.min()+Y0),int(xs.max()-xs.min()+1),int(ys.max()-ys.min()+1)]
    # head: top rows
    top=ys.min(); band=(ys<=top+6)
    hx=float(np.median(xs[band]))+X0
    return nb,(hx,float(top+Y0))
def track(c,a,b,seed,out,win=45):
    res={}
    im=load(c,a); bb=list(seed)
    bb,head=refine(im,bb,None)
    res[a]={'bb':bb,'head':head}
    for f in range(a+1,b+1):
        pim=im; im=load(c,f)
        x,y,w,h=bb
        tpl=pim[max(0,y-4):y+h+4,max(0,x-4):x+w+4]
        X0,Y0=max(0,x-win),max(0,y-win)
        reg=im[Y0:y+h+win,X0:x+w+win]
        r=cv2.matchTemplate(reg,tpl,cv2.TM_CCOEFF_NORMED)
        _,mv,_,ml=cv2.minMaxLoc(r)
        nb=[ml[0]+X0+4,ml[1]+Y0+4,w,h]
        rb,head=refine(im,nb,bb)
        # clamp size change
        if head is not None and 0.75<rb[2]/w<1.35 and 0.75<rb[3]/h<1.35: bb=rb
        else: bb=nb; head=(bb[0]+bb[2]/2,bb[1])
        res[f]={'bb':bb,'head':head,'score':mv}
    json.dump(res,open(out,'w'))
if __name__=='__main__':
    c,a,b=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]); seed=list(map(int,sys.argv[4:8])); track(c,a,b,seed,sys.argv[8])
