import onnxruntime as ort
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"
DEFAULT_MODEL_PATH = MODEL_DIR / "silero_vad.onnx"
STATE_SHAPE = (2, 1, 128)
PCM16_SCALE = 32768.0
FRAME_SIZE = 512
CONTEXT_SIZE = 128
class VoiceActivityDetector:
    def __init__(
        self,
        threshold: float = 0.5,
        sample_rate: int = 16000,
    ):        
        if not DEFAULT_MODEL_PATH.exists():
            raise FileNotFoundError(DEFAULT_MODEL_PATH)

        self.session = ort.InferenceSession(str(DEFAULT_MODEL_PATH), providers=["CPUExecutionProvider"])
        self.threshold = max(0.0, min(threshold, 1.0))
        self.state = np.zeros(STATE_SHAPE, dtype=np.float32)
        self.sample_rate = np.array(sample_rate, dtype=np.int64)
        self.context = np.zeros((1,CONTEXT_SIZE), dtype=np.float32)

    def detect(self, frame) -> bool:
        return self.score(frame) > self.threshold

    def score(self, frame) :
        frame = self._preprocess(frame)
        model_input = self._build_input(frame)

        output, stateN = self.session.run(None, {'input':model_input,'state':self.state,'sr':self.sample_rate})
        
        self.state = stateN
        self.context = frame.copy()[:,-CONTEXT_SIZE:]

        return float(output[0][0])

    def _preprocess(self, frame) -> np.float32:

        if frame.ndim == 1:
            if frame.shape[0] != FRAME_SIZE:
                raise ValueError(f"Expected a 1D audio frame with {FRAME_SIZE} sample.")
        elif frame.ndim == 2:
            if frame.shape != (1, FRAME_SIZE):
                raise ValueError("Invaid audio sample.")

        if frame.ndim == 1:
            frame = np.expand_dims(frame, axis=0)
        if frame.dtype == np.int16:
            frame = frame.astype(np.float32) / PCM16_SCALE
        else:
            frame = frame.astype(np.float32)

        return frame
        
    def reset(self) -> None:
        self.context.fill(0)
        self.state.fill(0)  

    def _build_input(self, frame):
        return np.concatenate((self.context, frame),axis = 1)  
