# vector_store.py

import os
import json
import numpy as np
import faiss
from loguru import logger
from config import AppConfig

config = AppConfig()


class VectorStore:
    def __init__(self):
        self.index = None
        self.chunks = []
        self.dimension = None

    def build_index(self, embedded_chunks: list[dict]) -> None:
        if not embedded_chunks:
            raise ValueError("No embeddings provided.")

        embeddings = np.array(
            [c["embedding"] for c in embedded_chunks],
            dtype=np.float32
        )

        self.dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(embeddings)

        # store metadata only (drop embedding vectors)
        self.chunks = [
            {k: v for k, v in c.items() if k != "embedding"}
            for c in embedded_chunks
        ]

        logger.info(f"Indexed {self.index.ntotal} vectors.")
 

    def search(self, query_vector: np.ndarray, top_k: int | None = None) -> list[dict]:
        if self.index is None:
            raise RuntimeError("Index not built.")

        top_k = top_k or config.TOP_K_RETRIEVAL
        query = np.array([query_vector], dtype=np.float32)

        distances, indices = self.index.search(query, top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            item = self.chunks[idx].copy()
            item["score"] = float(dist)
            results.append(item)

        return results
 

    def save(self, path: str | None = None) -> None:
        path = path or config.VECTOR_STORE_PATH
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        faiss.write_index(self.index, path + ".index")

        with open(path + ".json", "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False)

    def load(self, path: str | None = None) -> None:
        path = path or config.VECTOR_STORE_PATH

        index_path = path + ".index"
        meta_path = path + ".json"

        if not os.path.exists(index_path):
            raise FileNotFoundError(index_path)

        self.index = faiss.read_index(index_path)

        with open(meta_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

        self.dimension = self.index.d

    def is_empty(self) -> bool:
        return self.index is None or self.index.ntotal == 0