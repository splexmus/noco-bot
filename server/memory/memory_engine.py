from collections import deque
from .chroma_store import Chromadb

SYSTEM_PROMPT = """
Your name is NOCO, a helpful and cheerful robot assistant.

Speak naturally as if talking to a person.

Rules:
- Understand both Thai and English.
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
    ):
        self.history = deque(maxlen=max_history)
        self.chroma = Chromadb()

    def search(
        self,
        query: str
    ) -> list:
        return self.chroma.query(query_texts = query)["documents"][0]

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

        self.chroma.add(conversation)

    def clear(self) -> None:
        self.history.clear()

    def build_context(
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