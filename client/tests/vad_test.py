from client.audio import Microphone, VoiceActivityDetector

mic = Microphone()
vad = VoiceActivityDetector()

mic.start()

try:
    while True:
        frame = mic.read()
        print(vad.score(frame))
        print('-'*50)
except KeyboardInterrupt:
    pass
finally:
    mic.stop()
