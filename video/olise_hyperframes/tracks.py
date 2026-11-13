import cv2,numpy as np,json
S='/tmp/claude-0/-home-user-Fofana/adbce7f5-53e3-54dc-bd95-fa9317b2d1f9/scratchpad'
R=S+'/olise/assets'
def load(c,f): return cv2.imread(f'{R}/{c}/{f:04d}.jpg')
def interp_keys(keys,frames):
    ks=sorted(keys); out={}
    for f in frames:
        out[f]=(float(np.interp(f,ks,[keys[k][0] for k in ks])),float(np.interp(f,ks,[keys[k][1] for k in ks])))
    return out
def refine_between(clip,keys,patch=(44,44),off=(0,18),win=30):
    """template-track head patch forward from each key and backward from next key; blend."""
    ks=sorted(keys); res={k:tuple(keys[k]) for k in ks}
    pw,ph=patch
    def tr(f0,p0,f1):
        pts={f0:p0}; im=load(clip,f0); x,y=p0
        for f in range(f0+(1 if f1>f0 else -1),f1+(1 if f1>f0 else -1),1 if f1>f0 else -1):
            cx,cy=int(x+off[0]),int(y+off[1])
            tpl=im[cy-ph//2:cy+ph//2,cx-pw//2:cx+pw//2]
            nim=load(clip,f)
            X0,Y0=cx-pw//2-win,cy-ph//2-win
            reg=nim[Y0:Y0+ph+2*win,X0:X0+pw+2*win]
            r=cv2.matchTemplate(reg,tpl,cv2.TM_CCOEFF_NORMED); _,_,_,ml=cv2.minMaxLoc(r)
            x+= (X0+ml[0])-(cx-pw//2); y+=(Y0+ml[1])-(cy-ph//2)
            pts[f]=(x,y); im=nim
        return pts
    for a,b in zip(ks,ks[1:]):
        fw=tr(a,keys[a],b); bw=tr(b,keys[b],a)
        for f in range(a+1,b):
            w=(f-a)/(b-a)
            # blend forward/backward template tracks, then correct linear drift so ends hit keys
            fx=fw[f][0]+(keys[b][0]-fw[b][0])*w; fy=fw[f][1]+(keys[b][1]-fw[b][1])*w
            bx=bw[f][0]+(keys[a][0]-bw[a][0])*(1-w); by=bw[f][1]+(keys[a][1]-bw[a][1])*(1-w)
            res[f]=((1-w)*fx+w*bx,(1-w)*fy+w*by)
    return res
def build():
    T={}
    kA=json.load(open(S+'/work/track/keeperA.json'))
    T['keeperA']={int(k):{'head':v['head'],'bb':v['bb']} for k,v in kA.items()}
    kB=json.load(open(S+'/work/track/keeperB.json'))
    T['keeperB']={int(k):{'head':v['head'],'bb':v['bb']} for k,v in kB.items()}
    oW=json.load(open(S+'/work/track/oliseW.json'))
    keys={f:oW[str(f)]['head'] for f in range(250,262)}
    keys.update({262:(1285,305),266:(1274,302),270:(1273,302),274:(1262,305),278:(1257,304),282:(1252,309),286:(1255,306),290:(1243,304),294:(1243,304),298:(1237,306),302:(1235,306),306:(1235,304),310:(1241,301),312:(1247,302)})
    hw=interp_keys(keys,range(250,313))
    T['oliseW']={f:{'head':hw[f],'bb':[hw[f][0]-45,hw[f][1],90,102]} for f in hw}
    rk={590:(862,355),600:(818,341),610:(804,354),620:(790,346),630:(800,351),640:(828,343),650:(860,361),655:(875,372),660:(897,376),665:(926,371),670:(952,371),675:(970,364),681:(1005,357)}
    hr=refine_between('A',rk,patch=(50,50),off=(0,25),win=25)
    T['oliseR']={f:{'head':hr[f],'bb':[hr[f][0]-250,hr[f][1]-10,500,580]} for f in sorted(hr)}
    # keeper reverse: maroon blob
    kr={}
    for f in range(495,600):
        im=load('A',f).astype(int);B,G,Rr=im[...,0],im[...,1],im[...,2]
        m=((Rr>G+35)&(Rr>B+15)&(Rr<230)&(G<120)).astype(np.uint8); m[:300]=0; m[:,:1000]=0 if f<560 else m[:,:1000]
        m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
        n,lab,st,_=cv2.connectedComponentsWithStats(m)
        i=1+int(np.argmax(st[1:,4])); x,y,w,h,a=st[i]
        hh=int(h*0.22)
        kr[f]={'head':(x+w/2,y-hh),'bb':[int(x-15),int(y-hh-10),int(w+30),int(h+hh+25)]}
    T['keeperR']=kr
    return T
if __name__=='__main__':
    T=build()
    json.dump({k:{str(f):v for f,v in d.items()} for k,d in T.items()},open(S+'/work/tracks.json','w'),default=float)
    print({k:len(v) for k,v in T.items()})
