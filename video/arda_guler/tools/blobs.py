import cv2,numpy as np,sys
P=sys.argv[1]; clip=sys.argv[2]; frames=[int(v) for v in sys.argv[3].split(',')]
for k in frames:
    im=cv2.imread(f'{P}/frames/{clip}/{k:04d}.jpg'); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
    grass=(hsv[...,0]>=30)&(hsv[...,0]<=90)&(hsv[...,1]>=50)&(hsv[...,2]>=50)
    m=(~grass).astype(np.uint8)*255; m[:140,1560:]=0
    m=cv2.morphologyEx(m,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    n,l,st,c=cv2.connectedComponentsWithStats(m)
    out=[(int(x),int(y),int(w),int(h),int(a)) for x,y,w,h,a in st[1:] if a>800]
    print(k,out)
