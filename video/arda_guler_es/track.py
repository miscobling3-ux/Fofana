import cv2, numpy as np, glob, os, json, sys
S='/tmp/claude-0/-home-user-Fofana/663162a9-9ff1-508a-a745-47f437945801/scratchpad/frames'
_cache={}
def img(clip,f):
    k=(clip,f)
    if k in _cache: return _cache[k]
    for d in sorted(glob.glob(f'{S}/{clip}_*')):
        p=f'{d}/f{f:05d}.jpg'
        if os.path.exists(p):
            im=cv2.imread(p); 
            if len(_cache)>400: _cache.clear()
            _cache[k]=im; return im
    raise FileNotFoundError((clip,f))
def grass(im):
    hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
    h,s,v=hsv[...,0].astype(int),hsv[...,1].astype(int),hsv[...,2].astype(int)
    return (h>=30)&(h<=85)&(s>=60)&(v>=55)
def track(clip,seedf,sx,sy,f_from,f_to,ph,pw=None,search=None):
    """track head-top point. ph=player height px. template box: x +-pw/2, y from head-ph*0.05 to head+ph*0.6"""
    pw=pw or ph*0.6; search=search or max(20,ph*0.5)
    res={seedf:(sx,sy)}
    for direction in (1,-1):
        end=f_to if direction==1 else f_from
        x,y=sx,sy; im=img(clip,seedf)
        def box(x,y): return int(x-pw/2),int(y-ph*0.08),int(pw),int(ph*0.7)
        bx,by,bw,bh=box(x,y); tpl=im[by:by+bh,bx:bx+bw].astype(np.float32)
        vx=vy=0
        f=seedf
        while f!=end:
            f+=direction
            im=img(clip,f)
            px,py=x+vx,y+vy
            bx,by,bw,bh=box(px,py); s=int(search)
            X0=max(0,bx-s);Y0=max(0,by-s);X1=min(im.shape[1],bx+bw+s);Y1=min(im.shape[0],by+bh+s)
            win=im[Y0:Y1,X0:X1].astype(np.float32)
            if win.shape[0]<bh or win.shape[1]<bw: res[f]=(x,y); continue
            r=cv2.matchTemplate(win,tpl,cv2.TM_CCOEFF_NORMED)
            _,mv,_,ml=cv2.minMaxLoc(r)
            nx=X0+ml[0]+pw/2; ny=Y0+ml[1]+ph*0.08
            vx=0.5*vx+0.5*(nx-x); vy=0.5*vy+0.5*(ny-y)
            x,y=nx,ny
            bx,by,bw,bh=box(x,y)
            new=im[by:by+bh,bx:bx+bw].astype(np.float32)
            if new.shape==tpl.shape: tpl=0.75*tpl+0.25*new
            res[f]=(float(x),float(y))
    return res
def refine_top(clip,f,x,y,ph):
    """find top of head: topmost non-grass row in column band near x, searching y-ph*0.25..y+ph*0.25"""
    im=img(clip,f); g=grass(im)
    band=max(3,int(ph*0.07))
    y0=int(max(0,y-ph*0.3)); y1=int(min(im.shape[0]-1,y+ph*0.3))
    xs=slice(int(x-band),int(x+band)+1)
    col=~g[y0:y1,xs]
    rows=col.mean(1)>0.4
    # want first row of a run of >=3 non-grass rows
    for i in range(len(rows)-3):
        if rows[i] and rows[i+1] and rows[i+2]: return float(y0+i)
    return y

def pinkmask(im):
    hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
    h,s,v=hsv[...,0],hsv[...,1],hsv[...,2]
    return (((h>=160)|(h<=6))&(s>=40)&(v>=110)).astype(np.uint8)
