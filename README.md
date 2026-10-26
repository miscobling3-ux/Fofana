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

# Vidéo 2 — Balón de Oro 2026, style borne d'arcade

Vidéo prête à poster : **`output/balon_de_oro_2026_es.mp4`**. Format 1080×1920, 66 s, voix et textes en espagnol.

Le déroulé reprend l'image de référence, une borne d'arcade avec un écran de sélection de personnages :
1. La borne s'allume (INSERT COIN), puis l'écran titre « BALÓN DE ORO 2026 · 70ª EDICIÓN · LONDRES » avec la skyline de Londres.
2. Dembélé, tenant du titre, avec sa couronne, puis « ¿SU SUCESOR? ».
3. L'écran de sélection avec 10 des 30 nominés (Kane, Yamal, Mbappé, Dembélé, Rodri, Olise, Kvaratskhelia, Vitinha, Fabián Ruiz, Messi). Le curseur 1P passe sur chaque joueur cité, avec son club et un fait marquant.
4. Les 2 finalistes, Kane (1P) contre Yamal (2P), avec leurs stats qui s'affichent au fil de la voix, puis l'écran VS avec le tampon « FAVORITO ».
5. Le pronostic : roulette entre les deux joueurs, puis « ¡GANADOR! HARRY KANE » avec fanfare et confettis.
6. L'appel aux commentaires : « ¿Kane o Lamine? ».

Effets : écran CRT (lignes de balayage, lueur, reflet), manettes et boutons qui bougent, musique chiptune 8 bits et bruitages d'arcade.

- Portraits : générés avec ElevenLabs (gpt-image) en style pixel art, dans `video/assets/players/`.
- Faits : liste officielle des nommés, cérémonie du 26/10/2026 au London Palladium, cotes des bookmakers avant la cérémonie (Kane favori). **Le vainqueur annoncé est un pronostic.**

Refaire la vidéo : `cd video && python3 make_arcade.py`. Le texte se modifie dans `video/guion_balon_oro_es.py`.

---

# Vidéo 3 — Balón de Oro 2026 : mon top 10, avec photo + stats de chaque joueur

Vidéo prête à poster : **`output/balon_de_oro_2026_top10_es.mp4`**. Format 1080×1920, 1 min 49 s, en espagnol.

- **Intro sur la borne d'arcade** (Londres, 70ª edición, Dembélé tenant du titre, grille « TOP 10 »), puis plongée dans l'écran.
- **Un segment par joueur**, du n°10 au n°1 : Fabián Ruiz, Vitinha, Dembélé, Messi, Kvaratskhelia, Olise, Rodri, Mbappé, Yamal, Kane. À chaque fois, la photo apparaît quand on cite son nom. Le cadre s'ouvre ensuite en deux, et chaque statistique arrive **une par une** dans un disque relié par des lignes fines, puis s'ajoute à la liste sous la photo. C'est le style de la vidéo de référence : cadre octogonal noir et blanc, petit texte + grand mot, transitions en zoom, faisceaux de lumière.
- **Les 2 finalistes** : le disque « 2 » devient le rond central d'un terrain. Yamal et Kane passent sur fond noir.
- **Fin** : FAVORITO, pronostic (projecteur qui hésite), Kane en couleur avec confettis, puis retour sur la borne « ¿Kane o Lamine? ».

Refaire : `cd video && python3 make_top10.py`. Le texte et les stats sont dans `video/guion_top10_es.py`.

**Voix ElevenLabs (Adam - Dominant, Firm).** Si des fichiers `video/assets/voice_adam/00.wav`, `01.wav`, … existent (un par ligne de `LINES`), ils remplacent automatiquement la voix de synthèse au prochain rendu.
