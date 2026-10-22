#!/usr/bin/env bash
# Installe les dépendances (Ubuntu) et télécharge la voix Kokoro (hors-ligne) dans video/models/
set -e
cd "$(dirname "$0")"
sudo apt-get install -y ffmpeg libegl1 fonts-montserrat || apt-get install -y ffmpeg libegl1 fonts-montserrat
pip install skia-python kokoro-onnx soundfile scipy numpy
mkdir -p models
[ -f models/kokoro.onnx ] || curl -L -o models/kokoro.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
[ -f models/voices.bin ] || curl -L -o models/voices.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
echo "OK. Lance : python3 make_video.py"
