from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from ollama import Client

from server.config import settings
from server.tools.camera_tool import CameraToolError, RobotCameraClient


CAMERA_TOOL = {
    "type": "function",
    "function": {
        "name": "capture_camera_image",
        "description": (
            "Get the latest image from the robot camera and inspect it. "
            "Use this when the user asks what the robot sees, requests a camera "
            "check, or asks a question that requires current visual information."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The specific question to answer from the image.",
                }
            },
            "required": ["question"],
        },
    },
}


class OllamaEngine:
    """Run chat completion and the robot-camera tool loop."""

    def __init__(
        self,
        model: str | None = None,
        vision_model: str | None = None,
        client: Client | None = None,
        camera: RobotCameraClient | None = None,
        max_tool_rounds: int = 3,
    ) -> None:
        self.model = model or settings.chat_model
        self.vision_model = vision_model or settings.vision_model
        self.client = client or Client(host=settings.ollama_host)
        self.camera = camera or RobotCameraClient()
        self.max_tool_rounds = max(1, max_tool_rounds)

    def generate(self, prompt: Sequence[Mapping[str, Any]]) -> str:
        messages: list[Any] = [dict(message) for message in prompt]
        tool_rounds = 0

        while True:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                tools=[CAMERA_TOOL],
            )
            assistant_message = self._response_message(response)
            messages.append(assistant_message)
            tool_calls = self._value(assistant_message, "tool_calls") or []

            if not tool_calls:
                content = self._value(assistant_message, "content") or ""
                return str(content).strip()

            if tool_rounds >= self.max_tool_rounds:
                raise RuntimeError("Ollama exceeded the camera tool-call limit")

            for tool_call in tool_calls:
                function = self._value(tool_call, "function")
                function_name = self._value(function, "name")
                arguments = self._value(function, "arguments") or {}

                if function_name != "capture_camera_image":
                    tool_result = json.dumps(
                        {"ok": False, "error": f"Unknown tool: {function_name}"}
                    )
                else:
                    question = str(
                        arguments.get("question")
                        or "Describe what is visible in the robot camera image."
                    )
                    tool_result = self._run_camera_tool(question)

                messages.append(
                    {
                        "role": "tool",
                        "tool_name": str(function_name),
                        "content": tool_result,
                    }
                )
            tool_rounds += 1

    def _run_camera_tool(self, question: str) -> str:
        try:
            capture = self.camera.capture()
            vision_response = self.client.chat(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": question,
                        "images": [capture.content],
                    }
                ],
            )
            vision_message = self._response_message(vision_response)
            observation = str(
                self._value(vision_message, "content") or ""
            ).strip()
            if not observation:
                raise CameraToolError("Vision model returned an empty observation")

            return json.dumps(
                {
                    "ok": True,
                    "observation": observation,
                    "image": {
                        "content_type": capture.content_type,
                        "size_bytes": capture.size_bytes,
                        "sha256": capture.sha256,
                    },
                }
            )
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)})

    @staticmethod
    def _response_message(response: Any) -> Any:
        message = OllamaEngine._value(response, "message")
        if message is None:
            raise RuntimeError("Ollama response did not contain a message")
        return message

    @staticmethod
    def _value(value: Any, key: str) -> Any:
        if isinstance(value, Mapping):
            return value.get(key)
        return getattr(value, key, None)
