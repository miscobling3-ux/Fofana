import cv2,numpy as np,json,sys
def load(i): return cv2.imread(f'frames/f{i:04d}.jpg')
def track(seed,frames,hw=24,up=6,down=50,search=40,alpha=0.25):
  """seed=(x,y) head top at frames[0]; returns {i:(x,y)}"""
  im=load(frames[0]).astype(np.float32); x,y=seed
  T=im[y-up:y+down,x-hw:x+hw].copy(); out={frames[0]:(float(x),float(y))}
  for i in frames[1:]:
    im=load(i).astype(np.float32)
    X0=max(0,int(x-hw-search));Y0=max(0,int(y-up-search))
    win=im[Y0:int(y+down+search),X0:int(x+hw+search)]
    r=cv2.matchTemplate(win,T,cv2.TM_CCOEFF_NORMED); _,mx,_,loc=cv2.minMaxLoc(r)
    x=X0+loc[0]+hw; y=Y0+loc[1]+up
    xi,yi=int(round(x)),int(round(y))
    T=(1-alpha)*T+alpha*im[yi-up:yi+down,xi-hw:xi+hw]
    out[i]=(float(x),float(y))
  return out
def refine_top(i,x,y,box=(18,30,25)):
  """move y to the topmost non-grass pixel of the blob near (x,y). Only valid on pitch background."""
  im=load(i); dx,dup,ddn=box
  y0=int(y-dup); x0=int(x-dx)
  p=im[y0:int(y+ddn),x0:int(x+dx)].astype(int); b,g,r=p[...,0],p[...,1],p[...,2]
  grass=(g>r+8)&(g>b+8)&(g>70)
  ng=~grass
  ng=cv2.morphologyEx(ng.astype(np.uint8),cv2.MORPH_OPEN,np.ones((2,2),np.uint8))
  n,lab,st,cen=cv2.connectedComponentsWithStats(ng)
  if n<2: return x,y
  # component containing point closest to (x, y+12)
  cy=int(dup+12); cx=dx
  best=None
  for k in range(1,n):
    ys,xs=np.nonzero(lab==k)
    d=np.min((xs-cx)**2+(ys-cy)**2)
    if st[k][4]>15 and (best is None or d<best[0]): best=(d,k)
  ys,xs=np.nonzero(lab==best[1]); top=ys.min()
  sel=xs[ys<=top+3]
  return x0+float(np.mean(sel)), y0+float(top)
