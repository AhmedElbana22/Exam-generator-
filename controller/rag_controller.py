"""
RAG pipeline controller.

Changes vs v1: updated with more advanced RAG features: 
    - difficulty_aware_retrieve(): rewrites query based on cognitive level
    - MMR (Maximal Marginal Relevance) re-ranking for chunk diversity
    - Chunk rotation: tracks used chunk IDs per session, avoids repeats
    - retrieve_as_context() accepts difficulty param and passes it through
"""

import hashlib
import numpy as np
from loguru import logger
from config import AppConfig
from services.text_processor import TextProcessor
from services.embedding_service import EmbeddingService
from services.vector_store import VectorStore

config = AppConfig()

# Difficulty -> query prefix that steers FAISS toward different semantic regions
_DIFFICULTY_QUERY_PREFIX = {
    "easy":   "basic definition introduction overview what is {topic}",
    "medium": "how mechanism process application explain why {topic}",
    "hard":   "compare contrast analyze limitations tradeoffs advanced {topic}",
}

# How many extra candidates to fetch before MMR re-ranking
_MMR_CANDIDATE_MULTIPLIER = 3

# MMR lambda: 0 = max diversity, 1 = max relevance (0.6 balances both)
_MMR_LAMBDA = 0.6


class RAGController:

    def __init__(self):
        self.text_processor    = TextProcessor()
        self.embedding_service = EmbeddingService()
        self.vector_store      = VectorStore()
        self.is_loaded         = False
        # rolling set of chunk IDs used across sessions → forces rotation
        self._used_chunk_ids: set[str] = set()
        logger.info("RAGController initialized")

    # Document loading  

    def load_document(self, pdf_path: str) -> int:
        logger.info(f"Loading PDF: {pdf_path}")
        chunks = self.text_processor.process_pdf(pdf_path)
        return self._embed_and_index(chunks)

    def load_text(self, text: str) -> int:
        logger.info(f"Loading text ({len(text)} chars)")
        chunks = self.text_processor.process_text(text)
        return self._embed_and_index(chunks)

    def _embed_and_index(self, chunks: list[dict]) -> int:
        # attach a stable chunk ID based on content hash
        for chunk in chunks:
            chunk["chunk_id"] = hashlib.sha1(
                chunk["text"].encode()
            ).hexdigest()[:12]

        embedded_chunks = self.embedding_service.embed_chunks(chunks)
        self.vector_store.build_index(embedded_chunks)
        self._used_chunk_ids.clear()   # reset rotation on new document
        self.is_loaded = True
        logger.success(f"RAG ready — {len(chunks)} chunks indexed")
        return len(chunks)

    # Core retrieval 

    def retrieve(
        self,
        query:      str,
        top_k:      int  = None,
        difficulty: str  = "medium",
        rotate:     bool = True,
    ) -> list[dict]:
        """
        Retrieve top-K chunks with:
            1. Difficulty-aware query rewriting
            2. MMR diversity re-ranking
            3. Chunk rotation (avoids reusing same chunks across quizzes)

        Args:
            query:      User topic string
            top_k:      Final number of chunks to return
            difficulty: 'easy' | 'medium' | 'hard'
            rotate:     If True, deprioritise previously used chunks

        Returns:
            List of chunk dicts with 'text', 'chunk_id', 'score'
        """
        if not self.is_loaded:
            raise RuntimeError("No document loaded.")

        top_k      = top_k or config.TOP_K_RETRIEVAL
        candidates = top_k * _MMR_CANDIDATE_MULTIPLIER

        # Step 1: rewrite query for this difficulty level
        rewritten_query = self._rewrite_query(query, difficulty)
        logger.info(
            f"RAG retrieve | difficulty={difficulty} | "
            f"query='{rewritten_query[:80]}'"
        )

        # Step 2: embed the rewritten query
        query_vector = self.embedding_service.embed_query(rewritten_query)

        # Step 3: fetch more candidates than needed for MMR
        raw_results = self.vector_store.search(query_vector, top_k=candidates)

        # Step 4: rotation filter — push used chunks to bottom
        if rotate and self._used_chunk_ids:
            fresh  = [r for r in raw_results if r.get("chunk_id") not in self._used_chunk_ids]
            used   = [r for r in raw_results if r.get("chunk_id") in self._used_chunk_ids]
            raw_results = fresh + used
            if fresh:
                logger.debug(f"Rotation: {len(fresh)} fresh chunks prioritised")

        # Step 5: MMR re-ranking for diversity
        final_chunks = self._mmr_rerank(
            query_vector = query_vector,
            candidates   = raw_results,
            top_k        = top_k,
        )

        # Step 6: register chosen chunks as used
        for chunk in final_chunks:
            if "chunk_id" in chunk:
                self._used_chunk_ids.add(chunk["chunk_id"])

        # rolling cap on used set — forget oldest 50% when too large
        if len(self._used_chunk_ids) > config.MAX_USED_CHUNKS:
            overflow   = list(self._used_chunk_ids)
            keep_from  = len(overflow) // 2
            self._used_chunk_ids = set(overflow[keep_from:])
            logger.debug("Chunk rotation set pruned (50% oldest dropped)")

        logger.success(f"Retrieved {len(final_chunks)} chunks after MMR + rotation")
        return final_chunks

    def retrieve_as_context(
        self,
        query:      str,
        top_k:      int  = None,
        difficulty: str  = "medium",
    ) -> str:
        """Return retrieved chunks joined as a single context string."""
        chunks = self.retrieve(query, top_k=top_k, difficulty=difficulty)
        parts  = [f"[Chunk {i}]\n{c['text']}" for i, c in enumerate(chunks, 1)]
        context = "\n\n".join(parts)
        logger.debug(f"Context built — {len(context)} chars from {len(chunks)} chunks")
        return context

    # Query rewriting  

    @staticmethod
    def _rewrite_query(topic: str, difficulty: str) -> str:
        """
        Prepend difficulty-specific semantic steering words.
        This shifts the FAISS search toward different regions of the
        embedding space for the same topic.
        """
        template = _DIFFICULTY_QUERY_PREFIX.get(difficulty, "{topic}")
        return template.replace("{topic}", topic)

    # MMR re-ranking  

    def _mmr_rerank(
        self,
        query_vector: np.ndarray,
        candidates:   list[dict],
        top_k:        int,
    ) -> list[dict]:
        """
        Maximal Marginal Relevance re-ranking.

        Balances relevance to query vs diversity among selected chunks.
        Prevents the index from returning 4 chunks that all say the same thing.

        MMR score = λ * sim(chunk, query) - (1-λ) * max_sim(chunk, selected)
        """
        if len(candidates) <= top_k:
            return candidates

        # get or compute embeddings for candidates
        candidate_vecs = []
        for c in candidates:
            if "embedding" in c and c["embedding"] is not None:
                vec = np.array(c["embedding"], dtype=np.float32)
            else:
                vec = self.embedding_service.embed_query(c["text"])
            candidate_vecs.append(vec)

        query_vec   = np.array(query_vector, dtype=np.float32)
        selected_idx: list[int] = []
        remaining    = list(range(len(candidates)))

        while len(selected_idx) < top_k and remaining:
            best_idx   = None
            best_score = -float("inf")

            for i in remaining:
                relevance = float(np.dot(candidate_vecs[i], query_vec) / (
                    np.linalg.norm(candidate_vecs[i]) * np.linalg.norm(query_vec) + 1e-9
                ))

                if selected_idx:
                    sim_to_selected = max(
                        float(np.dot(candidate_vecs[i], candidate_vecs[j]) / (
                            np.linalg.norm(candidate_vecs[i])
                            * np.linalg.norm(candidate_vecs[j]) + 1e-9
                        ))
                        for j in selected_idx
                    )
                else:
                    sim_to_selected = 0.0

                score = _MMR_LAMBDA * relevance - (1 - _MMR_LAMBDA) * sim_to_selected

                if score > best_score:
                    best_score = score
                    best_idx   = i

            if best_idx is not None:
                selected_idx.append(best_idx)
                remaining.remove(best_idx)

        return [candidates[i] for i in selected_idx]

    # Persistence 

    def save_index(self, path: str = None) -> None:
        self.vector_store.save(path)

    def load_index(self, path: str = None) -> None:
        self.vector_store.load(path)
        self.is_loaded = True
        logger.success("RAG index loaded from disk")

    def reset_rotation(self) -> None:
        """Call this if you want a fresh start with no chunk memory."""
        self._used_chunk_ids.clear()