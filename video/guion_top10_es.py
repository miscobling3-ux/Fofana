"""Vidéo : Balón de Oro 2026 — mon top 10 des nommés, chaque joueur avec sa photo et ses stats une par une.

Intro sur la borne d'arcade, puis plongée dans l'écran vers le style « éditorial » de la référence.
Syntaxe : {cmd:arg} sur le mot suivant, *mot* doré, affiché=prononcé.
Commandes : scene:<boot|title|champ|grid|cta> (borne), coin, qmark, dive (entrée dans l'écran),
player:<id>:<rang>, stat:<VALEUR>|<libellé_avec_tirets_bas>, two, fav, predict, winner.
"""

BRAND = "FOFANA FÚTBOL"
VOICE = "em_alex"
SPEED = 1.1
OUTRO_LEN = 2.5
# voix off ElevenLabs (Adam - Dominant, Firm) : si ce fichier existe, il remplace la voix Kokoro ligne par ligne
ELEVEN_VOICE_DIR = "assets/voice_adam"

GRID = ["kane", "yamal", "mbappe", "dembele", "rodri", "olise", "kvara", "vitinha", "ruiz", "messi"]
GRID_TITLE = ("TOP 10", "NOMINADOS")
RANK_WORDS = {10: "diez", 9: "nueve", 8: "ocho", 7: "siete", 6: "seis", 5: "cinco", 4: "cuatro", 3: "tres",
              2: "dos", 1: "uno"}
PLAYERS = {
    "kane": dict(name="HARRY KANE", club="BAYERN · INGLATERRA", fact="73 GOLES"),
    "yamal": dict(name="LAMINE YAMAL", club="BARÇA · ESPAÑA", fact="CAMPEÓN DEL MUNDO"),
    "mbappe": dict(name="KYLIAN MBAPPÉ", club="REAL MADRID · FRANCIA", fact="BOTA DE ORO MUNDIAL"),
    "dembele": dict(name="OUSMANE DEMBÉLÉ", club="PSG · FRANCIA", fact="BALÓN DE ORO 2025"),
    "rodri": dict(name="RODRI", club="MAN. CITY · ESPAÑA", fact="MVP DEL MUNDIAL"),
    "olise": dict(name="MICHAEL OLISE", club="BAYERN · FRANCIA", fact="REY DE LAS ASISTENCIAS"),
    "kvara": dict(name="KVARATSKHELIA", club="PSG · GEORGIA", fact="CAMPEÓN DE EUROPA"),
    "vitinha": dict(name="VITINHA", club="PSG · PORTUGAL", fact="CAMPEÓN DE EUROPA"),
    "ruiz": dict(name="FABIÁN RUIZ", club="PSG · ESPAÑA", fact="CAMPEÓN DE EUROPA"),
    "messi": dict(name="LIONEL MESSI", club="INTER MIAMI · ARGENTINA", fact="BALÓN DE PLATA"),
}

