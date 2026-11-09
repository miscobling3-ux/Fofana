import cv2,numpy as np,sys,json
# check.py dir track.json out step [hw]
d,tj,out=sys.argv[1],sys.argv[2],sys.argv[3]; step=int(sys.argv[4]); hw=int(sys.argv[5]) if len(sys.argv)>5 else 30
t=json.load(open(tj)); fr=sorted(map(int,t))[::step]
ims=[]
for f in fr:
  x,y=t[str(f)]; im=cv2.imread(f'{d}/{f:04d}.jpg'); x,y=int(round(x)),int(round(y))
  c=im[y-hw:y+2*hw,x-hw:x+hw].copy(); s=3; c=cv2.resize(c,None,fx=s,fy=s,interpolation=cv2.INTER_NEAREST)
  cx,cy=hw*s,hw*s; cv2.line(c,(cx-10,cy),(cx+10,cy),(0,0,255),1); cv2.line(c,(cx,cy-10),(cx,cy+10),(0,0,255),1)
  cv2.putText(c,str(f),(3,14),0,0.45,(0,255,255),1); ims.append(c)
cols=10
while len(ims)%cols: ims.append(np.zeros_like(ims[0]))
cv2.imwrite(out,np.vstack([np.hstack(ims[i:i+cols]) for i in range(0,len(ims),cols)]))
