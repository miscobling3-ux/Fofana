import cv2,json,numpy as np,sys
T=json.load(open('analysis/tracks.json'))
for name in sys.argv[2:]:
    t=T[name]; src=t['src']; fr=t['frames']; keys=sorted(fr,key=int)[::int(sys.argv[1])]
    tiles=[]
    for k in keys:
        d=fr[k]; im=cv2.imread(f'frames/{src}/{int(k):04d}.jpg')
        s=max(d['w'],d['h'])*1.6; x0=int(d['cx']-s/2); y0=int(d['cy']-s/2)
        im=cv2.copyMakeBorder(im,400,400,400,400,cv2.BORDER_CONSTANT)
        cv2.rectangle(im,(int(d['cx']-d['w']/2)+400,int(d['cy']-d['h']/2)+400),(int(d['cx']+d['w']/2)+400,int(d['cy']+d['h']/2)+400),(255,0,255),1)
        hx,hy=int(d['hx'])+400,int(d['hy'])+400
        cv2.line(im,(hx-6,hy),(hx+6,hy),(0,0,255),1);cv2.line(im,(hx,hy-6),(hx,hy+6),(0,0,255),1)
        c=im[y0+400:y0+400+int(s),x0+400:x0+400+int(s)]; c=cv2.resize(c,(150,150))
        cv2.putText(c,k,(3,12),0,0.4,(0,255,255),1); tiles.append(c)
    while len(tiles)%10: tiles.append(np.zeros_like(tiles[0]))
    rows=[np.hstack(tiles[i:i+10]) for i in range(0,len(tiles),10)]
    cv2.imwrite(f'analysis/board_{name}.jpg',np.vstack(rows))
