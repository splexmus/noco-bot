from .audio import VoiceActivityDetector, AudioPlayer, Microphone, Recorder
from .wakeword import WakeWordDetector
from .networks import ChatClient, STTClient, TTSClient
from enum import Enum

detector = WakeWordDetector(wakeword_name = 'hey_noco')
mic = Microphone()
vad = VoiceActivityDetector()
rec = Recorder(vad)
player = AudioPlayer()
stt = STTClient()
chat = ChatClient()
tts = TTSClient()

class Status(Enum):
    WAITING     = 1
    LISTENING   = 2
    STT_REQUEST = 3
    CHAT_REQUEST= 4
    TTS_REQUEST = 5

state = Status.WAITING
prestart = False

try:
    mic.start()

    while True:
        frame = mic.read()

        match state:

            case Status.WAITING:
                start = detector.detect(frame)

                if not start and prestart:
                    print("\nWake word detected")
                    rec.reset()
                    state = Status.LISTENING

                prestart = start

            case Status.LISTENING:
                audio = rec.update(frame)

                if audio is not None:
                    print("\nSTT...")
                    state = Status.STT_REQUEST

            case Status.STT_REQUEST:
                result = stt.transcribe(audio=audio)
                text = result["text"]

                if text:
                    print("User:", text)
                    state = Status.CHAT_REQUEST
                else:
                    state = Status.WAITING

            case Status.CHAT_REQUEST:
                result = chat.chat(text)
                response = result["response"]

                if response:
                    print("NOCO:", response)
                    state = Status.TTS_REQUEST
                else:
                    state = Status.WAITING

            case Status.TTS_REQUEST:
                audio = tts.synthesize(response)

                if audio is not None:
                    player.play(audio)
                    player.close()

                state = Status.WAITING

except KeyboardInterrupt:
    print("Stopping...")

finally:
    mic.stop()
    player.close()