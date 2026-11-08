# usage: sheet.py out.jpg clip x0 y0 w h scale cols f1 f2 f3 ...  (frames by global index)
import cv2, sys, os, glob
S='/tmp/claude-0/-home-user-Fofana/663162a9-9ff1-508a-a745-47f437945801/scratchpad/frames'
out,clip=sys.argv[1],sys.argv[2]
x0,y0,w,h=map(int,sys.argv[3:7]); sc=float(sys.argv[7]); cols=int(sys.argv[8])
fr=[int(a) for a in sys.argv[9:]]
def path(f):
    for d in sorted(glob.glob(f'{S}/{clip}_*')):
        p=f'{d}/f{f:05d}.jpg'
        if os.path.exists(p): return p
tiles=[]
step=int(sys.argv[0+0] and os.environ.get('GRID','20'))
for f in fr:
    im=cv2.imread(path(f))
    c=im[y0:y0+h,x0:x0+w].copy()
    c=cv2.resize(c,None,fx=sc,fy=sc,interpolation=cv2.INTER_CUBIC)
    for gx in range((x0//step+1)*step,x0+w,step):
        X=int((gx-x0)*sc); major=gx%100==0
        cv2.line(c,(X,0),(X,c.shape[0]),(255,255,0) if major else (90,90,90),1)
        if major: cv2.putText(c,str(gx),(X+2,12),0,0.4,(255,255,0),1)
    for gy in range((y0//step+1)*step,y0+h,step):
        Y=int((gy-y0)*sc); major=gy%100==0
        cv2.line(c,(0,Y),(c.shape[1],Y),(255,255,0) if major else (90,90,90),1)
        if major: cv2.putText(c,str(gy),(2,Y-2),0,0.4,(255,255,0),1)
    cv2.putText(c,f'f{f} t{f/60:.3f}',(5,c.shape[0]-8),0,0.6,(0,0,255),2)
    tiles.append(c)
import numpy as np
rows=[]
for i in range(0,len(tiles),cols):
    r=tiles[i:i+cols]
    while len(r)<cols: r.append(np.zeros_like(tiles[0]))
    rows.append(np.hstack(r))
cv2.imwrite(out,np.vstack(rows),[cv2.IMWRITE_JPEG_QUALITY,88])
