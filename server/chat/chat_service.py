from fastapi import APIRouter
from pydantic import BaseModel
from server.llm.ollama_engine import OllamaEngine
from server.memory.memory_engine import MemoryEngine

class Request(BaseModel):
    text: str

memory = MemoryEngine()
llm = OllamaEngine()
router = APIRouter()

@router.post("/chat", tags=["chat"])
async def chat(request: Request):

    # prompt = request.text

    messages = [
        {
            "role": "user",
            "content": request.text,
        }
    ]
    # memories = memory.search(request.text)

    # prompt = memory.build_context(
    #     request.text,
    #     memories
    # )

    answer = llm.generate(messages)

    # memory.add(request.text)
    # memory.add(answer)

    return {
        "response": answer
    } 