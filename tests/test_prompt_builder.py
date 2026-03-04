import pytest
from services.prompt_builder import PromptBuilder

SAMPLE_CONTEXT = """
Transformers are a neural network architecture introduced in 2017.
They use a mechanism called self-attention to process sequences.
BERT is a transformer model trained for language understanding.
GPT is a transformer model trained for language generation.
"""


def test_mcq_prompt_builds():
    prompt, system = (
        PromptBuilder()
        .set_context(SAMPLE_CONTEXT)
        .set_question_type("MCQ")
        .set_difficulty("medium")
        .set_num_questions(3)
        .build()
    )
    assert "CONTEXT:" in prompt
    assert '"answer"' in prompt
    assert '"options"' in prompt


def test_true_false_prompt_builds():
    prompt, system = (
        PromptBuilder()
        .set_context(SAMPLE_CONTEXT)
        .set_question_type("true_false")
        .set_difficulty("easy")
        .set_num_questions(2)
        .build()
    )
    assert "true" in prompt.lower() or "false" in prompt.lower()
    assert "CONTEXT:" in prompt


def test_short_answer_prompt_builds():
    prompt, system = (
        PromptBuilder()
        .set_context(SAMPLE_CONTEXT)
        .set_question_type("short_answer")
        .set_difficulty("hard")
        .set_num_questions(2)
        .build()
    )
    assert "key_points" in prompt
    assert "CONTEXT:" in prompt


def test_arabic_language():
    prompt, system = (
        PromptBuilder()
        .set_context(SAMPLE_CONTEXT)
        .set_question_type("MCQ")
        .set_difficulty("easy")
        .set_num_questions(2)
        .set_language("arabic")
        .build()
    )
    assert "Arabic" in system


def test_invalid_question_type_raises():
    with pytest.raises(ValueError):
        PromptBuilder().set_question_type("invalid_type")


def test_invalid_difficulty_raises():
    with pytest.raises(ValueError):
        PromptBuilder().set_difficulty("super_hard")


def test_empty_context_raises():
    with pytest.raises(ValueError):
        PromptBuilder().set_question_type("MCQ").build()