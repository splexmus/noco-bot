import unittest

from server.memory.chroma_store import ChromaMemory


class FakeCollection:
    def __init__(self):
        self.requested_results = None

    def count(self):
        return 2

    def query(self, query_texts, n_results):
        self.requested_results = n_results
        return {"documents": [["first memory", "first memory"]]}


class ChromaMemoryQueryTest(unittest.TestCase):
    def test_query_clamps_result_count_and_removes_duplicates(self):
        memory = ChromaMemory.__new__(ChromaMemory)
        memory.n_result = 5
        memory.collection = FakeCollection()

        result = memory.query("question")

        self.assertEqual(memory.collection.requested_results, 2)
        self.assertEqual(result, ["first memory"])

    def test_blank_query_does_not_call_embedding_function(self):
        memory = ChromaMemory.__new__(ChromaMemory)
        memory.n_result = 5
        memory.collection = FakeCollection()

        self.assertEqual(memory.query("  "), [])
        self.assertIsNone(memory.collection.requested_results)


if __name__ == "__main__":
    unittest.main()
