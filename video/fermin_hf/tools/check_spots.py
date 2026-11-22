import json,sys,cv2,numpy as np,os
FR={"a":sys.argv[1],"b":sys.argv[2]}; out=sys.argv[3]
d=json.load(open("data/state.json"))["frames"]
groups={}
for e in d:
    if "spot" in e and e["spot"]["a"]>0.5: groups.setdefault((e["clip"],tuple(round(v) for v in e["spot"]["src_c"][:0]),round(e["spot"]["src_r"])),[]).append(e)
os.makedirs(out,exist_ok=True)
for gi,(key,lst) in enumerate(groups.items()):
    tiles=[];seen=set()
    for e in lst[::4]:
        if (e["clip"],e["f"]) in seen: continue
        seen.add((e["clip"],e["f"]))
        im=cv2.imread(f"{FR[e['clip']]}/{e['f']:04d}.jpg"); im=cv2.copyMakeBorder(im,400,400,400,400,cv2.BORDER_CONSTANT)
        cx,cy=e["spot"]["src_c"]; r=e["spot"]["src_r"]; cx+=400; cy+=400
        cv2.circle(im,(int(cx),int(cy)),int(r),(255,255,255),3)
        b=e["spot"]["box"]; cv2.rectangle(im,(int(b[0])+400,int(b[1])+400),(int(b[2])+400,int(b[3])+400),(0,0,255),1)
        h=int(r*1.25); crop=im[int(cy)-h:int(cy)+h,int(cx)-h:int(cx)+h]
        crop=cv2.resize(crop,(240,240)); cv2.putText(crop,f"{e['clip']}{e['f']} t{e['k']/30:.1f}",(4,16),0,0.5,(0,255,255),1)
        tiles.append(crop)
    cols=8
    while len(tiles)%cols: tiles.append(tiles[0]*0)
    cv2.imwrite(f"{out}/spot_{gi:02d}.jpg",np.vstack([np.hstack(tiles[k:k+cols]) for k in range(0,len(tiles),cols)]))
    print(gi,key,len(lst),"frames")
