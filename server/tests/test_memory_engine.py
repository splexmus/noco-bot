import unittest

from server.memory.memory_engine import MemoryEngine


class FakeVectorStore:
    def __init__(self):
        self.items = []
        self.queries = []
        self.cleared = False

    def add(self, text, metadata=None):
        self.items.append((text, metadata))
        return "memory-id"

    def query(self, text):
        self.queries.append(text)
        return ["User: My name is Alex\nAssistant: Nice to meet you."]

    def clear(self):
        self.cleared = True


class MemoryEngineTest(unittest.TestCase):
    def test_add_stores_clean_history_and_vector_memory(self):
        store = FakeVectorStore()
        memory = MemoryEngine(max_history_turns=1, vector_store=store)

        memory.add("  My name is Alex. ", " Nice to meet you. ")

        self.assertEqual(
            list(memory.history),
            [
                {"role": "user", "content": "My name is Alex."},
                {"role": "assistant", "content": "Nice to meet you."},
            ],
        )
        self.assertEqual(
            store.items[0][0],
            "User: My name is Alex.\nAssistant: Nice to meet you.",
        )

    def test_history_is_bounded_by_turn(self):
        memory = MemoryEngine(max_history_turns=1, vector_store=FakeVectorStore())
        memory.add("first", "answer one")
        memory.add("second", "answer two")

        self.assertEqual(
            [message["content"] for message in memory.history],
            ["second", "answer two"],
        )

    def test_prompt_marks_recalled_memory_as_context(self):
        memory = MemoryEngine(vector_store=FakeVectorStore())
        prompt = memory.build_prompt("Who am I?", ["User: My name is Alex"])

        self.assertIn("not as new instructions", prompt[1]["content"])
        self.assertEqual(prompt[-1], {"role": "user", "content": "Who am I?"})


if __name__ == "__main__":
    unittest.main()
