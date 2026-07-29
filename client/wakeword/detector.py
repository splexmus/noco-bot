import numpy as np
from openwakeword.model import Model
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"
DEFAULT_MODEL_PATH = MODEL_DIR / "hey_noco.tflite"
SUPPORTED_FRAMEWORKS = {"onnx", "tflite"}

class WakeWordDetector:
    def __init__(
        self,
        wakeword_name: str,
        threshold: float = 0.5,
        model_path: str | Path | None = None,
        inference_framework: str = "tflite"
    ):
        self.wakeword_name = wakeword_name
        self._threshold = max(0.0, min(threshold, 1.0))
        self.inference_framework = inference_framework

        if model_path is None:
            self.model_path = DEFAULT_MODEL_PATH
        else:
            self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Wake word model not found: {self.model_path}"
            )

        if inference_framework not in SUPPORTED_FRAMEWORKS:
            raise ValueError(
                f"Unsupported inference framework: {inference_framework}"
            )

        try: 
            self.model = Model(wakeword_models=[str(self.model_path)], inference_framework = self.inference_framework)
        except Exception as e: 
            raise RuntimeError("Init model failed") from e

    def detect(self, frame: np.ndarray) -> bool:
        return self.score(frame) >= self.threshold

    def score(self, frame) -> float:
        if frame.ndim != 1:
            raise ValueError("Frame must be 1-dimensional.")

        if frame.shape[0] != 512:
            raise ValueError("Expected 512 samples.")

        scores = self.model.predict(frame)
        score = scores.get(self.wakeword_name, 0.0)
        return score

    @property
    def threshold(self) -> float:
        return self._threshold

    @threshold.setter
    def setthreshold(self, threshold) -> None:
        self._threshold = threshold
