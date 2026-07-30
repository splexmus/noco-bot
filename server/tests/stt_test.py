import numpy as np
import soundfile as sf
from server.stt.whisper_engine import Whisper_engine

whisper = Whisper_engine()
datas = sf.read('client/sounds/stereo_file.wav')

whisper.transcribe(datas[0])
