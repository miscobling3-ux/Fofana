# track.py name clip f0 f1 kf1 kf2 ...   kf = frame:x:y:w:h  (box: x,y top-left = head top region; covers whole body)
# writes tracks/name.json {frame:[x,y,w,h]}; and a check sheet tracks/name.jpg
import cv2, sys, json, numpy as np, os
R="/tmp/claude-0/-home-user-Fofana/ee96c0df-7bfe-5d5b-8578-10ba5a54e09d/scratchpad"
name,clip,f0,f1=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4])
kfs={}
for s in sys.argv[5:]:
    f,x,y,w,h=map(int,s.split(":")); kfs[f]=np.array([x,y,w,h],float)
cache={}
def img(f):
    if f not in cache: cache[f]=cv2.GaussianBlur(cv2.imread(f"{R}/hfproj/frames/{clip}/{f:05d}.jpg"),(3,3),0)
    return cache[f]
def run(fa,fb,box):
    step=1 if fb>=fa else -1
    out={fa:box.copy()}; b=box.copy()
    tpl=None
    def patch(im,b):
        # template = upper 60% of body (head+torso), more stable
        x,y,w,h=b; hh=h*0.6
        return im[int(y):int(y+hh),int(x):int(x+w)].astype(np.float32)
    tpl=patch(img(fa),b)
    for f in range(fa+step,fb+step,step):
        im=img(f); x,y,w,h=b
        r=int(max(25,0.5*w))
        X0=int(max(0,x-r));Y0=int(max(0,y-r));X1=int(min(im.shape[1],x+w+r));Y1=int(min(im.shape[0],y+h*0.6+r))
        reg=im[Y0:Y1,X0:X1].astype(np.float32)
        if reg.shape[0]<=tpl.shape[0] or reg.shape[1]<=tpl.shape[1]: out[f]=b.copy(); continue
        res=cv2.matchTemplate(reg,tpl,cv2.TM_CCOEFF_NORMED)
        _,mv,_,ml=cv2.minMaxLoc(res)
        nb=np.array([X0+ml[0],Y0+ml[1],w,h],float)
        b=nb; out[f]=b.copy()
        np_=patch(im,b)
        if np_.shape==tpl.shape: tpl=0.85*tpl+0.15*np_
    return out
ks=sorted(kfs)
res={}
for i,ka in enumerate(ks):
    kb=ks[i+1] if i+1<len(ks) else None
    if i==0 and ka>f0:
        for f,v in run(ka,f0,kfs[ka]).items(): res[f]=v
    if kb is None:
        for f,v in run(ka,f1,kfs[ka]).items(): res[f]=v
        continue
    fw=run(ka,kb,kfs[ka]); bw=run(kb,ka,kfs[kb])
    for f in range(ka,kb+1):
        a=(f-ka)/(kb-ka); v=(1-a)*fw[f]+a*bw[f]
        # size interpolated linearly
        v[2:]=(1-a)*kfs[ka][2:]+a*kfs[kb][2:]
        res[f]=v
os.makedirs(R+"/tracks",exist_ok=True)
json.dump({int(f):[round(float(t),1) for t in v] for f,v in sorted(res.items()) if f0<=f<=f1},open(f"{R}/tracks/{name}.json","w"))
# sheet: every 4th frame crop around box
fr=[f for f in range(f0,f1+1,int(sys.argv[0:1] and 4))]
tiles=[]
for f in fr:
    im=cv2.imread(f"{R}/hfproj/frames/{clip}/{f:05d}.jpg"); x,y,w,h=res[f]
    cx,cy=x+w/2,y+h/2; s=max(w,h)*1.4
    X0=int(max(0,cx-s/2));Y0=int(max(0,cy-s/2));X1=int(min(1920,cx+s/2));Y1=int(min(1080,cy+s/2))
    cv2.rectangle(im,(int(x),int(y)),(int(x+w),int(y+h)),(0,255,0),1)
    hx,hy=int(x+w/2),int(y)
    cv2.line(im,(hx-8,hy),(hx+8,hy),(0,0,255),1);cv2.line(im,(hx,hy-8),(hx,hy+8),(0,0,255),1)
    t=cv2.resize(im[Y0:Y1,X0:X1],(200,200))
    cv2.putText(t,str(f),(3,15),cv2.FONT_HERSHEY_SIMPLEX,0.5,(255,255,0),1)
    tiles.append(t)
while len(tiles)%10: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(f"{R}/tracks/{name}.jpg",np.vstack([np.hstack(tiles[i:i+10]) for i in range(0,len(tiles),10)]))
print("ok",len(res))
