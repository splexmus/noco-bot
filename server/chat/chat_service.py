import logging
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from server.llm.ollama_engine import OllamaEngine
from server.memory.memory_engine import MemoryEngine

class ChatRequest(BaseModel):
    text: str = Field(min_length=1)


class ChatResponse(BaseModel):
    response: str


router = APIRouter()
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_memory() -> MemoryEngine:
    return MemoryEngine()


@lru_cache(maxsize=1)
def get_llm() -> OllamaEngine:
    return OllamaEngine()


@router.post("/chat", tags=["chat"], response_model=ChatResponse)
def chat(
    request: ChatRequest,
    memory: MemoryEngine = Depends(get_memory),
    llm: OllamaEngine = Depends(get_llm),
) -> ChatResponse:
    text = request.text.strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Text must not be blank",
        )

    try:
        memories = memory.search(text)
    except Exception as exc:
        logger.warning("Memory search failed: %s", exc)
        memories = []

    prompt = memory.build_prompt(text, memories)
    answer = llm.generate(prompt).strip()
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The language model returned an empty response",
        )

    try:
        memory.add(request=text, answer=answer)
    except Exception as exc:
        # A vector database or embedding outage must not discard a valid answer.
        logger.warning("Memory persistence failed: %s", exc)

    return ChatResponse(response=answer)
