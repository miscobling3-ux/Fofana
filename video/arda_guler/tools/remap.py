import json
def loadmap(S):
    m=json.load(open(f'{S}/vo/cutmap.json'))['map']
    def f(t):
        for a,b,n in m:
            if t<=b+1e-6:
                return n+max(0,t-a) if t>=a else n
        a,b,n=m[-1];return n+t-a
    return f
