import cv2,numpy as np
def barca_mask(im):
    hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV); h,s,v=cv2.split(hsv)
    blue=(h>=100)&(h<=130)&(s>70)&(v>25)&(v<200)
    garnet=((h>=150)|(h<=8))&(s>70)&(v>25)&(v<190)
    navy=(s<120)&(v<70)&(h>=100)&(h<=140)
    return ((blue|garnet|navy)*255).astype(np.uint8)
def blobs(im,minarea=25,dil=5):
    m=barca_mask(im); m=cv2.dilate(m,np.ones((dil,dil),np.uint8))
    n,lab,st,cen=cv2.connectedComponentsWithStats(m)
    return [(int(st[i,0]),int(st[i,1]),int(st[i,2]),int(st[i,3]),int(st[i,4])) for i in range(1,n) if st[i,4]>=minarea]
