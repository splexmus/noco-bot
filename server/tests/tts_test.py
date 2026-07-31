from server.tts.piper_engine import PiperEngine
from client.audio import AudioPlayer

piper = PiperEngine()
player = AudioPlayer()

audio = piper.text_to_speech("I Hate thai. You make me suffer. KUAY KUAY KUAY")

print(audio, type(audio), audio.shape)

player.play(audio)

player.close()