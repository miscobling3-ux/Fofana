#!/usr/bin/env bash
# anim.js = outils communs (moteur de la vidéo actu_mbappe) + scènes de l'histoire
cd "$(dirname "$0")"
{ sed -n '1,63p' ../actu_mbappe/anim.js | sed 's/^const DUR = .*/const DUR = 62.5;/'; cat scenes.js; } > anim.js
