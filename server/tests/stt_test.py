import numpy as np
import soundfile as sf
from server.stt.whisper_engine import WhisperEngine

whisper = WhisperEngine()
datas = sf.read('client/sounds/stereo_file.wav')

print(whisper.transcribe(datas[0]))
