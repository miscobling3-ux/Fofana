# Texte exact de l'audio fourni (Adam, ElevenLabs, espagnol), aligné sur les segments mesurés (silences RMS 20 ms, -38 dB)
import json, re
S = json.load(open('voice_user/segments.json'))
TXT = ["Este gol que marcó hoy Jude Bellingham ya es considerado el más bonito de", "toda su carrera.",
 "Todo empieza en esta jugada,", "cuando Bernardo Silva avanza con el balón", "y decide abrir por la banda para Vinícius.",
 "Este recibe y se lanza hacia el área rival.", "En ese momento,", "un defensor le cierra el paso y le impide entrar directamente",
 "al área.", "Los defensores creen que va a jugar aquí con Cucurella,", "pero decide devolverle el balón a Bernardo Silva,",
 "fuera del área.", "Bernardo recibe el pase y se perfila para jugar con la zurda.", "Mbappé le pide el balón,",
 "pero él decide abrir por la banda para Cucurella.", "En cuanto Cucurella recibe,", "avanza y entra al área.",
 "Fíjate en la posición de los defensores del AEK.", "Están bien alineados", "y se concentran principalmente en marcar a los jugadores del Real Madrid",
 "que están dentro del área.", "Piensan que Cucurella va a mandar un centro,", "por eso intentan cubrir", "todos los espacios.",
 "Pero Cucurella decide no centrar.", "En el último momento,", "levanta la cabeza y ve a Bellingham llegando a", "toda velocidad.",
 "Entonces,", "decide darle un pase dentro del área.", "Y Bellingham ni siquiera controla el balón,", "remata de tacón",
 "y lo manda", "directamente al fondo de la red."]
segs = S['segments']; assert len(segs) == len(TXT), (len(segs), len(TXT))
def syl(w): return max(1, len(re.findall(r'[aeiouyáéíóúü]+', w.lower())))
words = []
for sg, t in zip(segs, TXT):
    ws = t.split(); wt = [syl(w) + 0.35 for w in ws]; tot = sum(wt); c = sg['start']; d = sg['end'] - sg['start']
    for w, x in zip(ws, wt):
        words.append(dict(word=w, start=round(c, 3), end=round(c + d * x / tot, 3))); c += d * x / tot
json.dump(dict(sentences=TXT, segments=segs, words=words, duration=S['duration']), open('voice_user/words.json', 'w'), ensure_ascii=False, indent=0)
print(len(words), 'mots', S['duration'])
