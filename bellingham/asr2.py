# Transcription (Whisper small, sherpa-onnx) par phrases de 25 s pour vérifier la prononciation
import sys, numpy as np, soundfile as sf, sherpa_onnx, scipy.signal as ss
D='/home/user/Fofana/video/models/sherpa-onnx-whisper-small'
r=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f'{D}/small-encoder.int8.onnx',decoder=f'{D}/small-decoder.int8.onnx',tokens=f'{D}/small-tokens.txt',language=sys.argv[2] if len(sys.argv)>2 else "fr",task='transcribe')
x,sr=sf.read(sys.argv[1]); x=ss.resample_poly(x,16000,sr).astype(np.float32)
for i in range(0,len(x),16000*25):
    s=r.create_stream(); s.accept_waveform(16000,x[i:i+16000*25]); r.decode_stream(s); print(f'[{i//16000}s]',s.result.text)
