"""Images clés posées à la main (grille 10 px) -> interpolation -> affinage auto du haut de la tête."""
import json, sys, cv2, numpy as np
from scipy.interpolate import PchipInterpolator
from blobs import frame
KEYS = {
 "jovic_A": ("A", {196:(723,476),198:(719,474.5),202:(709,471),206:(694,469),212:(666,468),220:(643,478),232:(638,479),244:(633,478),250:(627.5,479.5),258:(621,482.5),266:(621,472.5),274:(622,472.5),280:(619.5,479.5),286:(627,484)}),
 "koita_A": ("A", {278:(1021,554),310:(1101,559),317:(1112.5,560.5),321:(1118.5,553.5),325:(1126.7,551.3),329:(1135,551),333:(1142.2,548.8),346:(1146,544),358:(1169,544),362:(1175,544.7),370:(1184,530),382:(1186,531),387:(1177.5,533.8),390:(1168.8,531.5),394:(1150,527),404:(1133,515),412:(1110,517),419:(1091,524)}),
 "koita_Bh": ("B", {250:(730,613.5),260:(757.5,608.8),270:(775,610.3),280:(774.3,608.5),287:(778.5,615.0),290:(783,614.8),296:(794.6,624.9),300:(795.5,619.5),310:(788.5,613.3),320:(770.5,622),330:(741.3,606.8),340:(726.3,594.3),346:(718.3,592),352:(712.3,587.5)}),
 "koita_Bl": ("B", {556:(646.3,357.5),564:(681.5,366.8),572:(685,371),580:(677.5,378.3),588:(658.8,373.3),596:(652,388.8),604:(658,402.5),612:(702.5,389.5),620:(719.5,388.3),628:(735,402),634:(732.5,406.3),637:(730.8,406.8)}),
}
def dark(img):
    h = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    g = cv2.inRange(h, (30, 50, 70), (90, 255, 255)) > 0   # pelouse : verte ET lumineuse
    return (~g) & (h[..., 2] < 150)
def refine(img, gx, gy, wx=4, up=6, down=8):
    x1, x2 = int(round(gx - wx)), int(round(gx + wx)) + 1
    y1, y2 = int(round(gy - up)), int(round(gy + down)) + 1
    d = dark(img[y1:y2, x1:x2])
    cnt = d.sum(1)
    for r in range(d.shape[0] - 3):
        if cnt[r] >= 2 and cnt[r + 1] >= 2 and cnt[r + 2] >= 2:
            xs = np.where(d[r:r + 3].any(0))[0]
            return float(x1 + xs.mean()), float(y1 + r), True
    return gx, gy, False
def build(name):
    clip, keys = KEYS[name]
    ks = sorted(keys)
    fx = PchipInterpolator(ks, [keys[k][0] for k in ks]); fy = PchipInterpolator(ks, [keys[k][1] for k in ks])
    out = {}
    for n in range(ks[0], ks[-1] + 1):
        gx, gy = float(fx(n)), float(fy(n))
        img = frame(clip, n)
        rx, ry, ok = refine(img, gx, gy)
        # garde-fou : l'affinage ne s'écarte pas de plus de 5 px de l'interpolation
        if not ok or abs(rx - gx) > 4 or abs(ry - gy) > 6: rx, ry = gx, gy
        out[n] = {"head": [round(rx, 1), round(ry, 1)], "interp": [round(gx, 1), round(gy, 1)], "refined": bool(ok)}
    json.dump(out, open(f"head_{name}.json", "w"))
    return clip, out
def sheet(clip, out, path, half=26, s=4, per=14):
    ims = []
    for n in sorted(out):
        hx, hy = out[n]["head"]
        x1, y1 = int(hx - half), int(hy - half)
        im = cv2.resize(frame(clip, n)[y1:y1 + 2 * half, x1:x1 + 2 * half], None, fx=s, fy=s, interpolation=cv2.INTER_NEAREST)
        cx, cy = int((hx - x1) * s), int((hy - y1) * s)
        cv2.line(im, (cx - 14, cy), (cx + 14, cy), (0, 0, 255), 2); cv2.line(im, (cx, cy - 14), (cx, cy + 14), (0, 0, 255), 2)
        cv2.putText(im, str(n), (3, 18), 0, 0.6, (0, 255, 255), 2)
        ims.append(im)
    while len(ims) % per: ims.append(ims[0] * 0)
    cv2.imwrite(path, np.vstack([np.hstack(ims[i:i + per]) for i in range(0, len(ims), per)]))
if __name__ == "__main__":
    AN = "/tmp/claude-0/-home-user-Fofana/daca3ac7-e701-5674-9337-1a49ad094954/scratchpad/an"
    for name in sys.argv[1:]:
        clip, out = build(name)
        sheet(clip, out, f"{AN}/hd_{name}.jpg")
        print(name, len(out), sum(v["refined"] for v in out.values()))
