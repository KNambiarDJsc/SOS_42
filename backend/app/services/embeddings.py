import os
import asyncio
import numpy as np
from typing import List
from openai import AsyncOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


class EmbeddingService:
    EMBEDDING_DIM = 3072
    MAX_CHARS = 8000  # Prevent pathological latency

    def __init__(
        self,
        model: str = "text-embedding-3-large",
        batch_size: int = 64,
        max_concurrent_requests: int = 5,
    ):
        self.model = model
        self.batch_size = batch_size

        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )

        # Rate limiter to avoid OpenAI 429s
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.embedding_dim = self.EMBEDDING_DIM

    # ============================================================
    # Public API
    # ============================================================

    async def embed_documents(self, texts: List[str]) -> np.ndarray:
        """
        Embed document chunks.
        Tiny chunks (<10 chars) return zero vectors.
        """
        valid_texts, valid_indices = self._filter_texts(texts)

        if not valid_texts:
            return np.zeros((len(texts), self.EMBEDDING_DIM))

        embeddings = await self._embed_in_batches(valid_texts)

        full_embeddings = np.zeros((len(texts), self.EMBEDDING_DIM))
        full_embeddings[valid_indices] = embeddings
        return full_embeddings

    async def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a query using a multimodal, retrieval-oriented instruction.
        """
        if len(query.strip()) < 10:
            return np.zeros(self.EMBEDDING_DIM)

        instruction = (
            "Instruct: You are a retrieval system. "
            "Given a user question, generate an embedding that retrieves the most "
            "relevant information from documents including plain text, tables, "
            "and image descriptions. "
            "Focus on semantic meaning, entities, relationships, and factual context.\n\n"
            f"Query: {query}"
        )

        vectors = await self._embed_in_batches([instruction])
        return vectors[0]

    # ============================================================
    # Internal helpers
    # ============================================================

    def _filter_texts(self, texts: List[str]):
        valid_texts = []
        valid_indices = []

        for idx, text in enumerate(texts):
            if len(text.strip()) >= 10:
                valid_texts.append(text)
                valid_indices.append(idx)

        return valid_texts, valid_indices

    async def _embed_in_batches(self, texts: List[str]) -> np.ndarray:
        tasks = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            tasks.append(self._embed_batch(batch))

        results = await asyncio.gather(*tasks)
        return np.vstack(results)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=20),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def _embed_batch(self, batch: List[str]) -> np.ndarray:
        async with self.semaphore:
            # Truncate very long inputs for latency safety
            batch = [text[:self.MAX_CHARS] for text in batch]

            response = await self.client.embeddings.create(
                model=self.model,
                input=batch,
            )

            return np.array([item.embedding for item in response.data])
