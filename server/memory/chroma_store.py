from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions.ollama_embedding_function import (
    OllamaEmbeddingFunction,
)

from server.config import settings


class ChromaMemory:
    def __init__(
        self,
        ollama_url: str | None = None,
        ollama_model: str | None = None,
        n_result: int | None = None,
        database_path: str | Path | None = None,
        collection_name: str = "NOCO_memory",
    ) -> None:
        self.n_result = max(1, n_result or settings.memory_results)
        self.collection_name = collection_name
        self.database_path = Path(database_path or settings.memory_db_path).resolve()
        self.database_path.mkdir(parents=True, exist_ok=True)

        self.ollama_ef = OllamaEmbeddingFunction(
            url=ollama_url or settings.ollama_host,
            model_name=ollama_model or settings.embedding_model,
        )
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.database_path)
        )
        self.collection = self._get_or_create_collection()

    def add(
        self,
        text: str,
        metadata: dict[str, str] | None = None,
    ) -> str:
        normalized_text = text.strip()
        if not normalized_text:
            raise ValueError("Memory text must not be empty")

        memory_id = str(uuid.uuid4())
        stored_metadata = {
            "type": "conversation",
            "created_at": datetime.now(UTC).isoformat(),
            **(metadata or {}),
        }
        self.collection.add(
            ids=[memory_id],
            documents=[normalized_text],
            metadatas=[stored_metadata],
        )
        return memory_id

    def query(
        self,
        query_text: str,
    ) -> list[str]:
        normalized_query = query_text.strip()
        count = self.collection.count()
        if not normalized_query or count == 0:
            return []

        results = self.collection.query(
            query_texts=[normalized_query],
            n_results=min(self.n_result, count),
        )
        documents = results.get("documents") or []
        if not documents:
            return []

        # Preserve relevance order while removing duplicate text.
        return list(dict.fromkeys(document for document in documents[0] if document))

    def clear(self) -> None:
        try:
            self.chroma_client.delete_collection(self.collection_name)
        except ValueError:
            pass
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        return self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.ollama_ef,
        )
