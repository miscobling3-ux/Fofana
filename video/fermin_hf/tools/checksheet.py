import cv2,json,sys,numpy as np
# checksheet.py folder track.json out.jpg [half=40] [scale=3] [every=1] [cols=12]
folder,tp,out=sys.argv[1],sys.argv[2],sys.argv[3]
half=int(sys.argv[4]) if len(sys.argv)>4 else 40; sc=float(sys.argv[5]) if len(sys.argv)>5 else 3
every=int(sys.argv[6]) if len(sys.argv)>6 else 1; cols=int(sys.argv[7]) if len(sys.argv)>7 else 12
tr=json.load(open(tp)); keys=sorted(int(k) for k in tr)[::every]; tiles=[]
for f in keys:
    d=tr[str(f)]; im=cv2.imread(f"{folder}/{f:04d}.jpg"); im=cv2.copyMakeBorder(im,200,200,200,200,cv2.BORDER_CONSTANT)
    cx,cy=int(d["hx"])+200,int(d["hy"])+200+half//3
    crop=im[cy-half:cy+half,cx-half:cx+half].copy()
    z=cv2.resize(crop,None,fx=sc,fy=sc,interpolation=cv2.INTER_LINEAR)
    px=(d["hx"]+200-(cx-half))*sc; py=(d["hy"]+200-(cy-half))*sc
    c=(0,0,255) if d["ok"] else (255,0,255)
    cv2.line(z,(int(px-10),int(py)),(int(px+10),int(py)),c,2); cv2.line(z,(int(px),int(py-10)),(int(px),int(py+10)),c,2)
    cv2.putText(z,str(f),(3,16),0,0.55,(0,255,255),2); tiles.append(z)
while len(tiles)%cols: tiles.append(tiles[0]*0)
cv2.imwrite(out,np.vstack([np.hstack(tiles[k:k+cols]) for k in range(0,len(tiles),cols)]),[cv2.IMWRITE_JPEG_QUALITY,85])
