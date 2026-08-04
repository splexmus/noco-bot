from faster_whisper import WhisperModel
import numpy as np

class WhisperEngine:
    def __init__(
        self,
        model_size_or_path: str = "large-v2",
        device: str = "cpu",
        compute_type: str = "int8",
    ):
        self.model = WhisperModel(model_size_or_path = model_size_or_path, device=device, compute_type=compute_type)

    def transcribe(
        self,
        data: np.ndarray,
        language: str | None = None
    ):
        try:
            segments, info = self.model.transcribe(audio = data, vad_filter = False, language = language, chunk_length = 5)
            return [segments, info]
        
        except KeyboardInterrupt:
            pass
        
        except Exception as e:
            raise RuntimeError (f"Error occur at {e}")
        
