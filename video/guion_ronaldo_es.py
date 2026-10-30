"""Vidéo : les gestes de respect de Cristiano Ronaldo — montage en espagnol à partir de 4 vidéos (montage.py).

Chaque ligne : L(texte, plans=[(source, début, fin), …], zoom=(zoom départ, zoom fin, centre x, centre y), …)
  *mot*        -> mot-clé (jaune + petit zoom « punch »)
  plans        -> passages des vidéos sources joués pendant la phrase (accélérés / ralentis pour tomber juste)
  tag="..."    -> étiquette jaune en haut (nom du joueur, lieu…)
  chapter="…"  -> grand titre animé au début de la ligne
"""


def L(text, shots, zoom=(1.0, 1.15, 0.5, 0.5), tag=None, chapter=None):
    return dict(text=text, shots=shots, zoom=zoom, tag=tag, chapter=chapter)


SOURCES = {
    "R": "sources/ronaldo_respeto.mp4",  # compilation principale (suit le texte)
    "F": "sources/ronaldo_fans.mp4",     # fans / enfants (légendes anglaises en bas : on zoome au-dessus)
    "N": "sources/ronaldo_ninos.mp4",    # enfants sur le terrain
    "G": "sources/ronaldo_nina.mp4",     # petite fille en fauteuil, Portugal
}
BRAND = "FOFANA FÚTBOL"
LANG = "es"
# Voix locale (Kokoro) : "em_alex", "em_santa". Voix ElevenLabs : --voice-dir (un fichier par phrase)
VOICE = "em_alex"
SPEED = 1.12
BPM, SEED = 92, 23
HOOK = ("RESPETO", "mira bien este momento")
CTA = ("ESCRIBE «RESPETO»", "en los comentarios")

