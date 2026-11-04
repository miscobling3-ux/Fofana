# Analyse du but de Koita — AEK 1-0 Real Madrid (12e), version française

Vidéo prête à poster : **`out/koita_but_fr.mp4`** (1080×1920, 30 i/s, H.264 + AAC).
Couvertures : `out/couverture_1080x1920.png` et `out/couverture_1080x1080.png`.

Faite en suivant le master prompt v3 « analyse d'un but ».

## Chaîne de fabrication
1. **Analyse** (`analysis/`, Python + OpenCV, analyse seulement) : images clés posées à la main sur grille
   zoomée de 10 px (`heads.py`), interpolation + affinage automatique du haut de la tête, cercles du
   projecteur (`spots.py`), planches de contrôle.
2. **Voix** : `make_voice.py` (2 prises), `process_voice.py` (silences RMS 20 ms / −38 dB ramenés à
   0,06 s, limiteur −2 dBTP, `words.json` aligné sur le script).
3. **Montage** : `build_comp.py` écrit `hf/index.html` (HyperFrames + GSAP) : chaque image source
   50 i/s est un `<img class="clip">`, caméra 9:16 qui suit le joueur, étiquettes, projecteur,
   sous-titres mot à mot, bandeau de score, bruitages.
4. **Rendu** : `cd hf && hyperframes check && hyperframes render --fps 30 --crf 20`.
5. **Vérification** : `verify.py out/koita_but_fr.mp4` (étiquettes image par image, bonne image
   source, image propre, synchro, son, durée).

Les clips source (non versionnés) sont attendus extraits en JPEG dans le dossier `SRC` indiqué dans
les scripts (`ffmpeg -i clip.mp4 -q:v 2 A/%04d.jpg`).