def track_pink(clip,seedf,sx,sy,f_from,f_to,ph,manual=None):
    """seed = head top. track pink blob below head. manual: dict f->(x,y) overrides/anchors"""
    manual=manual or {}
    res={}
    for direction in (1,-1):
        end=f_to if direction==1 else f_from
        f=seedf; hx,hy=sx,sy
        # offset from blob centroid to head
        im=img(clip,f); m=pinkmask(im)
        def blob(m,px,py,rad):
            X0=int(max(0,px-rad));Y0=int(max(0,py-rad));X1=int(px+rad);Y1=int(py+rad)
            sub=m[Y0:Y1,X0:X1]
            if sub.size==0: return None
            sub=cv2.morphologyEx(sub,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
            nl,lab,st,cen=cv2.connectedComponentsWithStats(sub)
            best=None;bd=1e9
            for k in range(1,nl):
                if st[k][4]<max(6,ph*ph*0.01): continue
                cx,cy=cen[k][0]+X0,cen[k][1]+Y0
                d=np.hypot(cx-px,cy-py)-0.02*st[k][4]
                if d<bd: bd=d;best=(cx,cy,st[k][4])
            return best
        b=blob(m,hx,hy+ph*0.3,ph*0.4)
        off=(hx-b[0],hy-b[1]) if b else (0,-ph*0.3)
        cx,cy=hx-off[0],hy-off[1]; vx=vy=0
        res[f]=(hx,hy)
        while f!=end:
            f+=direction
            if f in manual:
                hx,hy=manual[f]; res[f]=(hx,hy)
                im=img(clip,f); b=blob(pinkmask(im),hx,hy+ph*0.3,ph*0.4)
                if b: off=(hx-b[0],hy-b[1]); cx,cy=b[0],b[1]
                continue
            im=img(clip,f); m=pinkmask(im)
            b=blob(m,cx+vx,cy+vy,ph*0.45)
            if b:
                nvx,nvy=b[0]-cx,b[1]-cy
                if abs(nvx)>ph*0.5 or abs(nvy)>ph*0.5: b=None
            if b:
                vx=0.6*vx+0.4*(b[0]-cx); vy=0.6*vy+0.4*(b[1]-cy); cx,cy=b[0],b[1]
            else:
                cx+=vx; cy+=vy
            hx,hy=cx+off[0],cy+off[1]
            res[f]=(float(hx),float(hy))
    return res

def head_sil(clip,f,hx,hy,ph,maxshift=None):
    """silhouette-based head top near estimate (hx,hy)"""
    im=img(clip,f); maxshift=maxshift or ph*0.25
    X0=int(max(0,hx-ph*0.6));X1=int(min(im.shape[1],hx+ph*0.6))
    Y0=int(max(0,hy-ph*0.4));Y1=int(min(im.shape[0],hy+ph*0.9))
    sub=im[Y0:Y1,X0:X1]
    ng=(~grass(sub)).astype(np.uint8)
    ng=cv2.morphologyEx(ng,cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
    nl,lab,st,cen=cv2.connectedComponentsWithStats(ng)
    # component under the torso point (hx, hy+0.3ph)
    tx,ty=int(hx-X0),int(min(sub.shape[0]-1,hy+ph*0.3-Y0))
    k=lab[ty,tx]
    if k==0:
        d=1e9
        for j in range(1,nl):
            if st[j][4]<ph: continue
            dd=np.hypot(cen[j][0]-tx,cen[j][1]-ty)
            if dd<d: d=dd;k=j
    if k==0: return hx,hy
    comp=(lab==k)
    ys,xs=np.nonzero(comp)
    # only consider pixels within +-0.3ph of hx horizontally
    sel=np.abs(xs+X0-hx)<ph*0.3
    if sel.sum()<3: return hx,hy
    ys,xs=ys[sel],xs[sel]
    top=ys.min()
    nx=xs[ys<=top+2].mean()+X0; ny=top+Y0
    if abs(nx-hx)>maxshift or abs(ny-hy)>maxshift: return hx,hy
    return float(nx),float(ny)
