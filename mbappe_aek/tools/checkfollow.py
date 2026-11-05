# zoomed board of ALL tracked frames with cross on head top
import cv2,json,sys,numpy as np
H=json.load(open("work/follow_check.json")); names=sys.argv[2:] or list(H); out=sys.argv[1]
tiles=[]
for n in names:
    s=H[n]; r=s["r"]; h=max(40,r*4)
    for f,(x,y) in sorted(s["pts"].items(),key=lambda kv:int(kv[0])):
        im=cv2.imread(f"src/{s['clip']}/{int(f):04d}.jpg")
        x0,y0=int(x-h),int(y-h); pad=cv2.copyMakeBorder(im,h*2,h*2,h*2,h*2,cv2.BORDER_CONSTANT)
        c=pad[y0+2*h:y0+4*h,x0+2*h:x0+4*h]; c=cv2.resize(c,(200,200),interpolation=cv2.INTER_CUBIC)
        k=200/(2*h); cx,cy=int((x-x0)*k),int((y-y0)*k)
        cv2.line(c,(cx-12,cy),(cx+12,cy),(0,0,255),1); cv2.line(c,(cx,cy-12),(cx,cy+12),(0,0,255),1)
        cv2.putText(c,f"{n} {s['clip']}{f}",(3,14),0,.45,(0,255,255),1); tiles.append(c)
cols=10
while len(tiles)%cols: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out,np.vstack([np.hstack(tiles[i:i+cols]) for i in range(0,len(tiles),cols)]))
