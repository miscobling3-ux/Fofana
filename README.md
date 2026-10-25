# Fofana Fútbol — vidéos TikTok d'analyse tactique (en espagnol)

Vidéo prête à poster : **`output/psg_luis_enrique_es.mp4`**. Format TikTok 1080×1920, 30 fps, 70 s, son normalisé à -14 LUFS.

Elle reprend le format de la vidéo de référence (« Luis Enrique est un génie ») : terrain 3D, pions numérotés, chapitres avec barre de progression, sous-titres mot par mot, teinte rouge sur les moments « problème » et outro avec appel aux commentaires. Tout le texte et la voix off sont en **espagnol**.

## Ce qui a été amélioré par rapport à l'original
- Mouvements de caméra fluides (plans larges, zooms, petits « punch-in » sur les moments forts) et léger flottement permanent.
- Titres animés (GENIO, 4 vs 3, ROMBO, TRIÁNGULO, 2025) et accroche visuelle dès la première seconde.
- Flèches de déplacement, « fantômes » des positions d'origine, trou laissé par le central, losange, triangles qui tournent, marquages qui « explosent », joueur libre.
- Musique tendue et bruitages (whoosh, pop, boom, riser) synchronisés, avec la musique qui baisse automatiquement sous la voix.
- Lumières colorées et confettis dorés pour la Ligue des champions 2025, puis un outro « ¿UN GENIO? Dímelo en los comentarios » avec « SÍGUEME ».
- Les sous-titres restent hors des zones couvertes par l'interface TikTok.

## Refaire ou modifier une vidéo
```bash
cd video
./setup.sh                 # une seule fois
python3 make_video.py      # crée output/psg_luis_enrique_es.mp4 (environ 4 min)
python3 make_video.py --stills 5,20,40   # aperçu rapide : quelques images PNG dans video/build/
```
- **Texte / voix** : `video/guion_psg_es.py` → `LINES`. `*mot*` = mot surligné en doré, `{commande}` = animation déclenchée sur ce mot.
- **Nom de la chaîne** : `BRAND = "FOFANA FÚTBOL"`.
- **Voix** : `VOICE` (`em_alex`, `em_santa` ou `ef_dora` pour une voix féminine) et `SPEED`.
- Pour une nouvelle vidéo, copie `guion_psg_es.py` et lance `python3 make_video.py --script mon_script`.

---

# Pixel Story (niche 4) — « La Copa robada »

Deux versions prêtes à poster, format TikTok 1080×1920, 30 fps, son à -14 LUFS :
- **français** : **`output/pixel_story_coupe_fr.mp4`** (75 s, voix ElevenLabs « Adam - Dominant, Firm »), script `video/histoire_coupe_fr.py`
- **espagnol** : **`output/pixel_story_copa_es.mp4`** (79 s, voix ElevenLabs « Adam - Dominant, Firm »), script `video/historia_copa_es.py`

Histoire vraie : en 1966, la Coupe du monde (Jules Rimet) est volée à Londres, puis retrouvée par le chien Pickles. La vidéo se termine sur le second vol de 1983 à Rio, où la coupe n'a jamais été retrouvée.

Le style suit le prompt « Pixel Story » : pixel art 16 bits avec de gros pixels (toile 270×480 agrandie ×4 sans lissage), palette ambre, gris et rouge, ombres tramées, halo de bougie, une seule vignette au centre, étiquettes lieu/date en police pixel, compteurs qui défilent, tampons rouges qui s'écrasent, bulles, transitions en dissolution de pixels ou en balayage, mouvements par à-coups, musique chiptune et bruitages 8 bits. Tout est dessiné en code, sans aucune image externe.

```bash
cd video
python3 pixel_story.py                                # version espagnole (~1 min)
python3 pixel_story.py --script histoire_coupe_fr     # version française
python3 pixel_story.py --stills 5,20,40    # aperçu : quelques PNG dans video/build/
```
- **Texte / voix** : `video/historia_copa_es.py` → `LINES` (scène, texte). `*mot*` = mot-clé en ambre, `1966=mil-novecientos-sesenta-y-seis` = affiché / prononcé, commandes `{label:…}`, `{stamp:…}`, `{count:£15000}`, `{ev:…}`, `{sfx:…}` (les `_` deviennent des espaces).
- **Voix off externe** (ElevenLabs ou ton propre enregistrement) : `VOICE_FILE = "voix/mon_fichier.mp3"` dans le script. Le fichier doit lire les lignes de `LINES` dans l'ordre, avec une petite pause entre chaque ; le moteur le découpe tout seul aux silences et recale les animations. Sans `VOICE_FILE`, c'est la voix Kokoro `VOICE` qui est utilisée.
- **Langue** : `LANG` (`es`, `fr-fr`), `VOICE`, et `TXT` pour les textes dessinés dans les scènes (titre, lettre de rançon, appel à l'action…).
- **Scènes** : fonctions `sc_*` dans `video/pixel_story.py`. **Son** : `video/chiptune.py`.
