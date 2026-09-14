import unittest

import numpy as np

from server.stt.whisper_engine import WhisperEngine


class FakeTranscriber:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def __call__(self, audio, **kwargs):
        self.calls.append((audio, kwargs))
        return self.result


class HuggingFaceWhisperTest(unittest.TestCase):
    def test_transcribes_pcm16_with_timestamps(self):
        transcriber = FakeTranscriber(
            {
                "text": "สวัสดี โนโค",
                "chunks": [
                    {"text": "สวัสดี", "timestamp": (0.0, 0.5)},
                    {"text": "โนโค", "timestamp": (0.5, 1.0)},
                ],
            }
        )
        engine = WhisperEngine(language="th", transcriber=transcriber)

        segments, info = engine.transcribe(
            np.array([0, 16_384, -32_768], dtype=np.int16)
        )

        audio_input, options = transcriber.calls[0]
        self.assertEqual(audio_input["sampling_rate"], 16_000)
        np.testing.assert_allclose(
            audio_input["array"],
            np.array([0.0, 0.5, -1.0], dtype=np.float32),
        )
        self.assertTrue(options["return_timestamps"])
        self.assertEqual(options["generate_kwargs"]["language"], "th")
        self.assertEqual(
            [segment.text for segment in segments],
            ["สวัสดี", "โนโค"],
        )
        self.assertEqual(info.language, "th")
        self.assertEqual(info.language_probability, 1.0)

    def test_text_without_chunks_gets_one_duration_segment(self):
        engine = WhisperEngine(
            language="en",
            transcriber=FakeTranscriber({"text": "hello"}),
        )

        segments, _info = engine.transcribe(np.zeros(8_000, dtype=np.float32))

        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].start, 0.0)
        self.assertEqual(segments[0].end, 0.5)
        self.assertEqual(segments[0].text, "hello")

    def test_rejects_multichannel_audio(self):
        engine = WhisperEngine(transcriber=FakeTranscriber({"text": ""}))

        with self.assertRaisesRegex(ValueError, "mono"):
            engine.transcribe(np.zeros((2, 100), dtype=np.float32))


if __name__ == "__main__":
    unittest.main()
