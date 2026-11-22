import json,sys
from faster_whisper import WhisperModel
m=WhisperModel(sys.argv[1],device="cpu",compute_type="int8",cpu_threads=4)
import soundfile as sf
audio,_sr=sf.read(sys.argv[2],dtype="float32")
segs,_=m.transcribe(audio,language="es",word_timestamps=True,beam_size=5,vad_filter=False)
out=[]
for s in segs:
    print(f"[{s.start:6.2f}-{s.end:6.2f}] {s.text}")
    for w in s.words: out.append({"text":w.word.strip(),"start":round(w.start,3),"end":round(w.end,3)})
json.dump(out,open(sys.argv[3],"w"),ensure_ascii=False,indent=0)
