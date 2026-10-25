"""Pixel Story : la Copa Jules Rimet robada en Londres (1966) y encontrada por el perro Pickles.

Chaque ligne : (scène, texte). `*mot*` = mot-clé en ambre, `affiché=parlé` pour les nombres,
{commande:argument} déclenchée sur le mot (les _ deviennent des espaces) :
  {label:TEXTE}  étiquette lieu / date en haut     {stamp:TEXTE}  tampon rouge qui s'écrase
  {count:£15000} compteur qui défile                {ev:nom}       animation propre à la scène
  {sfx:nom}      bruitage
"""

BRAND = "FOFANA FÚTBOL"
VOICE = "em_alex"
# voix off ElevenLabs « Adam - Dominant, Firm » (eleven_v4) ; sans ce fichier, voix Kokoro VOICE
VOICE_FILE = "voix/adam_copa_es.mp3"
SPEED = 1.0
SUBTITLES = True

LINES = [
    ("hook", "En 1966=mil-novecientos-sesenta-y-seis, alguien {ev:steal} *robó* la *Copa del Mundo*..."),
    ("hook", "y quien la encontró {ev:dog} fue un *perro*. {stamp:¿UN_PERRO?}"),

    ("londres", "{label:LONDRES_·_1966} *Londres*, marzo de 1966=mil-novecientos-sesenta-y-seis."),
    ("londres", "Faltan cuatro meses {ev:cal} para el *Mundial*."),

    ("vitrina", "{label:WESTMINSTER_·_MARZO} La copa *Jules Rimet* se exhibe en una feria de {ev:stamps} *sellos*,"),
    ("vitrina", "protegida por una simple vitrina."),
    ("vitrina", "Pero el domingo veinte de marzo, la vitrina {ev:empty} aparece *vacía*. {stamp:ROBADA}"),

    ("sellos", "Los ladrones ignoraron sellos que valían {count:£3000000} *millones*..."),
    ("sellos", "y se llevaron {ev:only} solo la *copa*."),

    ("policia", "{label:SCOTLAND_YARD} *Scotland Yard* busca por {ev:search} todo Londres."),
    ("policia", "Pero nadie tiene {ev:none} ni una pista."),

    ("nota", "Días después, llega una {ev:note} *carta*:"),
    ("nota", "*quince mil libras*, o la copa será *fundida*."),
    ("nota", "La policía atrapa al mensajero... {stamp:DETENIDO}"),
    ("nota", "pero de la copa, {ev:trace} *ni rastro*."),

    ("paseo", "{label:SUR_DE_LONDRES_·_27_MARZO} Domingo veintisiete de marzo."),
    ("paseo", "David Corbett saca a pasear a su perro: {ev:name} *Pickles*."),

    ("seto", "De repente, Pickles se detiene {ev:sniff} junto a un seto,"),
    ("seto", "y olfatea un paquete {ev:parcel} envuelto en *periódico*."),
    ("seto", "David lo {ev:open} abre... y no puede creerlo. {stamp:¡ENCONTRADA!}"),
    ("seto", "Es la *Copa del Mundo*."),

    ("wembley", "{label:WEMBLEY_·_30_JULIO} Cuatro meses después, {ev:score} *Inglaterra* gana su único *Mundial*."),
    ("banquete", "Y Pickles es invitado {ev:woof} al *banquete* de los campeones. {stamp:HÉROE}"),

    ("rio", "{label:RÍO_DE_JANEIRO_·_1983} Pero la historia no acaba ahí."),
    ("rio", "En 1983=mil-novecientos-ochenta-y-tres, la copa fue {ev:gone} robada *otra vez*..."),
    ("rio", "y esta vez, *nadie* la encontró. {stamp:PERDIDA}"),

    ("outro", "{ev:q} ¿Conocías esta historia? {ev:cta} Dímelo en los comentarios."),
]

# intensité de la musique par scène (0 = calme, 1 = tension maximale)
LEVELS = {
    "hook": 0.7, "londres": 0.3, "vitrina": 0.5, "sellos": 0.8, "policia": 0.7, "nota": 0.9,
    "paseo": 0.25, "seto": 0.6, "wembley": 1.0, "banquete": 0.5, "rio": 0.7, "outro": 0.4,
}

# bruitage joué automatiquement sur chaque {ev:...}
EV_SFX = {
    "steal": "sweep", "dog": "bark", "cal": "blip", "stamps": "blip", "empty": "alarm", "only": "blip",
    "search": "blip", "none": "blip", "note": "blip", "trace": "blip", "name": "blip", "sniff": "bark",
    "parcel": "sparkle", "open": "jingle", "score": "jingle", "woof": "bark", "gone": "sweep",
    "q": "blip", "cta": "coin",
}

OUT = "pixel_story_copa_es.mp4"
