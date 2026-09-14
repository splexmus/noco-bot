import unittest

from server.chat.chat_service import ChatRequest, chat


class FakeMemory:
    def __init__(self, search_error=None):
        self.search_error = search_error
        self.saved = []
        self.prompt_memories = None

    def search(self, _text):
        if self.search_error is not None:
            raise self.search_error
        return ["remembered context"]

    def build_prompt(self, text, memories):
        self.prompt_memories = memories
        return [{"role": "user", "content": text}]

    def add(self, request, answer):
        self.saved.append((request, answer))


class FakeLlm:
    def generate(self, _prompt):
        return " A useful answer. "


class ChatServiceTest(unittest.TestCase):
    def test_successful_answer_is_saved_to_memory(self):
        memory = FakeMemory()

        response = chat(ChatRequest(text="hello"), memory=memory, llm=FakeLlm())

        self.assertEqual(response.response, "A useful answer.")
        self.assertEqual(memory.saved, [("hello", "A useful answer.")])

    def test_chat_continues_when_vector_search_is_unavailable(self):
        memory = FakeMemory(search_error=RuntimeError("embedding service offline"))

        response = chat(ChatRequest(text="hello"), memory=memory, llm=FakeLlm())

        self.assertEqual(response.response, "A useful answer.")
        self.assertEqual(memory.prompt_memories, [])
        self.assertEqual(memory.saved, [("hello", "A useful answer.")])


if __name__ == "__main__":
    unittest.main()
