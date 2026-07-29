class Recorder:
    
    def __init__(
        self,
        sample_rate: int = 16000,
        frame_size: int  = 512,
        speech_threshold: float = 0.5,
        max_silence_frames: int = 30,
        preroll_ms=300,
        min_duration_ms=200,
    ):
        self.frames = []
        self.recording = False
        self.silence_frames = 0
        self.max_silence_frames = max_silence_frames
        self.min_speech_frames = 5
        self.max_frames = 512

    def start():
        pass
    
    def stop():
        pass

    def append(frame):
        pass

    def save(path):
        pass