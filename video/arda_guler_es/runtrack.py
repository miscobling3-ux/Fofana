import sys, json, cv2, numpy as np
sys.path.insert(0,'.')
from track import track, refine_top, img
def verify(clip,pts,out,ph,every=1,cols=12,half=None,sc=2):
    half=half or int(min(70,max(30,ph*0.9)))
    tiles=[]
    for f in sorted(pts)[::every]:
        x,y=pts[f]; im=img(clip,f)
        X0=int(x-half);Y0=int(y-half)
        pad=cv2.copyMakeBorder(im,200,200,200,200,cv2.BORDER_CONSTANT)
        c=pad[Y0+200:Y0+200+2*half, X0+200:X0+200+2*half].copy()
        c=cv2.resize(c,None,fx=sc,fy=sc,interpolation=cv2.INTER_NEAREST)
        cx,cy=int((x-X0)*sc),int((y-Y0)*sc)
        cv2.line(c,(cx-8,cy),(cx+8,cy),(0,0,255),1); cv2.line(c,(cx,cy-8),(cx,cy+8),(0,0,255),1)
        cv2.putText(c,str(f),(2,12),0,0.4,(0,255,255),1)
        tiles.append(c)
    rows=[]
    for i in range(0,len(tiles),cols):
        r=tiles[i:i+cols]
        while len(r)<cols: r.append(np.zeros_like(tiles[0]))
        rows.append(np.hstack(r))
    cv2.imwrite(out,np.vstack(rows),[cv2.IMWRITE_JPEG_QUALITY,85])
if __name__=='__main__':
    spec=json.loads(sys.argv[1])
    name,clip,seedf,sx,sy,f0,f1,ph=spec['name'],spec['clip'],spec['seed'],spec['x'],spec['y'],spec['f0'],spec['f1'],spec['ph']
    from track import track_pink
    man={int(k):tuple(v) for k,v in spec.get("manual",{}).items()}
    tr=track_pink(clip,seedf,sx,sy,f0,f1,ph,man) if spec.get("pink",True) else track(clip,seedf,sx,sy,f0,f1,ph)
    out={}
    for f,(x,y) in tr.items():
        from track import head_sil
        out[f]=head_sil(clip,f,x,y,ph) if spec.get('refine',True) else (x,y)
    json.dump({str(k):v for k,v in sorted(out.items())},open(f'ann/trk_{name}.json','w'))
    verify(clip,out,f'ann/v_{name}.jpg',ph,every=spec.get('every',1))
    print(name,len(out))
