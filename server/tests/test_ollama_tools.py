import json
import unittest
from copy import deepcopy

from server.llm.ollama_engine import OllamaEngine
from server.tools.camera_tool import CameraCapture, CameraToolError


JPEG = b"\xff\xd8\xffcamera frame\xff\xd9"


class FakeCamera:
    def __init__(self, error=None):
        self.error = error
        self.calls = 0

    def capture(self):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return CameraCapture(
            content=JPEG,
            content_type="image/jpeg",
            size_bytes=len(JPEG),
            sha256="test-sha",
        )


class FakeOllamaClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(deepcopy(kwargs))
        return self.responses.pop(0)


def camera_call(question="What is ahead?"):
    return {
        "message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "capture_camera_image",
                        "arguments": {"question": question},
                    }
                }
            ],
        }
    }


class OllamaCameraToolTest(unittest.TestCase):
    def test_camera_tool_uses_vision_model_then_returns_final_answer(self):
        ollama = FakeOllamaClient(
            [
                camera_call(),
                {"message": {"role": "assistant", "content": "A chair."}},
                {
                    "message": {
                        "role": "assistant",
                        "content": "I can see a chair ahead.",
                    }
                },
            ]
        )
        camera = FakeCamera()
        engine = OllamaEngine(
            model="chat-model",
            vision_model="vision-model",
            client=ollama,
            camera=camera,
        )

        answer = engine.generate([{"role": "user", "content": "What do you see?"}])

        self.assertEqual(answer, "I can see a chair ahead.")
        self.assertEqual(camera.calls, 1)
        self.assertEqual(ollama.calls[1]["model"], "vision-model")
        self.assertEqual(ollama.calls[1]["messages"][0]["images"], [JPEG])
        tool_message = ollama.calls[2]["messages"][-1]
        self.assertEqual(tool_message["role"], "tool")
        self.assertEqual(json.loads(tool_message["content"])["observation"], "A chair.")

    def test_camera_error_is_reported_to_chat_model(self):
        ollama = FakeOllamaClient(
            [
                camera_call(),
                {
                    "message": {
                        "role": "assistant",
                        "content": "I cannot access the camera right now.",
                    }
                },
            ]
        )
        engine = OllamaEngine(
            client=ollama,
            camera=FakeCamera(CameraToolError("offline")),
        )

        answer = engine.generate([{"role": "user", "content": "Look around"}])

        self.assertIn("cannot access", answer)
        tool_result = json.loads(ollama.calls[1]["messages"][-1]["content"])
        self.assertEqual(tool_result, {"ok": False, "error": "offline"})


if __name__ == "__main__":
    unittest.main()
