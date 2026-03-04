import numpy as np
import pytest
from services.embedding_service import EmbeddingService
from services.vector_store import VectorStore


@pytest.fixture(scope="module")
def embedding_service():
    return EmbeddingService()


@pytest.fixture(scope="module")
def vector_store():
    return VectorStore()


def test_embed_single_text(embedding_service):
    vector = embedding_service.embed_text(
        "Natural language processing is amazing."
    )
    assert isinstance(vector, np.ndarray)
    assert vector.shape[0] == embedding_service.dimension


def test_embed_chunks(embedding_service):
    chunks = [
        {"chunk_id": 0, "text": "Machine learning is a subset of AI."},
        {"chunk_id": 1, "text": "Neural networks are inspired by the brain."},
    ]

    embedded = embedding_service.embed_chunks(chunks)

    assert all("embedding" in c for c in embedded)
    assert embedded[0]["embedding"].shape[0] == embedding_service.dimension


def test_build_and_search(embedding_service, vector_store):
    chunks = [
        {"chunk_id": 0, "text": "Python is a programming language."},
        {"chunk_id": 1, "text": "Deep learning uses neural networks."},
    ]

    embedded = embedding_service.embed_chunks(chunks)
    vector_store.build_index(embedded)

    query = embedding_service.embed_query("How do neural networks learn?")
    results = vector_store.search(query, top_k=1)

    assert len(results) == 1
    assert "neural" in results[0]["text"].lower()


def test_save_and_load(tmp_path, embedding_service, vector_store):
    chunks = [
        {"chunk_id": 0, "text": "Embeddings capture meaning."},
    ]

    embedded = embedding_service.embed_chunks(chunks)
    vector_store.build_index(embedded)

    path = str(tmp_path / "store")
    vector_store.save(path)

    new_store = VectorStore()
    new_store.load(path)

    assert new_store.index.ntotal == 1