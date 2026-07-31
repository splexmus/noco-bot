import io
import wave
import numpy as np
from piper import PiperVoice, SynthesisConfig

class PiperEngine:
    def __init__(
        self,
        path: str = "server/tts/models/en_US-lessac-low.onnx",
    ):        
        self.voice = PiperVoice.load(path)
        self.syn_config = SynthesisConfig(
            volume=2.0,  # half as loud
            length_scale=1.2,  # twice as slow
            noise_scale=1.0,  # more audio variation
            noise_w_scale=1.0,  # more speaking variation
            normalize_audio=False, # use raw audio from voice
        )

    def text_to_speech(
        self,
        speech: str,
    ):
        buffer = io.BytesIO()

        with wave.open(buffer, "wb") as wav_file:
            self.voice.synthesize_wav(
                speech,
                wav_file,
                syn_config=self.syn_config,
            )

        buffer.seek(0)

        with wave.open(buffer, "rb") as wav_file:
            audio_bytes = wav_file.readframes(wav_file.getnframes())

            audio = np.frombuffer(
                audio_bytes,
                dtype=np.int16,
            ).copy()

        return audio