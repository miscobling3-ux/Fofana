import cv2,numpy as np,json,glob
tpl=cv2.cvtColor(cv2.imread("work/wm_tpl.png"),cv2.COLOR_BGR2GRAY)
# use edges for robustness to background
def prep(g): return cv2.Canny(g,80,200)
out={}
for clip in "AB":
    files=sorted(glob.glob(f"src/{clip}/*.jpg")); res=[]
    for f in files:
        g=cv2.cvtColor(cv2.imread(f),cv2.COLOR_BGR2GRAY)
        best=(-1,None)
        for s in (0.9,1.0,1.1):
            t=cv2.resize(tpl,None,fx=s,fy=s)
            r=cv2.matchTemplate(prep(g[500:],),prep(t),cv2.TM_CCOEFF_NORMED)
            _,mx,_,loc=cv2.minMaxLoc(r)
            if mx>best[0]: best=(mx,(loc[0],loc[1]+500,int(t.shape[1]),int(t.shape[0])))
        res.append([round(float(best[0]),3),*best[1]])
    out[clip]=res
json.dump(out,open("work/wm.json","w"))
for clip in "AB":
    r=out[clip]
    for i in range(0,len(r),25): print(clip,i+1,r[i])
