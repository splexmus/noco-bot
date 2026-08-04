from collections import deque
from .chroma_store import ChromaMemory

SYSTEM_PROMPT = """
Your name is NOCO, a helpful, friendly and cheerful robot assistant.

Speak naturally as if talking to a person.

Rules:
- Only understand in Thai or English.
- Respond in English only.
- Never use emojis.
- Avoid markdown.
- Avoid bullet lists unless requested.
- Keep answers concise (normally under 3 sentences).
- If the user speaks Thai, understand the request and answer in English.
- If the request is unclear, ask one brief clarifying question.
- Do not invent facts. If uncertain, say you don't know.
"""

class MemoryEngine:
    def __init__(
        self,
        max_history: int = 20,
        n_result: int | None = None,
    ):
        self.history = deque(maxlen=max_history)
        if n_result: 
            self.vector_store = ChromaMemory(n_result = n_result)
        else:
            self.vector_store = ChromaMemory()

    def search(self, query: str) -> list[str]:
        return self.vector_store.query(query)

    def add(
        self,
        request: str,
        answer: str, 
    ):
        self.history.append({
            "role": "user",
            "content": request,
        })

        self.history.append({
            "role": "assistant",
            "content": answer,
        })

        conversation = f"""
        User: {request}
        Assistant: {answer}
        """

        self.vector_store.add(conversation)

    def clear_history(self) -> None:
        self.history.clear()

    def clear_memory(self) -> None:
        self.vector_store.clear()

    def reset(self)-> None:
        self.clear_history()
        self.clear_memory()

    def build_prompt(
        self,
        request: str,
        memories: str | None = None,
    ):
        messages = []

        messages.append({
            "role": "system",
            "content": SYSTEM_PROMPT
        })

        if memories:
            memory_text = "\n".join(memories)

            messages.append({
                "role": "system",
                "content": f"Relevant memories:\n" + memory_text
            })

        messages.extend(self.history)

        messages.append({
            "role": "user",
            "content": request
        })

        return messages