"""Vidéo : ongle incarné et petites peaux (envies) — remontage en français de sources/ongles_source.mp4.

Chaque ligne : L(texte, src=(début, fin) dans la vidéo source, zoom=(zoom départ, zoom fin, centre x, centre y), ...)
  *mot*          -> mot-clé (jaune + petit zoom « punch » sur la vidéo)
  zoom           -> centre en coordonnées 0..1 de l'image source (0.5, 0.5 = milieu)
  tag="ok"/"bad" -> badge « BON GESTE » (vert) ou « ATTENTION » (rouge + teinte rouge)
  chapter="..."  -> grand titre animé au début de la ligne
"""


def L(text, src, zoom, tag=None, chapter=None):
    return dict(text=text, src=src, zoom=zoom, tag=tag, chapter=chapter)


SOURCE = "sources/ongles_source.mp4"
BRAND = "FOFANA"
LANG = "fr-fr"
# Voix : "ff_siwis" (Kokoro, femme), "ff_siwis+am_onyx" (Kokoro, mélange plus grave),
#        "piper:fr-siwis-medium" (femme), "piper:fr-gilles-low" (homme)
VOICE = "ff_siwis"
SPEED = 1.08
HOOK = ("ONGLE INCARNÉ", "ce que personne ne te dit")
TAGS = {"ok": "BON GESTE", "bad": "ATTENTION"}
CTA = ("ABONNE-TOI", "pour plus d'astuces santé")

LINES = [
    L("Tu as déjà eu un *ongle* *incarné* ?", (0.0, 2.2), (1.0, 1.35, 0.62, 0.55)),
    L("Le coin de l'ongle se met à pousser *directement* dans la peau.", (2.2, 6.0), (1.1, 1.45, 0.6, 0.5)),
    L("À chaque pas, la chaussure appuie dessus, et l'ongle s'*enfonce* encore plus dans la chair.",
      (6.0, 12.0), (1.0, 1.3, 0.65, 0.55)),
    L("Si ça continue, la peau peut *saigner*, et même se remplir de *pus*.", (12.0, 16.0),
      (1.15, 1.55, 0.62, 0.48), tag="bad"),
    L("Pour l'éviter, ne coupe jamais les coins : coupe ton ongle bien *droit*.", (16.0, 20.0),
      (1.0, 1.25, 0.5, 0.55), tag="ok"),
    L("Mais s'il est déjà trop enfoncé, un spécialiste doit *anesthésier* l'orteil,", (20.0, 23.2),
      (1.05, 1.4, 0.55, 0.55)),
    L("glisser un petit outil *sous* l'ongle, pour décoller la partie coincée,", (23.2, 28.0),
      (1.1, 1.45, 0.55, 0.55)),
    L("puis couper cette bande, de la pointe jusqu'à la *racine*,", (28.0, 31.0), (1.0, 1.3, 0.55, 0.5)),
    L("et la retirer d'un *seul* *coup* !", (31.0, 33.0), (1.3, 1.0, 0.45, 0.4)),
    L("Et cette petite peau au bord de l'ongle ? On appelle ça une *envie*.", (33.0, 37.0),
      (1.0, 1.4, 0.62, 0.42), chapter="ET LES ENVIES ?"),
    L("Quand tu tires dessus, elle est encore attachée à de la peau *saine*.", (37.0, 40.0),
      (1.1, 1.45, 0.55, 0.45)),
    L("Tu arraches plus que prévu, et tu laisses une petite *plaie* ouverte.", (40.0, 44.0),
      (1.1, 1.5, 0.5, 0.45), tag="bad"),
    L("Ça *brûle*, ça peut saigner, et les *bactéries* ont une porte d'entrée directe.", (44.0, 48.0),
      (1.0, 1.45, 0.4, 0.55), tag="bad"),
    L("Le mieux, c'est de ne *pas* l'arracher.", (48.0, 50.0), (1.0, 1.2, 0.6, 0.45)),
    L("Coupe-la doucement avec un coupe-ongles *propre*,", (50.0, 52.2), (1.05, 1.35, 0.45, 0.45), tag="ok"),
    L("puis *hydrate* la zone, pour qu'elle ne se fende pas à nouveau.", (52.2, 55.0),
      (1.0, 1.3, 0.5, 0.5), tag="ok"),
    L("Alors souviens-toi : même si c'est tentant, ne l'arrache *jamais* !", (55.0, 58.6),
      (1.0, 1.35, 0.52, 0.45)),
    L("*Abonne-toi* pour plus d'astuces santé !", (58.6, 60.7), (1.35, 1.1, 0.5, 0.45)),
]
