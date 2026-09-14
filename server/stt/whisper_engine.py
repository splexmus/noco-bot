from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from server.config import settings


SAMPLE_RATE = 16_000
PCM16_SCALE = 32_768.0


@dataclass(frozen=True)
class TranscriptionSegment:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class TranscriptionInfo:
    language: str
    language_probability: float


class WhisperEngine:
    """Hugging Face Whisper inference with the legacy NOCO result shape."""

    def __init__(
        self,
        model_id: str | None = None,
        language: str | None = None,
        device: str | None = None,
        chunk_length_seconds: int | None = None,
        transcriber: Any | None = None,
    ) -> None:
        self.model_id = model_id or settings.stt_model_id
        self.language = language if language is not None else settings.stt_language
        self.device = device or settings.stt_device
        self.chunk_length_seconds = (
            chunk_length_seconds or settings.stt_chunk_length_seconds
        )
        self.transcriber = (
            transcriber if transcriber is not None else self._load_transcriber()
        )

    def transcribe(
        self,
        data: np.ndarray,
        language: str | None = None,
    ) -> tuple[list[TranscriptionSegment], TranscriptionInfo]:
        audio = self._prepare_audio(data)
        requested_language = language if language is not None else self.language
        generate_kwargs: dict[str, str] = {"task": "transcribe"}
        if requested_language:
            generate_kwargs["language"] = requested_language

        try:
            result = self.transcriber(
                {"array": audio, "sampling_rate": SAMPLE_RATE},
                return_timestamps=True,
                generate_kwargs=generate_kwargs,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Hugging Face Whisper transcription failed: {exc}"
            ) from exc

        segments = self._segments_from_result(result)
        text = str(result.get("text", "")).strip()
        if not segments and text:
            duration = len(audio) / SAMPLE_RATE
            segments = [TranscriptionSegment(start=0.0, end=duration, text=text)]

        # The pipeline does not expose a calibrated language probability. A forced
        # language is therefore certain by configuration; automatic mode is unknown.
        info = TranscriptionInfo(
            language=requested_language or "unknown",
            language_probability=1.0 if requested_language else 0.0,
        )
        return segments, info

    def _load_transcriber(self):
        try:
            import torch
            from transformers import pipeline
        except ImportError as exc:
            raise RuntimeError(
                "Hugging Face STT requires torch and transformers. "
                "Install the updated environments/stt.yml environment."
            ) from exc

        if self.device == "auto":
            pipeline_device = 0 if torch.cuda.is_available() else -1
        elif self.device == "cpu":
            pipeline_device = -1
        elif self.device.startswith("cuda"):
            _, _, index = self.device.partition(":")
            pipeline_device = int(index or 0)
        else:
            raise ValueError("STT_DEVICE must be auto, cpu, cuda, or cuda:<index>")

        dtype = torch.float16 if pipeline_device >= 0 else torch.float32
        return pipeline(
            task="automatic-speech-recognition",
            model=self.model_id,
            device=pipeline_device,
            dtype=dtype,
            chunk_length_s=self.chunk_length_seconds,
        )

    @staticmethod
    def _prepare_audio(data: np.ndarray) -> np.ndarray:
        audio = np.asarray(data)
        if audio.ndim == 2 and 1 in audio.shape:
            audio = audio.reshape(-1)
        if audio.ndim != 1:
            raise ValueError("STT audio must be a mono one-dimensional array")
        if audio.size == 0:
            raise ValueError("STT audio must not be empty")

        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / PCM16_SCALE
        else:
            audio = audio.astype(np.float32)
        if not np.isfinite(audio).all():
            raise ValueError("STT audio contains non-finite samples")
        return np.clip(audio, -1.0, 1.0)

    @staticmethod
    def _segments_from_result(result: dict[str, Any]) -> list[TranscriptionSegment]:
        segments = []
        for chunk in result.get("chunks") or []:
            timestamp = chunk.get("timestamp") or (None, None)
            start, end = timestamp
            if start is None:
                start = 0.0
            if end is None:
                end = start
            segments.append(
                TranscriptionSegment(
                    start=float(start),
                    end=float(end),
                    text=str(chunk.get("text", "")).strip(),
                )
            )
        return segments
