import cv2,sys,numpy as np
R="/tmp/claude-0/-home-user-Fofana/ee96c0df-7bfe-5d5b-8578-10ba5a54e09d/scratchpad"
c,f=sys.argv[1],int(sys.argv[2]); x0,y0,x1,y1=map(int,sys.argv[3:7])
im=cv2.imread(f"{R}/hfproj/frames/{c}/{f:05d}.jpg");h=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
m=cv2.inRange(h,(150,45,50),(174,235,255)); m[:175,:330]=0 if im.shape[1]>1000 else 0
m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((2,2),np.uint8));m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
n,lab,st,cen=cv2.connectedComponentsWithStats(m)
for i in range(1,n):
  x,y,w,hh,a=st[i]
  if a>=15 and x0<=x+w/2<=x1 and y0<=y+hh/2<=y1: print(f,i,(x,y,w,hh,a))
