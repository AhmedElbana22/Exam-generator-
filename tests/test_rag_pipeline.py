import pytest
from controller.rag_controller import RAGController


SAMPLE_TEXT = """
Artificial intelligence (AI) is intelligence demonstrated by machines.
Machine learning is a subset of AI that learns from data automatically.
Deep learning uses neural networks with many layers to solve complex problems.
Natural language processing (NLP) allows computers to understand human language.
Transformers are a neural network architecture that revolutionized NLP in 2017.
BERT and GPT are famous transformer models used in many applications.
Retrieval Augmented Generation (RAG) combines search with language generation.
Vector databases store embeddings for fast semantic similarity search.
FAISS is a library developed for efficient vector search.
Embeddings are numerical representations that capture the meaning of text.
""" * 5


@pytest.fixture(scope="module")
def rag():
    controller = RAGController()
    controller.load_text(SAMPLE_TEXT)
    return controller


def test_load_text():
    rag = RAGController()
    count = rag.load_text(SAMPLE_TEXT)

    assert count > 0
    assert rag.is_loaded


def test_retrieve_returns_results(rag):
    results = rag.retrieve("What is deep learning?", top_k=3)

    assert len(results) == 3
    assert all("text" in r for r in results)
    assert all("score" in r for r in results)


def test_retrieve_relevance(rag):
    results = rag.retrieve("natural language processing transformers", top_k=2)

    top_text = results[0]["text"].lower()
    assert "language" in top_text or "transformer" in top_text


def test_retrieve_as_context(rag):
    context = rag.retrieve_as_context("What is FAISS?", top_k=2)

    assert "[Chunk 1]" in context
    assert "[Chunk 2]" in context
    assert len(context) > 50


def test_save_and_load_index(tmp_path, rag):
    save_path = str(tmp_path / "test_rag")
    rag.save_index(save_path)

    rag2 = RAGController()
    rag2.load_index(save_path)

    results = rag2.retrieve("embeddings and vectors", top_k=2)
    assert len(results) == 2