from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


SERVER_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Settings:
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    chat_model: str = os.getenv("OLLAMA_CHAT_MODEL", "qwen3:0.6b")
    vision_model: str = os.getenv("OLLAMA_VISION_MODEL", "gemma3:4b")
    embedding_model: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    robot_api_url: str = os.getenv("ROBOT_API_URL", "http://localhost:8001")
    camera_timeout_seconds: float = float(os.getenv("CAMERA_TIMEOUT_SECONDS", "10"))
    memory_results: int = int(os.getenv("MEMORY_RESULTS", "5"))
    memory_db_path: Path = Path(
        os.getenv("MEMORY_DB_PATH", str(SERVER_DIR / "memory" / "memory_db"))
    ).expanduser()


settings = Settings()
