# Suivi du haut de la tête : images clés manuelles (grille 10 px) -> template matching -> affinage "non pelouse"
import cv2, numpy as np, json, sys
FR='/tmp/claude-0/-home-user-Fofana/73e3ae01-f789-5811-8ac5-09dda17df3e8/scratchpad/frames'
def load(v,f): return cv2.imread(f'{FR}/{v}/{f+1:05d}.jpg')
def grass(im):
    hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV); h,s,v=hsv[...,0],hsv[...,1],hsv[...,2]
    return (h>=28)&(h<=85)&(s>70)&(v>70)      # vert ET assez lumineux (sinon cheveux foncés = gazon)
def interp(keys,f):
    ks=sorted(keys); 
    if f<=ks[0][0]: return np.array(ks[0][1:],float)
    for a,b in zip(ks,ks[1:]):
        if a[0]<=f<=b[0]: t=(f-a[0])/(b[0]-a[0]); return np.array(a[1:],float)*(1-t)+np.array(b[1:],float)*t
    return np.array(ks[-1][1:],float)
def track(v,f0,f1,keys,half=7,tw=14,th=14,search=10,refine=True):
    out={}; tmpl=None; prev=None
    for f in range(f0,f1+1):
        im=load(v,f); prior=interp(keys,f)
        if any(k[0]==f for k in keys): pos=prior.copy()
        else:
            pos=prior.copy()
            if tmpl is not None:
                g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
                cx,cy=int(prev[0]+(prior[0]-interp(keys,f-1)[0])),int(prev[1]+(prior[1]-interp(keys,f-1)[1]))
                x0,y0=cx-tw-search,cy-search; reg=g[y0:y0+2*th+2*search, x0:x0+2*tw+2*search]
                if reg.shape[0]>tmpl.shape[0] and reg.shape[1]>tmpl.shape[1]:
                    r=cv2.matchTemplate(reg,tmpl,cv2.TM_CCOEFF_NORMED); _,mv,_,ml=cv2.minMaxLoc(r)
                    cand=np.array([x0+ml[0]+tw,y0+ml[1]],float)
                    if mv>0.5 and np.linalg.norm(cand-prior)<25: pos=cand
        if refine:
            gm=grass(im); x=int(round(pos[0])); y=int(round(pos[1]))
            band=~gm[y-15:y+20, x-half:x+half+1]
            rows=np.where(band.sum(1)>=3)[0]
            if len(rows): pos[1]=y-15+rows[0]
        out[f]=[float(pos[0]),float(pos[1])]
        g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY); x=int(pos[0]); y=int(pos[1])
        tmpl=g[y:y+2*th, x-tw:x+tw].copy(); prev=pos
    return out
if __name__=='__main__':
    cfg=json.load(open(sys.argv[1])); res={}
    for name,c in cfg.items():
        res[name]=track(c['clip'],c['f0'],c['f1'],c['keys'],**c.get('opt',{}))
    json.dump(res,open(sys.argv[2],'w'),indent=0)
