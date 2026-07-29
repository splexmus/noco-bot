from client.audio import Microphone, VoiceActivityDetector, Recorder, AudioPlayer
import soundfile as sf

mic = Microphone()
vad = VoiceActivityDetector()
rec = Recorder(vad)
player = AudioPlayer()

mic.start()

try:
    while True:
        frame = mic.read()
        audio = rec.update(frame)
        if audio is not None:
            sf.write('client/sounds/stereo_file.wav', audio, 16000)            
        print(rec.is_recording, rec.duration)
        print('-'*50)
except KeyboardInterrupt:
    pass
finally:
    datas = sf.read('client/sounds/stereo_file.wav')
    player.play(datas[0])
    player.close()
    mic.stop()