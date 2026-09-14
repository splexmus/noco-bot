from __future__ import annotations

from collections.abc import Callable
from enum import Enum, auto
from time import monotonic

from .audio import AudioPlayer, Microphone, Recorder, VoiceActivityDetector
from .networks import ChatClient, STTClient, TTSClient
from .wakeword import WakeWordDetector


class Status(Enum):
    WAITING = auto()
    LISTENING = auto()
    STT_REQUEST = auto()
    CHAT_REQUEST = auto()
    TTS_REQUEST = auto()
    ERROR = auto()


StateCallback = Callable[[Status, str | None], None]


class VoiceAssistant:
    """Coordinate the robot voice pipeline and report visible state changes."""

    def __init__(self, on_state_change: StateCallback | None = None) -> None:
        self.detector = WakeWordDetector(wakeword_name="hey_noco")
        self.microphone = Microphone()
        self.vad = VoiceActivityDetector()
        self.recorder = Recorder(self.vad)
        self.player = AudioPlayer()
        self.stt = STTClient()
        self.chat = ChatClient()
        self.tts = TTSClient()

        self.on_state_change = on_state_change
        self.state = Status.WAITING
        self.running = False
        self._previous_wakeword_result = False
        self._audio = None
        self._text = ""
        self._response = ""
        self._error_until = 0.0

    def run(self) -> None:
        self.running = True
        self._set_state(Status.WAITING, "Say hey noco")

        try:
            self.microphone.start()

            while self.running:
                try:
                    frame = self.microphone.read()
                except RuntimeError:
                    if not self.running:
                        break
                    raise

                self._step(frame)
        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            self.running = False
            self.microphone.stop()
            self.player.close()

    def stop(self) -> None:
        """Request a clean stop; safe to call from the display thread."""
        self.running = False
        self.microphone.stop()
        self.player.close()

    def _step(self, frame) -> None:
        if self.state is Status.ERROR:
            if monotonic() >= self._error_until:
                self._set_state(Status.WAITING, "Say hey noco")
            return

        if self.state is Status.WAITING:
            detected = self.detector.detect(frame)

            if not detected and self._previous_wakeword_result:
                print("\nWake word detected")
                self.recorder.reset()
                self._set_state(Status.LISTENING, "I'm listening")

            self._previous_wakeword_result = detected
            return

        if self.state is Status.LISTENING:
            audio = self.recorder.update(frame)
            if audio is not None:
                self._audio = audio
                print("\nSTT...")
                self._set_state(Status.STT_REQUEST, "Understanding")
            return

        if self.state is Status.STT_REQUEST:
            try:
                result = self.stt.transcribe(audio=self._audio)
                self._text = result.get("text", "").strip()
            except Exception as exc:
                self._recover_from_error("STT", exc)
                return

            if not self._text:
                self._recover_from_error("STT", ValueError("No speech detected"))
                return

            print("User:", self._text)
            self._set_state(Status.CHAT_REQUEST, "Thinking")
            return

        if self.state is Status.CHAT_REQUEST:
            try:
                result = self.chat.chat(self._text)
                self._response = result.get("response", "").strip()
            except Exception as exc:
                self._recover_from_error("Chat", exc)
                return

            if not self._response:
                self._recover_from_error("Chat", ValueError("Empty response"))
                return

            print("NOCO:", self._response)
            self._set_state(Status.TTS_REQUEST, "Speaking")
            return

        if self.state is Status.TTS_REQUEST:
            try:
                audio = self.tts.synthesize(self._response)
                if audio is not None:
                    self.player.play(audio)
                    self.player.close()
            except Exception as exc:
                self._recover_from_error("TTS", exc)
                return

            self._set_state(Status.WAITING, "Say hey noco")

    def _recover_from_error(self, service: str, error: Exception) -> None:
        print(f"\n{service} error: {error}")
        self.recorder.reset()
        self._error_until = monotonic() + 1.5
        self._set_state(Status.ERROR, f"{service} error")

    def _set_state(self, state: Status, message: str | None = None) -> None:
        self.state = state
        if self.on_state_change is not None:
            self.on_state_change(state, message)


def main() -> None:
    VoiceAssistant().run()


if __name__ == "__main__":
    main()
