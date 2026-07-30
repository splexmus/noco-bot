import wave
from piper import PiperVoice, SynthesisConfig

class PiperEngine:
    def __init__(
        self,
        path: str = "server/tts/models/en_US-lessac-medium.onnx",
    ):        
        self.voice = PiperVoice.load(path)
        self.syn_config = SynthesisConfig(
            volume=0.5,  # half as loud
            length_scale=2.0,  # twice as slow
            noise_scale=1.0,  # more audio variation
            noise_w_scale=1.0,  # more speaking variation
            normalize_audio=False, # use raw audio from voice
        )

    def texttospeech(
        self,
        speech: str,
    ):
        with wave.open("server/tts/sounds/test.wav", "wb") as wav_file:
            self.voice.synthesize_wav(speech, wav_file)
