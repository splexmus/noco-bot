# wakeword_test.py
from client.audio import Microphone
# test code here


mic = Microphone()
mic.stop()
try:
    mic.start()

    while True:
        frame = mic.read()
        print(frame.shape, mic.get_volume(frame))

except KeyboardInterrupt:
    print("Stopping...")

finally:
    mic.stop()