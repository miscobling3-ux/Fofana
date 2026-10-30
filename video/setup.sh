#!/usr/bin/env bash
# Installe les dépendances (Ubuntu) et télécharge les voix (hors-ligne) et les polices dans video/models/
set -e
cd "$(dirname "$0")"
sudo apt-get install -y ffmpeg libegl1 || apt-get install -y ffmpeg libegl1 || true
pip install skia-python kokoro-onnx soundfile scipy numpy opencv-python-headless pillow piper-tts
mkdir -p models/fonts
[ -f models/kokoro.onnx ] || curl -L -o models/kokoro.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
[ -f models/voices.bin ] || curl -L -o models/voices.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
# voix Piper françaises (pour remix.py --voice piper:...)
for v in fr-siwis-medium fr-gilles-low; do
  [ -f models/$v.onnx ] || curl -L https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-$v.tar.gz | tar xz -C models
done
for w in Black ExtraBold; do
  [ -f models/fonts/Montserrat-$w.ttf ] || curl -L -o models/fonts/Montserrat-$w.ttf https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/Montserrat-$w.ttf
done
echo "OK. Lance : python3 make_video.py  ou  python3 remix.py --script guion_ongles_fr"
