from fastapi import APIRouter
from pydantic import BaseModel, Field

from server.llm.ollama_engine import OllamaEngine
from server.memory.memory_engine import MemoryEngine

class ChatRequest(BaseModel):
    text: str = Field(min_length=1)

memory = MemoryEngine()
llm = OllamaEngine()
router = APIRouter()

@router.post("/chat", tags=["chat"])
async def chat(request: ChatRequest):

    text = request.text.strip()

    memories = memory.search(text)

    prompt = memory.build_prompt(
        text,
        memories
    )

    answer = llm.generate(prompt)

    memory.add(request = text, answer = answer)

    return {
        "response": answer,
        # "prompt": prompt
    } 