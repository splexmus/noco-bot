import unittest

from client.display.face import EXPRESSIONS, FaceState, coerce_face_state


class PipelineState:
    def __init__(self, name: str) -> None:
        self.name = name


class DisplayStateTest(unittest.TestCase):
    def test_every_face_state_has_an_expression(self):
        self.assertEqual(set(EXPRESSIONS), set(FaceState))

    def test_pipeline_states_map_to_expressions(self):
        expected = {
            "WAITING": FaceState.WAITING,
            "LISTENING": FaceState.LISTENING,
            "STT_REQUEST": FaceState.THINKING,
            "CHAT_REQUEST": FaceState.THINKING,
            "TTS_REQUEST": FaceState.SPEAKING,
            "ERROR": FaceState.ERROR,
        }

        for state_name, face_state in expected.items():
            with self.subTest(state=state_name):
                self.assertEqual(
                    coerce_face_state(PipelineState(state_name)), face_state
                )

    def test_unknown_state_is_rejected(self):
        with self.assertRaises(ValueError):
            coerce_face_state("dancing")


if __name__ == "__main__":
    unittest.main()
