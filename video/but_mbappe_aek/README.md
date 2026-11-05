# Analyse du but de Mbappé — AEK 2-2 Real Madrid (78')

Vidéo : `output/mbappe_aek/mbappe_aek_2-2_fr.mp4` (1080×1920, 30 i/s, 86,7 s, −14 LUFS).
Couvertures : `output/mbappe_aek/couverture_1080x1920.png` et `couverture_1080x1080.png`.

- `script.txt` : texte de la voix off (308 mots, 9 blocs). `voice.json` : un mot par entrée avec début et fin.
- `tools/voice.py` : voix off locale (Kokoro), synthèse segment par segment, compression des silences.
- `tools/track.py`, `tools/fix.py`, `tools/tsheet.py` : suivi des têtes et planches de contrôle.
- `tools/gen.py` + `tools/template.html` : génèrent le projet HyperFrames (EDL, caméra, étiquettes, spotlights, sons).
- `tools/verify_tags.py` : contrôle de la pointe des flèches sur la vidéo rendue.
- `suivis/` : suivis mesurés et position du filigrane.

Rendu : `hyperframes render --fps 30 --crf 20` dans le projet généré.

## Version avec la voix « Adam » (ElevenLabs, fournie)
Vidéo : `output/mbappe_aek/mbappe_aek_2-2_fr_voix_adam.mp4` (77,2 s, −13,9 LUFS).
- Transcription Whisper small (faster-whisper) → `voix_adam_transcription.json`, sous-titres corrigés → `voix_adam_words.json`.
- Montage : `tools/gen2.py` (même gabarit, EDL calée sur cette voix).
