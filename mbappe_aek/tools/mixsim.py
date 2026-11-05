# Offline measurement of the planned mix (same files, times and volumes as hf/index.html) — analysis only
import re,subprocess,sys
h=open("hf/index.html").read()
items=re.findall(r'<audio id="[^"]+" class="clip" src="([^"]+)" data-start="([\d.]+)" data-duration="([\d.]+)" data-volume="([\d.]+)"',h)
args=[];flt=[]
for i,(src,st,du,vol) in enumerate(items):
    args+=["-i","hf/"+src]
    d=int(float(st)*1000)
    flt.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=mono,atrim=0:{du},volume={vol},adelay={d}|{d}[a{i}]")
mix="".join(f"[a{i}]" for i in range(len(items)))+f"amix=inputs={len(items)}:normalize=0:duration=longest,atrim=0:59.9,ebur128=peak=true[o]"
cmd=["ffmpeg","-v","info","-nostats"]+args+["-filter_complex",";".join(flt)+";"+mix,"-map","[o]","-f","null","-"]
out=subprocess.run(cmd,capture_output=True,text=True).stderr
s=out[out.rfind("Summary"):]
print(len(items), re.findall(r"I:\s+(-?[\d.]+) LUFS",s), re.findall(r"Peak:\s+(-?[\d.]+) dBFS",s))
