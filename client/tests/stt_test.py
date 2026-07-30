from client.networks import STTClient
import soundfile as sf

stt = STTClient()

audio = sf.read('client/sounds/stereo_file.wav')
print(stt.transcribe(audio = audio[0]))