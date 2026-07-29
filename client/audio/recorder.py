import soundfile as sf
from pathlib import Path
import numpy as np
from .vad import VoiceActivityDetector
from collections import deque
class Recorder:
    
    def __init__(
        self,
        vad: VoiceActivityDetector,
        sample_rate: int = 16000,
        max_frames: int  = 256, #estimate 10 secend
        max_silence_frames: int = 30,
        preroll_frames: int = 10,
        min_speech_frames: int = 5,
        frame_size: int = 512
    ):
        self.frames = []
        self.vad = vad
        self.preroll_buffer = deque(maxlen=preroll_frames)
        self.recording = False
        self.silence_counter = 0
        self.max_silence_frames = max_silence_frames
        self.min_speech_frames = min_speech_frames
        self.max_frames = max_frames
        self.sample_rate = sample_rate
        self.frame_size = frame_size

    def reset(self) -> None:
        self.frames = []
        self.silence_counter = 0
        self.recording = False
        self.vad.reset()

    def update(self, frame:  np.ndarray) -> np.ndarray | None:
        self.preroll_buffer.append(frame)

        if self.recording and len(self.frames) >= self.max_frames:
            return self._finish_recording()
        
        if self.vad.detect(frame):
            if not self.recording:
                self.recording = True
                self.frames.extend(list(self.preroll_buffer)[:-1])
            self.frames.append(frame)
            self.silence_counter = 0
        else:

            if self.recording:
                if len(self.frames) < self.min_speech_frames:
                    self.reset()
                    return None
                else:
                    self.frames.append(frame)
                    self.silence_counter += 1

                    if self.silence_counter >= self.max_silence_frames:
                        return self._finish_recording()
                
    @property
    def is_recording(self):
        return self.recording

    def _finish_recording(self) -> np.ndarray:
        audio = np.concatenate(self.frames)
        self.reset()
        return audio

    @property
    def duration(self):
        return len(self.frames) * self.frame_size / self.sample_rate