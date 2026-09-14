from __future__ import annotations

import threading
import tkinter as tk

from .face import FaceState, RobotFaceDisplay


class RobotScreenApplication:
    def __init__(self, fullscreen: bool = True, demo: bool = False) -> None:
        self.root = tk.Tk()
        self.face = RobotFaceDisplay(self.root, fullscreen=fullscreen)
        self.assistant = None
        self.demo = demo
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("q", lambda _event: self.close())

    def run(self) -> None:
        if self.demo:
            self._start_demo()
        else:
            self.face.set_state(FaceState.THINKING, "Starting systems")
            threading.Thread(
                target=self._run_assistant,
                name="noco-voice-assistant",
                daemon=True,
            ).start()
        self.root.mainloop()

    def close(self) -> None:
        if self.assistant is not None:
            self.assistant.stop()
        self.root.destroy()

    def _run_assistant(self) -> None:
        try:
            # Delay hardware/model imports until after the window is visible.
            from client.app import VoiceAssistant

            self.assistant = VoiceAssistant(on_state_change=self.face.set_state)
            self.assistant.run()
        except Exception as exc:
            print(f"Display voice worker error: {exc}")
            self.face.set_state(FaceState.ERROR, str(exc))

    def _start_demo(self) -> None:
        states = [
            (FaceState.WAITING, "Say hey noco"),
            (FaceState.LISTENING, "I'm listening"),
            (FaceState.THINKING, "Thinking"),
            (FaceState.SPEAKING, "Speaking"),
            (FaceState.ERROR, "Connection error"),
        ]
        current = 0

        def advance() -> None:
            nonlocal current
            state, message = states[current]
            self.face.set_state(state, message)
            current = (current + 1) % len(states)
            self.root.after(2500, advance)

        advance()
