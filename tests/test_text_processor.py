import pytest
from services.text_processor import TextProcessor


@pytest.fixture
def processor():
    return TextProcessor()


def test_clean_text_removes_extra_spaces(processor):
    dirty = "Hello   World!!!\n\n\nThis   is   a   test."
    clean = processor.clean_text(dirty)

    assert "  " not in clean
    assert clean.startswith("Hello")
    assert clean.endswith("test.")


def test_clean_text_handles_empty_string(processor):
    clean = processor.clean_text("")
    assert clean == ""


def test_chunk_text_structure(processor):
    text = "This is a sentence. " * 100
    chunks = processor.chunk_text(text)

    assert len(chunks) > 1

    for i, chunk in enumerate(chunks):
        assert "chunk_id" in chunk
        assert "text" in chunk
        assert "char_start" in chunk
        assert "char_end" in chunk
        assert chunk["char_start"] < chunk["char_end"]
        assert chunk["chunk_id"] == i


def test_chunk_text_overlap_behavior(processor):
    text = "This is a sentence. " * 200
    chunks = processor.chunk_text(text)

    if len(chunks) > 1:
        assert chunks[1]["char_start"] < chunks[0]["char_end"]


def test_small_text_creates_single_chunk(processor):
    small_text = "Short text example."
    chunks = processor.chunk_text(small_text)

    assert len(chunks) <= 1


def test_process_text_pipeline(processor):
    sample = "Natural language processing is a field of AI. " * 50
    chunks = processor.process_text(sample)

    assert len(chunks) >= 1
    assert isinstance(chunks, list)
    