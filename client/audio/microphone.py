import numpy as np
import sounddevice as sd
from client.logger import Logger
import queue
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
        self.audio_queue = queue.Queue(maxsize=20)

    def start(self) -> None:
        if not self.running:
            self._clear_queue()
            try:
                self.stream = sd.InputStream(
                            samplerate=self.samplerate,
                            channels=self.channels,
                            blocksize=self.blocksize,
                            device=self.device,
                            dtype=self.dtype,
                            callback=self.callback
                        )
                self.stream.start()
                self.running = True

            except Exception as e:
                raise RuntimeError("Cannot open microphone") from e

    def read(self) -> np.ndarray:
        
        # if not self.running:
        #     raise RuntimeError("Microphone not started")
        
        # try:
        #     data, overflow = self.stream.read(self.blocksize)
        #     if overflow:
        #         self.logger.log_warning('Audio overflow')
        #     return data.flatten()

        # except Exception as e:
        #     self.stop()
        #     raise RuntimeError("Microphone read failed") from e

        if not self.running:
            raise RuntimeError("Microphone not started")

        try:
            return self.audio_queue.get(timeout=1.0)
        except Exception as e:
            self.stop()
            raise RuntimeError("Microphone read failed") from e

    def list_device(self):
        print(sd.query_devices())

    def stop(self) -> None:
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        self.running = False
        self._clear_queue()

    def find_input_devices(self):
        return sd.query_devices(kind='input')

    @property
    def is_running(self):
        return self.running

    def get_volume(self, frame) -> float:
        return np.sqrt(np.mean(frame.astype(np.float32) ** 2))

    #TODO : finish callback if needed
    def callback(self, indata, frames, time, status):
        if status:
            self.logger.log_warning(str(status))

        try:
            self.audio_queue.put_nowait(indata.copy().flatten())
        except queue.Full:
            self.logger.log_warning("Audio queue is full")

    def _clear_queue(self):
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