LINES = [
    "{scene:boot}Esta noche, el mundo del fútbol tiene los ojos puestos en {coin}*Londres*.",
    "{scene:title}Es la edición número *setenta* del *Balón* *de* *Oro*, y por primera vez, la gala se celebra en *Londres*.",
    "{scene:champ}*Ousmane* *Dembélé* pone en juego su *corona*. Pero... ¿quién será su {qmark}*sucesor*?",
    "{scene:grid}Este es mi *top* *diez* de los nominados.",

    "{dive}{player:ruiz:10}Número diez: *Fabián* *Ruiz*. {stat:UCL|CAMPEÓN_DE_EUROPA}Campeón de Europa con el PSG, y {stat:MUNDIAL|CAMPEÓN_DEL_MUNDO}campeón del mundo con España. {stat:2/2|EL_ÚNICO_CON_LOS_DOS}El *único* que ganó las dos este año.",
    "{player:vitinha:9}Número nueve: *Vitinha*. El motor del PSG. {stat:7|GOLES}*Siete* goles, {stat:10|ASISTENCIAS}*diez* asistencias, y {stat:UCL|OTRA_CHAMPIONS}otra *Champions*.",
    "{player:dembele:8}Número ocho: *Ousmane* *Dembélé*. El rey defensor. {stat:L1|CAMPEÓN_DE_FRANCIA}Campeón de Francia, y {stat:UCL|BICAMPEÓN_DE_EUROPA}otra vez *campeón* *de* *Europa*.",
    "{player:messi:7}Número siete: *Lionel* *Messi*. {stat:39|AÑOS}A los *treinta* *y* *nueve* años: {stat:PLATA|BALÓN_DE_PLATA_MUNDIAL}Balón de *Plata* del Mundial, y {stat:2º|SUBCAMPEÓN_DEL_MUNDO}subcampeón del mundo.",
    "{player:kvara:6}Número seis: *Kvaratskhelia*. {stat:19|GOLES}*Diecinueve* goles, {stat:11|ASISTENCIAS}*once* asistencias, y {stat:2|CHAMPIONS_SEGUIDAS}la segunda *Champions* seguida.",
    "{player:olise:5}Número cinco: *Michael* *Olise*. {stat:15|GOLES_EN_BUNDESLIGA}*Quince* goles {stat:19|ASISTENCIAS_EN_BUNDESLIGA}y *diecinueve* asistencias en la Bundesliga, y {stat:7|ASISTENCIAS_EN_EL_MUNDIAL}máximo asistente del Mundial, con *siete*.",
    "{player:rodri:4}Número cuatro: *Rodri*. {stat:MVP|MEJOR_JUGADOR_DEL_MUNDIAL}Mejor jugador del *Mundial*. {stat:93%|PASES_ACERTADOS}*Noventa* *y* *tres* por ciento de pases acertados, y {stat:MUNDIAL|CAMPEÓN_DEL_MUNDO}campeón del *mundo*.",
    "{player:mbappe:3}Número tres: *Kylian* *Mbappé*. {stat:25|GOLES_PICHICHI_LALIGA}Pichichi de LaLiga con *veinticinco* goles, {stat:15|GOLES_EN_CHAMPIONS}máximo goleador de la Champions con *quince*, y {stat:BOTA|BOTA_DE_ORO_DEL_MUNDIAL}Bota de Oro del *Mundial*.",
    "{two}Pero esta noche, todo se decide entre *dos* jugadores.",
    "{player:yamal:2}Número dos: *Lamine* *Yamal*. {stat:MUNDIAL|CAMPEÓN_DEL_MUNDO}Campeón del *mundo* con España, {stat:LIGA|CAMPEÓN_DE_LIGA}campeón de *Liga* con el Barça, {stat:16|GOLES_EN_LALIGA}*dieciséis* goles, {stat:11|ASISTENCIAS_EN_LALIGA}*once* asistencias, y {stat:MVP|MEJOR_JUGADOR_DE_LALIGA}mejor jugador de *LaLiga*.",
    "{player:kane:1}Número uno: *Harry=Jarri* *Kane.=Kein.* {stat:61|GOLES_CON_EL_BAYERN}*Sesenta* *y* *un* goles con el Bayern, {stat:73|GOLES_CON_INGLATERRA}*setenta* *y* *tres* contando Inglaterra, {stat:BOTA|BOTA_DE_ORO_EUROPEA}Bota de *Oro* europea, y {stat:6|GOLES_EN_EL_MUNDIAL}*seis* goles en el Mundial.",
    "{fav}Las casas de apuestas lo tienen claro: Harry=Jarri Kane=Kein es el gran *favorito*.",
    "{predict}Y mi predicción... el Balón de Oro dos mil veintiséis es para...",
    "{winner}*¡Harry=¡Jarri* *Kane!=Kein!*",
    "{scene:cta}¿Y tú? *¿Kane=¿Kein* o *Lamine*? Te leo en comentarios.",
]

CAMERA = {
    "boot": (1.0, 960), "title": (1.12, 880), "champ": (1.24, 830), "grid": (1.24, 830), "cta": (1.05, 940),
}
MUSIC = {"boot": 0.3, "title": 0.6, "champ": 0.6, "grid": 1.0, "cta": 0.7}
