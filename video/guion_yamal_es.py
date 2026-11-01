"""Gol de Lamine Yamal (Barça - Alavés) : texte de la voix off, découpé en plans.

Chaque phrase = un plan du montage (voir yamal.py -> SHOTS).
Pas de sous-titres, pas de musique : seulement la voix off et quelques bruitages.
"""
LANG = "es"
VOICE = "em_alex"   # "em_alex", "em_santa" (homme) ou "ef_dora" (femme)
SPEED = 1.08

LINES = [
    "Este gol de Lamine Yamal en esta jugada nos demuestra por qué el tiki-taka es una de las mejores tácticas del mundo.",
    "El Barcelona tiene el balón con Pedri en el centro del campo.",
    "Controla la pelota y hace un pase hacia un costado.",
    "El lateral controla el balón antes de jugarlo hacia Fermín López en la entrada del área.",
    "Cuando Fermín recibe la pelota, la mayoría de los jugadores habría hecho un pase hacia el lateral que se mueve a la espalda de la defensa,",
    "pero este está bloqueado por un defensor.",
    "Fermín descarta entonces esa opción, levanta la cabeza para buscar otra solución",
    "y se da cuenta de que Cancelo está dentro del área, en un espacio reducido y rodeado por tres defensores.",
    "Fermín López le envía entonces un pase dentro del área",
    "y sin siquiera controlar el balón, Cancelo se lo devuelve directamente a Lamine Yamal.",
    "Lamine Yamal ve llegar el balón y se coloca inmediatamente en posición de disparo.",
    "Levanta la mano derecha, planta el pie de apoyo en el suelo",
    "y en ese momento ya se puede sentir que está preparando un misil.",
    "Cuando llega el balón, Lamine Yamal conecta un disparo magnífico que termina en el fondo de la portería rival.",
]

# Voix enregistrée (ElevenLabs, « Adam ») : si le fichier existe, elle remplace la voix de synthèse.
# LINE_STARTS = début de chaque phrase dans ce fichier (s), mesuré sur les pauses ; les plans sont calés dessus.
VOICE_FILE = "sources/yamal_voz.mp3"
LINE_STARTS = [0.0, 6.86, 10.37, 13.67, 18.85, 26.46, 29.20, 34.41, 41.44, 44.79, 50.29, 55.27, 58.79, 62.81]
VOICE_END = 68.91
