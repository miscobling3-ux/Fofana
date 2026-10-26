"""Vidéo : Balón de Oro 2026 — écran de sélection arcade, finalistes et pronostic (version espagnole).

Même syntaxe que guion_psg_es.py : {cmd:arg} déclenche une action sur le mot suivant, *mot* = mot-clé doré,
affiché=prononcé pour corriger la prononciation (ex. Harry=Jarri).
Commandes : scene:<boot|title|champ|grid|finalists|p1|p2|vs|predict|winner|cta>, coin, qmark, pick:<id>,
stat:<texte_avec_tirets_bas>, fav, winner, shake.
"""

BRAND = "FOFANA FÚTBOL"
VOICE = "em_alex"
SPEED = 1.1
OUTRO_LEN = 2.5

# grille 2 x 5 (portraits dans assets/players/<id>.png)
GRID = ["kane", "yamal", "mbappe", "dembele", "rodri", "olise", "kvara", "vitinha", "ruiz", "messi"]
PLAYERS = {
    "kane": dict(name="HARRY KANE", club="BAYERN · ING", fact="73 GOLES"),
    "yamal": dict(name="LAMINE YAMAL", club="BARÇA · ESP", fact="CAMPEÓN DEL MUNDO"),
    "mbappe": dict(name="MBAPPÉ", club="REAL MADRID · FRA", fact="BOTA DE ORO MUNDIAL"),
    "dembele": dict(name="DEMBÉLÉ", club="PSG · FRA", fact="BALÓN DE ORO 2025"),
    "rodri": dict(name="RODRI", club="MAN. CITY · ESP", fact="MVP DEL MUNDIAL"),
    "olise": dict(name="OLISE", club="BAYERN · FRA", fact="REY DE LAS ASISTENCIAS"),
    "kvara": dict(name="KVARATSKHELIA", club="PSG · GEO", fact="CAMPEÓN DE EUROPA"),
    "vitinha": dict(name="VITINHA", club="PSG · POR", fact="CAMPEÓN DE EUROPA"),
    "ruiz": dict(name="FABIÁN RUIZ", club="PSG · ESP", fact="CAMPEÓN DE EUROPA"),
    "messi": dict(name="MESSI", club="INTER MIAMI · ARG", fact="VUELVE A LA LISTA"),
}

LINES = [
    "{scene:boot}Esta noche, el mundo del fútbol tiene los ojos puestos en {coin}*Londres*.",
    "{scene:title}{shake:0.6}Es la edición número *setenta* del *Balón* *de* *Oro*, y por primera vez, la gala se celebra en *Londres*.",
    "{scene:champ}*Ousmane* *Dembélé* pone en juego su *corona*.",
    "Pero... ¿quién será su {qmark}*sucesor*?",
    "{scene:grid}Estos son *diez* de los *treinta* nominados.",
    "{pick:mbappe}*Kylian* *Mbappé*, Bota de Oro del Mundial.",
    "{pick:rodri}*Rodri*, mejor jugador del Mundial.",
    "{pick:olise}*Olise*, el rey de las asistencias.",
    "{pick:kvara}*Kvaratskhelia*, {pick:vitinha}*Vitinha* y {pick:ruiz}*Fabián* *Ruiz*, otra vez campeones de Europa con el PSG.",
    "Y {pick:messi}*Lionel* *Messi*... vuelve a la lista.",
    "{scene:finalists}{shake:0.5}Pero esta noche, todo se decide entre *dos* jugadores.",
    "{scene:p1}Jugador uno: *Harry=Jarri* *Kane.=Kein.* {stat:73_GOLES}*Setenta* *y* *tres* goles con el Bayern e Inglaterra, {stat:BOTA_DE_ORO_EUROPEA}*Bota* *de* *Oro* europea, y {stat:PICHICHI_BUNDESLIGA_x3}máximo goleador de la Bundesliga por tercera vez.",
    "{scene:p2}Jugador dos: *Lamine* *Yamal*. {stat:CAMPEÓN_DEL_MUNDO}Campeón del *mundo* con España, {stat:CAMPEÓN_DE_LIGA}campeón de *Liga* con el Barça, y {stat:MVP_DE_LALIGA}mejor jugador de *LaLiga*.",
    "{scene:vs}{shake:0.7}Las casas de apuestas lo tienen claro: Harry=Jarri Kane=Kein es el gran {fav}*favorito*.",
    "{scene:predict}Y mi predicción... el Balón de Oro dos mil veintiséis... es para...",
    "{scene:winner}{winner}{shake:1.2}*¡Harry=¡Jarri* *Kane!=Kein!*",
    "{scene:cta}¿Y tú? *¿Kane=¿Kein* o *Lamine*? Te leo en comentarios.",
]

# caméra : (zoom, centre vertical) à chaque scène — 1.0 = borne entière, 1.24 = écran plein cadre
CAMERA = {
    "boot": (1.0, 960), "title": (1.12, 880), "champ": (1.24, 830), "grid": (1.24, 830),
    "finalists": (1.2, 850), "p1": (1.24, 830), "p2": (1.24, 830), "vs": (1.1, 900),
    "predict": (1.26, 820), "winner": (1.3, 815), "cta": (1.05, 940),
}

# intensité de la musique par scène (0 = calme, 1 = à fond)
MUSIC = {
    "boot": 0.3, "title": 0.6, "champ": 0.6, "grid": 1.0, "finalists": 0.8, "p1": 1.0, "p2": 1.0,
    "vs": 1.0, "predict": 0.2, "winner": 1.0, "cta": 0.7,
}
