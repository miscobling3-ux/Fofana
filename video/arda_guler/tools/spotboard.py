import cv2,numpy as np,json,sys
S=sys.argv[1]; d=json.load(open(f'{S}/an/plan.json'))
fr=[f for f in d['frames'] if f['spot']]
groups={}
for f in fr: groups.setdefault(f['seg'],[]).append(f)
for seg,fs in groups.items():
    tiles=[]
    for f in fs[::4]:
        cx,cy,h=f['cam']; s=1920/h; w=h*9/16
        X,Y,r=f['spot']; xs=X/s+(cx-w/2); ys=Y/s+(cy-h/2); rs=r/s
        im=cv2.imread(f"{S}/proj/frames/{f['clip']}/{f['k']:04d}.jpg")
        cv2.circle(im,(int(xs),int(ys)),int(rs),(255,255,255),4)
        x0,y0=int(cx-w/2),int(cy-h/2); cv2.rectangle(im,(x0,y0),(int(x0+w),int(y0+h)),(0,200,255),2)
        cv2.putText(im,f"{f['k']}",(20,80),0,2.5,(0,255,255),5)
        tiles.append(cv2.resize(im,(480,270)))
    while len(tiles)%4: tiles.append(np.zeros_like(tiles[0]))
    cv2.imwrite(f'{S}/an/spot_{seg}.jpg',np.vstack([np.hstack(tiles[i:i+4]) for i in range(0,len(tiles),4)]),[cv2.IMWRITE_JPEG_QUALITY,80])
    print(seg,len(fs))
