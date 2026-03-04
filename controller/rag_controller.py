from loguru import logger
from config import AppConfig
from services.text_processor import TextProcessor
from services.embedding_service import EmbeddingService
from services.vector_store import VectorStore

config = AppConfig()


class RAGController:
    """
    Full RAG pipeline controller which connects TextProcessor -> EmbeddingService -> VectorStore.
    """

    def __init__(self):
        self.text_processor  = TextProcessor() 
        self.embedding_service = EmbeddingService()
        self.vector_store    = VectorStore()
        self.is_loaded       = False
        logger.info("RAGController initialized")

    def load_document(self, pdf_path: str) -> int:
        logger.info(f"Loading PDF document: {pdf_path}")

        # Step 1 : extract+clean+chunk
        chunks = self.text_processor.process_pdf(pdf_path)
        logger.info(f"Got {len(chunks)} chunks from PDF")

        # Step 2 : embed+index
        return self._embed_and_index(chunks)

    def load_text(self, text: str) -> int:
        logger.info(f"Loading raw text ({len(text)} chars)")

        # Step 1 : clean+chunk
        chunks = self.text_processor.process_text(text)
        logger.info(f"Got {len(chunks)} chunks from text")

        # Step 2 : embed+index
        return self._embed_and_index(chunks)

    def _embed_and_index(self, chunks: list[dict]) -> int:
        # Step 1 : embed all chunks
        embedded_chunks = self.embedding_service.embed_chunks(chunks)
        # Step 2 : build FAISS index
        self.vector_store.build_index(embedded_chunks)

        self.is_loaded = True
        logger.success(f"RAG pipeline ready — {len(chunks)} chunks indexed")
        return len(chunks)

    def retrieve(self, query: str, top_k: int = None) -> list[dict]:
        if not self.is_loaded:
            raise RuntimeError("No document loaded! Call load_document() or load_text() first.")

        top_k = top_k or config.TOP_K_RETRIEVAL

        logger.info(f"Retrieving top-{top_k} chunks for: '{query[:60]}...'")
        # Step 1 : embed the query
        query_vector = self.embedding_service.embed_query(query)
        # Step 2 : search FAISS
        results = self.vector_store.search(query_vector, top_k=top_k)

        logger.success(f"Retrieved {len(results)} relevant chunks")
        return results

    def retrieve_as_context(self, query: str, top_k: int = None) -> str:
        chunks = self.retrieve(query, top_k=top_k)

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"[Chunk {i}]\n{chunk['text']}")

        context = "\n\n".join(context_parts)
        logger.debug(f"Context built — {len(context)} characters")
        return context

    def save_index(self, path: str = None) -> None:
        """Save current FAISS index to disk for reuse."""
        self.vector_store.save(path)

    def load_index(self, path: str = None) -> None:
        """Load a previously saved FAISS index from disk."""
        self.vector_store.load(path)
        self.is_loaded = True
        logger.success("RAG index loaded from disk")