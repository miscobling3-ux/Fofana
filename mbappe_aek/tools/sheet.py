import cv2, sys, numpy as np
# usage: sheet.py clipdir start_frame end_frame step out [cols] [crop x0,y0,x1,y1] [w]
d, s, e, st, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
cols = int(sys.argv[6]) if len(sys.argv)>6 else 5
crop = [int(v) for v in sys.argv[7].split(',')] if len(sys.argv)>7 and sys.argv[7]!='-' else None
w = int(sys.argv[8]) if len(sys.argv)>8 else 480
tiles=[]
for f in range(s, e+1, st):
    im = cv2.imread(f"{d}/{f:04d}.jpg")
    if im is None: continue
    if crop: im = im[crop[1]:crop[3], crop[0]:crop[2]]
    h = int(im.shape[0]*w/im.shape[1]); im = cv2.resize(im,(w,h))
    cv2.putText(im, f"{f} {(f-1)/50:.2f}s", (5,25), cv2.FONT_HERSHEY_SIMPLEX, .7,(0,0,0),4)
    cv2.putText(im, f"{f} {(f-1)/50:.2f}s", (5,25), cv2.FONT_HERSHEY_SIMPLEX, .7,(0,255,255),2)
    tiles.append(im)
while len(tiles)%cols: tiles.append(np.zeros_like(tiles[0]))
rows=[np.hstack(tiles[i:i+cols]) for i in range(0,len(tiles),cols)]
cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
