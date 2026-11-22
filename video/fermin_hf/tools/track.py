import cv2,numpy as np,json,sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from barca import barca_mask
def grass(im):
    hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV); h,s,v=cv2.split(hsv)
    return (h>=28)&(h<=95)&(s>=45)&(v>=75)
def blobs_in(im,roi,minarea,dil):
    x0,y0,x1,y1=roi; sub=im[y0:y1,x0:x1]
    m=barca_mask(sub); m=cv2.dilate(m,np.ones((dil,dil),np.uint8))
    n,lab,st,cen=cv2.connectedComponentsWithStats(m)
    g=grass(sub); res=[]
    for i in range(1,n):
        if st[i,4]<minarea: continue
        x,y,w,h=st[i,0],st[i,1],st[i,2],st[i,3]
        pad=max(4,int(0.4*max(w,h)))
        ring=g[max(0,y-pad):y+h+pad,max(0,x-pad):x+w+pad]
        if ring.size and ring.mean()<0.18: continue
        res.append((x+x0,y+y0,w,h,st[i,4]))
    return res
def headtop(im,bx,by,bw,bh):
    g=grass(im); H,W=g.shape
    cx=bx+bw/2; half=max(3,int(bw*0.3))
    xa,xb=int(max(0,cx-half)),int(min(W,cx+half+1))
    y=by+int(bh*0.15); last=y; empty=0; ys=[]
    thr=max(1,int(0.12*(xb-xa)))
    while y>0 and empty<3 and (by-y)<bh*0.6+6:
        row=~g[y,xa:xb]
        if row.sum()>=thr: last=y; empty=0; ys.append((y,np.nonzero(row)[0].mean()+xa))
        else: empty+=1
        y-=1
    top=last
    xs=[x for (yy,x) in ys if yy<=top+max(3,bh*0.08)]
    hx=float(np.mean(xs)) if xs else cx
    return hx,float(top)
def run(folder,f0,f1,seed,size,maxjump=None,minarea=None,dil=5):
    sx,sy=seed; sy=sy+size*0.45; prev=None; vel=np.zeros(2); out={}
    maxjump=maxjump or size*0.8; minarea=minarea or max(15,int((size*0.25)**2))
    step=1 if f1>=f0 else -1; pos=np.array([sx,sy],float)
    for f in range(f0,f1+step,step):
        im=cv2.imread(f"{folder}/{f:04d}.jpg")
        pred=pos+vel
        r=int(size*1.6)
        roi=(int(max(0,pred[0]-r)),int(max(0,pred[1]-r)),int(min(1920,pred[0]+r)),int(min(1080,pred[1]+r*1.5)))
        pos=np.clip(pos,[0,0],[1919,1079]); vel=np.clip(vel,-size,size)
        cands=blobs_in(im,roi,minarea,dil) if roi[2]-roi[0]>4 and roi[3]-roi[1]>4 else []
        best=None;bd=1e9
        for (x,y,w,h,a) in cands:
            p=np.array([x+w/2,y+h/2]); d=np.linalg.norm(p-pred)
            if d<bd: bd=d;best=(x,y,w,h)
        if best is not None and bd<=maxjump:
            x,y,w,h=best; newpos=np.array([x+w/2,y+h/2],float)
            vel=0.5*vel+0.5*(newpos-pos) if prev is not None else vel
            pos=newpos; prev=best
            hx,hy=headtop(im,x,y,w,h); ok=True
        else:
            pos=pred; hx,hy=(out[f-step]["hx"]+vel[0],out[f-step]["hy"]+vel[1]) if (f-step) in out else (pos[0],pos[1]); ok=False; x,y,w,h=(prev if prev else (pos[0]-5,pos[1],10,10))
        out[f]={"hx":round(float(hx),1),"hy":round(float(hy),1),"bx":int(x),"by":int(y),"bw":int(w),"bh":int(h),"ok":ok}
    return out
if __name__=="__main__":
    folder,f0,f1,sx,sy,size,outp=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),float(sys.argv[4]),float(sys.argv[5]),float(sys.argv[6]),sys.argv[7]
    res=run(folder,f0,f1,(sx,sy),size)
    json.dump({str(k):v for k,v in res.items()},open(outp,"w"))
    bad=[k for k,v in res.items() if not v["ok"]]; print(outp,"frames",len(res),"lost",bad[:30])
