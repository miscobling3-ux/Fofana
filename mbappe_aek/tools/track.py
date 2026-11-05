# Head tracking: template matching on head patch, then head-top refinement ("non pelouse", pelouse = vert ET lumineuse)
import cv2,numpy as np,json,sys
SEGS={ # name: clip, f0, f1, (x_top,y_top) at f0, head radius
 "L0":("A",786,791,(1310,572),12,"Kylian Mbappé","rm"),
 "L1":("B",100,143,(1416,615),7,"Denzel Dumfries","rm"),
 "L2":("B",188,222,(987,573),7,"Jude Bellingham","rm"),
 "L3":("A",490,550,(1192,333),26,"Jude Bellingham","rm"),
 "L4":("B",205,205,(976,574),7,"Jude Bellingham","rm"),
 "L5":("A",672,688,(805,409),22,"Denzel Dumfries","rm"),
 "L6":("A",330,366,(126,292),14,"Denzel Dumfries","rm"),
 "L7":("B",312,317,(1558,540),7,"Denzel Dumfries","rm"),
 "L8":("A",778,791,(1345,584),12,"Kylian Mbappé","rm"),
}
def img(c,f): return cv2.imread(f"src/{c}/{f:04d}.jpg")
def grass(px):
    b,g,r=[int(v) for v in px]; return g>r+12 and g>b+12 and g>70
def refine(im,x,y,r):
    H,W=im.shape[:2]; best=None
    # scan columns near x for the top-most non-grass pixel in [y-r, y+r]
    tops=[]
    for dx in range(-max(2,r//3),max(2,r//3)+1):
        xx=int(np.clip(x+dx,0,W-1))
        for yy in range(int(max(0,y-r)),int(min(H-1,y+r))):
            if not grass(im[yy,xx]): tops.append(yy); break
    if len(tops)<3: return None
    return float(np.percentile(tops,25))
def track(name,manual=None):
    c,f0,f1,(x,y),r,_,_=SEGS[name]; out={}
    im=img(c,f0); cy=y+r; P=int(r*1.3)
    tpl=im[int(cy-P):int(cy+P),int(x-P):int(x+P)].astype(np.float32)
    out[f0]=[x,y]; px,py=x,cy
    for f in range(f0+1,f1+1):
        im=img(c,f); S=int(r*3+10)
        x0,y0=int(px-P-S),int(py-P-S)
        x0=max(0,x0);y0=max(0,y0)
        win=im[y0:int(py+P+S),x0:int(px+P+S)].astype(np.float32)
        res=cv2.matchTemplate(win,tpl,cv2.TM_CCOEFF_NORMED); _,mx,_,loc=cv2.minMaxLoc(res)
        nx,ny=x0+loc[0]+P,y0+loc[1]+P
        new=im[int(ny-P):int(ny+P),int(nx-P):int(nx+P)].astype(np.float32)
        if new.shape==tpl.shape: tpl=0.7*tpl+0.3*new
        px,py=nx,ny
        top=ny-r
        if c=="B" or r<=14:
            t=refine(im,nx,top,r)
            if t is not None and abs(t-top)<r: top=t
        out[f]=[float(nx),float(top)]
    if manual:
        for f,v in manual.items(): out[int(f)]=v
    return out
if __name__=="__main__":
    man=json.load(open("work/manual_keys.json")) if len(sys.argv)>1 else {}
    res={}
    for n in SEGS:
        t=track(n)
        # manual keyframes override + linear interpolation between manual keys
        mk={int(k):v for k,v in man.get(n,{}).items()}
        if mk:
            ks=sorted(mk)
            for f in t:
                if f in mk: t[f]=mk[f]
                elif ks[0]<f<ks[-1]:
                    a=max(k for k in ks if k<f); b=min(k for k in ks if k>f); u=(f-a)/(b-a)
                    t[f]=[mk[a][0]+u*(mk[b][0]-mk[a][0]), mk[a][1]+u*(mk[b][1]-mk[a][1])]
        res[n]={"clip":SEGS[n][0],"name":SEGS[n][5],"r":SEGS[n][4],"pts":{str(k):[round(v[0],1),round(v[1],1)] for k,v in t.items()}}
    json.dump(res,open("work/heads.json","w"),indent=0)
    print({n:len(v["pts"]) for n,v in res.items()})
