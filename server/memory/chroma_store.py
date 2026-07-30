from chromadb.utils.embedding_functions.ollama_embedding_function import (
    OllamaEmbeddingFunction,
)
import chromadb
import uuid

class Chromadb:
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        ollama_model: str = "nomic-embed-text",
        n_result: int = 5,
    ):
        self.ollama_ef = OllamaEmbeddingFunction(
            url=ollama_url,
            model_name=ollama_model,
        )
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.get_or_create_collection(
            name="NOCO_memory",
            embedding_function=self.ollama_ef,
        )
        self.n_result = n_result

    def add(
        self,
        text: str, 
    ):
        self.collection.add(
            ids=[str(uuid.uuid4())],
            documents=[text],
            metadatas=[
                {
                    "type": "conversation",
                    "speaker": "assistant",
                }
            ]
        )

    def query(
        self,
        query_texts: str,
    ):
        if self.collection.count() == 0:
            return []
        
        results = self.collection.query(
            query_texts=[query_texts],
            n_results = self.n_result
        )
        return results