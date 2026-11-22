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

# Vidéos « santé » remontées : ongle incarné et petites peaux (FR + ES)

Vidéos prêtes à poster : **`output/ongles_fr.mp4`** (français, 55 s) et **`output/ongles_es.mp4`** (espagnol, 60 s). Format 1080×1920, 30 fps, son à -14 LUFS.

Elles sont remontées à partir de `video/sources/ongles_source.mp4` :
- Nouveau texte (réécrit), nouvelle voix off, nouveaux sous-titres. Les anciens sous-titres incrustés sont effacés.
- Zoom lent sur la zone importante de chaque plan, petit zoom « punch » sur chaque mot-clé, recadrage + flash + whoosh à chaque phrase.
- Sous-titres mot par mot : mot prononcé surligné en rose, mots-clés en jaune.
- Titre d'accroche (ONGLE INCARNÉ), titre de chapitre (ET LES ENVIES ?), badges « BON GESTE » / « ATTENTION » (avec teinte rouge), barre de progression et écran final « ABONNE-TOI ».
- Musique et bruitages synthétisés, avec la musique qui baisse sous la voix.

## Choisir la voix
Les extraits sont dans `output/voix/` :

| Fichier | Voix | Réglage `VOICE` |
|---|---|---|
| `fr_1_femme_kokoro_siwis.mp3` | Femme, la plus naturelle (utilisée par défaut) | `ff_siwis` |
| `fr_2_homme_kokoro_grave.mp3` | Voix plus grave (mélange de deux voix) | `ff_siwis+am_onyx` |
| `fr_3_femme_piper_siwis.mp3` | Femme, plus posée | `piper:fr-siwis-medium` |
| `fr_4_homme_piper_gilles.mp3` | Homme, plus robotique | `piper:fr-gilles-low` |
| `es_1_homme_alex.mp3` | Espagnol, homme (utilisée par défaut) | `em_alex` |
| `es_2_homme_santa.mp3` | Espagnol, homme | `em_santa` |
| `es_3_femme_dora.mp3` | Espagnol, femme | `ef_dora` |

```bash
cd video
./setup.sh                                          # une seule fois
python3 remix.py --script guion_ongles_fr           # -> output/ongles_fr.mp4 (environ 3 min)
python3 remix.py --script guion_ongles_es           # -> output/ongles_es.mp4
python3 remix.py --script guion_ongles_fr --voice piper:fr-gilles-low --out ../output/ongles_fr_homme.mp4
python3 remix.py --script guion_ongles_fr --stills 2,14,45   # aperçu rapide en PNG dans video/build/
```
- **Texte, zooms et badges** : `video/guion_ongles_fr.py` / `guion_ongles_es.py` → `LINES`. Chaque phrase indique le passage de la vidéo source (`src`) et le zoom (`zoom=(départ, fin, centre x, centre y)`).
- **Autre vidéo source** : copie un script, change `SOURCE` et les passages. Si la source n'a pas de sous-titres au même endroit, adapte `BAND` / `WATERMARK` dans `remix.py`.

---

# Analyse d'un but : Fermín López (Barça 2-2 Villarreal, 60') — espagnol

Vidéo prête à poster : **`output/fermin_lopez_es.mp4`** (1080×1920, 30 fps, H.264 + AAC, voix off espagnole fournie, durée = durée de la voix).
Couvertures : `output/fermin_cover_9x16.png` et `output/fermin_cover_1x1.png`.

Montage fait avec **HyperFrames** (`video/fermin_hf/`, HTML + GSAP), selon le master prompt v3 :
recadrage 9:16 qui suit le joueur (sans jamais montrer le score télé, le filigrane ni le hashtag),
étiquette flèche rouge + nom + logo au-dessus du porteur du ballon, effet projecteur sur le joueur nommé,
sous-titres mot par mot, bandeau de score qui passe de 1-2 à 2-2, sons Mixkit, aucun son d'origine.

## Refaire la vidéo
```bash
cd video/fermin_hf
# 1. extraire les images des deux clips (50 i/s) dans deux dossiers
ffmpeg -i clipA.mov -vsync 0 -q:v 2 frames_a/%04d.jpg   # direct
ffmpeg -i clipB.mov -vsync 0 -q:v 2 frames_b/%04d.jpg   # ralentis
# 2. générer la composition (index.html) à partir du plan, du suivi et de data/words.json
python3 tools/build.py --frames-a frames_a --frames-b frames_b
npx hyperframes check
npx hyperframes render --fps 30 --crf 20 -o renders/final.mp4
# 3. vérifier la vidéo finale (étiquettes image par image, image propre, bonne image source)
python3 tools/verify.py renders/final.mp4 frames_a frames_b renders/verif
```
- **Plan de montage** : `tools/plan.py` (`SEGMENTS` : temps de sortie, plan source, vitesse, cibles caméra, étiquettes, projecteurs).
- **Suivi des joueurs** : `data/tracks/*.json` (produits par `tools/track.py`, contrôlés image par image).
- **Texte / timing** : `data/script_es.txt` et `data/words.json` (alignement script ↔ transcription).
