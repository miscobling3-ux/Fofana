"""Pixel Story : la coupe Jules Rimet volée à Londres (1966) et retrouvée par le chien Pickles.

Même format que historia_copa_es.py (voir sa docstring pour les commandes).
Faits : vol le 20 mars 1966 au Central Hall de Westminster (exposition de timbres, timbres estimés à
3 millions de livres) ; rançon de 15 000 £ sous menace de fondre la coupe ; l'intermédiaire Edward
Betchley arrêté ; coupe retrouvée le 27 mars par Pickles sous une haie, emballée dans du journal ;
Pickles invité au banquet des champions ; nouveau vol à Rio en décembre 1983, jamais retrouvée.
"""
from historia_copa_es import EV_SFX, LEVELS  # noqa: F401

BRAND = "FOFANA FÚTBOL"
LANG = "fr-fr"
VOICE = "ff_siwis"
SPEED = 1.0
SUBTITLES = True
OUT = "pixel_story_coupe_fr.mp4"

TXT = {
    "title": ("LA COUPE", "VOLÉE"), "sub": "HISTOIRE VRAIE EN PIXEL ART", "woof": "OUAF !",
    "month": "JUILLET", "cup": "MONDIAL", "note": ("£15.000", "OU LA COUPE", "SERA FONDUE"),
    "trace": "ET LA COUPE ?", "final": "FINALE", "q": ("TU CONNAISSAIS", "CETTE HISTOIRE?"),
    "cta": ("DIS-LE-MOI EN", "COMMENTAIRE"), "follow": "ABONNE-TOI",
}

LINES = [
    ("hook", "En 1966=mille-neuf-cent-soixante-six, quelqu'un a {ev:steal} *volé* la *Coupe du monde*..."),
    ("hook", "et c'est un *chien* qui l'a {ev:dog} retrouvée. {stamp:UN_CHIEN_?}"),

    ("londres", "{label:LONDRES_·_1966} *Londres*, mars 1966=mille-neuf-cent-soixante-six."),
    ("londres", "Le *Mondial* commence {ev:cal} dans quatre mois."),

    ("vitrina", "{label:WESTMINSTER_·_MARS} La coupe *Jules Rimet* est exposée dans un salon de {ev:stamps} *timbres*,"),
    ("vitrina", "protégée par une simple vitrine."),
    ("vitrina", "Mais le dimanche vingt mars, la vitrine {ev:empty} est *vide*. {stamp:VOLÉE}"),

    ("sellos", "Les voleurs ont ignoré des timbres valant {count:£3000000} trois *millions* de livres..."),
    ("sellos", "et n'ont pris {ev:only} que la *coupe*."),

    ("policia", "{label:SCOTLAND_YARD} *Scotland Yard* fouille {ev:search} tout Londres."),
    ("policia", "Mais personne n'a {ev:none} la moindre piste."),

    ("nota", "Peu après, le patron du football anglais reçoit une {ev:note} *lettre*."),
    ("nota", "*Quinze mille livres*, ou la coupe sera *fondue*."),
    ("nota", "La police arrête l'intermédiaire... {stamp:ARRÊTÉ}"),
    ("nota", "mais de la coupe, {ev:trace} *aucune trace*."),

    ("paseo", "{label:SUD_DE_LONDRES_·_27_MARS} Dimanche vingt-sept mars."),
    ("paseo", "David Corbett promène son chien, {ev:name} *Pickles*."),

    ("seto", "Soudain, Pickles s'arrête {ev:sniff} près d'une haie,"),
    ("seto", "et renifle un paquet {ev:parcel} emballé dans du *journal*."),
    ("seto", "David {ev:open} l'ouvre... et n'en croit pas ses yeux. {stamp:RETROUVÉE_!}"),
    ("seto", "C'est la *Coupe du monde*."),

    ("wembley", "{label:WEMBLEY_·_30_JUILLET} Quatre mois plus tard, {ev:score} l'*Angleterre* remporte son seul *Mondial*."),
    ("banquete", "Et Pickles est invité {ev:woof} au *banquet* des champions. {stamp:HÉROS}"),

    ("rio", "{label:RIO_DE_JANEIRO_·_1983} Mais l'histoire ne s'arrête pas là."),
    ("rio", "En 1983=mille-neuf-cent-quatre-vingt-trois, la coupe est {ev:gone} volée *une seconde fois*..."),
    ("rio", "et cette fois, *personne* ne l'a retrouvée. {stamp:PERDUE}"),

    ("outro", "{ev:q} Tu connaissais cette histoire? {ev:cta} Dis-le-moi en commentaire."),
]
