"""Vidéo : uña encarnada y padrastros — remontage en espagnol (même format que guion_ongles_fr.py)."""
from guion_ongles_fr import L, SOURCE, BRAND  # noqa: F401

LANG = "es"
# Voix : "em_alex", "em_santa" (homme), "ef_dora" (femme)
VOICE = "em_alex"
SPEED = 1.1
HOOK = ("UÑA ENCARNADA", "lo que nadie te cuenta")
TAGS = {"ok": "BIEN HECHO", "bad": "CUIDADO"}
CTA = ("SÍGUEME", "para más trucos de salud")

LINES = [
    L("¿Alguna vez tuviste una *uña* *encarnada*?", (0.0, 2.2), (1.0, 1.35, 0.62, 0.55)),
    L("La esquina de la uña empieza a crecer *directamente* contra la piel.", (2.2, 6.0), (1.1, 1.45, 0.6, 0.5)),
    L("Con cada paso, el zapato la aprieta, y la uña se *clava* todavía más en la carne.",
      (6.0, 12.0), (1.0, 1.3, 0.65, 0.55)),
    L("Si sigue así, la piel puede *sangrar*, y hasta llenarse de *pus*.", (12.0, 16.0),
      (1.15, 1.55, 0.62, 0.48), tag="bad"),
    L("Para evitarlo, no cortes las esquinas: corta la uña bien *recta*.", (16.0, 20.0),
      (1.0, 1.25, 0.5, 0.55), tag="ok"),
    L("Pero si ya está muy clavada, un especialista tiene que *anestesiar* el dedo,", (20.0, 23.2),
      (1.05, 1.4, 0.55, 0.55)),
    L("meter una pequeña herramienta *debajo* de la uña, para separar la parte enterrada,", (23.2, 28.0),
      (1.1, 1.45, 0.55, 0.55)),
    L("cortar esa franja desde la punta hasta la *raíz*,", (28.0, 31.0), (1.0, 1.3, 0.55, 0.5)),
    L("y sacarla de un *solo* *tirón*.", (31.0, 33.0), (1.3, 1.0, 0.45, 0.4)),
    L("¿Y ese pellejito que sale junto a la uña? Se llama *padrastro*.", (33.0, 37.0),
      (1.0, 1.4, 0.62, 0.42), chapter="¿Y LOS PADRASTROS?"),
    L("Cuando lo jalas, todavía está unido a piel *sana*.", (37.0, 40.0), (1.1, 1.45, 0.55, 0.45)),
    L("Arrancas más de lo que crees, y dejas una pequeña *herida* abierta.", (40.0, 44.0),
      (1.1, 1.5, 0.5, 0.45), tag="bad"),
    L("Te *arde*, puede sangrar, y las *bacterias* tienen una entrada directa.", (44.0, 48.0),
      (1.0, 1.45, 0.4, 0.55), tag="bad"),
    L("Lo mejor es *no* arrancarlo.", (48.0, 50.0), (1.0, 1.2, 0.6, 0.45)),
    L("Córtalo con cuidado con un cortaúñas *limpio*,", (50.0, 52.2), (1.05, 1.35, 0.45, 0.45), tag="ok"),
    L("y después *hidrata* la zona, para que no se vuelva a romper.", (52.2, 55.0),
      (1.0, 1.3, 0.5, 0.5), tag="ok"),
    L("Así que recuerda: aunque te dé tentación, no lo arranques *nunca*.", (55.0, 58.6),
      (1.0, 1.35, 0.52, 0.45)),
    L("*Sígueme* para más trucos de salud.", (58.6, 60.7), (1.35, 1.1, 0.5, 0.45)),
]
