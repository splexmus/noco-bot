from __future__ import annotations

import math
import queue
import tkinter as tk
from dataclasses import dataclass
from enum import Enum
from time import monotonic


class FaceState(str, Enum):
    WAITING = "waiting"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass(frozen=True)
class FaceTheme:
    """Colors and sizing ratios intended to be easy to customize."""

    background: str = "#07111f"
    face: str = "#59f3ff"
    face_dim: str = "#178b9b"
    pupil: str = "#07111f"
    error: str = "#ff5876"
    text: str = "#bdfbff"
    font_family: str = "DejaVu Sans"
    eye_spacing: float = 0.19
    eye_width: float = 0.16
    eye_height: float = 0.19
    line_width: float = 0.012


@dataclass(frozen=True)
class Expression:
    eye_openness: float
    pupil_offset: float
    mouth: str


# Edit these values to change the geometry of each expression.
EXPRESSIONS = {
    FaceState.WAITING: Expression(0.72, 0.0, "smile"),
    FaceState.LISTENING: Expression(1.0, 0.0, "listen"),
    FaceState.THINKING: Expression(0.55, 0.28, "flat"),
    FaceState.SPEAKING: Expression(0.82, 0.0, "speak"),
    FaceState.ERROR: Expression(1.0, 0.0, "error"),
}

STATE_ALIASES = {
    "WAITING": FaceState.WAITING,
    "LISTENING": FaceState.LISTENING,
    "STT_REQUEST": FaceState.THINKING,
    "CHAT_REQUEST": FaceState.THINKING,
    "TTS_REQUEST": FaceState.SPEAKING,
    "ERROR": FaceState.ERROR,
}


def coerce_face_state(value: FaceState | str | object) -> FaceState:
    """Map UI states and voice-pipeline enum values to a face state."""
    if isinstance(value, FaceState):
        return value

    name = getattr(value, "name", value)
    normalized = str(name).strip().upper()
    if normalized in STATE_ALIASES:
        return STATE_ALIASES[normalized]

    try:
        return FaceState(str(value).strip().lower())
    except ValueError as exc:
        raise ValueError(f"Unsupported face state: {value}") from exc


