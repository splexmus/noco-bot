import numpy as np
import sounddevice as sd
from client.logger import Logger
class Microphone:
    def __init__(
        self,
        samplerate: int = 16000,
        channels: int = 1,
        dtype: str = "int16",
        blocksize: int = 512,
        device: int | None = None
    ):
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype
        self.device = device
        self.blocksize = blocksize
        self.running = False
        self.stream = None
        self.logger = Logger()

    def start(self) -> None:
        if not self.running:
            try:
                self.stream = sd.InputStream(
                            samplerate=self.samplerate,
                            channels=self.channels,
                            blocksize=self.blocksize,
                            device=self.device,
                            dtype=self.dtype
                        )
                self.stream.start()
                self.running = True

            except Exception as e:
                raise RuntimeError("Cannot open microphone") from e

    def read(self) -> np.ndarray:
        
        if not self.running:
            raise RuntimeError("Microphone not started")
        
        try:
            data, overflow = self.stream.read(self.blocksize)
            if overflow:
                self.logger.log_warning('Audio overflow')
            return data.flatten()

        except Exception as e:
            self.stop()
            raise RuntimeError("Microphone read failed") from e

    def list_device(self):
        print(sd.query_devices())

    def stop(self) -> None:
        if self.running:
            self.stream.stop()
            self.stream.close()
            self.running = False
            self.stream=None

    def find_input_devices(self):
        return sd.query_devices(kind='input')

    @property
    def is_running(self):
        return self.running

    def get_volume(self, frame) -> float:
        return np.sqrt(np.mean(frame.astype(np.float32) ** 2))

    #TODO : finish callback if needed
    def callback(self):
        pass

