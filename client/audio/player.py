import numpy as np
import sounddevice as sd
import sys
import queue

PCM16_SCALE = 32768.0

#TODO : implement callback function instead of steam block
class AudioPlayer:
    def __init__(
        self,
        sample_rate: int =16000,
        channels: int = 1,
        dtype: str = "float32",
        blocksize: int = 512,
        buffersize: int = 20,
        device: int | None = None
    ):
        self.playing = False
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.device = device
        self.blocksize = blocksize
        self.stream = None
        self.q = queue.Queue(maxsize=buffersize)

    def play(
        self,
        audio: np.ndarray
    ) -> None:
        if audio.ndim not in (1,2):
            raise ValueError("Expected a 1D or 2D audio")
        
        if not self.playing:
            try:
                if self.stream is None:
                    self.stream = sd.OutputStream(
                                samplerate=self.sample_rate,
                                channels=self.channels,
                                blocksize=self.blocksize,
                                device=self.device,
                                dtype=self.dtype,
                                # callback=self._callback
                            )
                    self.stream.start()
                audio = self._prepare_audio(audio)
                # self.q.put(audio)
                self.playing = True
                self.stream.write(audio)

            except Exception as e:
                raise RuntimeError(f"Audio playback failed: {e}") from e
            finally:
                self.stop()

    def close(self) -> None:
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        self.playing = False

    def stop(self) -> None:
        if self.stream is not None:
            self.stream.stop()
        self.playing = False

    @property
    def is_playing(self) -> bool:
        return self.playing

    def _prepare_audio(self, audio: np.ndarray) -> np.ndarray:
        if audio.dtype != np.float32:
            if audio.dtype == np.int16:
                audio = audio.astype(np.float32) / PCM16_SCALE
            else: audio = audio.astype(np.float32)
        audio = np.clip(audio, -1.0, 1.0)
        return audio

    def _callback(self, outdata, frames, time, status):
        if frames != self.blocksize:
            raise RuntimeError("Frames not equal to blocksize")
        if status.output_underflow:
            print('Output underflow: increase blocksize?', file=sys.stderr)
            raise sd.CallbackAbort
        if status:
            print(status)
        try:
            data = self.q.get_nowait()
        except queue.Empty as e:
            print('Buffer is empty: increase buffersize?', file=sys.stderr)
            raise sd.CallbackAbort from e
        if len(data) < len(outdata):
            outdata[:len(data)] = data
            outdata[len(data):].fill(0)
            raise sd.CallbackStop
        else:
            outdata[:] = data
        