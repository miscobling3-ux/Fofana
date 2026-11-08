import json, sys, numpy as np, cv2
sys.path.insert(0,'.')
from track import img, grass
F=json.load(open('frames_debug.json')); R=json.load(open('verify_tags.json'))
out=[]
for r in R:
    if r.get('missing') or r['tipx'] is None: continue
    fr=F[r['k']]; sc=1920/fr['ch']
    sx=fr['x0']+r['tipx']/sc; sy=fr['y0']+r['tipy']/sc
    im=img(fr['clip'],fr['f'])
    bw=max(2,int(round(6/sc)))
    y0=int(sy)-int(40/sc); y1=int(sy)+int(120/sc)
    win=im[max(0,y0):y1, max(0,int(sx)-int(40/sc)):int(sx)+int(40/sc)+1]
    gr=grass(win).mean() if win.size else 0
    band=im[max(0,y0):y1, max(0,int(sx)-bw):int(sx)+bw+1]
    ng=~grass(band)
    rows=ng.mean(1)>0.35
    head=None
    for i in range(len(rows)-2):
        if rows[i] and rows[i+1] and rows[i+2]: head=i; break
    if gr>0.35 and head is not None:
        gap=(max(0,y0)+head - sy)*sc
        out.append((r['k'],round(gap,1),r['dx']))
    else:
        out.append((r['k'],None,r['dx']))
meas=[o for o in out if o[1] is not None]
ok=[o for o in meas if 0<=o[1]<=16 and abs(o[2])<=6]
print('tag frames with arrow',len(out),'measurable',len(meas),'ok',len(ok))
bad=[o for o in meas if not (0<=o[1]<=16 and abs(o[2])<=6)]
print('bad',len(bad))
import collections
print(bad[:200])
json.dump(out,open('verify2.json','w'))
