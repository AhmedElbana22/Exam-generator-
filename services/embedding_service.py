from sentence_transformers import SentenceTransformer
from loguru import logger
from config import AppConfig

config = AppConfig()


class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer(config.EMBED_MODEL)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding model loaded ({config.EMBED_MODEL})")

    def embed_text(self, text: str):
        return self.model.encode(text, convert_to_numpy=True)

    def embed_chunks(self, chunks: list[dict]) -> list[dict]:
        if not chunks:
            return chunks

        texts = [c["text"] for c in chunks]

        vectors = self.model.encode(
            texts,
            convert_to_numpy=True,
            batch_size=32,
            show_progress_bar=False
        )

        for chunk, vector in zip(chunks, vectors):
            chunk["embedding"] = vector

        return chunks

    def embed_query(self, query: str):
        return self.model.encode(query, convert_to_numpy=True)