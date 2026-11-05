"""Corrections manuelles : fix.py track.json f0 f1 dx dy [f0 f1 dx dy ...] (interpolé linéairement si dy0:dy1)"""
import sys, json
T = json.load(open(sys.argv[1])); a = sys.argv[2:]
for i in range(0, len(a), 4):
    f0, f1 = int(a[i]), int(a[i+1]); dx, dy = a[i+2], a[i+3]
    def rng(v):
        p = v.split(':'); return (float(p[0]), float(p[-1]))
    dx0, dx1 = rng(dx); dy0, dy1 = rng(dy)
    for f in range(f0, f1 + 1):
        if str(f) not in T: continue
        t = 0 if f1 == f0 else (f - f0) / (f1 - f0)
        T[str(f)]['head'][0] += dx0 + (dx1 - dx0) * t; T[str(f)]['head'][1] += dy0 + (dy1 - dy0) * t
        T[str(f)]['src'] = 'man'
json.dump(T, open(sys.argv[1], 'w'))
