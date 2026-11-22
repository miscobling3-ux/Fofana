# Suivi des joueurs (analyse uniquement) : CSRT + affinage du haut de la tete (pixels non-pelouse)
import cv2, json, numpy as np, sys
FPS={'A':30,'B':25}
SPECS={
 # id: (src, t_init, t0, t1, cx, cy, w, h)
 'salah1':('A',5.7,5.7,8.4,559,470,30,62),
 'salah2':('A',13.5,12.7,15.6,471,440,30,58),
 'salah3':('A',22.0,22.0,26.4,325,352,26,54),
 'salah4':('A',26.55,26.55,27.7,179,452,30,60),
 'rice1':('A',18.0,17.9,20.7,559,418,30,58),
 'rice2':('A',24.4,24.3,26.4,612,353,30,58),
 'rice3':('A',26.55,26.55,27.7,503,432,34,62),
 'rice4':('A',30.3,29.6,31.0,572,348,36,64),
 'riceB':('B',5.0,3.0,9.2,490,232,22,40),
 'saliba':('A',16.4,15.5,21.2,156,408,28,58),
 'salah5':('A',16.4,15.5,21.2,241,450,28,56),
 'salahB':('B',5.0,3.0,9.2,160,192,18,36),
 'salahC':('A',1136/30,1132/30,1167/30,460,300,220,560),
 'trent':('A',41.5,40.9,43.1,279,271,200,420),
}
def load(src,i): return cv2.imread(f'frames/{src}/{i:04d}.jpg')
def grass(im):
    hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV); h,s,v=cv2.split(hsv)
    return (h>=28)&(h<=58)&(s>60)&(v>70)&~((s>150)&(v>200))
def run(name,spec):
    src,ti,t0,t1,cx,cy,w,h=spec; f=FPS[src]; fi=int(round(ti*f)); f0=int(round(t0*f)); f1=int(round(t1*f))
    res={}
    for direction,rng in ((1,range(fi,f1+1)),(-1,range(fi,f0-1,-1))):
        tr=cv2.TrackerCSRT_create(); im=load(src,fi)
        tr.init(im,(int(cx-w/2),int(cy-h/2),w,h))
        for i in rng:
            im=load(src,i)
            if im is None: break
            if i!=fi: ok,b=tr.update(im)
            else: ok,b=True,(cx-w/2,cy-h/2,w,h)
            x,y,bw,bh=b
            # haut de la tete : premiere ligne avec pixels non-pelouse dans la colonne centrale
            H,W=im.shape[:2]
            X0=max(0,int(x+bw*0.12));X1=min(W,max(X0+2,int(x+bw*0.88)));Y0=min(H-2,max(0,int(y-bh*0.18)));Y1=min(H,max(Y0+2,int(y+bh*0.3)))
            hsv=cv2.cvtColor(im[Y0:Y1,X0:X1],cv2.COLOR_BGR2HSV); hh,ss,vv=cv2.split(hsv)
            g=grass(im[Y0:Y1,X0:X1]); kit=(hh>=26)&(hh<=48)&(ss>110)&(vv>150)
            ok_=(~g)&(~kit)
            rows=np.where(ok_.sum(1)>=2)[0]
            top=Y0+rows[0] if len(rows) else y+bh*0.02
            if len(rows):
                band=ok_[rows[0]:rows[0]+max(3,int(bh*0.1))]; cols=np.where(band.any(0))[0]
                hx=X0+cols.mean() if len(cols) else x+bw/2
            else: hx=x+bw/2
            res[i]=dict(cx=x+bw/2,cy=y+bh/2,w=bw,h=bh,hx=float(hx),hy=float(top))
    return dict(src=src,fps=f,frames={k:res[k] for k in sorted(res)})
out={n:run(n,s) for n,s in SPECS.items() if len(sys.argv)<2 or n in sys.argv[1:]}
try: old=json.load(open('analysis/tracks.json'))
except: old={}
old.update(out); json.dump(old,open('analysis/tracks.json','w'))
print('ok',list(out))
