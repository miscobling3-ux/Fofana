import cv2, numpy as np, sys
SRC = "/tmp/claude-0/-home-user-Fofana/daca3ac7-e701-5674-9337-1a49ad094954/scratchpad/src"
def frame(clip, n): return cv2.imread(f"{SRC}/{clip}/{n+1:04d}.jpg")  # n 0-based
def mask(img, kind):
    h = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    if kind == "yellow": m = cv2.inRange(h, (18, 120, 120), (35, 255, 255))
    elif kind == "white": m = cv2.inRange(h, (0, 0, 175), (180, 50, 255))
    elif kind == "orange": m = cv2.inRange(h, (0, 90, 150), (16, 255, 255))
    return m
def blobs(img, kind, minarea=25):
    m = mask(img, kind)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    return [(tuple(cen[i]), st[i]) for i in range(1, n) if st[i][4] >= minarea and 112 < cen[i][1] < 1000]
if __name__ == "__main__":
    clip, n, kind = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    img = frame(clip, n)
    for i, (c, s) in enumerate(blobs(img, kind)):
        cv2.rectangle(img, (s[0], s[1]), (s[0]+s[2], s[1]+s[3]), (0, 0, 255), 2)
        cv2.putText(img, str(i), (s[0], s[1]-4), 0, 0.9, (0, 0, 255), 2)
        print(i, [round(v) for v in c], s.tolist())
    cv2.imwrite(sys.argv[4], img[112:1000])
