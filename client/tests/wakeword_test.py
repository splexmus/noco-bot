# wakeword_test.py
from client.wakeword import WakeWordDetector
from client.audio import Microphone
# test code here

detector = WakeWordDetector(wakeword_name = 'hey_noco')
mic = Microphone()
try:
    mic.start()

    while True:
        frame = mic.read()
        print(detector.detect(frame), mic.get_volume(frame))

except KeyboardInterrupt:
    print("Stopping...")

finally:
    mic.stop()