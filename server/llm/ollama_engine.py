import asyncio
from ollama import chat

class OllamaEngine:
    def __init__(
        self,
        model: str = "gemma4:e4b",
    ):
        self.model = model

    def generate(self, prompt):
        response = chat(self.model, messages=prompt)
        return response['message']['content']