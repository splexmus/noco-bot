from client.networks import STTClient
from client.audio import Microphone, VoiceActivityDetector, Recorder

mic = Microphone()
vad = VoiceActivityDetector()
rec = Recorder(vad)
stt = STTClient()

mic.start()

try:
    while True:
        frame = mic.read()
        audio = rec.update(frame)
        if audio is not None:
            print("STT.. :")
            print(stt.transcribe(audio = audio))
        # print(rec.is_recording, rec.duration)
        # print('-'*50)
except KeyboardInterrupt:
    pass
finally:
    mic.stop()