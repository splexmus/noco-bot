from client.networks import TTSClient
from client.audio import AudioPlayer
import soundfile as sf

tts = TTSClient()
player = AudioPlayer()

audio = tts.synthesize(". Hi pleang. How are you. Are you OK")
print(audio)
print(audio.dtype)
print(audio.shape)
print(audio.min())
print(audio.max())

player.play(audio)
player.stop()

sf.write('client/stereo_file2.wav', audio, 16000)