LINES = [
    L("Mira bien este momento primero.", [("R", 0.0, 1.8)], (1.0, 1.2, 0.45, 0.45)),
    L("Cristiano Ronaldo es *sustituido* y empieza a salir del campo.", [("R", 1.0, 2.6)],
      (1.1, 1.3, 0.55, 0.5), tag="PORTUGAL vs HUNGRÍA"),
    L("Un momento normal, ¿verdad? Pero Ronaldo hace algo *más*.", [("R", 1.6, 2.4)], (1.25, 1.45, 0.6, 0.55),
      tag="PORTUGAL vs HUNGRÍA"),
    L("Antes de irse, se toma el tiempo de saludar a Dominik *Szoboszlai*, un enorme fan suyo.",
      [("R", 2.0, 3.9)], (1.15, 1.35, 0.5, 0.55), tag="SZOBOSZLAI"),
    L("*Respeto* total.", [("R", 2.3, 2.9)], (1.4, 1.6, 0.48, 0.55), tag="SZOBOSZLAI"),
    L("Luego, termina el partido. Portugal *gana* y un jugador rival se acerca a Ronaldo para pedirle su "
      "*camiseta*.", [("R", 4.0, 10.0)], (1.05, 1.25, 0.5, 0.45), tag="FIN DEL PARTIDO"),
    L("Ronaldo se mantiene tranquilo, respetuoso y *acepta*.", [("R", 10.0, 13.9)], (1.15, 1.35, 0.5, 0.45),
      tag="FIN DEL PARTIDO"),
    L("Más tarde, en el *vestuario*, realmente le entrega la camiseta.", [("R", 14.0, 15.9)],
      (1.0, 1.15, 0.5, 0.5), tag="EN EL VESTUARIO"),
    L("Solo mira la *felicidad* en el rostro del jugador. Lo dice todo.", [("R", 14.0, 15.9)],
      (1.25, 1.5, 0.5, 0.3), tag="EN EL VESTUARIO"),
    L("Pero espera, todavía no *termina*.", [("R", 20.0, 21.0)], (1.0, 1.2, 0.5, 0.5), chapter="¡NO TERMINA!"),
    L("En otro momento, *Georgia* derrota a Portugal. Todos los jugadores georgianos celebran como *locos*,",
      [("R", 20.0, 23.4)], (1.0, 1.2, 0.5, 0.5), tag="GEORGIA vs PORTUGAL"),
    L("pero Khvicha *Kvaratskhelia* hace algo diferente. Va directamente hacia Ronaldo y le pide su camiseta.",
      [("R", 23.4, 27.9)], (1.05, 1.3, 0.5, 0.5), tag="KVARATSKHELIA"),
    L("Incluso después de la *derrota*, Ronaldo acepta y se la entrega en el vestuario.",
      [("R", 26.0, 27.9), ("R", 28.0, 29.9)], (1.0, 1.15, 0.5, 0.5), tag="KVARATSKHELIA"),
    L("Pura *clase*.", [("R", 28.6, 29.9)], (1.3, 1.5, 0.5, 0.4), tag="KVARATSKHELIA"),
    L("Otra escena poderosa. Durante una jugada, Ronaldo le hace falta a Frank *Lampard* y se disculpa "
      "*inmediatamente*.", [("R", 30.0, 36.9)], (1.0, 1.2, 0.5, 0.5), tag="LAMPARD"),
    L("*Respeto*.", [("R", 34.0, 35.5)], (1.3, 1.45, 0.5, 0.45), tag="LAMPARD"),
    L("Luego, cerca de las gradas *VIP*, un fan reconoce a Ronaldo mientras se toma una foto.",
      [("R", 16.0, 18.0)], (1.0, 1.15, 0.5, 0.55), tag="GRADAS VIP"),
    L("Ronaldo se detiene de *repente* y aparece en la foto con él.", [("R", 17.0, 19.9)],
      (1.2, 1.4, 0.5, 0.6), tag="GRADAS VIP"),
    L("Después de ganar el *Balón* *de* *Oro* en el Santiago Bernabéu, Ronaldo llama a un hombre mayor,",
      [("R", 37.0, 42.9)], (1.0, 1.2, 0.5, 0.5), tag="BALÓN DE ORO"),
    L("lo invita a entrar en la foto de celebración e incluso pone el Balón de Oro en sus *manos*.",
      [("R", 43.0, 47.9)], (1.05, 1.3, 0.5, 0.55), tag="BALÓN DE ORO"),
    L("Antes de un partido contra *Turquía*, un niño pequeño corre inesperadamente al campo hacia Ronaldo.",
      [("R", 54.0, 55.9), ("R", 48.0, 49.5)], (1.0, 1.2, 0.5, 0.5), tag="PORTUGAL vs TURQUÍA"),
    L("En lugar de ignorarlo, Ronaldo se detiene y se toma una foto con él. Un momento *mágico*.",
      [("R", 49.5, 51.9), ("R", 52.0, 53.9)], (1.0, 1.15, 0.5, 0.5), tag="PORTUGAL vs TURQUÍA"),
    L("Y finalmente, otro gesto que demuestra todo sobre su *carácter*.", [("G", 0.5, 6.0), ("G", 14.0, 18.0)],
      (1.0, 1.15, 0.5, 0.45), chapter="SU CARÁCTER"),
    L("Durante un partido, Edinson *Cavani* se lesiona y tiene dificultades para salir del campo.",
      [("R", 56.0, 57.9)], (1.0, 1.2, 0.5, 0.5), tag="CAVANI"),
    L("Cristiano Ronaldo va a *ayudarlo*.", [("R", 57.0, 58.9)], (1.15, 1.35, 0.5, 0.45), tag="CAVANI"),
    L("No le importa el marcador, no le importa que Cavani sea un *rival*, simplemente lo ayuda a salir del "
      "terreno de juego.", [("R", 59.0, 61.9), ("R", 65.0, 69.3)], (1.0, 1.2, 0.5, 0.5), tag="CAVANI"),
    L("Respeto entre *guerreros*, respeto entre *leyendas*.", [("F", 30.0, 35.0), ("G", 22.0, 27.0)],
      (1.3, 1.4, 0.5, 0.4)),
    L("Si tú también respetas esto, escribe *“respeto”* en los comentarios.", [("R", 45.0, 47.9)],
      (1.05, 1.2, 0.5, 0.5)),
]
