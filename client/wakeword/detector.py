import numpy as np
import openwakeword
from openwakeword.model import Model
from pathlib import Path

MODEL_DIR = Path(__file__).parent.parent / "models"
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "hey_noco.tflite"
class WakeWordDetector:
    def __init__(
        self,
        wakeword_name: str,
        threshold: float = 0.5,
        model_path: str | Path | None = None,
        inference_framework: str = "tflite"
    ):
        self.wakeword_name = wakeword_name
        self.threshold = max(0.0, min(threshold, 1.0))
        self.inference_framework = inference_framework

        if model_path is None:
            self.model_path = MODEL_PATH
        else:
            self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Wake word model not found: {self.model_path}"
            )
        
        try: 
            self.model = Model(wakeword_models=[str(self.model_path)], inference_framework = self.inference_framework)
        except Exception as e: 
            raise RuntimeError("Init model failed") from e

    def detect(self, frame: np.ndarray) -> bool:
        scores = self.model.predict(frame)
        score = scores.get(self.wakeword_name, 0.0)
        return score >= self.threshold