class RobotFaceDisplay:
    """Responsive animated robot face drawn entirely with Tkinter."""

    def __init__(
        self,
        root: tk.Tk,
        theme: FaceTheme | None = None,
        fullscreen: bool = True,
    ) -> None:
        self.root = root
        self.theme = theme or FaceTheme()
        self.state = FaceState.WAITING
        self.message = "Say hey noco"
        self._updates: queue.SimpleQueue[tuple[FaceState, str | None]] = (
            queue.SimpleQueue()
        )

        self.root.title("NOCO Robot Face")
        self.root.configure(bg=self.theme.background)
        self.root.attributes("-fullscreen", fullscreen)
        self.root.bind("<Escape>", self._leave_fullscreen)
        self.root.bind("<F11>", self._toggle_fullscreen)

        self.canvas = tk.Canvas(
            root,
            background=self.theme.background,
            highlightthickness=0,
            cursor="none" if fullscreen else "",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _event: self._draw())

        self._animation_started = monotonic()
        self.root.after(0, self._tick)

    def set_state(
        self,
        state: FaceState | str | object,
        message: str | None = None,
    ) -> None:
        """Queue an update safely from the voice worker thread."""
        self._updates.put((coerce_face_state(state), message))

    def _tick(self) -> None:
        while True:
            try:
                state, message = self._updates.get_nowait()
            except queue.Empty:
                break
            self.state = state
            if message is not None:
                self.message = message
            self._animation_started = monotonic()

        self._draw()
        self.root.after(50, self._tick)

    def _draw(self) -> None:
        width = max(self.canvas.winfo_width(), 320)
        height = max(self.canvas.winfo_height(), 240)
        size = min(width, height)
        center_x = width / 2
        center_y = height * 0.43
        expression = EXPRESSIONS[self.state]
        elapsed = monotonic() - self._animation_started
        color = self.theme.error if self.state is FaceState.ERROR else self.theme.face
        line_width = max(3, int(size * self.theme.line_width))

        self.canvas.delete("all")
        self._draw_ambient(center_x, center_y, size, elapsed, color, line_width)
        self._draw_eyes(
            center_x, center_y, size, elapsed, expression, color, line_width
        )
        self._draw_mouth(
            center_x, center_y, size, elapsed, expression.mouth, color, line_width
        )

        self.canvas.create_text(
            center_x,
            height * 0.86,
            text=self.message,
            fill=self.theme.text if self.state is not FaceState.ERROR else color,
            font=(self.theme.font_family, max(14, int(size * 0.035)), "bold"),
        )

    def _draw_ambient(
        self,
        x: float,
        y: float,
        size: float,
        elapsed: float,
        color: str,
        line_width: int,
    ) -> None:
        if self.state is FaceState.LISTENING:
            pulse = 1.0 + 0.08 * math.sin(elapsed * 4)
            radius = size * 0.36 * pulse
            self.canvas.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                outline=self.theme.face_dim,
                width=max(2, line_width // 2),
            )
        elif self.state is FaceState.THINKING:
            for index in range(3):
                phase = elapsed * 4 - index * 0.8
                dot_y = y - size * 0.34 - max(0.0, math.sin(phase)) * size * 0.025
                dot_x = x + (index - 1) * size * 0.055
                radius = size * 0.012
                self.canvas.create_oval(
                    dot_x - radius,
                    dot_y - radius,
                    dot_x + radius,
                    dot_y + radius,
                    fill=color,
                    outline="",
                )

    def _draw_eyes(
        self,
        x: float,
        y: float,
        size: float,
        elapsed: float,
        expression: Expression,
        color: str,
        line_width: int,
    ) -> None:
        eye_y = y - size * 0.08
        eye_width = size * self.theme.eye_width
        eye_height = size * self.theme.eye_height * expression.eye_openness
        blink = self.state is FaceState.WAITING and elapsed % 4.2 < 0.14
        if blink:
            eye_height = max(line_width, eye_height * 0.08)

        for side in (-1, 1):
            eye_x = x + side * size * self.theme.eye_spacing
            bounds = (
                eye_x - eye_width / 2,
                eye_y - eye_height / 2,
                eye_x + eye_width / 2,
                eye_y + eye_height / 2,
            )

            if self.state is FaceState.ERROR:
                half_width = eye_width * 0.42
                half_height = size * self.theme.eye_height * 0.38
                self.canvas.create_line(
                    eye_x - half_width,
                    eye_y - half_height,
                    eye_x + half_width,
                    eye_y + half_height,
                    fill=color,
                    width=line_width,
                    capstyle=tk.ROUND,
                )
                self.canvas.create_line(
                    eye_x + half_width,
                    eye_y - half_height,
                    eye_x - half_width,
                    eye_y + half_height,
                    fill=color,
                    width=line_width,
                    capstyle=tk.ROUND,
                )
                continue

            self.canvas.create_oval(*bounds, fill=color, outline="")
            if not blink:
                pupil_radius = min(eye_width, eye_height) * 0.22
                pupil_x = eye_x + expression.pupil_offset * side * eye_width
                self.canvas.create_oval(
                    pupil_x - pupil_radius,
                    eye_y - pupil_radius,
                    pupil_x + pupil_radius,
                    eye_y + pupil_radius,
                    fill=self.theme.pupil,
                    outline="",
                )

    def _draw_mouth(
        self,
        x: float,
        y: float,
        size: float,
        elapsed: float,
        mouth: str,
        color: str,
        line_width: int,
    ) -> None:
        mouth_y = y + size * 0.18
        mouth_width = size * 0.23

        if mouth == "speak":
            openness = 0.05 + 0.035 * (1 + math.sin(elapsed * 10))
            self.canvas.create_oval(
                x - mouth_width / 2,
                mouth_y - size * openness,
                x + mouth_width / 2,
                mouth_y + size * openness,
                fill=color,
                outline="",
            )
        elif mouth == "listen":
            radius = size * (0.035 + 0.007 * math.sin(elapsed * 5))
            self.canvas.create_oval(
                x - radius,
                mouth_y - radius,
                x + radius,
                mouth_y + radius,
                outline=color,
                width=line_width,
            )
        elif mouth == "flat":
            self.canvas.create_line(
                x - mouth_width / 2,
                mouth_y,
                x + mouth_width / 2,
                mouth_y,
                fill=color,
                width=line_width,
                capstyle=tk.ROUND,
            )
        elif mouth == "error":
            points = []
            for index in range(7):
                points.extend(
                    (
                        x - mouth_width / 2 + index * mouth_width / 6,
                        mouth_y + (-1 if index % 2 else 1) * size * 0.018,
                    )
                )
            self.canvas.create_line(
                *points,
                fill=color,
                width=line_width,
                capstyle=tk.ROUND,
                joinstyle=tk.ROUND,
            )
        else:
            self.canvas.create_arc(
                x - mouth_width / 2,
                mouth_y - size * 0.08,
                x + mouth_width / 2,
                mouth_y + size * 0.07,
                start=200,
                extent=140,
                style=tk.ARC,
                outline=color,
                width=line_width,
            )

    def _leave_fullscreen(self, _event=None) -> None:
        self.root.attributes("-fullscreen", False)
        self.canvas.configure(cursor="")

    def _toggle_fullscreen(self, _event=None) -> None:
        fullscreen = not bool(self.root.attributes("-fullscreen"))
        self.root.attributes("-fullscreen", fullscreen)
        self.canvas.configure(cursor="none" if fullscreen else "")
