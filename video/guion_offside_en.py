"""Gol de Lamine Yamal : « why no offside? » — texte de la voix off (anglais), une phrase = un plan (offside.py).

Pas de sous-titres, pas de musique. Pour mettre ta propre voix (ElevenLabs...), mets le fichier dans
sources/ et remplis VOICE_FILE + LINE_STARTS (début de chaque phrase en secondes), comme guion_yamal_es.py.
"""
LANG = "en-us"
VOICE = "am_michael"   # voix anglaises : "am_michael", "am_adam", "am_onyx", "bm_george" ; femme : "af_heart"
SPEED = 1.05

LINES = [
    "Why didn't the referee call offside on Lamine Yamal's goal, when at first glance it clearly appears that he was offside during the play?",
    "An opposing player attempts to clear the ball with a header,",
    "but his header is poorly controlled and ends up at the feet of Gabriel Jesus,",
    "who controls the ball and sees Yamal making a run into the open space.",
    "Take a close look at the play.",
    "At the start of the play, Yamal was in a completely legal position, so there was no offside.",
    "But the moment Jesus receives the ball, controls it, and prepares to make the pass,",
    "Lamine Yamal appears, at first glance, to already be in an offside position.",
    "However, when we look at the play more closely, we can see that Yamal is not offside.",
    "He is exactly on the same line as the last defender.",
    "Then, Jesus plays a through ball to Lamine Yamal.",
    "Yamal controls the ball and forces the goalkeeper to come out of his area.",
    "And there, with great intelligence, he advances and executes a magnificent chip shot to score an incredible goal.",
]

VOICE_FILE = None
LINE_STARTS = None
VOICE_END = None
