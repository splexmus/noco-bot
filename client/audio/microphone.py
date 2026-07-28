import numpy as np
import sounddevice as sd

class Microphone:
    def __init__(
        self,
        samplerate=16000,
        channels=1,
        dtype="int16",
        blocksize=512,
        device=None
    ):
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype
        self.device = device
        self.blocksize = blocksize
        self.running = False
        self.stream = None

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
                print("Audio overflow")
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

    #TODO : find the usable microphone
    def find_input_devices(self):
        print(sd.query_devices(kind='input'))

    @property
    def is_running(self):
        return self.running

    def get_volume(self, frame) -> float:
        return np.sqrt(np.mean(frame.astype(np.float32) ** 2))

    def callback(self):
        pass
