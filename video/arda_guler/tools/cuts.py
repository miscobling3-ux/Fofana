import cv2,numpy as np,sys,glob
for c in 'ABC':
    fs=sorted(glob.glob(f'{sys.argv[1]}/frames/{c}/*.jpg'));prev=None;cuts=[]
    for i,f in enumerate(fs):
        im=cv2.resize(cv2.imread(f),(160,90));h=cv2.calcHist([cv2.cvtColor(im,cv2.COLOR_BGR2HSV)],[0,1],None,[16,16],[0,180,0,256]);h=cv2.normalize(h,h).flatten()
        if prev is not None:
            d=cv2.compareHist(prev,h,cv2.HISTCMP_BHATTACHARYYA)
            if d>0.3: cuts.append((i+1,round(d,2)))
        prev=h
    print(c,len(fs),cuts)
