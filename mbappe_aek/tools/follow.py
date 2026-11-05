import json,sys
sys.argv=[sys.argv[0]]
import importlib.util
spec=importlib.util.spec_from_file_location("trk","tools/track.py"); trk=importlib.util.module_from_spec(spec); spec.loader.exec_module(trk)
H=json.load(open("work/heads.json"))
def run(clip,finit,pt,r,a,b):
    out={}
    trk.SEGS["tmp"]=(clip,finit,b,pt,r,"","")
    out.update(trk.track("tmp"))
    if a<finit:
        # backward: emulate by tracking on reversed frame order
        orig=trk.img
        trk.img=lambda c,f: orig(c,2*finit-f)
        trk.SEGS["tmp"]=(clip,finit,2*finit-a,pt,r,"","")
        back=trk.track("tmp"); trk.img=orig
        for f,v in back.items(): out[2*finit-f]=v
    return {str(k):[round(v[0],1),round(v[1],1)] for k,v in sorted(out.items())}
F={}
F["FD1"]={"clip":"B","r":7,"pts":run("B",100,(1416,615),7,50,168)}
F["FB2"]={"clip":"B","r":7,"pts":run("B",188,(987,573),7,165,262)}
F["FB3"]={"clip":"A","r":26,"pts":run("A",490,(1192,333),26,490,578)}
F["FD10"]={"clip":"B","r":7,"pts":run("B",312,(1558,540),7,300,372)}
F["FM"]={"clip":"A","r":12,"pts":run("A",778,(1345,584),12,760,870)}
F["FD8"]={"clip":"A","r":14,"pts":run("A",330,(126,292),14,330,368)}
json.dump(F,open("work/follow.json","w"))
print({k:len(v["pts"]) for k,v in F.items()})
