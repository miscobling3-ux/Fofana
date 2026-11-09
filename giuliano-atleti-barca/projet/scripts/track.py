import cv2,numpy as np,sys,json
# track.py dir "f:x:y;f:x:y" f_start f_end out.json  [boxw boxh]
# keyframes are head-top points. Tracks forward from each keyframe; blends to hit next keyframe.
d=sys.argv[1]; kf=sorted([tuple(map(float,s.split(':'))) for s in sys.argv[2].split(';')]); fs,fe=int(sys.argv[3]),int(sys.argv[4]); out=sys.argv[5]
bw=int(sys.argv[6]) if len(sys.argv)>6 else 22; bh=int(sys.argv[7]) if len(sys.argv)>7 else 44
cache={}
def img(f):
  if f not in cache: cache[f]=cv2.imread(f'{d}/{f:04d}.jpg')
  return cache[f]
def grassmask(im):
  hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV); h,s,v=cv2.split(hsv)
  return ((h>=30)&(h<=55)&(s>70)&(v>80))
def refine_top(f,x,y):
  im=img(f); x=int(round(x)); y=int(round(y))
  reg=im[y-14:y+16, x-6:x+7]
  if reg.size==0: return y
  g=grassmask(reg); non=~g
  rows=non.sum(1)
  for i,r in enumerate(rows):
    if r>=3:
      # require continuation below
      if rows[i:i+4].min()>=2: return y-14+i
  return y
def track(f0,p0,f1):
  pts={f0:np.array(p0,float)}; p=np.array(p0,float); v=np.zeros(2)
  step=1 if f1>f0 else -1
  for f in range(f0+step,f1+step,step):
    a=img(f-step); b=img(f)
    x,y=int(round(p[0])),int(round(p[1]))
    tpl=a[y-2:y-2+bh, x-bw//2:x+bw//2]
    pr=p+v; px,py=int(round(pr[0])),int(round(pr[1])); R=14
    reg=b[py-2-R:py-2+bh+R, px-bw//2-R:px+bw//2+R]
    if tpl.shape[0]<bh or reg.shape[0]<bh+2*R or reg.shape[1]<bw+2*R: pts[f]=pr; p=pr; continue
    res=cv2.matchTemplate(reg,tpl,cv2.TM_CCOEFF_NORMED); _,_,_,ml=cv2.minMaxLoc(res)
    np_=np.array([px-R+ml[0], py-R+ml[1]],float)
    v=0.5*v+0.5*(np_-p); p=np_; pts[f]=p.copy()
  return pts
res={}
for i in range(len(kf)):
  f0=int(kf[i][0]); a=track(f0,kf[i][1:],fe if i==len(kf)-1 else int(kf[i+1][0]))
  if i+1<len(kf):
    f1=int(kf[i+1][0]); err=np.array(kf[i+1][1:])-a[f1]
    b=track(f1,kf[i+1][1:],f0)
    for f in range(f0,f1+1):
      w=(f-f0)/(f1-f0); res[f]=(1-w)*a[f]+w*b[f]
  else:
    for f in a: res[f]=a[f]
  if i==0 and f0>fs:
    for f,pv in track(f0,kf[0][1:],fs).items(): res.setdefault(f,pv)
out_d={}
for f in sorted(res):
  if fs<=f<=fe:
    x,y=res[f]; out_d[f]=[round(float(x),1),round(float(y),1)]
json.dump(out_d,open(out,'w'))
print(len(out_d),'frames')
