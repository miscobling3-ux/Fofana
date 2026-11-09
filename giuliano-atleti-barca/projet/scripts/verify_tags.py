import cv2,numpy as np,json,sys,re
S='/tmp/claude-0/-home-user-Fofana/65b9b5f7-ae08-5e33-bf51-d3ab031f6ee5/scratchpad'
vid=sys.argv[1]
G=json.loads(re.sub(r'^window\.GOL=|;$','',open(S+'/gol/data.js').read()))
fr=G['frames']; cap=cv2.VideoCapture(vid); k=-1; res=[]; bad=[]; crops=[]
while True:
    ok,im=cap.read()
    if not ok: break
    k+=1
    o=fr[k] if k<len(fr) else {}
    if 'tag' not in o: continue
    _,hx,hy=o['tag']
    t=k/30; bounce=5*abs(np.sin(2*np.pi*1.4*t))
    # red arrow pixels in a window around the expected tip
    x0,x1=int(hx-60),int(hx+60); y0,y1=int(hy-140),int(hy+20)
    x0c,y0c=max(0,x0),max(0,y0); reg=im[y0c:min(1920,y1),x0c:min(1080,x1)]
    if reg.size==0: bad.append((k,'offscreen')); continue
    b,g,r=[reg[:,:,i].astype(int) for i in range(3)]
    m=((r>215)&(g<80)&(b<80)).astype(np.uint8)
    n,lab,st,_=cv2.connectedComponentsWithStats(m)
    best=[i for i in range(1,n) if st[i][4]>700]
    best=max(best,key=lambda i:st[i][4]) if best else None
    ys,xs=(np.nonzero(lab==best) if best else (np.array([]),np.array([])))
    if len(ys)<30: 
        if 0<=hx<1080 and 0<=hy<1920: bad.append((k,'notfound'))
        continue
    tipy=ys.max()+y0c; tipx=np.median(xs[ys>=ys.max()-4])+x0c
    dy=hy-tipy; dx=tipx-hx
    res.append((k,round(dx,1),round(dy,1)))
    if not (0<=dy<=16 and abs(dx)<=6): bad.append((k,'tol',round(dx,1),round(dy,1)))
    c=im[max(0,int(hy)-110):int(hy)+60, max(0,int(hx)-60):int(hx)+60].copy()
    if c.shape[0]==170 and c.shape[1]==120:
        cv2.putText(c,str(k),(2,12),0,0.4,(0,255,255),1); crops.append(c)
print('tag frames measured',len(res),'out of tolerance',len([b for b in bad if b[1]=='tol']),'notfound',len([b for b in bad if b[1]=='notfound']))
if res:
    a=np.array(res); print('dy range',a[:,2].min(),a[:,2].max(),'dx range',a[:,1].min(),a[:,1].max())
print(bad[:40])
cols=20
for p in range(0,len(crops),400):
    ch=crops[p:p+400]
    while len(ch)%cols: ch.append(np.zeros_like(ch[0]))
    cv2.imwrite(f'{S}/verify/tags_{p//400}.jpg',np.vstack([np.hstack(ch[i:i+cols]) for i in range(0,len(ch),cols)]))
